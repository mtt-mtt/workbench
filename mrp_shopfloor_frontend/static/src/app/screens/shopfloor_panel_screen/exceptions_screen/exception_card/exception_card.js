/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { ShopfloorAttentionNote } from "../../../../../components/shopfloor_status_components/shopfloor_attention_note";
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

export class ShopfloorExceptionCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExceptionCard";
    static components = {
        ShopfloorAttentionNote,
        ShopfloorStatusBadge,
    };
    static props = {
        item: Object,
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
