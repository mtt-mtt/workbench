/** @odoo-module **/

import { Component } from "@odoo/owl";
import { getShopfloorRouteMeta } from "../../router/shopfloor_router";
import { ShopfloorWorkspaceShell } from "../../components/shopfloor_workspace_shell/shopfloor_workspace_shell";
import { ShopfloorDashboardScreen } from "./dashboard_screen/dashboard_screen";
import { ShopfloorQueueScreen } from "./queue_screen/queue_screen";
import { ShopfloorExecutionScreen } from "./execution_screen/execution_screen";
import { ShopfloorDevicesScreen } from "./devices_screen/devices_screen";
import { ShopfloorExceptionsScreen } from "./exceptions_screen/exceptions_screen";

const PANEL_COMPONENTS = {
    dashboard: ShopfloorDashboardScreen,
    queue: ShopfloorQueueScreen,
    execution: ShopfloorExecutionScreen,
    devices: ShopfloorDevicesScreen,
    exceptions: ShopfloorExceptionsScreen,
};

export class ShopfloorPanelScreen extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorPanelScreen";
    static components = {
        ShopfloorWorkspaceShell,
    };
    static props = {
        currentPanel: String,
        queue: Array,
        devices: Array,
        exceptions: Array,
        commands: Array,
        timelineEntries: Array,
        logEntries: Array,
        execution: Object,
        selectedQueueItem: Object,
        selectedQueueContext: Object,
        selectedDevice: Object,
        responseSummary: Object,
        commandQueueStatus: Object,
        sessionRef: [String, Boolean],
        workstation: Object,
        metrics: Object,
        lastResponse: [Object, Boolean],
        onStartExecution: Function,
        onPauseExecution: Function,
        onFinishExecution: Function,
        onReportException: Function,
        onOpenQueueItem: Function,
        onOpenDevice: Function,
        onRefreshQueue: Function,
        onQueueDeviceAction: Function,
    };

    get activeScreen() {
        return PANEL_COMPONENTS[this.props.currentPanel] || PANEL_COMPONENTS.dashboard;
    }

    get workspaceShellProps() {
        return {
            currentPanel: this.props.currentPanel,
            workstation: this.props.workstation,
            metrics: this.props.metrics,
            commandQueueStatus: this.props.commandQueueStatus,
            sessionRef: this.props.sessionRef,
            lastResponse: this.props.lastResponse,
        };
    }

    get currentPanelMeta() {
        const meta = getShopfloorRouteMeta(this.props.currentPanel) || {};
        return {
            key: this.props.currentPanel || "dashboard",
            label: meta.label || "Dashboard",
            group: meta.group || "Workspace",
            description: meta.description || "Active shopfloor panel",
        };
    }

    get activeScreenProps() {
        const shared = {
            onStartExecution: this.props.onStartExecution,
            onPauseExecution: this.props.onPauseExecution,
            onFinishExecution: this.props.onFinishExecution,
            onReportException: this.props.onReportException,
            onOpenQueueItem: this.props.onOpenQueueItem,
            onOpenDevice: this.props.onOpenDevice,
            onRefreshQueue: this.props.onRefreshQueue,
            onQueueDeviceAction: this.props.onQueueDeviceAction,
        };

        switch (this.props.currentPanel) {
            case "queue":
                return {
                    ...shared,
                    queue: this.props.queue,
                    selectedQueueItem: this.props.selectedQueueItem,
                    selectedQueueContext: this.props.selectedQueueContext,
                };
            case "execution":
                return {
                    ...shared,
                    execution: this.props.execution,
                    selectedQueueItem: this.props.selectedQueueItem,
                    selectedQueueContext: this.props.selectedQueueContext,
                    logEntries: this.props.logEntries,
                    workstation: this.props.workstation,
                    sessionRef: this.props.sessionRef,
                };
            case "devices":
                return {
                    ...shared,
                    devices: this.props.devices,
                    selectedDevice: this.props.selectedDevice,
                    commands: this.props.commands,
                };
            case "exceptions":
                return {
                    ...shared,
                    exceptions: this.props.exceptions,
                };
            case "dashboard":
            default:
                return {
                    ...shared,
                    queue: this.props.queue,
                    execution: this.props.execution,
                    selectedQueueItem: this.props.selectedQueueItem,
                    selectedQueueContext: this.props.selectedQueueContext,
                    responseSummary: this.props.responseSummary,
                    commandQueueStatus: this.props.commandQueueStatus,
                    sessionRef: this.props.sessionRef,
                    workstation: this.props.workstation,
                    metrics: this.props.metrics,
                    commands: this.props.commands,
                    exceptions: this.props.exceptions,
                    lastResponse: this.props.lastResponse,
                };
        }
    }

    startExecution(ev) {
        this.props.onStartExecution?.(ev);
    }

    pauseExecution(ev) {
        this.props.onPauseExecution?.(ev);
    }

    finishExecution(ev) {
        this.props.onFinishExecution?.(ev);
    }

    reportException(ev) {
        this.props.onReportException?.(ev);
    }

    openQueueItem(ev) {
        this.props.onOpenQueueItem?.(ev);
    }

    openDevice(ev) {
        this.props.onOpenDevice?.(ev);
    }

    refreshQueue(ev) {
        this.props.onRefreshQueue?.(ev);
    }
}
