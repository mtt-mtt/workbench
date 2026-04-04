/** @odoo-module **/

import {
    buildCommandQueueStatus,
    buildQueueContext,
    buildSeedTimelineEntries,
    matchQueueSelection,
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
        ok: null,
        message: null,
        nextPage: null,
    };
}

function buildIdleCommandQueueStatus() {
    return buildCommandQueueStatus([]);
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

    (normalized?.commands || []).slice(0, 3).forEach((command, index) => {
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

    (normalized?.exceptions || []).slice(0, 2).forEach((exception, index) => {
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
        entries.push({
            id: `log-activity-${index}-${Date.now()}`,
            title: entry,
            label: entry,
            detail: null,
            kind: "activity",
            status: "info",
            statusKey: "info",
            statusLabel: "Info",
            statusTone: "info",
            timestamp: null,
        });
    });

    return entries.slice(0, 12);
}

function refreshDerivedState(state, preservedMetricKeys = []) {
    const derivedMetrics = {
        pendingJobs: state.queue.filter((item) => item.status !== "done").length,
        activeExceptions: state.exceptions.filter((item) => item.state !== "resolved" && item.state !== "closed").length,
        deviceOnline: state.devices.some((device) => device.state !== "offline" && device.state !== "error"),
        lastSync: new Date().toLocaleTimeString(),
    };
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

    if (normalized?.responseSummary) {
        state.responseSummary = normalized.responseSummary;
    }

    if (normalized?.commandQueueStatus) {
        state.commandQueueStatus = normalized.commandQueueStatus;
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
        buildLogEntries,
        refreshDerivedState,
        applyNormalizedEnvelope,
        buildQueueContext,
        matchQueueSelection,
        buildSeedTimelineEntries,
        normalizeShopfloorEnvelope,
    };
}
