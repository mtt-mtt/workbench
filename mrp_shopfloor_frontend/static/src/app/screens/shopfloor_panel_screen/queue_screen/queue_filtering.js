/** @odoo-module **/

export const QUEUE_STATUS_FILTERS = [
    { key: "all", label: "All" },
    { key: "attention", label: "Attention" },
    { key: "ready", label: "Ready" },
    { key: "in_progress", label: "In progress" },
    { key: "paused", label: "Paused" },
    { key: "waiting", label: "Waiting" },
    { key: "blocked", label: "Blocked" },
    { key: "done", label: "Done" },
];

export const QUEUE_SORT_OPTIONS = [
    { key: "priority_desc", label: "Priority" },
    { key: "status", label: "Status" },
    { key: "progress_desc", label: "Progress" },
    { key: "reference", label: "Reference" },
    { key: "name", label: "Name" },
];

export const QUEUE_STATUS_FILTER_LABELS = Object.fromEntries(
    QUEUE_STATUS_FILTERS.map((filter) => [filter.key, filter.label])
);

export const QUEUE_SORT_LABELS = Object.fromEntries(
    QUEUE_SORT_OPTIONS.map((option) => [option.key, option.label])
);

const STATUS_RANKS = {
    blocked: 0,
    error: 1,
    rejected: 2,
    paused: 3,
    waiting: 4,
    in_progress: 5,
    running: 5,
    ready: 6,
    done: 7,
    draft: 8,
    unknown: 9,
};

const PRIORITY_RANKS = {
    critical: 0,
    urgent: 1,
    high: 2,
    medium: 3,
    normal: 4,
    low: 5,
};

const ATTENTION_STATUSES = new Set(["blocked", "error", "paused", "rejected"]);

export function normalizeQueueStatus(value) {
    return String(value || "unknown").trim().replace(/\s+/g, "_").toLowerCase() || "unknown";
}

export function normalizeQueueText(value) {
    return String(value ?? "").trim().toLowerCase();
}

export function isQueueAttentionStatus(statusKey) {
    return ATTENTION_STATUSES.has(normalizeQueueStatus(statusKey));
}

export function matchesQueueStatusFilter(item, statusFilter) {
    const filterKey = normalizeQueueStatus(statusFilter || "all");
    const statusKey = normalizeQueueStatus(item?.status);
    switch (filterKey) {
        case "all":
            return true;
        case "attention":
            return isQueueAttentionStatus(statusKey);
        case "ready":
            return statusKey === "ready";
        case "in_progress":
            return ["in_progress", "running"].includes(statusKey);
        case "paused":
            return statusKey === "paused";
        case "waiting":
            return statusKey === "waiting";
        case "blocked":
            return statusKey === "blocked";
        case "done":
            return statusKey === "done";
        default:
            return statusKey === filterKey;
    }
}

export function matchesQueueSearch(item, needle) {
    const searchText = normalizeQueueText(needle);
    if (!searchText) {
        return true;
    }
    const haystack = [
        item?.name,
        item?.product,
        item?.workorder,
        item?.reference,
        item?.stage,
        item?.message,
        item?.workorder_ref,
        item?.production_ref,
        item?.source,
        item?.status,
        item?.priority,
    ]
        .map(normalizeQueueText)
        .filter(Boolean)
        .join(" ");
    return haystack.includes(searchText);
}

function compareText(left, right) {
    return normalizeQueueText(left).localeCompare(normalizeQueueText(right), undefined, {
        numeric: true,
        sensitivity: "base",
    });
}

function compareStatus(left, right) {
    return (STATUS_RANKS[normalizeQueueStatus(left)] ?? STATUS_RANKS.unknown) - (STATUS_RANKS[normalizeQueueStatus(right)] ?? STATUS_RANKS.unknown);
}

function comparePriority(left, right) {
    return (PRIORITY_RANKS[normalizeQueueText(left)] ?? PRIORITY_RANKS.normal) - (PRIORITY_RANKS[normalizeQueueText(right)] ?? PRIORITY_RANKS.normal);
}

function getQueueProgressRatio(item) {
    const done = Number(item?.done ?? 0);
    const quantity = Number(item?.quantity ?? 0);
    if (Number.isFinite(done) && Number.isFinite(quantity) && quantity > 0) {
        return done / quantity;
    }
    const progress = normalizeQueueText(item?.progress);
    const parsed = progress.match(/(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/);
    if (parsed) {
        const parsedDone = Number(parsed[1]);
        const parsedQuantity = Number(parsed[2]);
        if (Number.isFinite(parsedDone) && Number.isFinite(parsedQuantity) && parsedQuantity > 0) {
            return parsedDone / parsedQuantity;
        }
    }
    return 0;
}

function getQueueReference(item) {
    return item?.reference || item?.workorder_ref || item?.production_ref || item?.workorder || item?.name || "";
}

export function compareQueueItems(left, right, sortKey) {
    const key = normalizeQueueStatus(sortKey || "priority_desc");
    const leftStatus = normalizeQueueStatus(left?.status);
    const rightStatus = normalizeQueueStatus(right?.status);
    const leftPriority = left?.priority;
    const rightPriority = right?.priority;
    const leftName = left?.name;
    const rightName = right?.name;
    const leftReference = getQueueReference(left);
    const rightReference = getQueueReference(right);
    const leftProgress = getQueueProgressRatio(left);
    const rightProgress = getQueueProgressRatio(right);

    let diff = 0;
    switch (key) {
        case "status":
            diff = compareStatus(leftStatus, rightStatus);
            if (diff) {
                return diff;
            }
            diff = comparePriority(leftPriority, rightPriority);
            if (diff) {
                return diff;
            }
            diff = compareText(leftReference, rightReference);
            if (diff) {
                return diff;
            }
            break;
        case "progress_desc":
            diff = rightProgress - leftProgress;
            if (diff) {
                return diff;
            }
            diff = comparePriority(leftPriority, rightPriority);
            if (diff) {
                return diff;
            }
            diff = compareStatus(leftStatus, rightStatus);
            if (diff) {
                return diff;
            }
            diff = compareText(leftReference, rightReference);
            if (diff) {
                return diff;
            }
            break;
        case "reference":
            diff = compareText(leftReference, rightReference);
            if (diff) {
                return diff;
            }
            diff = compareStatus(leftStatus, rightStatus);
            if (diff) {
                return diff;
            }
            break;
        case "name":
            diff = compareText(leftName, rightName);
            if (diff) {
                return diff;
            }
            diff = compareStatus(leftStatus, rightStatus);
            if (diff) {
                return diff;
            }
            break;
        case "priority_desc":
        default:
            diff = comparePriority(leftPriority, rightPriority);
            if (diff) {
                return diff;
            }
            diff = compareStatus(leftStatus, rightStatus);
            if (diff) {
                return diff;
            }
            diff = compareText(leftReference, rightReference);
            if (diff) {
                return diff;
            }
            break;
    }
    return compareText(left?.id, right?.id);
}
