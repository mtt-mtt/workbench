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

function compareEntryRecency(left, right) {
    if (left.timestamp !== right.timestamp) {
        return right.timestamp - left.timestamp;
    }
    return right.index - left.index;
}

export function sortGatewayCommands(commands) {
    const list = Array.isArray(commands) ? commands : [];
    return list
        .map((entry, index) => ({
            entry,
            index,
            state: resolveEntryState(entry),
            timestamp: extractTimestamp(entry),
        }))
        .sort(compareEntryRecency)
        .map(({ entry }) => entry);
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

function extractPrintExecution(entry) {
    const fromEntry = entry?.print_execution || entry?.printExecution || null;
    const fromSummary = entry?.summary?.print_execution || entry?.summary?.printExecution || null;
    const fromDiagnostic = entry?.diagnostic_summary?.print_execution || entry?.diagnostic_state?.print_execution || null;
    const fromResult = entry?.result?.print_execution || null;
    const execution = fromEntry || fromSummary || fromDiagnostic || fromResult || {};
    if (!execution || typeof execution !== "object") {
        return {};
    }
    return {
        serviceMode: execution.service_mode || execution.serviceMode || entry?.service_mode || entry?.serviceMode || null,
        executionMode: execution.execution_mode || execution.executionMode || entry?.execution_mode || entry?.executionMode || null,
        serviceJobId: execution.service_job_id || execution.serviceJobId || entry?.service_job_id || entry?.serviceJobId || null,
        serviceStatusCode:
            execution.service_status_code || execution.serviceStatusCode || entry?.service_status_code || entry?.serviceStatusCode || null,
        serviceErrorCode: execution.service_error_code || execution.serviceErrorCode || entry?.service_error_code || entry?.serviceErrorCode || null,
        serviceErrorDetail:
            execution.service_error_detail || execution.serviceErrorDetail || entry?.service_error_detail || entry?.serviceErrorDetail || null,
        serviceAcceptedAt: execution.service_accepted_at || execution.serviceAcceptedAt || entry?.service_accepted_at || entry?.serviceAcceptedAt || null,
        serviceCompletedAt: execution.service_completed_at || execution.serviceCompletedAt || entry?.service_completed_at || entry?.serviceCompletedAt || null,
        serviceStatusUrl:
            execution.service_status_url || execution.serviceStatusUrl || entry?.service_status_url || entry?.serviceStatusUrl || null,
        serviceCheckedAt:
            execution.service_checked_at || execution.serviceCheckedAt || entry?.service_checked_at || entry?.serviceCheckedAt || null,
        serviceDocumentUrl:
            execution.service_document_url || execution.serviceDocumentUrl || entry?.service_document_url || entry?.serviceDocumentUrl || null,
        servicePreviewUrl:
            execution.service_preview_url || execution.servicePreviewUrl || entry?.service_preview_url || entry?.servicePreviewUrl || null,
        servicePrinterCode:
            execution.service_printer_code || execution.servicePrinterCode || entry?.service_printer_code || entry?.servicePrinterCode || null,
        driverOrigin: execution.driver_origin || execution.driverOrigin || entry?.driver_origin || entry?.driverOrigin || null,
        driverReady: execution.driver_ready ?? execution.driverReady ?? entry?.driver_ready ?? entry?.driverReady ?? null,
        driverLabel: execution.driver_label || execution.driverLabel || entry?.driver_label || entry?.driverLabel || null,
        driverType: execution.driver_type || execution.driverType || entry?.driver_type || entry?.driverType || null,
        driverPath: execution.driver_path || execution.driverPath || entry?.driver_path || entry?.driverPath || null,
        driverCapabilities:
            execution.driver_capabilities || execution.driverCapabilities || entry?.driver_capabilities || entry?.driverCapabilities || {},
        printerStatus: execution.printer_status || execution.printerStatus || entry?.printer_status || entry?.printerStatus || null,
        printedCopies: execution.printed_copies || execution.printedCopies || entry?.printed_copies || entry?.printedCopies || null,
        executionState: execution.execution_state || execution.executionState || null,
        completed: execution.completed ?? null,
        terminal: execution.terminal ?? null,
        serviceSummary: execution.service_summary || execution.serviceSummary || entry?.service_summary || entry?.serviceSummary || null,
        result: execution.result || null,
        simulated: execution.simulated ?? null,
    };
}

function resolveExecutionTone(execution) {
    const state = String(execution?.executionState || execution?.state || execution?.result || "").trim().toLowerCase();
    if (["failed", "error", "rejected"].includes(state)) {
        return "danger";
    }
    if (["submitted", "acknowledged", "accepted", "queued", "pending", "processing", "running"].includes(state)) {
        return "warning";
    }
    if (["done", "completed", "success", "printed"].includes(state)) {
        return "success";
    }
    return "info";
}

function resolveExecutionBadgeText(execution) {
    if (!execution || !Object.keys(execution).length) {
        return null;
    }
    const parts = [
        execution.executionState ? `state ${execution.executionState}` : null,
        execution.serviceMode ? `mode ${execution.serviceMode}` : null,
        execution.executionMode ? `execution ${execution.executionMode}` : null,
        execution.driverOrigin ? `driver ${execution.driverOrigin}` : null,
        execution.driverReady === true ? "driver ready" : execution.driverReady === false ? "driver not ready" : null,
        execution.serviceJobId ? `job ${execution.serviceJobId}` : null,
        execution.serviceStatusCode !== null && execution.serviceStatusCode !== undefined ? `code ${execution.serviceStatusCode}` : null,
        execution.serviceErrorCode ? `error ${execution.serviceErrorCode}` : null,
        execution.printerStatus ? `printer ${execution.printerStatus}` : null,
        execution.servicePrinterCode ? `device ${execution.servicePrinterCode}` : null,
        execution.serviceCheckedAt ? `checked ${execution.serviceCheckedAt}` : null,
        execution.completed === true ? "completed" : execution.completed === false ? "pending" : null,
        execution.terminal === true ? "terminal" : execution.terminal === false ? "non-terminal" : null,
        execution.printedCopies !== null && execution.printedCopies !== undefined ? `${execution.printedCopies} copies` : null,
    ].filter(Boolean);
    return parts.length ? parts.join(" | ") : null;
}

function resolveExecutionDetailItems(execution) {
    if (!execution || !Object.keys(execution).length) {
        return [];
    }
    return [
        execution.executionState ? `state ${execution.executionState}` : null,
        execution.executionMode ? `execution ${execution.executionMode}` : null,
        execution.serviceMode ? `mode ${execution.serviceMode}` : null,
        execution.driverOrigin ? `driver ${execution.driverOrigin}` : null,
        execution.driverLabel ? `label ${execution.driverLabel}` : null,
        execution.driverType ? `type ${execution.driverType}` : null,
        execution.driverReady === true ? "driver ready" : execution.driverReady === false ? "driver not ready" : null,
        execution.driverCapabilities?.supports_refresh_status === true
            ? "refresh-status supported"
            : execution.driverCapabilities?.supports_refresh_status === false
              ? "refresh-status unavailable"
              : null,
        execution.driverCapabilities?.status_polling_supported === true
            ? "polling ready"
            : execution.driverCapabilities?.status_polling_supported === false
              ? "polling limited"
              : null,
        execution.serviceJobId ? `job ${execution.serviceJobId}` : null,
        execution.serviceStatusCode !== null && execution.serviceStatusCode !== undefined ? `code ${execution.serviceStatusCode}` : null,
        execution.serviceErrorCode ? `error ${execution.serviceErrorCode}` : null,
        execution.serviceErrorDetail ? execution.serviceErrorDetail : null,
        execution.serviceAcceptedAt ? `accepted ${execution.serviceAcceptedAt}` : null,
        execution.serviceCompletedAt ? `completed ${execution.serviceCompletedAt}` : null,
        execution.serviceStatusUrl ? `status ${execution.serviceStatusUrl}` : null,
        execution.serviceCheckedAt ? `checked ${execution.serviceCheckedAt}` : null,
        execution.serviceSummary ? execution.serviceSummary : null,
        execution.printerStatus ? `printer ${execution.printerStatus}` : null,
        execution.servicePrinterCode ? `device ${execution.servicePrinterCode}` : null,
        execution.printedCopies !== null && execution.printedCopies !== undefined ? `${execution.printedCopies} copies` : null,
        execution.serviceDocumentUrl ? "document ready" : null,
        execution.servicePreviewUrl ? "preview ready" : null,
    ]
        .filter(Boolean)
        .map((label, index) => ({
            key: `${index}-${label}`,
            label,
        }));
}

export function summarizeGatewayCommands(commands) {
    const list = Array.isArray(commands) ? commands : [];
    const normalized = sortGatewayCommands(list).map((entry, index) => ({
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
        if (!latest || item.timestamp > latest.timestamp || (item.timestamp === latest.timestamp && item.index < latest.index)) {
            latest = item;
        }
    }

    const latestEntry = latest?.entry || null;
    const latestState = latest?.state || "queued";
    const latestPrintExecution = extractPrintExecution(latestEntry);
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
        latestPrintExecution,
        latestPrintExecutionBadge: resolveExecutionBadgeText(latestPrintExecution),
        latestPrintExecutionDetails: resolveExecutionDetailItems(latestPrintExecution),
        latestPrintExecutionTone: resolveExecutionTone(latestPrintExecution),
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
        current.latestPrintExecutionBadge,
    ].filter((part) => String(part || "").trim());
    return {
        label: current.latestStateLabel || "Queued",
        tone: current.latestStateTone || "info",
        detail: detailParts.length ? detailParts.join(" | ") : "No gateway.command entries available yet.",
    };
}

export function latestGatewayCommand(commands) {
    const sorted = sortGatewayCommands(commands);
    return sorted.length ? sorted[0] : null;
}

export function normalizeGatewayCommandEntry(entry) {
    const state = resolveEntryState(entry);
    const printExecution = extractPrintExecution(entry);
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
        printExecution,
        printExecutionLabel: resolveExecutionBadgeText(printExecution),
        printExecutionDetails: resolveExecutionDetailItems(printExecution),
        printExecutionTone: resolveExecutionTone(printExecution),
    };
}
