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

function buildGatewayRuntimeNotice(summary, metrics) {
    if (!summary) {
        return null;
    }
    const openDriverIssues = Number(summary?.issueCounts?.open || 0);
    const protocolRuntime = summary?.protocolRuntime || {};
    const protocolRuntimeStateCounts = protocolRuntime.stateCounts || summary?.protocolRuntimeStateCounts || {};
    const hasSharedProtocolRuntimeAttention = metrics?.protocolRuntimeAttention !== undefined && metrics?.protocolRuntimeAttention !== null;
    const protocolRuntimeCount = Number(summary?.protocolRuntimeCount || protocolRuntime.count || 0);
    const protocolRuntimeEntryCount = Number(summary?.protocolRuntimeEntryCount || protocolRuntime.entryCount || 0);
    const protocolRuntimeSummary = summary?.protocolRuntimeSummary || protocolRuntime.summary || null;
    const protocolRuntimeState = String(summary?.protocolRuntimeState || protocolRuntime.state || protocolRuntime.stateKey || "")
        .trim()
        .toLowerCase();
    const protocolErrorCount = Number(protocolRuntimeStateCounts.error || 0);
    const protocolPendingCount = Number(protocolRuntimeStateCounts.pending || 0);
    const protocolUnavailableCount = Number(protocolRuntimeStateCounts.unavailable || 0);
    const protocolReadyCount = Number(protocolRuntimeStateCounts.ready || 0);
    const protocolRuntimeAttentionCount = hasSharedProtocolRuntimeAttention
        ? Number(metrics?.protocolRuntimeAttention || 0)
        : protocolErrorCount + protocolPendingCount + protocolUnavailableCount;
    const protocolRuntimeHasError = protocolRuntimeState === "error" || (!hasSharedProtocolRuntimeAttention && protocolErrorCount > 0);
    const protocolRuntimeNeedsFollowUp = protocolRuntimeState === "attention" || protocolRuntimeAttentionCount > 0;
    const protocolRuntimeNotice =
        protocolRuntimeHasError
            ? `${protocolErrorCount || protocolRuntimeAttentionCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) are reporting errors.`
            : protocolRuntimeNeedsFollowUp
              ? `${protocolRuntimeAttentionCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) need follow-up.`
              : protocolRuntimeCount > 0 || protocolRuntimeEntryCount > 0 || protocolReadyCount > 0
                ? `${protocolReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`
                : protocolRuntimeSummary;
    const edgeDeadLetterCount = Number(summary?.edgeDeadLetter?.count || 0);
    const edgeReplayPending = Number(summary?.edgeReplay?.pending || 0);
    const edgeReplayDue = Number(summary?.edgeReplay?.due || 0);
    const edgeReplayScheduled = Number(summary?.edgeReplay?.scheduled || 0);
    const edgeReplayOutcome = String(summary?.edgeReplay?.lastOutcome || "").trim().toLowerCase();
    const edgeActionProcessing = Number(summary?.edgeActionCounts?.processing || 0);

    if (openDriverIssues > 0) {
        return {
            tone: summary?.stateTone || summary?.state || "danger",
            title: summary?.label || "Driver issues open",
            detail:
                [
                    summary?.detail || summary?.summary || "Runtime driver attention is active.",
                    protocolRuntimeNotice ? `Protocol runtime: ${protocolRuntimeNotice}` : null,
                ]
                    .filter(Boolean)
                    .join(" "),
        };
    }
    if (edgeDeadLetterCount > 0) {
        return {
            tone: "danger",
            title: "Edge dead letters present",
            detail:
                summary?.edgeDeadLetter?.summary ||
                summary?.detail ||
                summary?.summary ||
                "Some outbound requests exhausted retry budget.",
        };
    }
    if (edgeReplayDue > 0) {
        return {
            tone: "warning",
            title: "Edge replay due",
            detail:
                summary?.edgeReplay?.lastSummary ||
                summary?.edgeReplay?.summary ||
                summary?.detail ||
                summary?.summary ||
                "Some offline requests are ready to replay.",
        };
    }
    if (edgeReplayScheduled > 0 && edgeReplayOutcome === "waiting_backoff") {
        return {
            tone: "info",
            title: "Edge replay cooling down",
            detail:
                summary?.edgeReplay?.lastSummary ||
                summary?.edgeReplay?.summary ||
                summary?.detail ||
                summary?.summary ||
                "Some offline requests are cooling down before the next retry.",
        };
    }
    if (edgeReplayPending > 0) {
        return {
            tone: "warning",
            title: "Edge replay pending",
            detail:
                summary?.edgeReplay?.summary ||
                summary?.detail ||
                summary?.summary ||
                "Some offline requests are still waiting to replay.",
        };
    }
    if (edgeActionProcessing > 0) {
        return {
            tone: "info",
            title: "Edge actions processing",
            detail:
                summary?.edgeActionSummary ||
                summary?.detail ||
                summary?.summary ||
                "Edge actions are currently being processed.",
        };
    }
    if (protocolRuntimeHasError) {
        return {
            tone: "danger",
            title: "Protocol runtime error",
            detail:
                protocolRuntimeSummary ||
                summary?.detail ||
                summary?.summary ||
                `${protocolErrorCount || protocolRuntimeAttentionCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) are reporting errors.`,
        };
    }
    if (protocolRuntimeNeedsFollowUp) {
        return {
            tone: "warning",
            title: "Protocol runtime attention",
            detail:
                protocolRuntimeSummary ||
                summary?.detail ||
                summary?.summary ||
                `${protocolRuntimeAttentionCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) need follow-up.`,
        };
    }
    if (protocolRuntimeSummary || protocolRuntimeCount || protocolRuntimeEntryCount || protocolReadyCount > 0) {
        return {
            tone: "info",
            title: "Protocol runtime ready",
            detail:
                protocolRuntimeNotice ||
                summary?.detail ||
                summary?.summary ||
                `${protocolReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`,
        };
    }
    return null;
}

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
        gatewayRuntimeSummary: [Object, Boolean],
        sessionRef: [String, Boolean],
        workstation: Object,
        metrics: Object,
        ui: [Object, Boolean],
        connectivity: Object,
        lastResponse: [Object, Boolean],
        onStartExecution: Function,
        onPauseExecution: Function,
        onFinishExecution: Function,
        onReportException: Function,
        onOpenQueueItem: Function,
        onOpenDevice: Function,
        onRefreshQueue: Function,
        onQueueDeviceAction: Function,
        onToggleFullscreen: Function,
        onToggleFocusMode: Function,
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
            gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
            sessionRef: this.props.sessionRef,
            lastResponse: this.props.lastResponse,
            ui: this.props.ui,
            onStartExecution: this.props.onStartExecution,
            onPauseExecution: this.props.onPauseExecution,
            onFinishExecution: this.props.onFinishExecution,
            onReportException: this.props.onReportException,
            onRefreshQueue: this.props.onRefreshQueue,
            onToggleFullscreen: this.props.onToggleFullscreen,
            onToggleFocusMode: this.props.onToggleFocusMode,
        };
    }

    get panelNotice() {
        const connectivity = this.props.connectivity || {};
        if (connectivity.state && connectivity.state !== "online") {
            return {
                tone: connectivity.tone || "danger",
                title: connectivity.label || "Offline",
                detail: connectivity.detail || "The workstation is temporarily using local fallback data.",
            };
        }
        if (connectivity.recovered) {
            return {
                tone: connectivity.tone || "success",
                title: connectivity.lastTransitionLabel || "Recovered",
                detail: connectivity.detail || "The workstation connection has been restored.",
            };
        }
        const gatewayRuntimeNotice = buildGatewayRuntimeNotice(this.props.gatewayRuntimeSummary, this.props.metrics);
        if (gatewayRuntimeNotice) {
            return gatewayRuntimeNotice;
        }
        if (this.props.currentPanel === "queue" && !this._hasRealItem(this.props.queue, "QUEUE-EMPTY")) {
            return {
                tone: "secondary",
                title: "Queue is empty",
                detail: "No queue item is ready for this workstation yet.",
            };
        }
        if (this.props.currentPanel === "devices" && !this._hasRealItem(this.props.devices, "DEVICE-EMPTY")) {
            return {
                tone: "secondary",
                title: "No devices linked",
                detail: "Link a device or wait for runtime discovery to populate this screen.",
            };
        }
        if (this.props.currentPanel === "exceptions" && !(this.props.exceptions || []).length) {
            return {
                tone: "secondary",
                title: "No active exceptions",
                detail: "This workstation currently has no active exception records.",
            };
        }
        if (this.props.currentPanel === "execution" && !this.props.selectedQueueContext?.reference) {
            return {
                tone: "secondary",
                title: "No execution selected",
                detail: "Pick a queue item to load execution details and operator actions.",
            };
        }
        return null;
    }

    _hasRealItem(list = [], emptyCode) {
        return (list || []).some((item) => item && item.code !== emptyCode && item.id !== emptyCode && item.queue_id !== emptyCode);
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
                    logEntries: this.props.logEntries,
                    gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
                    metrics: this.props.metrics,
                };
            case "execution":
                return {
                    ...shared,
                    execution: this.props.execution,
                    selectedQueueItem: this.props.selectedQueueItem,
                    selectedQueueContext: this.props.selectedQueueContext,
                    logEntries: this.props.logEntries,
                    gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
                    workstation: this.props.workstation,
                    sessionRef: this.props.sessionRef,
                    metrics: this.props.metrics,
                };
            case "devices":
                return {
                    ...shared,
                    devices: this.props.devices,
                    selectedDevice: this.props.selectedDevice,
                    commands: this.props.commands,
                    logEntries: this.props.logEntries,
                    gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
                    metrics: this.props.metrics,
                };
            case "exceptions":
                return {
                    ...shared,
                    exceptions: this.props.exceptions,
                    logEntries: this.props.logEntries,
                    gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
                    metrics: this.props.metrics,
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
                    gatewayRuntimeSummary: this.props.gatewayRuntimeSummary,
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
