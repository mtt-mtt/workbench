/** @odoo-module **/

import {
    buildCommandQueueStatus,
    buildQueueContext,
    buildSeedTimelineEntries,
    matchQueueSelection,
    normalizeActivityEntry,
    normalizeShopfloorEnvelope,
} from "../utils/shopfloor_payload";

function buildSampleQueue(workstationCode) {
    const prefix = workstationCode || "WS-000";
    return [
        {
            id: `${prefix}-WO-001`,
            workorder_id: 1,
            production_id: 10,
            name: "Assembly order A",
            product: "Module A",
            workorder: "Cutting",
            workorder_ref: `${prefix}-WO-001`,
            production_ref: `${prefix}-MO-001`,
            quantity: 120,
            done: 24,
            priority: "High",
            status: "ready",
            progress: "24 / 120",
            reference: `${prefix}-REF-001`,
        },
        {
            id: `${prefix}-WO-002`,
            workorder_id: 2,
            production_id: 11,
            name: "Assembly order B",
            product: "Module B",
            workorder: "Wiring",
            workorder_ref: `${prefix}-WO-002`,
            production_ref: `${prefix}-MO-002`,
            quantity: 80,
            done: 60,
            priority: "Normal",
            status: "in_progress",
            progress: "60 / 80",
            reference: `${prefix}-REF-002`,
        },
        {
            id: `${prefix}-WO-003`,
            workorder_id: 3,
            production_id: 12,
            name: "Assembly order C",
            product: "Module C",
            workorder: "Inspection",
            workorder_ref: `${prefix}-WO-003`,
            production_ref: `${prefix}-MO-003`,
            quantity: 50,
            done: 12,
            priority: "Low",
            status: "waiting",
            progress: "12 / 50",
            reference: `${prefix}-REF-003`,
        },
    ];
}

function buildSampleDevices() {
    return [
        {
            code: "PLC-01",
            name: "Line PLC",
            kind: "PLC",
            state: "ready",
            signal: "machine_ready",
            value: "1",
            lastSeen: "just now",
            channel: "mqtt/line/plc",
            location: "Line A",
        },
        {
            code: "PRN-01",
            name: "Label Printer",
            kind: "Printer",
            state: "ready",
            signal: "print_ready",
            value: "idle",
            lastSeen: "just now",
            channel: "usb/print-1",
            location: "Line A",
        },
        {
            code: "SCN-01",
            name: "Scanner",
            kind: "Scanner",
            state: "ready",
            signal: "scan_focus",
            value: "active",
            lastSeen: "just now",
            channel: "usb/scan-1",
            location: "Line A",
        },
        {
            code: "SCL-01",
            name: "Scale",
            kind: "Scale",
            state: "degraded",
            signal: "weight_stable",
            value: "unstable",
            lastSeen: "2 min ago",
            channel: "modbus/scale-1",
            location: "Line B",
        },
    ];
}

function buildSampleExceptions() {
    return [
        {
            id: "EXC-001",
            title: "Missing barcode scan",
            severity: "medium",
            state: "new",
            source: "Execution",
            details: "Scan is required before completing the current step",
        },
    ];
}

function buildSampleLogs(workstationCode) {
    const prefix = workstationCode || "WS-000";
    return [
        {
            id: `${prefix}-LOG-1`,
            title: "Frontend shell loaded",
            detail: "Waiting for the first backend payload",
            kind: "boot",
            status: "info",
            timestamp: null,
        },
        {
            id: `${prefix}-LOG-2`,
            title: "Seed state active",
            detail: "Queue, devices, and exceptions use local fallback data until the backend responds",
            kind: "seed",
            status: "info",
            timestamp: null,
        },
    ];
}

