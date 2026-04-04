/** @odoo-module **/

const ALL_KEY = "all";

const EXCEPTION_SEVERITY_ALIASES = {
    blocker: "critical",
    critical: "critical",
    high: "high",
    medium: "medium",
    normal: "medium",
    low: "low",
};

const EXCEPTION_STATE_ALIASES = {
    new: "new",
    open: "open",
    claimed: "open",
    acknowledged: "acknowledged",
    ack: "acknowledged",
    blocked: "blocked",
    hold: "blocked",
    resolved: "resolved",
    fixed: "resolved",
    closed: "closed",
    cancelled: "cancelled",
    canceled: "cancelled",
};

const EXCEPTION_STATE_BRANCHES = {
    new: {
        label: "Follow-up",
        tone: "info",
        detail: "Queued for the next review cycle.",
    },
    open: {
        label: "Claimed",
        tone: "primary",
        detail: "Assigned to the current operator.",
    },
    acknowledged: {
        label: "Acknowledged",
        tone: "info",
        detail: "Waiting for verification or next action.",
    },
    blocked: {
        label: "Escalated",
        tone: "warning",
        detail: "Escalated to a supervisor or quality owner.",
    },
    resolved: {
        label: "Resolved",
        tone: "success",
        detail: "Work has been completed and verified.",
    },
    closed: {
        label: "Closed",
        tone: "secondary",
        detail: "Archived after closure.",
    },
    cancelled: {
        label: "Cancelled",
        tone: "secondary",
        detail: "Removed from the active workflow.",
    },
};

export const EXCEPTION_SEVERITY_FILTERS = [
    { key: ALL_KEY, label: "All severities" },
    { key: "critical", label: "Critical" },
    { key: "high", label: "High" },
    { key: "medium", label: "Medium" },
    { key: "low", label: "Low" },
];

export const EXCEPTION_STATE_FILTERS = [
    { key: ALL_KEY, label: "All states" },
    { key: "new", label: "New" },
    { key: "open", label: "Open" },
    { key: "acknowledged", label: "Acknowledged" },
    { key: "blocked", label: "Blocked" },
    { key: "resolved", label: "Resolved" },
    { key: "closed", label: "Closed" },
    { key: "cancelled", label: "Cancelled" },
];

export function normalizeExceptionKey(value) {
    return String(value || "").trim().toLowerCase().replace(/\s+/g, "_");
}

export function matchesExceptionSeverity(item, severityFilter) {
    const normalizedFilter = normalizeExceptionKey(severityFilter || ALL_KEY);
    if (!normalizedFilter || normalizedFilter === ALL_KEY) {
        return true;
    }
    const severity = EXCEPTION_SEVERITY_ALIASES[normalizeExceptionKey(item?.severity || "medium")] || "medium";
    return severity === normalizedFilter;
}

export function matchesExceptionState(item, stateFilter) {
    const normalizedFilter = normalizeExceptionKey(stateFilter || ALL_KEY);
    if (!normalizedFilter || normalizedFilter === ALL_KEY) {
        return true;
    }
    const state = EXCEPTION_STATE_ALIASES[normalizeExceptionKey(item?.state || "new")] || "new";
    return state === normalizedFilter;
}

export function exceptionFilterSummaryText(summary) {
    if (!summary?.isFiltered) {
        return null;
    }
    const parts = [];
    if (summary.severityFilterLabel && summary.severityFilter !== ALL_KEY) {
        parts.push(`Severity ${summary.severityFilterLabel}`);
    }
    if (summary.stateFilterLabel && summary.stateFilter !== ALL_KEY) {
        parts.push(`State ${summary.stateFilterLabel}`);
    }
    return parts.join(" | ");
}

export function exceptionStateBranchKey(value) {
    return EXCEPTION_STATE_ALIASES[normalizeExceptionKey(value || "new")] || "new";
}

export function exceptionStateBranchLabel(value) {
    const branch = EXCEPTION_STATE_BRANCHES[exceptionStateBranchKey(value)] || EXCEPTION_STATE_BRANCHES.new;
    return branch.label;
}

export function exceptionStateBranchTone(value) {
    const branch = EXCEPTION_STATE_BRANCHES[exceptionStateBranchKey(value)] || EXCEPTION_STATE_BRANCHES.new;
    return branch.tone;
}

export function exceptionStateBranchDetail(value) {
    const branch = EXCEPTION_STATE_BRANCHES[exceptionStateBranchKey(value)] || EXCEPTION_STATE_BRANCHES.new;
    return branch.detail;
}

export function summarizeExceptionBranches(exceptions) {
    const list = Array.isArray(exceptions) ? exceptions : [];
    const counts = {
        total: list.length,
        newCount: 0,
        openCount: 0,
        acknowledgedCount: 0,
        blockedCount: 0,
        resolvedCount: 0,
        closedCount: 0,
        cancelledCount: 0,
    };
    for (const item of list) {
        const branchKey = exceptionStateBranchKey(item?.state);
        counts[`${branchKey}Count`] = (counts[`${branchKey}Count`] || 0) + 1;
    }
    return counts;
}

export function exceptionBranchSummaryItems(summary) {
    const current = summary || {};
    return [
        { key: "new", label: "Follow-up", valueKey: "newCount", tone: "info" },
        { key: "open", label: "Claimed", valueKey: "openCount", tone: "primary", emphasis: true },
        { key: "acknowledged", label: "Acknowledged", valueKey: "acknowledgedCount", tone: "info" },
        { key: "blocked", label: "Escalated", valueKey: "blockedCount", tone: "warning", emphasis: true },
        { key: "resolved", label: "Resolved", valueKey: "resolvedCount", tone: "success" },
        { key: "closed", label: "Closed", valueKey: "closedCount", tone: "secondary" },
        { key: "cancelled", label: "Cancelled", valueKey: "cancelledCount", tone: "secondary" },
        { key: "total", label: "Total", valueKey: "total", tone: "secondary" },
    ].map((item) => ({
        ...item,
        value: current[item.valueKey] || 0,
    }));
}
