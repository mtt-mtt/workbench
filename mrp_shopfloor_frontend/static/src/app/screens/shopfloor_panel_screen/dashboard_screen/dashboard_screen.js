/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDashboardActionBar } from "./dashboard_action_bar/dashboard_action_bar";
import { ShopfloorDashboardLatestExecution } from "./dashboard_latest_execution/dashboard_latest_execution";
import { ShopfloorDashboardOverviewTiles } from "./dashboard_overview_tiles/dashboard_overview_tiles";
import { ShopfloorDashboardStatusPanel } from "./dashboard_status_panel/dashboard_status_panel";

export class ShopfloorDashboardScreen extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardScreen";
    static components = {
        ShopfloorDashboardActionBar,
        ShopfloorDashboardLatestExecution,
        ShopfloorDashboardOverviewTiles,
        ShopfloorDashboardStatusPanel,
    };
    static props = {
        queue: Array,
        execution: Object,
        selectedQueueItem: Object,
        selectedQueueContext: Object,
        responseSummary: Object,
        commandQueueStatus: Object,
        sessionRef: [String, Boolean],
        workstation: Object,
        metrics: Object,
        commands: Array,
        exceptions: Array,
        gatewayRuntimeSummary: [Object, Boolean],
        lastResponse: [Object, Boolean],
        onStartExecution: Function,
        onPauseExecution: Function,
        onFinishExecution: Function,
    };

    get actionBarProps() {
        return {
            onStartExecution: this.props.onStartExecution,
            onPauseExecution: this.props.onPauseExecution,
            onFinishExecution: this.props.onFinishExecution,
        };
    }

    get overviewTilesProps() {
        return {
            queue: this.props.queue,
            execution: this.props.execution,
            commands: this.props.commands,
            exceptions: this.props.exceptions,
            responseSummary: this.props.responseSummary,
            commandQueueStatus: this.props.commandQueueStatus,
            gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
            metrics: this.props.metrics,
        };
    }

    get latestExecutionProps() {
        return {
            execution: this.props.execution,
            selectedQueueItem: this.props.selectedQueueItem,
            selectedQueueContext: this.props.selectedQueueContext,
            commands: this.props.commands,
            logEntries: this.props.logEntries,
        };
    }

    get statusPanelProps() {
        return {
            responseSummary: this.props.responseSummary,
            commandQueueStatus: this.props.commandQueueStatus,
            sessionRef: this.props.sessionRef,
            lastResponse: this.props.lastResponse,
            commands: this.props.commands,
            gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
            metrics: this.props.metrics,
            logEntries: this.props.logEntries,
        };
    }
}