function buildIdleResponseSummary() {
    return {
        headline: "Awaiting backend payload",
        label: "Awaiting backend payload",
        detail: "Seed state active",
        state: "idle",
        stateKey: "idle",
        stateLabel: "Idle",
        stateTone: "secondary",
        tone: "secondary",
        protocolRuntimeAttention: 0,
        protocolRuntimeState: "idle",
        protocolRuntimeTone: "secondary",
        protocolRuntimeLabel: "Protocol runtime waiting",
        protocolRuntimeDetail: "Protocol runtime shared summary will appear after backend payloads load.",
        protocolRuntimeStateKey: "idle",
        protocolRuntimeStateLabel: "Idle",
        protocolRuntimeStateSummary: "Protocol runtime shared summary will appear after backend payloads load.",
        ok: null,
        message: null,
        nextPage: null,
    };
}

function buildIdleCommandQueueStatus() {
    return buildCommandQueueStatus([]);
}

function buildIdleGatewayRuntimeSummary() {
    return {
        state: "secondary",
        stateKey: "secondary",
        stateLabel: "Secondary",
        stateTone: "secondary",
        label: "Driver diagnostics waiting",
        detail: "Runtime diagnostics have not been loaded yet.",
        summary: "No runtime diagnostics loaded yet.",
        adapterCount: 0,
        protocolRuntimeCount: 0,
        protocolRuntimeEntryCount: 0,
        protocolRuntimeState: "idle",
        protocolRuntimeStateCounts: {
            ready: 0,
            attention: 0,
            error: 0,
            pending: 0,
            unavailable: 0,
        },
        protocolRuntimeSummary: null,
        issueCounts: {
            total: 0,
            open: 0,
            resolved: 0,
            adapters: 0,
            openAdapters: 0,
        },
        driverCounts: {
            ready: 0,
            attention: 0,
            error: 0,
            unknown: 0,
        },
        edgeActionCounts: {
            total: 0,
            pending: 0,
            processing: 0,
            processed: 0,
            adapters: 0,
            processingAdapters: 0,
        },
        edgeActionSummary: null,
        edgeReplay: {
            pending: 0,
            adapters: 0,
            summary: null,
        },
        edgeDeadLetter: {
            count: 0,
            adapters: 0,
            summary: null,
        },
    };
}

function sortByNewest(list) {
    return (Array.isArray(list) ? list : [])
        .map((entry, index) => ({
            entry,
            index,
            timestamp: Date.parse(entry?.createdAt || entry?.created_at || entry?.updated_at || entry?.timestamp || 0) || 0,
        }))
        .sort((left, right) => {
            if (left.timestamp !== right.timestamp) {
                return right.timestamp - left.timestamp;
            }
            return right.index - left.index;
        })
        .map(({ entry }) => entry);
}

function isSeedMode(state) {
    return !state?.lastResponse;
}

function hasRealRecords(list = [], emptyCode = null) {
    return Array.isArray(list) && list.some((item) => !emptyCode || item?.code !== emptyCode);
}

