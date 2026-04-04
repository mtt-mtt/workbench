/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorQueueDetail extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorQueueDetail";
    static props = {
        selectedQueueItem: Object,
        summary: Object,
        selectedQueueContext: Object,
        selectedQueueVisible: Boolean,
        onClearFilters: Function,
    };

    get statusKey() {
        return String(this.props.selectedQueueItem?.status || "unknown").trim().replace(/\s+/g, "_").toLowerCase();
    }

    get statusLabel() {
        return this.statusKey.replace(/_/g, " ");
    }

    get statusToneClass() {
        const map = {
            done: "text-bg-success",
            ready: "text-bg-success",
            in_progress: "text-bg-info",
            running: "text-bg-info",
            paused: "text-bg-warning",
            waiting: "text-bg-secondary",
            blocked: "text-bg-danger",
            error: "text-bg-danger",
            rejected: "text-bg-danger",
            draft: "text-bg-light",
        };
        return map[this.statusKey] || "text-bg-light";
    }

    get priorityLabel() {
        return String(this.props.selectedQueueItem?.priority || "Normal");
    }

    get priorityToneClass() {
        const key = this.priorityLabel.trim().toLowerCase();
        if (["high", "urgent", "critical"].includes(key)) {
            return "text-bg-warning";
        }
        return "text-bg-secondary";
    }

    get progressLabel() {
        const done = this.props.selectedQueueItem?.done ?? 0;
        const quantity = this.props.selectedQueueItem?.quantity ?? 0;
        return this.props.selectedQueueItem?.progress || `${done} / ${quantity}`;
    }

    get attentionLabel() {
        return ["blocked", "error", "rejected"].includes(this.statusKey) ? "Attention required" : null;
    }

    get hasSelectedQueueItem() {
        return Boolean(this.props.selectedQueueItem);
    }

    get filterSummaryLabel() {
        const summary = this.props.summary || {};
        if (!summary.isFiltered) {
            return null;
        }
        const parts = [];
        if (summary.searchText) {
            parts.push(`Search "${summary.searchText}"`);
        }
        if (summary.statusFilterLabel && summary.statusFilter !== "all") {
            parts.push(`Status ${summary.statusFilterLabel}`);
        }
        if (summary.sortLabel) {
            parts.push(`Sort ${summary.sortLabel}`);
        }
        return parts.join(" | ");
    }

    get selectionVisibilityLabel() {
        if (this.props.selectedQueueVisible === false) {
            return "Selected item is hidden by the current filters.";
        }
        return null;
    }

    get selectedContextReference() {
        return this.props.selectedQueueContext?.reference || this.props.selectedQueueItem?.reference || "n/a";
    }

    get selectedContextWorkorderRef() {
        return this.props.selectedQueueContext?.workorder_ref || this.props.selectedQueueItem?.workorder_ref || "n/a";
    }

    get selectedContextProductionRef() {
        return this.props.selectedQueueContext?.production_ref || this.props.selectedQueueItem?.production_ref || "n/a";
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
