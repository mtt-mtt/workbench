/** @odoo-module **/

const DEVICE_STATE_TONES = {
    ready: "success",
    active: "info",
    degraded: "warning",
    offline: "secondary",
    error: "danger",
};

const EXCEPTION_SEVERITY_TONES = {
    critical: "danger",
    high: "warning",
    medium: "info",
    low: "secondary",
};

const EXCEPTION_SEVERITY_LABELS = {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
};

const EXCEPTION_STATE_TONES = {
    new: "warning",
    open: "warning",
    ack: "info",
    acknowledged: "info",
    blocked: "danger",
    resolved: "success",
    closed: "secondary",
    cancelled: "secondary",
    canceled: "secondary",
};

const COMMAND_STATE_TONES = {
    draft: "secondary",
    queued: "info",
    pending: "warning",
    waiting: "warning",
    received: "info",
    accepted: "info",
    sent: "warning",
    acknowledged: "warning",
    running: "info",
    processing: "info",
    in_progress: "info",
    done: "success",
    completed: "success",
    success: "success",
    failed: "danger",
    error: "danger",
    rejected: "danger",
    cancelled: "secondary",
    canceled: "secondary",
    idle: "secondary",
    attention: "danger",
    active: "info",
};

const COMMAND_STATE_LABELS = {
    draft: "Draft",
    queued: "Queued",
    pending: "Pending",
    waiting: "Waiting",
    received: "Received",
    accepted: "Accepted",
    sent: "Sent",
    acknowledged: "Acknowledged",
    running: "Running",
    processing: "Processing",
    in_progress: "In progress",
    done: "Done",
    completed: "Completed",
    success: "Succeeded",
    failed: "Failed",
    error: "Error",
    rejected: "Rejected",
    cancelled: "Cancelled",
    canceled: "Cancelled",
    idle: "Idle",
    attention: "Attention",
    active: "Active",
};

const EXCEPTION_STATE_LABELS = {
    new: "New",
    open: "Open",
    ack: "Acknowledged",
    acknowledged: "Acknowledged",
    blocked: "Blocked",
    resolved: "Resolved",
    closed: "Closed",
    cancelled: "Cancelled",
    canceled: "Cancelled",
};

function normalizeKey(value, fallback = "unknown") {
    return String(value || fallback).trim().replace(/\s+/g, "_").toLowerCase();
}

