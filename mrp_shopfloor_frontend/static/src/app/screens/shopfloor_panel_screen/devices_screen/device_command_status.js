/** @odoo-module **/

import {
    buildStatusSummaryItems,
    commandStateKey as normalizeCommandStateKey,
    commandStateLabel as getCommandStateLabel,
    commandStateTone as getCommandStateTone,
} from "../../../../../components/shopfloor_status_components/shopfloor_status_metrics";

const COMMAND_SUMMARY_DESCRIPTORS = [
    { key: "total", label: "Total", valueKey: "total", tone: "secondary" },
    { key: "queued", label: "Queued", valueKey: "queuedCount", tone: "info", emphasis: true },
    { key: "sent", label: "Sent", valueKey: "sentCount", tone: "warning" },
    { key: "acknowledged", label: "Acknowledged", valueKey: "acknowledgedCount", tone: "warning", emphasis: true },
    { key: "done", label: "Done", valueKey: "doneCount", tone: "success" },
    { key: "failed", label: "Failed", valueKey: "failedCount", tone: "danger", emphasis: true },
];

function normalizeKey(value, fallback = "queued") {
    return String(value || fallback).trim().replace(/\s+/g, "_").toLowerCase();
}

export function normalizeCommandState(value, fallback = "queued") {
    const key = normalizeKey(value, fallback);
    if (!key) {
        return fallback;
    }
    if (key.includes("queued") || key.includes("queue")) {
        return "queued";
    }
    if (key.includes("ack") || key.includes("confirm")) {
        return "acknowledged";
    }
    if (key.includes("sent") || key.includes("dispatch") || key.includes("publish")) {
        return "sent";
    }
    if (key.includes("done") || key.includes("complete") || key.includes("success") || key.includes("finished")) {
        return "done";
    }
    if (key.includes("fail") || key.includes("error") || key.includes("reject") || key.includes("cancel")) {
        return "failed";
    }
    if (key === "draft") {
        return "draft";
    }
    if (key === "pending" || key === "waiting") {
        return "queued";
    }
    if (key === "accepted" || key === "received") {
        return "acknowledged";
    }
    return key;
}

export function commandStateLabel(value) {
    return getCommandStateLabel(normalizeCommandStateKey(normalizeCommandState(value)));
}

export function commandStateTone(value) {
    return getCommandStateTone(normalizeCommandStateKey(normalizeCommandState(value)));
}

function extractTimestamp(entry) {
    const rawTimestamp =
        entry?.last_attempt_at ||
        entry?.processed_at ||
        entry?.updated_at ||
        entry?.create_date ||
        entry?.created_at ||
        entry?.createdAt ||
        entry?.timestamp ||
        null;
    if (!rawTimestamp) {
        return 0;
    }
    const parsed = Date.parse(rawTimestamp);
    return Number.isNaN(parsed) ? 0 : parsed;
}

function resolveEntryState(entry) {
    return normalizeCommandState(
        entry?.state ||
            entry?.status ||
            entry?.status_key ||
            entry?.statusKey ||
            entry?.command_state ||
            entry?.commandState ||
            entry?.queue_state ||
            entry?.feedback_state ||
            entry?.result ||
            entry?.commandResult ||
            entry?.gateway_state ||
            entry?.commandStatus ||
            entry?.state_code ||
            entry?.stateCode ||
            "queued"
    );
}

function resolveEntryLabel(entry) {
    return (
        entry?.name ||
        entry?.command_name ||
        entry?.commandName ||
        entry?.code ||
        entry?.command_type ||
        entry?.commandType ||
        entry?.signal_code ||
        entry?.signalCode ||
        entry?.type ||
        "Command"
    );
}

function resolveEntryDetail(entry) {
    return (
        entry?.detail ||
        entry?.description ||
        entry?.message ||
        entry?.feedback_message ||
        entry?.feedbackMessage ||
        entry?.note ||
        entry?.state_message ||
        entry?.stateMessage ||
        entry?.error_message ||
        entry?.errorMessage ||
        entry?.result_message ||
        entry?.resultMessage ||
        entry?.idempotency_key ||
        entry?.idempotencyKey ||
        entry?.entry_code ||
        entry?.entryCode ||
        entry?.signal_code ||
        entry?.signalCode ||
        entry?.command_type ||
        entry?.commandType ||
        entry?.code ||
        null
    );
}

