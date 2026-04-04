/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import {
    exceptionSummaryItems,
    summarizeExceptions,
} from "../../../../components/shopfloor_status_components/shopfloor_status_metrics";
import {
    exceptionBranchSummaryItems,
    exceptionFilterSummaryText,
    matchesExceptionSeverity,
    matchesExceptionState,
    summarizeExceptionBranches,
} from "./exception_filtering";
import { ShopfloorExceptionActions } from "./exception_actions/exception_actions";
import { ShopfloorExceptionToolbar } from "./exception_toolbar/exception_toolbar";
import { ShopfloorExceptionList } from "./exception_list/exception_list";

export class ShopfloorExceptionsScreen extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExceptionsScreen";
    static components = {
        ShopfloorExceptionActions,
        ShopfloorExceptionToolbar,
        ShopfloorExceptionList,
    };
    static props = {
        exceptions: Array,
        onReportException: Function,
    };

    setup() {
        this.state = useState({
            severityFilter: "all",
            stateFilter: "all",
        });
    }

    get exceptionSummary() {
        return summarizeExceptions(this.props.exceptions);
    }

    get branchSummary() {
        return summarizeExceptionBranches(this.props.exceptions);
    }

    get visibleExceptions() {
        const exceptions = Array.isArray(this.props.exceptions) ? [...this.props.exceptions] : [];
        return exceptions
            .filter((item) => matchesExceptionSeverity(item, this.state.severityFilter))
            .filter((item) => matchesExceptionState(item, this.state.stateFilter));
    }

    get visibleSummary() {
        const visible = summarizeExceptions(this.visibleExceptions);
        return {
            ...visible,
            baseTotal: this.exceptionSummary.total,
            baseOpenCount: this.exceptionSummary.openCount,
            baseCriticalCount: this.exceptionSummary.criticalCount,
            severityFilter: this.state.severityFilter || "all",
            severityFilterLabel: String(this.state.severityFilter || "all").replace(/_/g, " "),
            stateFilter: this.state.stateFilter || "all",
            stateFilterLabel: String(this.state.stateFilter || "all").replace(/_/g, " "),
            isFiltered: this.hasActiveFilters,
            filterSummaryLabel: exceptionFilterSummaryText({
                isFiltered: this.hasActiveFilters,
                severityFilter: this.state.severityFilter || "all",
                severityFilterLabel: String(this.state.severityFilter || "all").replace(/_/g, " "),
                stateFilter: this.state.stateFilter || "all",
                stateFilterLabel: String(this.state.stateFilter || "all").replace(/_/g, " "),
            }),
        };
    }

    get exceptionSummaryItems() {
        return exceptionSummaryItems(this.exceptionSummary);
    }

    get branchSummaryItems() {
        return exceptionBranchSummaryItems(this.branchSummary);
    }

    get hasActiveFilters() {
        return (this.state.severityFilter || "all") !== "all" || (this.state.stateFilter || "all") !== "all";
    }

    get emptyStateLabel() {
        if (this.visibleExceptions.length) {
            return null;
        }
        if (this.hasActiveFilters) {
            return "No exceptions match the current filters.";
        }
        return "No exceptions have been reported yet.";
    }

    reportException(ev) {
        this.props.onReportException?.(ev);
    }

    onSeverityFilterChange(value) {
        this.state.severityFilter = value || "all";
    }

    onStateFilterChange(value) {
        this.state.stateFilter = value || "all";
    }

    onClearFilters(ev) {
        ev?.preventDefault?.();
        this.state.severityFilter = "all";
        this.state.stateFilter = "all";
    }
}
