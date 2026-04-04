/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorFeedbackBar } from "../../../../../components/shopfloor_status_components/shopfloor_feedback_bar";
import { ShopfloorStatusBadge } from "../../../../../components/shopfloor_status_components/shopfloor_status_badge";
import { ShopfloorStatusSummary } from "../../../../../components/shopfloor_status_components/shopfloor_status_summary";
import { gatewayCommandFeedback, gatewayCommandSummaryItems, summarizeGatewayCommands } from "../device_command_status";

export class ShopfloorDeviceActionConfirm extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceActionConfirm";
    static components = {
        ShopfloorFeedbackBar,
        ShopfloorStatusBadge,
        ShopfloorStatusSummary,
    };
    static props = {
        actionDraft: Object,
        commandSummary: {
            type: Object,
            optional: true,
        },
        onConfirmAction: Function,
        onCancelAction: Function,
    };

    get hasDraft() {
        return Boolean(this.props.actionDraft);
    }

    get commandSummary() {
        return this.props.commandSummary || summarizeGatewayCommands([]);
    }

    get commandSummaryItems() {
        return gatewayCommandSummaryItems(this.commandSummary);
    }

    get commandFeedback() {
        return gatewayCommandFeedback(this.commandSummary);
    }

    get hasCommandSummary() {
        return Boolean(this.commandSummary && this.commandSummary.total);
    }

    get commandStateTone() {
        return this.commandSummary?.latestStateTone || "info";
    }

    get commandStateLabel() {
        return this.commandSummary?.latestStateLabel || "Queued";
    }

    get commandStateDetail() {
        if (!this.commandSummary?.total) {
            return "No backend queue yet.";
        }
        return this.commandSummary?.latestCommandDetail || this.commandFeedback.detail;
    }

    get commandLifecycle() {
        const latest = String(this.commandSummary?.latestState || "").toLowerCase();
        return [
            { key: "queued", label: "Queued", active: ["queued", "draft"].includes(latest) },
            { key: "sent", label: "Sent", active: latest === "sent" },
            { key: "acknowledged", label: "Acknowledged", active: latest === "acknowledged" },
            { key: "done", label: "Done", active: latest === "done" },
            { key: "failed", label: "Failed", active: latest === "failed" },
        ];
    }

    noopFeedbackAction(ev) {
        ev?.preventDefault?.();
    }

    get visibilityLabel() {
        if (!this.props.actionDraft) {
            return null;
        }
        return this.props.actionDraft.selectedVisible === false
            ? "Selected device is hidden by the current filters."
            : null;
    }

    confirmAction(ev) {
        this.props.onConfirmAction?.(ev);
    }

    cancelAction(ev) {
        this.props.onCancelAction?.(ev);
    }
}
