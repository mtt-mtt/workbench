/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDashboardSummaryCard } from "../../../../components/shopfloor_dashboard_cards/dashboard_summary_card";

export class ShopfloorDashboardLatestExecution extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardLatestExecution";
    static components = {
        ShopfloorDashboardSummaryCard,
    };
    static props = {
        execution: Object,
        selectedQueueItem: Object,
        selectedQueueContext: Object,
    };

    get executionSummaryCardProps() {
        return {
            label: "Latest execution",
            title: this.props.execution.label || this.props.execution.name,
            badges: [
                this.props.execution.stateLabel || this.props.execution.state || "no state",
                this.props.execution.reference || "no reference",
                this.props.execution.command_key || "no command",
            ],
        };
    }

    get queueSummaryCardProps() {
        const item = this.props.selectedQueueItem;
        const context = this.props.selectedQueueContext || {};
        return {
            label: "Selected queue item",
            title: item.name,
            badges: [
                item.workorder || "no workorder",
                item.priority || "no priority",
                `${item.done || 0} / ${item.quantity || 0}`,
                `WO ${context.workorder_id || "n/a"}`,
                `MO ${context.production_id || "n/a"}`,
                `Ref ${context.reference || "n/a"}`,
            ],
        };
    }
}
