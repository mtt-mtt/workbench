/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorStatusSummary } from "../../../../../components/shopfloor_status_components/shopfloor_status_summary";
import {
    DEVICE_GROUP_OPTIONS,
    DEVICE_STATE_FILTERS,
    groupByLabel,
    stateFilterLabel,
} from "../devices_filtering";

export class ShopfloorDeviceToolbar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceToolbar";
    static components = {
        ShopfloorStatusSummary,
    };
    static props = {
        searchText: String,
        groupBy: String,
        stateFilter: String,
        summary: Object,
        onSearchTextChange: Function,
        onGroupByChange: Function,
        onStateFilterChange: Function,
        onClearFilters: Function,
    };

    get groupOptions() {
        return DEVICE_GROUP_OPTIONS;
    }

    get stateFilters() {
        return DEVICE_STATE_FILTERS;
    }

    get visibleSummaryItems() {
        return [
            { key: "visible", label: "Visible", value: this.props.summary?.total || 0, tone: "secondary" },
            { key: "ready", label: "Ready", value: this.props.summary?.readyCount || 0, tone: "success" },
            { key: "attention", label: "Attention", value: this.props.summary?.attentionCount || 0, tone: "warning" },
            { key: "selected", label: "Selected", value: this.props.summary?.selectedState || "unknown", tone: "info" },
        ];
    }

    get canClearFilters() {
        return Boolean(
            String(this.props.searchText || "").trim() ||
                (this.props.groupBy || "state") !== "state" ||
                (this.props.stateFilter || "all") !== "all"
        );
    }

    get groupLabel() {
        return groupByLabel(this.props.groupBy || "state");
    }

    get stateLabel() {
        return stateFilterLabel(this.props.stateFilter || "all");
    }

    onSearchInput(ev) {
        this.props.onSearchTextChange?.(ev.target.value);
    }

    changeGroupBy(ev) {
        this.props.onGroupByChange?.(ev.currentTarget.dataset.groupBy);
    }

    changeStateFilter(ev) {
        this.props.onStateFilterChange?.(ev.currentTarget.dataset.stateFilter);
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