function buildShellState(state, route = null) {
    const panel = route || state?.activeExecutionTab || "dashboard";
    const connectivity = state?.connectivity || {};
    const status = connectivity.status || "seed";
    const waitingBoot = !state?.booted && !state?.bootError;
    const seedMode = isSeedMode(state);

    let banner = null;
    if (waitingBoot) {
        banner = {
            label: "Booting",
            detail: "Preparing workstation state and loading the first payload.",
            tone: "info",
            visible: true,
        };
    } else if (status === "offline") {
        banner = {
            label: "Offline fallback",
            detail: connectivity.lastError || "Backend is unavailable. Showing the last known or local seed state.",
            tone: "danger",
            visible: true,
        };
    } else if (status === "degraded") {
        banner = {
            label: "Weak link",
            detail: connectivity.lastError || "State refresh failed. Keeping the current shell until the next successful sync.",
            tone: "warning",
            visible: true,
        };
    } else if (status === "recovered") {
        banner = {
            label: "Recovered",
            detail: connectivity.lastRecoveryLabel || "Connection restored. Live updates are active again.",
            tone: "info",
            visible: true,
        };
    } else if (seedMode) {
        banner = {
            label: "Seed mode",
            detail: "Backend payload not loaded yet. Local fallback data is still driving the workbench.",
            tone: "secondary",
            visible: true,
        };
    }

    const panelHints = {
        queue: !state?.queue?.length
            ? {
                  label: "Queue empty",
                  detail: "No work orders are visible for the current workstation.",
                  tone: "secondary",
                  visible: true,
              }
            : null,
        devices: !hasRealRecords(state?.devices, "DEVICE-EMPTY")
            ? {
                  label: "No devices linked",
                  detail: "No real device snapshot is available for the current workstation.",
                  tone: "secondary",
                  visible: true,
              }
            : null,
        exceptions: !state?.exceptions?.length
            ? {
                  label: "No active exceptions",
                  detail: "The exception lane is clear for the current context.",
                  tone: "info",
                  visible: true,
              }
            : null,
        execution: !state?.selectedQueueContext?.id
            ? {
                  label: "No execution selected",
                  detail: "Pick a queue item to inspect or execute a work order.",
                  tone: "secondary",
                  visible: true,
              }
            : null,
        dashboard: seedMode
            ? {
                  label: "Seed overview",
                  detail: "Dashboard metrics still come from the local shell fallback.",
                  tone: "secondary",
                  visible: true,
              }
            : null,
    };

    return {
        status,
        seedMode,
        summaryLabel:
            status === "offline"
                ? "Offline"
                : status === "degraded"
                  ? "Degraded"
                  : status === "recovered"
                    ? "Recovered"
                    : seedMode
                      ? "Seed"
                      : "Live",
        banner,
        panel: panelHints[panel] || null,
    };
}

