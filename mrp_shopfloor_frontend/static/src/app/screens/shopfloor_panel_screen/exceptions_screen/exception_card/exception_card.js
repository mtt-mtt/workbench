/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { ShopfloorAttentionNote } from "../../../../../components/shopfloor_status_components/shopfloor_attention_note";
import { ShopfloorFeedbackBar } from "../../../../../components/shopfloor_status_components/shopfloor_feedback_bar";
import { ShopfloorStatusBadge } from "../../../../../components/shopfloor_status_components/shopfloor_status_badge";
import {
    exceptionAttentionLabel,
    exceptionSeverityLabel,
    exceptionSeverityTone,
    exceptionStateLabel,
    exceptionStateTone,
} from "../../../../../components/shopfloor_status_components/shopfloor_status_metrics";
import {
    exceptionStateBranchDetail,
    exceptionStateBranchLabel,
    exceptionStateBranchTone,
} from "../../exception_filtering";

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

function normalizeTone(value) {
    const normalized = String(value || "secondary").trim().toLowerCase();
    if (normalized === "success" || normalized === "done") {
        return "success";
    }
    if (normalized === "warning" || normalized === "queued" || normalized === "submitted" || normalized === "acknowledged") {
        return "warning";
    }
    if (normalized === "danger" || normalized === "failed" || normalized === "error" || normalized === "attention") {
        return "danger";
    }
    if (normalized === "info" || normalized === "active" || normalized === "runtime") {
        return "info";
    }
    return "secondary";
}

export class ShopfloorExceptionCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExceptionCard";
    static components = {
        ShopfloorAttentionNote,
        ShopfloorFeedbackBar,
        ShopfloorStatusBadge,
    };
    static props = {
        item: Object,
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
    }

    get severityKey() {
        return String(this.props.item?.severityKey || this.props.item?.severity || "medium")
            .trim()
            .replace(/\s+/g, "_")
            .toLowerCase();
    }

    get severityLabel() {
        return this.props.item?.severityLabel || exceptionSeverityLabel(this.severityKey);
    }

    get severityToneClass() {
        return this.props.item?.severityTone || exceptionSeverityTone(this.severityKey);
    }

    get stateKey() {
        return String(this.props.item?.stateKey || this.props.item?.state || "new")
            .trim()
            .replace(/\s+/g, "_")
            .toLowerCase();
    }

    get stateLabel() {
        return this.props.item?.stateLabel || exceptionStateLabel(this.stateKey);
    }

    get stateToneClass() {
        return this.props.item?.stateTone || exceptionStateTone(this.stateKey);
    }

    get cardClass() {
        const classes = ["o_mrp_shopfloor_exception_card"];
        if (this.severityKey === "critical") {
            classes.push("border", "border-danger");
        } else if (this.severityKey === "high") {
            classes.push("border", "border-warning");
        } else {
            classes.push("border", "border-secondary");
        }
        return classes.join(" ");
    }

    get attentionLabel() {
        return exceptionAttentionLabel(this.severityKey, this.stateKey);
    }

    get attentionDetail() {
        if (!this.attentionLabel) {
            return null;
        }
        const parts = [this.severityLabel, this.stateLabel].filter(Boolean);
        return parts.length ? parts.join(" | ") : null;
    }

    get branchLabel() {
        return exceptionStateBranchLabel(this.stateKey);
    }

    get branchDetail() {
        return exceptionStateBranchDetail(this.stateKey);
    }

    get branchToneClass() {
        return exceptionStateBranchTone(this.stateKey);
    }

    get feedbackLabel() {
        return this.props.item?.label || this.props.item?.title || "Exception";
    }

    get feedbackDetail() {
        return (
            this.props.item?.resolutionNote ||
            this.props.item?.details ||
            this.branchDetail ||
            "Exception is waiting for the next operator action."
        );
    }

    get runtimeSummary() {
        return this.props.gatewayRuntimeSummary || null;
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

    get sharedProtocolRuntimeAttentionCount() {
        const sharedFeedback = this.sharedProtocolRuntimeFeedback;
        if (!sharedFeedback) {
            return null;
        }
        return sharedFeedback.attentionCount;
    }

    get runtimeAttentionLabel() {
        const sharedFeedback = this.sharedProtocolRuntimeFeedback;
        if (sharedFeedback) {
            return sharedFeedback.label;
        }
        return null;
    }

    get runtimeAttentionDetail() {
        const sharedFeedback = this.sharedProtocolRuntimeFeedback;
        if (sharedFeedback) {
            return sharedFeedback.detail || this.runtimeSummary?.summary || this.runtimeSummary?.detail;
        }
        return null;
    }

    get runtimeStateClass() {
        const sharedFeedback = this.sharedProtocolRuntimeFeedback;
        if (sharedFeedback) {
            return `badge rounded-pill text-bg-${normalizeTone(sharedFeedback.tone || "secondary")}`;
        }
        return `badge rounded-pill text-bg-${normalizeTone(
            this.props.latestRuntimeEntry?.statusTone ||
                this.props.latestRuntimeEntry?.status ||
                this.runtimeSummary?.stateTone ||
                this.runtimeSummary?.state ||
                "secondary"
        )}`;
    }

    get actions() {
        return EXCEPTION_ACTIONS;
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
        return `${action.label} will move this exception from ${this.branchLabel} to ${exceptionStateBranchLabel(action.state)} and set severity to ${exceptionSeverityLabel(action.severity)}.`;
    }

    get pendingActionToneClass() {
        return exceptionStateBranchTone(this.state.pendingAction?.state || this.stateKey);
    }

    get pendingActionSeverityToneClass() {
        return exceptionSeverityTone(this.state.pendingAction?.severity || this.severityKey);
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

    confirmAction() {
        const action = this.state.pendingAction;
        if (!action) {
            return;
        }
        this.props.onReportException?.({
            currentTarget: {
                dataset: {
                    action: action.key,
                    label: action.label,
                    confirmLabel: action.confirmLabel,
                    message:
                        action.message ||
                        this.props.item?.title ||
                        this.props.item?.message ||
                        "Exception action requested",
                    severity: action.severity,
                    state: action.state,
                    exceptionId: this.props.item?.id || null,
                    gatewayCommandCode: this.props.item?.gatewayCommandCode || null,
                    exceptionTitle: this.props.item?.title || null,
                },
            },
        });
        this.state.pendingAction = null;
    }

    cancelAction(ev) {
        ev?.preventDefault?.();
        this.state.pendingAction = null;
    }
}
