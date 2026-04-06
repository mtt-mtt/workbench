/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { findLatestRuntimeEntry, normalizeRuntimeEntry } from "../../../../utils/shopfloor_runtime_entries";
import { ShopfloorQueueDetail } from "./queue_detail/queue_detail";
import { ShopfloorQueueList } from "./queue_list/queue_list";
import { ShopfloorQueueToolbar } from "./queue_toolbar/queue_toolbar";
import { QUEUE_SORT_LABELS, QUEUE_STATUS_FILTER_LABELS } from "./queue_filtering";

const ATTENTION_STATUSES = new Set(["blocked", "error", "paused", "rejected"]);
const SORT_PRIORITY = {
    critical: 4,
    urgent: 3,
    high: 3,
    medium: 2,
    normal: 1,
    low: 0,
};
const STATUS_ORDER = {
    blocked: 60,
    error: 50,
    rejected: 45,
    paused: 40,
    in_progress: 35,
    running: 35,
    waiting: 30,
    ready: 20,
    draft: 10,
    done: 0,
};

function normalizeKey(value) {
    return String(value || "").trim().toLowerCase().replace(/\s+/g, "_");
}

function compareText(left, right) {
    return String(left || "").localeCompare(String(right || ""), undefined, {
        numeric: true,
        sensitivity: "base",
    });
}