function buildLogEntries(normalized, activity = []) {
    const entries = [];

    if (normalized?.responseSummary) {
        entries.push({
            id: `log-response-${Date.now()}`,
            title: normalized.responseSummary.label || normalized.responseSummary.headline || "Backend response",
            label: normalized.responseSummary.label || normalized.responseSummary.headline || "Backend response",
            detail: normalized.responseSummary.detail || null,
            kind: "response",
            status: normalized.responseSummary.stateTone || normalized.responseSummary.state || "info",
            statusKey: normalized.responseSummary.stateKey || normalized.responseSummary.state || "info",
            statusLabel: normalized.responseSummary.stateLabel || normalized.responseSummary.state || "Info",
            statusTone: normalized.responseSummary.stateTone || normalized.responseSummary.state || "info",
            timestamp: null,
        });
    }

    if (normalized?.messageText) {
        entries.push({
            id: `log-message-${Date.now()}`,
            title: "Message",
            label: "Message",
            detail: normalized.messageText,
            kind: "message",
            status: "info",
            statusKey: "info",
            statusLabel: "Info",
            statusTone: "info",
            timestamp: null,
        });
    }

    if (normalized?.commandQueueStatus) {
        entries.push({
            id: `log-queue-${Date.now()}`,
            title: normalized.commandQueueStatus.label || "Command queue",
            label: normalized.commandQueueStatus.label || "Command queue",
            detail: normalized.commandQueueStatus.detail || null,
            kind: "queue",
            status: normalized.commandQueueStatus.stateTone || normalized.commandQueueStatus.state || "idle",
            statusKey: normalized.commandQueueStatus.stateKey || normalized.commandQueueStatus.state || "idle",
            statusLabel: normalized.commandQueueStatus.stateLabel || normalized.commandQueueStatus.state || "Idle",
            statusTone: normalized.commandQueueStatus.stateTone || normalized.commandQueueStatus.state || "idle",
            timestamp: normalized.commandQueueStatus.lastUpdated || null,
        });
    }

    if (normalized?.gatewayRuntimeSummary?.summary || normalized?.gatewayRuntimeSummary?.detail) {
        entries.push({
            id: `log-runtime-${Date.now()}`,
            title: normalized.gatewayRuntimeSummary.label || "Driver diagnostics",
            label: normalized.gatewayRuntimeSummary.label || "Driver diagnostics",
            detail: normalized.gatewayRuntimeSummary.detail || normalized.gatewayRuntimeSummary.summary || null,
            kind: "runtime",
            status: normalized.gatewayRuntimeSummary.stateTone || normalized.gatewayRuntimeSummary.state || "info",
            statusKey: normalized.gatewayRuntimeSummary.stateKey || normalized.gatewayRuntimeSummary.state || "info",
            statusLabel: normalized.gatewayRuntimeSummary.stateLabel || normalized.gatewayRuntimeSummary.state || "Info",
            statusTone: normalized.gatewayRuntimeSummary.stateTone || normalized.gatewayRuntimeSummary.state || "info",
            timestamp: null,
        });
    }

    const protocolRuntimeStateCounts =
        normalized?.gatewayRuntimeSummary?.protocolRuntimeStateCounts ||
        normalized?.gatewayRuntimeSummary?.protocolRuntime?.stateCounts ||
        {};
    const protocolRuntimeCount = Number(
        normalized?.gatewayRuntimeSummary?.protocolRuntimeCount || normalized?.gatewayRuntimeSummary?.protocolRuntime?.count || 0
    );
    const protocolRuntimeEntryCount = Number(
        normalized?.gatewayRuntimeSummary?.protocolRuntimeEntryCount || normalized?.gatewayRuntimeSummary?.protocolRuntime?.entryCount || 0
    );
    const protocolRuntimeSummary =
        normalized?.gatewayRuntimeSummary?.protocolRuntimeSummary || normalized?.gatewayRuntimeSummary?.protocolRuntime?.summary || null;
    const protocolRuntimeState = String(
        normalized?.gatewayRuntimeSummary?.protocolRuntimeState ||
            normalized?.gatewayRuntimeSummary?.protocolRuntime?.state ||
            normalized?.gatewayRuntimeSummary?.protocolRuntime?.stateKey ||
            ""
    )
        .trim()
        .toLowerCase();
    const protocolRuntimeErrorCount = Number(protocolRuntimeStateCounts.error || 0);
    const protocolRuntimePendingCount = Number(protocolRuntimeStateCounts.pending || 0);
    const protocolRuntimeUnavailableCount = Number(protocolRuntimeStateCounts.unavailable || 0);
    const protocolRuntimeReadyCount = Number(protocolRuntimeStateCounts.ready || 0);
    const protocolRuntimeAttention = Math.max(
        protocolRuntimeErrorCount + protocolRuntimePendingCount + protocolRuntimeUnavailableCount,
        protocolRuntimeState === "error" || protocolRuntimeState === "attention"
            ? Number(protocolRuntimeCount || protocolRuntimeEntryCount || 0)
            : 0
    );
    const protocolRuntimePrimaryCount =
        protocolRuntimeAttention || protocolRuntimeReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount || 0;
    if (protocolRuntimeState === "error" || protocolRuntimeErrorCount > 0) {
        entries.push({
            id: `log-protocol-runtime-${Date.now()}`,
            title: "Protocol runtime error",
            label: "Protocol runtime error",
            detail:
                protocolRuntimeSummary ||
                `${protocolRuntimeErrorCount || protocolRuntimePrimaryCount} protocol runtime(s) are reporting errors.`,
            kind: "protocol-runtime",
            status: "danger",
            statusKey: "danger",
            statusLabel: "Danger",
            statusTone: "danger",
            timestamp: null,
        });
    } else if (protocolRuntimeAttention > 0 || protocolRuntimeState === "attention") {
        entries.push({
            id: `log-protocol-runtime-${Date.now()}`,
            title: "Protocol runtime attention",
            label: "Protocol runtime attention",
            detail:
                protocolRuntimeSummary || `${protocolRuntimeAttention || protocolRuntimePrimaryCount} protocol runtime(s) need follow-up.`,
            kind: "protocol-runtime",
            status: "warning",
            statusKey: "warning",
            statusLabel: "Warning",
            statusTone: "warning",
            timestamp: null,
        });
    } else if (protocolRuntimeSummary || protocolRuntimeCount || protocolRuntimeEntryCount || protocolRuntimeReadyCount > 0) {
        entries.push({
            id: `log-protocol-runtime-${Date.now()}`,
            title: "Protocol runtime ready",
            label: "Protocol runtime ready",
            detail:
                protocolRuntimeSummary ||
                `${protocolRuntimeReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`,
            kind: "protocol-runtime",
            status: "success",
            statusKey: "success",
            statusLabel: "Success",
            statusTone: "success",
            timestamp: null,
        });
    }

    sortByNewest(normalized?.commands).slice(0, 3).forEach((command, index) => {
        entries.push({
            id: `log-command-${index}-${command.id || Date.now()}`,
            title: command.label || command.name || "Command",
            label: command.label || command.name || "Command",
            detail: `${command.type || "command"} - ${command.statusLabel || command.status || "Queued"}`,
            kind: "command",
            status: command.statusTone || command.status || "queued",
            statusKey: command.statusKey || command.status || "queued",
            statusLabel: command.statusLabel || command.status || "Queued",
            statusTone: command.statusTone || command.status || "queued",
            timestamp: command.createdAt || null,
        });
    });

    sortByNewest(normalized?.exceptions).slice(0, 2).forEach((exception, index) => {
        entries.push({
            id: `log-exception-${index}-${exception.id || Date.now()}`,
            title: exception.label || exception.title || "Exception",
            label: exception.label || exception.title || "Exception",
            detail: `${exception.severityLabel || exception.severity || "Medium"} - ${exception.stateLabel || exception.state || "New"}`,
            kind: "exception",
            status: exception.stateTone || exception.severityTone || exception.state || "medium",
            statusKey: exception.stateKey || exception.state || "new",
            statusLabel: exception.stateLabel || exception.state || "New",
            statusTone: exception.stateTone || exception.severityTone || exception.state || "medium",
            timestamp: exception.createdAt || null,
        });
    });

    activity.slice(0, 4).forEach((entry, index) => {
        const normalizedActivity = normalizeActivityEntry(entry, index);
        entries.push({
            id: normalizedActivity.id || `log-activity-${index}-${Date.now()}`,
            title: normalizedActivity.title,
            label: normalizedActivity.label,
            detail: normalizedActivity.detail,
            kind: normalizedActivity.kind || "activity",
            status: normalizedActivity.status || "info",
            statusKey: normalizedActivity.statusKey || normalizedActivity.status || "info",
            statusLabel: normalizedActivity.statusLabel || normalizedActivity.status || "Info",
            statusTone: normalizedActivity.statusTone || normalizedActivity.status || "info",
            timestamp: normalizedActivity.timestamp || null,
        });
    });

    return entries.slice(0, 12);
}

