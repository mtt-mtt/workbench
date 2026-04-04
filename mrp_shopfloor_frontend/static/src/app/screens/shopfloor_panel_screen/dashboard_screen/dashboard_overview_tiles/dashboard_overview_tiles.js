/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDashboardKpiTile } from "../../../../components/shopfloor_dashboard_cards/dashboard_kpi_tile";

export class ShopfloorDashboardOverviewTiles extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardOverviewTiles";
    static components = {
        ShopfloorDashboardKpiTile,
    };
    static props = {
        queue: Array,
        execution: Object,
        commands: Array,
        exceptions: Array,
        responseSummary: Object,
        commandQueueStatus: Object,
    };

    get tiles() {
        return [
            {
                label: "Queue",
                value: this.props.queue.length,
                hint: "items waiting or active",
            },
            {
                label: "Execution",
                value: this.props.execution.stateLabel || this.props.execution.state,
                hint: this.props.execution.action_type,
            },
            {
                label: "Commands",
                value: this.props.commandQueueStatus?.stateLabel || this.props.commandQueueStatus?.state || this.props.commands.length,
                hint: this.props.commandQueueStatus?.detail || "queued or completed",
            },
            {
                label: "Exceptions",
                value: this.props.exceptions.length,
                hint: this.props.responseSummary?.stateLabel
                    ? `API ${this.props.responseSummary.stateLabel.toLowerCase()}`
                    : "open operator issues",
            },
        ];
    }
}
