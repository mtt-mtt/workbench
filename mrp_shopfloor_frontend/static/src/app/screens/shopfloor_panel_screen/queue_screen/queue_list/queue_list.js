/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorQueueRow } from "../queue_row/queue_row";

export class ShopfloorQueueList extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorQueueList";
    static components = {
        ShopfloorQueueRow,
    };
    static props = {
        queue: Array,
        selectedQueueItem: Object,
        summary: Object,
        hasActiveFilters: Boolean,
        onOpenQueueItem: Function,
        onClearFilters: Function,
    };

    get queueSummary() {
        return this.props.summary || {
            total: 0,
            attentionCount: 0,
            selectedStatus: "unknown",
            selectedReference: "n/a",
            baseTotal: 0,
            baseAttentionCount: 0,
        };
    }

    get hasItems() {
        return Array.isArray(this.props.queue) && this.props.queue.length > 0;
    }

    get emptyStateLabel() {
        if (this.hasItems) {
            return null;
        }
        if (this.queueSummary.isFiltered || this.props.hasActiveFilters) {
            return "No queue items match the current filters.";
        }
        return "No queue items available.";
    }

    get filterSummaryLabel() {
        const summary = this.queueSummary;
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

    openQueueItem(ev) {
        this.props.onOpenQueueItem?.(ev);
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