function resolveEntryDeviceCode(entry) {
    return (
        entry?.device_code ||
        entry?.deviceCode ||
        entry?.device ||
        entry?.target_device_code ||
        entry?.targetDeviceCode ||
        entry?.target_device ||
        entry?.targetDevice ||
        entry?.target ||
        "n/a"
    );
}

function resolveEntryDeviceName(entry) {
    return (
        entry?.device_name ||
        entry?.deviceName ||
        entry?.device_label ||
        entry?.deviceLabel ||
        entry?.device_code ||
        entry?.deviceCode ||
        entry?.target_device_name ||
        entry?.targetDeviceName ||
        entry?.target_device_label ||
        entry?.targetDeviceLabel ||
        entry?.target ||
        "Gateway device"
    );
}

function resolveEntryCreatedAt(entry) {
    return (
        entry?.last_attempt_at ||
        entry?.lastAttemptAt ||
        entry?.processed_at ||
        entry?.processedAt ||
        entry?.updated_at ||
        entry?.updatedAt ||
        entry?.created_at ||
        entry?.createdAt ||
        entry?.timestamp ||
        "Queued"
    );
}

export function summarizeGatewayCommands(commands) {
    const list = Array.isArray(commands) ? commands : [];
    const normalized = list.map((entry, index) => ({
        entry,
        index,
        state: resolveEntryState(entry),
        timestamp: extractTimestamp(entry),
    }));

    const counts = {
        queuedCount: 0,
        sentCount: 0,
        acknowledgedCount: 0,
        doneCount: 0,
        failedCount: 0,
        cancelledCount: 0,
    };

    let latest = null;
    for (const item of normalized) {
        counts[`${item.state}Count`] = (counts[`${item.state}Count`] || 0) + 1;
        if (
            !latest ||
            item.timestamp > latest.timestamp ||
            (item.timestamp === latest.timestamp && item.index < latest.index)
        ) {
            latest = item;
        }
    }

    const latestEntry = latest?.entry || null;
    const latestState = latest?.state || "queued";
    return {
        total: list.length,
        ...counts,
        latestState,
        latestStateLabel: commandStateLabel(latestState),
        latestStateTone: commandStateTone(latestState),
        latestCommandLabel: resolveEntryLabel(latestEntry),
        latestCommandDetail: resolveEntryDetail(latestEntry),
        latestDeviceCode: resolveEntryDeviceCode(latestEntry),
        latestDeviceName: resolveEntryDeviceName(latestEntry),
        latestCreatedAt: resolveEntryCreatedAt(latestEntry),
    };
}

export function gatewayCommandSummaryItems(summary) {
    return buildStatusSummaryItems(summary || {}, COMMAND_SUMMARY_DESCRIPTORS);
}

export function gatewayCommandFeedback(summary) {
    const current = summary || {};
    const detailParts = [
        current.latestCommandLabel,
        current.latestDeviceName,
        current.latestDeviceCode,
        current.latestCommandDetail,
    ].filter((part) => String(part || "").trim());
    return {
        label: current.latestStateLabel || "Queued",
        tone: current.latestStateTone || "info",
        detail: detailParts.length ? detailParts.join(" | ") : "No gateway.command entries available yet.",
    };
}

export function normalizeGatewayCommandEntry(entry) {
    const state = resolveEntryState(entry);
    return {
        id:
            entry?.id ||
            entry?.code ||
            entry?.name ||
            entry?.command_type ||
            entry?.commandType ||
            entry?.signal_code ||
            entry?.signalCode ||
            entry?.device_code ||
            entry?.deviceCode ||
            `${state}-${extractTimestamp(entry) || 0}`,
        label: resolveEntryLabel(entry),
        command:
            entry?.command_type ||
            entry?.commandType ||
            entry?.code ||
            entry?.command ||
            entry?.command_name ||
            entry?.commandName ||
            entry?.signal_code ||
            entry?.signalCode ||
            entry?.type ||
            "custom",
        status: state,
        statusLabel: commandStateLabel(state),
        tone: commandStateTone(state),
        detail: resolveEntryDetail(entry) || "Queued on backend",
        deviceCode: resolveEntryDeviceCode(entry),
        deviceName: resolveEntryDeviceName(entry),
        createdAt: resolveEntryCreatedAt(entry),
    };
}
