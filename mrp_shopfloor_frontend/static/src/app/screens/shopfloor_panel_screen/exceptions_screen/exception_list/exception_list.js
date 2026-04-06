/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorExceptionCard } from "../exception_card/exception_card";

export class ShopfloorExceptionList extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExceptionList";
    static components = {
        ShopfloorExceptionCard,
    };
    static props = {
        exceptions: Array,
        summary: Object,
        branchSummary: Object,
        branchSummaryItems: Array,
        latestRuntimeEntry: {
            type: Object,
            optional: true,
        },
        gatewayRuntimeSummary: {
            type: [Object, Boolean],
            optional: true,
        },
        metrics: {
            type: [Object, Boolean],
            optional: true,
        },
        emptyStateLabel: String,
        hasActiveFilters: Boolean,
        onClearFilters: Function,
        onReportException: Function,
    };

    get exceptionSummary() {
        return this.props.summary || { total: 0, openCount: 0, criticalCount: 0 };
    }

    get exceptionBranchSummary() {
        return this.props.branchSummary || { total: 0 };
    }

    get branchSummaryItems() {
        return Array.isArray(this.props.branchSummaryItems) ? this.props.branchSummaryItems : [];
    }

    get hasItems() {
        return Array.isArray(this.props.exceptions) && this.props.exceptions.length > 0;
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
