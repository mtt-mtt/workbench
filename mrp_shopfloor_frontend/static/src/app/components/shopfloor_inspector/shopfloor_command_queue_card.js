/** @odoo-module **/

import { Component } from "@odoo/owl";
import { latestGatewayCommand, normalizeGatewayCommandEntry } from "../../screens/shopfloor_panel_screen/devices_screen/device_command_status";

export class ShopfloorCommandQueueCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorCommandQueueCard";
    static props = {
        commandQueueStatus: Object,
        commands: Array,
        exceptions: Array,
    };

    get latestFeedbackLabel() {
        return this.props.commandQueueStatus.latestLabel || this.props.commandQueueStatus.label || "Command queue";
    }

    get latestFeedbackDetail() {
        return this.props.commandQueueStatus.latestDetail || this.props.commandQueueStatus.detail || "No command response yet.";
    }

    get latestCommand() {
        return latestGatewayCommand(this.props.commands);
    }

    get latestCommandDisplay() {
        return this.latestCommand ? normalizeGatewayCommandEntry(this.latestCommand) : null;
    }

    get latestException() {
        return Array.isArray(this.props.exceptions) && this.props.exceptions.length ? this.props.exceptions[0] : null;
    }

    get actionSummary() {
        if (this.latestCommandDisplay) {
            const label = this.latestCommandDisplay.statusLabel || this.latestCommandDisplay.status || "pending";
            const name = this.latestCommandDisplay.name || this.latestCommandDisplay.code || "Command";
            const execution = this.latestCommandDisplay.printExecutionLabel || null;
            return execution ? `${name} is currently ${String(label).toLowerCase()} | ${execution}.` : `${name} is currently ${String(label).toLowerCase()}.`;
        }
        if (this.latestException) {
            return `Latest exception ${this.latestException.title || this.latestException.reference || this.latestException.id} is still active.`;
        }
        return "No command or exception feedback has reached the inspector yet.";
    }

    get latestPrintExecutionDetails() {
        return this.latestCommandDisplay?.printExecutionDetails || [];
    }
}
