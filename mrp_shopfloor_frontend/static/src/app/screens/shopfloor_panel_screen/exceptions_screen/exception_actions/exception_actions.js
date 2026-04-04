/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { ShopfloorStatusSummary } from "../../../../../components/shopfloor_status_components/shopfloor_status_summary";
import { exceptionSummaryItems } from "../../../../../components/shopfloor_status_components/shopfloor_status_metrics";

const EXCEPTION_ACTIONS = [
    {
        key: "claim",
        label: "Claim",
        description: "Assign the exception to the current operator.",
        confirmLabel: "Claim exception",
        message: "Exception claimed for triage",
        severity: "medium",
        state: "open",
        buttonClass: "btn-outline-primary",
    },
    {
        key: "close",
        label: "Close",
        description: "Mark the exception as resolved and complete.",
        confirmLabel: "Close exception",
        message: "Exception closed after verification",
        severity: "low",
        state: "closed",
        buttonClass: "btn-outline-success",
    },
    {
        key: "escalate",
        label: "Escalate",
        description: "Escalate the exception to a supervisor or quality owner.",
        confirmLabel: "Escalate exception",
        message: "Exception escalated for review",
        severity: "critical",
        state: "blocked",
        buttonClass: "btn-outline-warning",
    },
    {
        key: "follow_up",
        label: "Follow-up",
        description: "Create a follow-up entry for the next review cycle.",
        confirmLabel: "Create follow-up",
        message: "Exception follow-up requested",
        severity: "medium",
        state: "new",
        buttonClass: "btn-outline-info",
    },
];

export class ShopfloorExceptionActions extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExceptionActions";
    static components = {
        ShopfloorStatusSummary,
    };
    static props = {
        summary: Object,
        branchSummary: Object,
        onReportException: Function,
    };

    setup() {
        this.state = useState({
            pendingAction: null,
        });
    }

    get exceptionSummary() {
        return this.props.summary || { total: 0, openCount: 0, criticalCount: 0 };
    }

    get summaryItems() {
        return exceptionSummaryItems(this.exceptionSummary);
    }

    get branchSummary() {
        return this.props.branchSummary || { total: 0 };
    }

    get branchSummaryText() {
        return [
            `Claimed ${this.branchSummary.openCount || 0}`,
            `Acknowledged ${this.branchSummary.acknowledgedCount || 0}`,
            `Escalated ${this.branchSummary.blockedCount || 0}`,
            `Resolved ${this.branchSummary.resolvedCount || 0}`,
            `Closed ${this.branchSummary.closedCount || 0}`,
        ].join(" | ");
    }

    get actions() {
        return EXCEPTION_ACTIONS;
    }

    get pendingAction() {
        return this.state.pendingAction;
    }

    get hasPendingAction() {
        return Boolean(this.state.pendingAction);
    }

    get pendingActionTitle() {
        return this.state.pendingAction?.confirmLabel || "Confirm action";
    }

    get pendingActionSummary() {
        const action = this.state.pendingAction;
        if (!action) {
            return null;
        }
        return `${action.label} will move this exception to ${action.state} with ${action.severity} severity.`;
    }

    requestAction(ev) {
        const dataset = ev?.currentTarget?.dataset || {};
        this.state.pendingAction = {
            key: dataset.action || "follow_up",
            label: dataset.label || "Action",
            confirmLabel: dataset.confirmLabel || "Confirm action",
            message: dataset.message || "Exception action requested",
            severity: dataset.severity || "medium",
            state: dataset.state || "new",
            description: dataset.description || "",
            buttonClass: dataset.buttonClass || "btn-outline-secondary",
        };
    }

    confirmAction(ev) {
        this.props.onReportException?.(ev);
        this.state.pendingAction = null;
    }

    cancelAction(ev) {
        ev?.preventDefault?.();
        this.state.pendingAction = null;
    }

    reportException(ev) {
        this.props.onReportException?.(ev);
    }
}
