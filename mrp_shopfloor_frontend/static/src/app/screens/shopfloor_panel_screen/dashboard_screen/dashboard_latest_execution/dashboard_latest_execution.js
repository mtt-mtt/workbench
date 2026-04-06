/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDashboardSummaryCard } from "../../../../components/shopfloor_dashboard_cards/dashboard_summary_card";
import {
    findLatestRuntimeEntry,
    isProtocolRuntimeEntry,
    normalizeRuntimeEntry,
} from "../../../../utils/shopfloor_runtime_entries";
import { latestGatewayCommand, normalizeGatewayCommandEntry } from "../../devices_screen/device_command_status";

function buildDriverDiagnosticBadges(printExecution) {
    if (!printExecution) {
        return [];
    }
    return [
        printExecution.driverOrigin ? `Driver ${printExecution.driverOrigin}` : null,
        printExecution.driverLabel ? `Label ${printExecution.driverLabel}` : null,
        printExecution.driverType ? `Type ${printExecution.driverType}` : null,
        printExecution.driverReady === true ? "Driver ready" : printExecution.driverReady === false ? "Driver not ready" : null,
        printExecution.driverCapabilities?.status_polling_supported === true
            ? "Polling supported"
            : printExecution.driverCapabilities?.status_polling_supported === false
              ? "Polling limited"
              : null,
    ].filter(Boolean);
}

function buildRuntimeBadges(runtimeEntry) {
    if (!runtimeEntry) {
        return [];
    }
    const badges = [];
    const isProtocolRuntime = isProtocolRuntimeEntry(runtimeEntry);

    if (isProtocolRuntime) {
        badges.push(runtimeEntry.label || runtimeEntry.title || "Protocol runtime");
        if (runtimeEntry.detail && runtimeEntry.detail !== runtimeEntry.label && runtimeEntry.detail !== runtimeEntry.title) {
            badges.push(runtimeEntry.detail);
        }
        if (runtimeEntry.statusLabel) {
            badges.push(`Runtime ${runtimeEntry.statusLabel}`);
        } else if (runtimeEntry.statusTone || runtimeEntry.status) {
            badges.push(`Runtime ${runtimeEntry.statusTone || runtimeEntry.status}`);
        }
        if (runtimeEntry.timestamp) {
            badges.push(`Runtime ${runtimeEntry.timestamp}`);
        }
        return badges;
    }

    badges.push(runtimeEntry.title || runtimeEntry.label);
    if (runtimeEntry.statusLabel) {
        badges.push(`Runtime ${runtimeEntry.statusLabel}`);
    }
    if (runtimeEntry.timestamp) {
        badges.push(`Runtime ${runtimeEntry.timestamp}`);
    }
    return badges.filter(Boolean);
}

export class ShopfloorDashboardLatestExecution extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardLatestExecution";
    static components = {
        ShopfloorDashboardSummaryCard,
    };
    static props = {
        execution: Object,
        selectedQueueItem: Object,
        selectedQueueContext: Object,
        commands: Array,
        logEntries: Array,
    };

    get latestCommandDisplay() {
        const latestCommand = latestGatewayCommand(this.props.commands || []);
        return latestCommand ? normalizeGatewayCommandEntry(latestCommand) : null;
    }

    get executionSummaryCardProps() {
        const latestCommand = this.latestCommandDisplay;
        const latestRuntime = normalizeRuntimeEntry(findLatestRuntimeEntry(this.props.logEntries || []));
        const badges = [
            this.props.execution.stateLabel || this.props.execution.state || "no state",
            this.props.execution.reference || "no reference",
            this.props.execution.command_key || "no command",
        ];
        badges.push(...buildRuntimeBadges(latestRuntime));
        if (latestCommand?.printExecutionLabel) {
            badges.push(latestCommand.printExecutionLabel);
        }
        if (latestCommand?.printExecution) {
            badges.push(...buildDriverDiagnosticBadges(latestCommand.printExecution));
        }
        if (latestCommand?.printExecutionDetails?.length) {
            badges.push(...latestCommand.printExecutionDetails.slice(0, 4).map((item) => item.label));
        }
        return {
            label: "Latest execution",
            title: this.props.execution.label || this.props.execution.name,
            badges,
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
