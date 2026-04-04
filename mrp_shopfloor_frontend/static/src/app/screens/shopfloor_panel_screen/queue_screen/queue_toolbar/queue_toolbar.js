/** @odoo-module **/

import { Component } from "@odoo/owl";
import {
    QUEUE_SORT_LABELS,
    QUEUE_SORT_OPTIONS,
    QUEUE_STATUS_FILTER_LABELS,
    QUEUE_STATUS_FILTERS,
} from "../queue_filtering";

export class ShopfloorQueueToolbar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorQueueToolbar";
    static props = {
        searchText: String,
        statusFilter: String,
        sortKey: String,
        queueSummary: Object,
        visibleSummary: Object,
        onSearchTextChange: Function,
        onStatusFilterChange: Function,
        onSortKeyChange: Function,
        onClearFilters: Function,
    };

    get statusFilters() {
        return QUEUE_STATUS_FILTERS;
    }

    get sortOptions() {
        return QUEUE_SORT_OPTIONS;
    }

    get canClearFilters() {
        return Boolean(
            String(this.props.searchText || "").trim() ||
                (this.props.statusFilter || "all") !== "all" ||
                (this.props.sortKey || "priority_desc") !== "priority_desc"
        );
    }

    get filterSummary() {
        const visible = this.props.visibleSummary || {};
        const total = this.props.queueSummary || {};
        return {
            visibleTotal: visible.total || 0,
            total: total.total || 0,
            attentionCount: total.attentionCount || 0,
            searchText: String(this.props.searchText || "").trim(),
            statusFilter: this.props.statusFilter || "all",
            statusFilterLabel: QUEUE_STATUS_FILTER_LABELS[this.props.statusFilter || "all"] || "All",
            sortKey: this.props.sortKey || "priority_desc",
            sortLabel: QUEUE_SORT_LABELS[this.props.sortKey || "priority_desc"] || "Priority",
        };
    }

    onSearchInput(ev) {
        this.props.onSearchTextChange?.(ev.target.value);
    }

    changeStatusFilter(ev) {
        this.props.onStatusFilterChange?.(ev.currentTarget.dataset.statusFilter);
    }

    changeSortKey(ev) {
        this.props.onSortKeyChange?.(ev.currentTarget.dataset.sortKey);
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
