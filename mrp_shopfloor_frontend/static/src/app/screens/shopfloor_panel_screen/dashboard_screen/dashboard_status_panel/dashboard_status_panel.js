/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDashboardStatusCard } from "../../../../components/shopfloor_dashboard_cards/dashboard_status_card";

function getStatusBadgeClass(state) {
    const normalized = String(state || "secondary").replace(/\s+/g, "_").toLowerCase();
    if (normalized === "success") {
        return "badge rounded-pill text-bg-success";
    }
    if (normalized === "warning" || normalized === "queued") {
        return "badge rounded-pill text-bg-warning";
    }
    if (normalized === "danger" || normalized === "attention" || normalized === "failed") {
        return "badge rounded-pill text-bg-danger";
    }
    if (normalized === "info" || normalized === "active") {
        return "badge rounded-pill text-bg-info";
    }
    return "badge rounded-pill text-bg-secondary";
}

export class ShopfloorDashboardStatusPanel extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardStatusPanel";
    static components = {
        ShopfloorDashboardStatusCard,
    };
    static props = {
        responseSummary: Object,
        commandQueueStatus: Object,
        sessionRef: [String, Boolean],
        lastResponse: [Object, Boolean],
    };

    get statusCards() {
        return [
            {
                label: "API state",
                title: this.props.responseSummary.label || this.props.responseSummary.headline,
                stateLabel: this.props.responseSummary.stateLabel || this.props.responseSummary.state,
                stateClass: getStatusBadgeClass(this.props.responseSummary.stateTone || this.props.responseSummary.state),
                detail: this.props.responseSummary.detail,
                metaItems: [
                    `Session ${this.props.sessionRef || "n/a"}`,
                    `Last response ${this.props.lastResponse ? "available" : "seed only"}`,
                ],
            },
            {
                label: "Command queue status",
                title: this.props.commandQueueStatus.label,
                stateLabel: this.props.commandQueueStatus.stateLabel || this.props.commandQueueStatus.state,
                stateClass: getStatusBadgeClass(this.props.commandQueueStatus.stateTone || this.props.commandQueueStatus.state),
                detail: this.props.commandQueueStatus.detail,
                metaItems: [
                    `Total ${this.props.commandQueueStatus.total}`,
                    `Queued ${this.props.commandQueueStatus.queued}`,
                    `Running ${this.props.commandQueueStatus.running}`,
                    `Done ${this.props.commandQueueStatus.done}`,
                    `Failed ${this.props.commandQueueStatus.failed}`,
                ],
            },
        ];
    }
}