function refreshDerivedState(state, preservedMetricKeys = []) {
    const protocolRuntime = state.gatewayRuntimeSummary?.protocolRuntime || {};
    const protocolRuntimeStateCounts = state.gatewayRuntimeSummary?.protocolRuntimeStateCounts || state.gatewayRuntimeSummary?.protocolRuntime?.stateCounts || {};
    const protocolRuntimeCount = Number(state.gatewayRuntimeSummary?.protocolRuntimeCount || protocolRuntime.count || 0);
    const protocolRuntimeEntryCount = Number(state.gatewayRuntimeSummary?.protocolRuntimeEntryCount || protocolRuntime.entryCount || 0);
    const protocolRuntimeSummary = state.gatewayRuntimeSummary?.protocolRuntimeSummary || protocolRuntime.summary || null;
    const protocolRuntimeState = String(
        state.gatewayRuntimeSummary?.protocolRuntimeState ||
            state.gatewayRuntimeSummary?.protocolRuntime?.state ||
            state.gatewayRuntimeSummary?.protocolRuntime?.stateKey ||
            ""
    )
        .trim()
        .toLowerCase();
    const protocolRuntimeErrorCount = Number(protocolRuntimeStateCounts.error || 0);
    const protocolRuntimePendingCount = Number(protocolRuntimeStateCounts.pending || 0);
    const protocolRuntimeUnavailableCount = Number(protocolRuntimeStateCounts.unavailable || 0);
    const protocolRuntimeReadyCount = Number(protocolRuntimeStateCounts.ready || 0);
    const protocolRuntimeAttention = Math.max(
        protocolRuntimeErrorCount + protocolRuntimePendingCount + protocolRuntimeUnavailableCount,
        protocolRuntimeState === "error" || protocolRuntimeState === "attention"
            ? Number(protocolRuntimeCount || protocolRuntimeEntryCount || 0)
            : 0
    );
    const protocolRuntimePrimaryCount =
        protocolRuntimeAttention || protocolRuntimeReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount || 0;
    let sharedProtocolRuntimeState = "idle";
    let sharedProtocolRuntimeTone = "secondary";
    let sharedProtocolRuntimeHeadline = null;
    let sharedProtocolRuntimeLabel = null;
    let sharedProtocolRuntimeDetail = null;

    if (protocolRuntimeState === "error" || protocolRuntimeErrorCount > 0) {
        sharedProtocolRuntimeState = "error";
        sharedProtocolRuntimeTone = "danger";
        sharedProtocolRuntimeHeadline = "Protocol runtime error";
        sharedProtocolRuntimeLabel = `Protocol error ${protocolRuntimeErrorCount || protocolRuntimePrimaryCount}`;
        sharedProtocolRuntimeDetail =
            protocolRuntimeSummary ||
            `${protocolRuntimeErrorCount || protocolRuntimePrimaryCount} protocol runtime(s) are reporting errors.`;
    } else if (protocolRuntimeAttention > 0 || protocolRuntimeState === "attention") {
        sharedProtocolRuntimeState = "attention";
        sharedProtocolRuntimeTone = "warning";
        sharedProtocolRuntimeHeadline = "Protocol runtime attention";
        sharedProtocolRuntimeLabel = `Protocol attention ${protocolRuntimeAttention || protocolRuntimePrimaryCount}`;
        sharedProtocolRuntimeDetail =
            protocolRuntimeSummary ||
            `${protocolRuntimeAttention || protocolRuntimePrimaryCount} protocol runtime(s) need follow-up.`;
    } else if (protocolRuntimeSummary || protocolRuntimeCount || protocolRuntimeEntryCount || protocolRuntimeReadyCount > 0) {
        sharedProtocolRuntimeState = "ready";
        sharedProtocolRuntimeTone = "success";
        sharedProtocolRuntimeHeadline = "Protocol runtime ready";
        sharedProtocolRuntimeLabel = `Protocol ready ${protocolRuntimeReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount}`;
        sharedProtocolRuntimeDetail =
            protocolRuntimeSummary ||
            `${protocolRuntimeReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`;
    }

    const derivedMetrics = {
        pendingJobs: state.queue.filter((item) => item.status !== "done").length,
        activeExceptions: state.exceptions.filter((item) => item.state !== "resolved" && item.state !== "closed").length,
        deviceOnline: state.devices.some((device) => device.state !== "offline" && device.state !== "error"),
        driverIssueOpen: state.gatewayRuntimeSummary?.issueCounts?.open || 0,
        driverIssueAdapters: state.gatewayRuntimeSummary?.issueCounts?.openAdapters || 0,
        protocolRuntimeAttention,
        protocolRuntimeState: sharedProtocolRuntimeState,
        protocolRuntimeTone: sharedProtocolRuntimeTone,
        protocolRuntimeLabel: sharedProtocolRuntimeLabel,
        protocolRuntimeDetail: sharedProtocolRuntimeDetail,
        edgeActionProcessing: state.gatewayRuntimeSummary?.edgeActionCounts?.processing || 0,
        lastSync: new Date().toLocaleTimeString(),
    };

    if (state.responseSummary && typeof state.responseSummary === "object") {
        const responseHeadline = String(state.responseSummary.headline || state.responseSummary.label || "")
            .trim()
            .toLowerCase();
        const responseFeedbackLabel = String(state.responseSummary.feedbackLabel || "").trim().toLowerCase();
        const responseSummaryProtected =
            Number(state.gatewayRuntimeSummary?.issueCounts?.open || 0) > 0 ||
            Number(state.gatewayRuntimeSummary?.edgeDeadLetter?.count || 0) > 0 ||
            Number(state.gatewayRuntimeSummary?.edgeReplay?.pending || 0) > 0 ||
            Number(state.gatewayRuntimeSummary?.edgeReplay?.due || 0) > 0 ||
            Number(state.gatewayRuntimeSummary?.edgeActionCounts?.processing || 0) > 0 ||
            [
                "attention required",
                "command failure detected",
                "driver issues open",
                "edge dead letters present",
                "edge replay pending",
                "edge replay cooling down",
                "edge actions processing",
                "operator follow-up pending",
            ].includes(responseHeadline) ||
            [
                "driver issues open",
                "edge dead letters present",
                "edge replay pending",
                "edge replay cooling down",
                "edge actions processing",
            ].includes(responseFeedbackLabel);
        const responseStateKeyByTone = {
            danger: "danger",
            warning: "warning",
            success: "success",
            info: "info",
            secondary: "secondary",
        };
        const responseStateLabelByKey = {
            danger: "Danger",
            warning: "Warning",
            success: "Success",
            info: "Info",
            secondary: "Secondary",
        };
        state.responseSummary = {
            ...state.responseSummary,
            protocolRuntimeAttention,
            protocolRuntimeState: sharedProtocolRuntimeState,
            protocolRuntimeTone: sharedProtocolRuntimeTone,
            protocolRuntimeLabel: sharedProtocolRuntimeLabel,
            protocolRuntimeDetail: sharedProtocolRuntimeDetail,
            protocolRuntimeStateKey: sharedProtocolRuntimeState,
            protocolRuntimeStateLabel: sharedProtocolRuntimeLabel,
            protocolRuntimeStateSummary: sharedProtocolRuntimeDetail,
            ...(!responseSummaryProtected && sharedProtocolRuntimeHeadline
                ? {
                      headline: sharedProtocolRuntimeHeadline,
                      label: sharedProtocolRuntimeHeadline,
                      detail: sharedProtocolRuntimeDetail || state.responseSummary.detail,
                      state: responseStateKeyByTone[sharedProtocolRuntimeTone] || sharedProtocolRuntimeTone,
                      stateKey: responseStateKeyByTone[sharedProtocolRuntimeTone] || sharedProtocolRuntimeTone,
                      stateLabel:
                          responseStateLabelByKey[responseStateKeyByTone[sharedProtocolRuntimeTone] || sharedProtocolRuntimeTone] || "Info",
                      stateTone: sharedProtocolRuntimeTone,
                      tone: sharedProtocolRuntimeTone,
                      feedbackLabel: sharedProtocolRuntimeLabel || sharedProtocolRuntimeHeadline,
                      feedbackDetail: sharedProtocolRuntimeDetail || state.responseSummary.feedbackDetail,
                  }
                : {}),
        };
    }

    if (Array.isArray(state.timeline) && state.timeline.length) {
        state.timeline = state.timeline.map((entry) => {
            if (!entry || typeof entry !== "object") {
                return entry;
            }
            const isProtocolRuntimeEntry =
                entry.id === "timeline-runtime-protocol" ||
                (entry.kind === "runtime" && String(entry.title || entry.label || "").toLowerCase().includes("protocol runtime"));
            if (!isProtocolRuntimeEntry) {
                return entry;
            }
            return {
                ...entry,
                status: sharedProtocolRuntimeState,
                statusKey: sharedProtocolRuntimeState,
                statusLabel: sharedProtocolRuntimeLabel || entry.statusLabel || "Info",
                statusTone: sharedProtocolRuntimeTone,
                title: sharedProtocolRuntimeLabel || entry.title || "Protocol runtime",
                label: sharedProtocolRuntimeLabel || entry.label || "Protocol runtime",
                detail: sharedProtocolRuntimeDetail || entry.detail || null,
            };
        });
    }

    const nextMetrics = { ...state.metrics };
    for (const [key, value] of Object.entries(derivedMetrics)) {
        if (!preservedMetricKeys.includes(key)) {
            nextMetrics[key] = value;
        }
    }
    state.metrics = nextMetrics;
}

