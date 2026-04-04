/** @odoo-module **/

import { Component } from "@odoo/owl";
import {
    EXCEPTION_SEVERITY_FILTERS,
    EXCEPTION_STATE_FILTERS,
} from "../exception_filtering";

export class ShopfloorExceptionToolbar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExceptionToolbar";
    static props = {
        summary: Object,
        branchSummary: Object,
        severityFilter: String,
        stateFilter: String,
        onSeverityFilterChange: Function,
        onStateFilterChange: Function,
        onClearFilters: Function,
    };

    get severityFilters() {
        return EXCEPTION_SEVERITY_FILTERS;
    }

    get stateFilters() {
        return EXCEPTION_STATE_FILTERS;
    }

    get canClearFilters() {
        return Boolean(
            (this.props.severityFilter || "all") !== "all" ||
                (this.props.stateFilter || "all") !== "all"
        );
    }

    get summary() {
        return this.props.summary || { total: 0, openCount: 0, criticalCount: 0 };
    }

    get branchSummary() {
        return this.props.branchSummary || { total: 0 };
    }

    get branchHeadlines() {
        return [
            { label: "Claimed", value: this.branchSummary.openCount || 0, tone: "primary" },
            { label: "Acknowledged", value: this.branchSummary.acknowledgedCount || 0, tone: "info" },
            { label: "Escalated", value: this.branchSummary.blockedCount || 0, tone: "warning" },
            { label: "Resolved", value: this.branchSummary.resolvedCount || 0, tone: "success" },
            { label: "Closed", value: this.branchSummary.closedCount || 0, tone: "secondary" },
        ];
    }

    changeSeverityFilter(ev) {
        this.props.onSeverityFilterChange?.(ev.currentTarget.dataset.severityFilter || "all");
    }

    changeStateFilter(ev) {
        this.props.onStateFilterChange?.(ev.currentTarget.dataset.stateFilter || "all");
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