function parseProgressValue(item) {
    const done = Number(item?.done);
    const quantity = Number(item?.quantity);
    if (Number.isFinite(done) && Number.isFinite(quantity) && quantity > 0) {
        return done / quantity;
    }

    const progressText = String(item?.progress || "");
    const percentMatch = progressText.match(/(\d+(?:\.\d+)?)\s*%/);
    if (percentMatch) {
        return Number(percentMatch[1]) / 100;
    }

    const ratioMatch = progressText.match(/(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/);
    if (ratioMatch) {
        const denominator = Number(ratioMatch[2]);
        if (Number.isFinite(denominator) && denominator > 0) {
            return Number(ratioMatch[1]) / denominator;
        }
    }

    return 0;
}

function buildSummary(queue, selectedQueueItem) {
    const normalizedQueue = Array.isArray(queue) ? queue : [];
    return {
        total: normalizedQueue.length,
        attentionCount: normalizedQueue.filter((item) =>
            ATTENTION_STATUSES.has(normalizeKey(item?.status))
        ).length,
        selectedStatus: selectedQueueItem?.status || "unknown",
        selectedReference: selectedQueueItem?.reference || "n/a",
    };
}

function matchesSearch(item, searchText) {
    if (!searchText) {
        return true;
    }
    const searchable = [
        item?.name,
        item?.product,
        item?.workorder,
        item?.reference,
        item?.workorder_ref,
        item?.production_ref,
        item?.status,
        item?.priority,
        item?.stage,
        item?.message,
        item?.source,
    ]
        .filter((value) => value !== null && value !== undefined)
        .join(" ")
        .toLowerCase();
    return searchable.includes(searchText);
}

function matchesStatus(item, statusFilter) {
    const normalizedStatus = normalizeKey(item?.status);
    const normalizedFilter = normalizeKey(statusFilter || "all");
    if (!normalizedFilter || normalizedFilter === "all") {
        return true;
    }
    if (normalizedFilter === "attention") {
        return ATTENTION_STATUSES.has(normalizedStatus);
    }
    if (normalizedFilter === "in_progress") {
        return ["in_progress", "running"].includes(normalizedStatus);
    }
    return normalizedStatus === normalizedFilter;
}

function compareQueueItems(left, right, sortKey) {
    const leftStatus = normalizeKey(left?.status);
    const rightStatus = normalizeKey(right?.status);
    switch (sortKey) {
        case "status": {
            const statusDelta = (STATUS_ORDER[rightStatus] ?? 0) - (STATUS_ORDER[leftStatus] ?? 0);
            if (statusDelta !== 0) {
                return statusDelta;
            }
            return compareText(left?.reference || left?.name, right?.reference || right?.name);
        }
        case "progress_desc": {
            const progressDelta = parseProgressValue(right) - parseProgressValue(left);
            if (Math.abs(progressDelta) > 0.0001) {
                return progressDelta;
            }
            return compareText(left?.reference || left?.name, right?.reference || right?.name);
        }
        case "reference":
            return compareText(left?.reference || left?.name, right?.reference || right?.name);
        case "name":
            return compareText(left?.name, right?.name);
        case "priority_desc":
        default: {
            const leftPriority = SORT_PRIORITY[normalizeKey(left?.priority)] ?? 1;
            const rightPriority = SORT_PRIORITY[normalizeKey(right?.priority)] ?? 1;
            const priorityDelta = rightPriority - leftPriority;
            if (priorityDelta !== 0) {
                return priorityDelta;
            }
            const statusDelta = (STATUS_ORDER[rightStatus] ?? 0) - (STATUS_ORDER[leftStatus] ?? 0);
            if (statusDelta !== 0) {
                return statusDelta;
            }
            return compareText(left?.reference || left?.name, right?.reference || right?.name);
        }
    }
}

export class ShopfloorQueueScreen extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorQueueScreen";
    static components = {
        ShopfloorQueueDetail,
        ShopfloorQueueList,
        ShopfloorQueueToolbar,
    };
    static props = {
        queue: Array,
        selectedQueueItem: Object,
        selectedQueueContext: Object,
        logEntries: Array,
        gatewayRuntimeSummary: [Object, Boolean],
        metrics: [Object, Boolean],
        onOpenQueueItem: Function,
        onRefreshQueue: Function,
    };

    setup() {
        this.state = useState({
            searchText: "",
            statusFilter: "all",
            sortKey: "priority_desc",
        });
    }

    get queueSummary() {
        return buildSummary(this.props.queue, this.props.selectedQueueItem);
    }

    get visibleQueue() {
        const searchText = String(this.state.searchText || "").trim().toLowerCase();
        const statusFilter = this.state.statusFilter || "all";
        const sortKey = this.state.sortKey || "priority_desc";
        const queue = Array.isArray(this.props.queue) ? [...this.props.queue] : [];
        return queue
            .filter((item) => matchesSearch(item, searchText))
            .filter((item) => matchesStatus(item, statusFilter))
            .sort((left, right) => compareQueueItems(left, right, sortKey));
    }

    get visibleSummary() {
        return {
            ...buildSummary(this.visibleQueue, this.props.selectedQueueItem),
            baseTotal: this.queueSummary.total,
            baseAttentionCount: this.queueSummary.attentionCount,
            searchText: String(this.state.searchText || "").trim(),
            statusFilter: this.state.statusFilter || "all",
            statusFilterLabel: QUEUE_STATUS_FILTER_LABELS[this.state.statusFilter || "all"] || "All",
            sortKey: this.state.sortKey || "priority_desc",
            sortLabel: QUEUE_SORT_LABELS[this.state.sortKey || "priority_desc"] || "Priority",
            isFiltered: this.hasActiveFilters,
            selectedVisible: this.selectedQueueVisible,
        };
    }

    get selectedQueueVisible() {
        const selectedId = this.props.selectedQueueItem?.id;
        if (selectedId === undefined || selectedId === null) {
            return false;
        }
        return this.visibleQueue.some((item) => String(item.id) === String(selectedId));
    }

    get searchText() {
        return this.state.searchText;
    }

    get statusFilter() {
        return this.state.statusFilter;
    }

    get sortKey() {
        return this.state.sortKey;
    }

    get hasActiveFilters() {
        return Boolean(
            String(this.state.searchText || "").trim() ||
                (this.state.statusFilter || "all") !== "all" ||
                (this.state.sortKey || "priority_desc") !== "priority_desc"
        );
    }

    get latestRuntimeEntry() {
        return normalizeRuntimeEntry(findLatestRuntimeEntry(this.props.logEntries || []));
    }

    openQueueItem(ev) {
        this.props.onOpenQueueItem?.(ev);
    }

    refreshQueue(ev) {
        this.props.onRefreshQueue?.(ev);
    }

    onSearchTextChange(ev) {
        this.state.searchText = typeof ev === "string" ? ev : ev?.target?.value || "";
    }

    onStatusFilterChange(ev) {
        this.state.statusFilter =
            typeof ev === "string" ? ev : ev?.currentTarget?.dataset?.statusFilter || "all";
    }

    onSortKeyChange(ev) {
        this.state.sortKey =
            typeof ev === "string" ? ev : ev?.currentTarget?.dataset?.sortKey || "priority_desc";
    }

    onClearFilters(ev) {
        ev?.preventDefault?.();
        this.state.searchText = "";
        this.state.statusFilter = "all";
        this.state.sortKey = "priority_desc";
    }
}