function applyNormalizedEnvelope(state, router, normalized, fallbackActivity = []) {
    if (normalized?.workstation && typeof normalized.workstation === "object") {
        state.workstation = {
            ...state.workstation,
            ...normalized.workstation,
        };
    }

    if (normalized?.currentUserName) {
        state.currentUser = {
            ...state.currentUser,
            name: normalized.currentUserName,
        };
    }

    if (normalized?.sessionRef) {
        state.sessionRef = normalized.sessionRef;
    }

    if (normalized?.execution && typeof normalized.execution === "object") {
        state.execution = {
            ...state.execution,
            ...normalized.execution,
        };
    }

    if (normalized?.queue?.length) {
        state.queue = normalized.queue;
        if (
            !state.selectedQueueId ||
            !state.queue.some((item) => String(item.id) === String(state.selectedQueueId) || String(item.queue_id) === String(state.selectedQueueId))
        ) {
            state.selectedQueueId = state.queue[0]?.queue_id || state.queue[0]?.id || null;
        }
    }

    if (normalized?.devices?.length) {
        state.devices = normalized.devices;
        if (!state.selectedDeviceCode || !state.devices.some((item) => item.code === state.selectedDeviceCode)) {
            state.selectedDeviceCode = state.devices[0]?.code || null;
        }
    }

    if (normalized?.exceptions?.length) {
        state.exceptions = normalized.exceptions;
    }

    if (normalized?.commands?.length) {
        state.commands = normalized.commands;
    }

    if (normalized?.timeline?.length) {
        state.timeline = normalized.timeline;
    }

    if (Array.isArray(normalized?.activity) && normalized.activity.length) {
        state.activity = normalized.activity;
    }

    if (normalized?.responseSummary) {
        state.responseSummary = normalized.responseSummary;
    }

    if (normalized?.commandQueueStatus) {
        state.commandQueueStatus = normalized.commandQueueStatus;
    }

    if (normalized?.gatewayRuntimeSummary && typeof normalized.gatewayRuntimeSummary === "object") {
        state.gatewayRuntimeSummary = normalized.gatewayRuntimeSummary;
    }

    if (normalized?.metrics && typeof normalized.metrics === "object") {
        state.metrics = {
            ...state.metrics,
            ...normalized.metrics,
        };
    }

    if (normalized?.nextState?.page || normalized?.nextState?.route) {
        const nextRoute = normalized.nextState.page || normalized.nextState.route;
        router.go(nextRoute);
        state.activeExecutionTab = nextRoute;
    }

    state.logs = buildLogEntries(normalized, fallbackActivity.length ? fallbackActivity : state.activity);
    refreshDerivedState(state, normalized?.metrics ? Object.keys(normalized.metrics) : []);
}

export function createShopfloorStateService() {
    return {
        buildSampleQueue,
        buildSampleDevices,
        buildSampleExceptions,
        buildSampleLogs,
        buildIdleResponseSummary,
        buildIdleCommandQueueStatus,
        buildIdleGatewayRuntimeSummary,
        buildCommandQueueStatus,
        buildShellState,
        buildLogEntries,
        refreshDerivedState,
        applyNormalizedEnvelope,
        buildQueueContext,
        matchQueueSelection,
        buildSeedTimelineEntries,
        normalizeShopfloorEnvelope,
    };
}
