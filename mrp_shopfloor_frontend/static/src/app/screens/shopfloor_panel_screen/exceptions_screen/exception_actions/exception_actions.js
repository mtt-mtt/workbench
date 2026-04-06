/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { ShopfloorFeedbackBar } from "../../../../../components/shopfloor_status_components/shopfloor_feedback_bar";
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
        ShopfloorFeedbackBar,
        ShopfloorStatusSummary,
    };
    static props = {
        summary: Object,
        branchSummary: Object,
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
        onReportException: Function,
    };

    setup() {
        this.state = useState({
            pendingAction: null,
        });
        this.onDocumentKeydown = (ev) => {
            if (ev?.key === "Escape" && this.hasPendingAction) {
                this.cancelAction(ev);
            }
        };
        onMounted(() => {
            document.addEventListener("keydown", this.onDocumentKeydown);
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", this.onDocumentKeydown);
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

    get sharedProtocolRuntimeFeedback() {
        const metrics = this.props.metrics || {};
        const sharedAttention = metrics.protocolRuntimeAttention;
        const attentionCount = sharedAttention === null || sharedAttention === undefined ? null : Number(sharedAttention) || 0;
        const label = metrics.protocolRuntimeLabel || null;
        const detail = metrics.protocolRuntimeDetail || null;
        const tone = String(metrics.protocolRuntimeTone || "").trim().toLowerCase() || null;
        if (!label && !detail && !tone && attentionCount === null) {
            return null;
        }
        const resolvedTone =
            tone ||
            (attentionCount !== null ? (attentionCount > 0 ? "warning" : "success") : null) ||
            "secondary";
        const resolvedLabel =
            label ||
            (attentionCount !== null
                ? attentionCount > 0
                    ? `Protocol runtime attention ${attentionCount}`
                    : "Protocol runtime ready"
                : resolvedTone === "danger"
                  ? "Protocol runtime error"
                  : resolvedTone === "warning"
                    ? "Protocol runtime attention"
                    : resolvedTone === "success"
                      ? "Protocol runtime ready"
                      : "Protocol runtime");
        const resolvedDetail =
            detail ||
            (attentionCount !== null
                ? attentionCount > 0
                    ? `${attentionCount} protocol runtime(s) need follow-up.`
                    : "Protocol runtime attention is clear."
                : `${resolvedLabel} reported.`);
        return {
            label: resolvedLabel,
            detail: resolvedDetail,
            tone: resolvedTone,
            attentionCount,
        };
    }

    get runtimeFeedback() {
        const sharedFeedback = this.sharedProtocolRuntimeFeedback;
        if (sharedFeedback) {
            return sharedFeedback;
        }
        const runtimeEntry = this.props.latestRuntimeEntry || null;
        const runtimeSummary = this.props.gatewayRuntimeSummary || null;
        if (runtimeEntry) {
            return {
                label: runtimeEntry.title || runtimeEntry.label || "Driver diagnostics",
                detail:
                    [runtimeEntry.detail, runtimeEntry.timestamp ? `Changed ${runtimeEntry.timestamp}` : null]
                        .filter(Boolean)
                        .join(" | ") || "Runtime event recorded.",
                tone: runtimeEntry.statusTone || runtimeEntry.status || "info",
            };
        }
        if (runtimeSummary) {
            return {
                label: runtimeSummary.label || "Driver diagnostics",
                detail: runtimeSummary.detail || runtimeSummary.summary || "Runtime diagnostics available.",
                tone: runtimeSummary.stateTone || runtimeSummary.state || "secondary",
            };
        }
        return null;
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

    get pendingActionTone() {
        const action = this.state.pendingAction;
        if (!action) {
            return "secondary";
        }
        if (action.severity === "critical") {
            return "danger";
        }
        if (action.severity === "medium") {
            return "warning";
        }
        if (action.severity === "low") {
            return "success";
        }
        return "secondary";
    }

    get pendingActionToneClass() {
        return `o_mrp_shopfloor_exception_modal--${this.pendingActionTone}`;
    }

    get pendingActionBadgeClass() {
        return `text-bg-${this.pendingActionTone}`;
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

    stopModalClick(ev) {
        ev?.stopPropagation?.();
    }

    reportException(ev) {
        this.props.onReportException?.(ev);
    }
}