function labelizeKey(value, fallback = "Unknown") {
    const normalized = normalizeKey(value, fallback);
    return normalized.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function toneForKey(key, map, fallback = "secondary") {
    return map[key] || fallback;
}

function resolveSummaryValue(summary, descriptor) {
    if (typeof descriptor.value === "function") {
        return descriptor.value(summary);
    }
    if (descriptor.valueKey) {
        return summary?.[descriptor.valueKey];
    }
    return descriptor.value;
}

function buildStatusSummaryItem(summary, descriptor) {
    return {
        key: descriptor.key || descriptor.label,
        label: descriptor.label || descriptor.key,
        value: resolveSummaryValue(summary, descriptor),
        tone: descriptor.tone || "secondary",
        detail: descriptor.detail,
        emphasis: Boolean(descriptor.emphasis),
    };
}

export function buildStatusSummaryItems(summary, descriptors) {
    const list = Array.isArray(descriptors) ? descriptors : [];
    return list.map((descriptor) => buildStatusSummaryItem(summary || {}, descriptor));
}

export function buildActionDescriptor(action) {
    const descriptor = action || {};
    return {
        key: descriptor.key || descriptor.label || "action",
        label: descriptor.label || descriptor.key || "Action",
        tone: descriptor.tone || "secondary",
        icon: descriptor.icon || null,
        detail: descriptor.detail || null,
        active: Boolean(descriptor.active),
        disabled: Boolean(descriptor.disabled),
        emphasis: Boolean(descriptor.emphasis),
        data: descriptor.data || {},
    };
}

export function buildActionDescriptors(actions) {
    const list = Array.isArray(actions) ? actions : [];
    return list.map((action) => buildActionDescriptor(action));
}

const DEVICE_SUMMARY_DESCRIPTORS = [
    { key: "total", label: "Total", valueKey: "total", tone: "secondary" },
    { key: "ready", label: "Ready", valueKey: "readyCount", tone: "success", emphasis: true },
    { key: "attention", label: "Attention", valueKey: "attentionCount", tone: "warning", emphasis: true },
    { key: "selected", label: "Selected", valueKey: "selectedState", tone: "info" },
];

const EXCEPTION_SUMMARY_DESCRIPTORS = [
    { key: "total", label: "Total", valueKey: "total", tone: "secondary" },
    { key: "open", label: "Open", valueKey: "openCount", tone: "warning", emphasis: true },
    { key: "critical", label: "Critical", valueKey: "criticalCount", tone: "danger", emphasis: true },
];

export function summarizeDevices(devices, selectedDevice) {
    const list = Array.isArray(devices) ? devices : [];
    const selectedState = selectedDevice?.state || "unknown";
    const readyCount = list.filter((device) => normalizeKey(device?.state) === "ready").length;
    const attentionCount = list.filter((device) => ["degraded", "offline", "error"].includes(normalizeKey(device?.state))).length;
    return {
        total: list.length,
        readyCount,
        attentionCount,
        selectedState,
    };
}

export function summarizeExceptions(exceptions) {
    const list = Array.isArray(exceptions) ? exceptions : [];
    const openCount = list.filter((item) => !["resolved", "closed"].includes(normalizeKey(item?.state))).length;
    const criticalCount = list.filter((item) => normalizeKey(item?.severity) === "critical").length;
    return {
        total: list.length,
        openCount,
        criticalCount,
    };
}

export function deviceSummaryItems(summary) {
    return buildStatusSummaryItems(summary, DEVICE_SUMMARY_DESCRIPTORS);
}

export function deviceToolbarItems(summary) {
    return buildStatusSummaryItems(summary, DEVICE_SUMMARY_DESCRIPTORS);
}

export function exceptionSummaryItems(summary) {
    return buildStatusSummaryItems(summary, EXCEPTION_SUMMARY_DESCRIPTORS);
}

export function exceptionToolbarItems(summary) {
    return buildStatusSummaryItems(summary, EXCEPTION_SUMMARY_DESCRIPTORS);
}

export function deviceStateKey(value) {
    return normalizeKey(value);
}

export function deviceStateLabel(value) {
    return deviceStateKey(value).replace(/_/g, " ");
}

export function deviceStateTone(value) {
    return toneForKey(deviceStateKey(value), DEVICE_STATE_TONES);
}

export function deviceAttentionLabel(value) {
    return ["degraded", "offline", "error"].includes(deviceStateKey(value)) ? "Attention" : null;
}

export function exceptionSeverityKey(value) {
    return normalizeKey(value, "medium");
}

export function exceptionSeverityLabel(value) {
    const key = exceptionSeverityKey(value);
    return EXCEPTION_SEVERITY_LABELS[key] || labelizeKey(key, "Medium");
}

export function exceptionSeverityTone(value) {
    return toneForKey(exceptionSeverityKey(value), EXCEPTION_SEVERITY_TONES, "info");
}

export function exceptionStateKey(value) {
    return normalizeKey(value, "new");
}

export function exceptionStateLabel(value) {
    const key = exceptionStateKey(value);
    return EXCEPTION_STATE_LABELS[key] || labelizeKey(key, "New");
}

export function exceptionStateTone(value) {
    return toneForKey(exceptionStateKey(value), EXCEPTION_STATE_TONES);
}

export function exceptionAttentionLabel(severity, state) {
    return ["critical", "high"].includes(exceptionSeverityKey(severity)) || ["new", "open", "ack", "acknowledged", "blocked"].includes(exceptionStateKey(state))
        ? "Attention"
        : null;
}

export function commandStateKey(value) {
    return normalizeKey(value, "queued");
}

export function commandStateLabel(value) {
    const key = commandStateKey(value);
    return COMMAND_STATE_LABELS[key] || labelizeKey(key, "Queued");
}

export function commandStateTone(value) {
    return toneForKey(commandStateKey(value), COMMAND_STATE_TONES, "secondary");
}

export function commandStateAttentionLabel(value) {
    return ["failed", "error", "rejected", "attention"].includes(commandStateKey(value)) ? "Attention" : null;
}

export function feedbackToneClass(tone) {
    return toneForKey(String(tone || "info").trim().toLowerCase(), {
        success: "text-bg-success",
        warning: "text-bg-warning",
        danger: "text-bg-danger",
        info: "text-bg-info",
        secondary: "text-bg-secondary",
        light: "text-bg-light",
    });
}
