/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDashboardStatusCard } from "../../../../components/shopfloor_dashboard_cards/dashboard_status_card";
import { findLatestRuntimeEntry, normalizeRuntimeEntry } from "../../../../utils/shopfloor_runtime_entries";
import { latestGatewayCommand, normalizeGatewayCommandEntry } from "../../devices_screen/device_command_status";

function buildDriverDiagnosticMeta(printExecution) {
    if (!printExecution) {
        return [];
    }
    return [
        printExecution.driverOrigin ? `Driver ${printExecution.driverOrigin}` : null,
        printExecution.driverLabel ? `Driver label ${printExecution.driverLabel}` : null,
        printExecution.driverType ? `Driver type ${printExecution.driverType}` : null,
        printExecution.driverReady === true ? "Driver ready" : printExecution.driverReady === false ? "Driver not ready" : null,
        printExecution.driverCapabilities?.supports_refresh_status === true
            ? "Refresh-status supported"
            : printExecution.driverCapabilities?.supports_refresh_status === false
              ? "Refresh-status unavailable"
              : null,
        printExecution.driverCapabilities?.status_polling_supported === true
            ? "Polling supported"
            : printExecution.driverCapabilities?.status_polling_supported === false
              ? "Polling limited"
              : null,
    ].filter(Boolean);
}

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

function buildGatewayRuntimeAttention(gatewayRuntime = {}, sharedMetrics = {}) {
    const issueCounts = gatewayRuntime.issueCounts || {};
    const edgeReplay = gatewayRuntime.edgeReplay || {};
    const edgeDeadLetter = gatewayRuntime.edgeDeadLetter || {};
    const edgeActionCounts = gatewayRuntime.edgeActionCounts || {};
    const protocolRuntime = gatewayRuntime.protocolRuntime || {};
    const protocolRuntimeStateCounts = protocolRuntime.stateCounts || gatewayRuntime.protocolRuntimeStateCounts || {};
    const protocolRuntimeCount = protocolRuntime.count || gatewayRuntime.protocolRuntimeCount || 0;
    const protocolRuntimeEntryCount = protocolRuntime.entryCount || gatewayRuntime.protocolRuntimeEntryCount || 0;
    const protocolRuntimeSummary =
        protocolRuntime.summary || gatewayRuntime.protocolRuntimeSummary || gatewayRuntime.protocolRuntime?.summary || null;
    const sharedProtocolRuntimeAttention = sharedMetrics?.protocolRuntimeAttention;
    const sharedProtocolRuntimeLabel = sharedMetrics?.protocolRuntimeLabel || null;
    const sharedProtocolRuntimeDetail = sharedMetrics?.protocolRuntimeDetail || null;
    const sharedProtocolRuntimeTone = String(sharedMetrics?.protocolRuntimeTone || "").trim().toLowerCase() || null;
    const hasSharedProtocolRuntimeAttention =
        sharedProtocolRuntimeAttention !== undefined && sharedProtocolRuntimeAttention !== null;
    const protocolRuntimeAttentionCount = hasSharedProtocolRuntimeAttention
        ? Number(sharedProtocolRuntimeAttention) || 0
        : Number(protocolRuntimeStateCounts.error || 0) +
          Number(protocolRuntimeStateCounts.pending || 0) +
          Number(protocolRuntimeStateCounts.unavailable || 0);
    const protocolErrorCount = protocolRuntimeStateCounts.error || 0;
    const protocolPendingCount = protocolRuntimeStateCounts.pending || 0;
    const protocolUnavailableCount = protocolRuntimeStateCounts.unavailable || 0;
    const protocolReadyCount = protocolRuntimeStateCounts.ready || 0;
    if ((issueCounts.open || 0) > 0) {
        return {
            title: "Driver issues open",
            stateLabel: "Danger",
            stateClass: getStatusBadgeClass("danger"),
            detail:
                gatewayRuntime.summary ||
                gatewayRuntime.detail ||
                `${issueCounts.open} driver issue(s) still need follow-up.`,
        };
    }
    if ((edgeDeadLetter.count || 0) > 0) {
        return {
            title: "Edge dead letters present",
            stateLabel: "Danger",
            stateClass: getStatusBadgeClass("danger"),
            detail:
                edgeDeadLetter.summary ||
                gatewayRuntime.detail ||
                `${edgeDeadLetter.count} dead letter(s) still need review.`,
        };
    }
    if ((edgeReplay.due || 0) > 0) {
        return {
            title: "Edge replay due",
            stateLabel: "Warning",
            stateClass: getStatusBadgeClass("warning"),
            detail:
                edgeReplay.lastSummary ||
                edgeReplay.summary ||
                gatewayRuntime.detail ||
                `${edgeReplay.due} replay item(s) are ready to resend.`,
        };
    }
    if ((edgeReplay.pending || 0) > 0) {
        return {
            title: edgeReplay.lastOutcome === "waiting_backoff" ? "Edge replay cooling down" : "Edge replay pending",
            stateLabel: edgeReplay.lastOutcome === "waiting_backoff" ? "Info" : "Warning",
            stateClass: getStatusBadgeClass(edgeReplay.lastOutcome === "waiting_backoff" ? "info" : "warning"),
            detail:
                edgeReplay.lastSummary ||
                edgeReplay.summary ||
                gatewayRuntime.detail ||
                `${edgeReplay.pending} replay item(s) are still pending.`,
        };
    }
    if ((edgeActionCounts.processing || 0) > 0) {
        return {
            title: "Edge actions processing",
            stateLabel: "Info",
            stateClass: getStatusBadgeClass("info"),
            detail:
                gatewayRuntime.edgeActionSummary ||
                gatewayRuntime.detail ||
                `${edgeActionCounts.processing} edge action(s) are still processing.`,
        };
    }
    if (sharedProtocolRuntimeLabel || sharedProtocolRuntimeDetail || sharedProtocolRuntimeTone || hasSharedProtocolRuntimeAttention) {
        if (sharedProtocolRuntimeTone === "danger" || (hasSharedProtocolRuntimeAttention && protocolErrorCount > 0)) {
            return {
                title: sharedProtocolRuntimeLabel || "Protocol runtime error",
                stateLabel: "Danger",
                stateClass: getStatusBadgeClass("danger"),
                detail:
                    sharedProtocolRuntimeDetail ||
                    protocolRuntimeSummary ||
                    gatewayRuntime.detail ||
                    `${protocolRuntimeAttentionCount || protocolErrorCount || protocolRuntimeEntryCount || protocolRuntimeCount} protocol runtime(s) are reporting errors.`,
            };
        }
        if (sharedProtocolRuntimeAttention > 0 || sharedProtocolRuntimeTone === "warning" || protocolPendingCount > 0 || protocolUnavailableCount > 0) {
            return {
                title: sharedProtocolRuntimeLabel || "Protocol runtime attention",
                stateLabel: "Warning",
                stateClass: getStatusBadgeClass("warning"),
                detail:
                    sharedProtocolRuntimeDetail ||
                    protocolRuntimeSummary ||
                    gatewayRuntime.detail ||
                    `${protocolRuntimeAttentionCount || protocolPendingCount + protocolUnavailableCount || protocolRuntimeEntryCount || protocolRuntimeCount} protocol runtime(s) need follow-up.`,
            };
        }
        return {
            title: sharedProtocolRuntimeLabel || "Protocol runtime ready",
            stateLabel: "Success",
            stateClass: getStatusBadgeClass("success"),
            detail:
                sharedProtocolRuntimeDetail ||
                protocolRuntimeSummary ||
                gatewayRuntime.detail ||
                `${protocolReadyCount || protocolRuntimeEntryCount || protocolRuntimeCount} protocol runtime(s) reported ready.`,
        };
    }
    if (hasSharedProtocolRuntimeAttention) {
        if (protocolRuntimeAttentionCount > 0) {
            return {
                title: "Protocol runtime attention",
                stateLabel: "Warning",
                stateClass: getStatusBadgeClass("warning"),
                detail:
                    protocolRuntimeSummary ||
                    gatewayRuntime.detail ||
                    `${protocolRuntimeAttentionCount} protocol runtime(s) need follow-up.`,
            };
        }
        if (protocolRuntimeSummary || protocolRuntimeCount || protocolRuntimeEntryCount) {
            return {
                title: "Protocol runtime ready",
                stateLabel: "Success",
                stateClass: getStatusBadgeClass("success"),
                detail:
                    protocolRuntimeSummary ||
                    gatewayRuntime.detail ||
                    `${protocolReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`,
            };
        }
    } else if (protocolRuntimeSummary || protocolRuntimeCount || protocolRuntimeEntryCount) {
        if (protocolErrorCount > 0) {
            return {
                title: "Protocol runtime error",
                stateLabel: "Danger",
                stateClass: getStatusBadgeClass("danger"),
                detail:
                    protocolRuntimeSummary ||
                    gatewayRuntime.detail ||
                    `${protocolErrorCount} protocol runtime(s) are reporting errors.`,
            };
        }
        if (protocolPendingCount > 0 || protocolUnavailableCount > 0) {
            return {
                title: "Protocol runtime attention",
                stateLabel: "Warning",
                stateClass: getStatusBadgeClass("warning"),
                detail:
                    protocolRuntimeSummary ||
                    gatewayRuntime.detail ||
                    `${protocolPendingCount + protocolUnavailableCount} protocol runtime(s) need follow-up.`,
            };
        }
        return {
            title: "Protocol runtime ready",
            stateLabel: "Success",
            stateClass: getStatusBadgeClass("success"),
            detail:
                protocolRuntimeSummary ||
                gatewayRuntime.detail ||
                `${protocolReadyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`,
        };
    }
    return {
        title: gatewayRuntime.label || "Driver diagnostics unavailable",
        stateLabel: gatewayRuntime.stateLabel || "Secondary",
        stateClass: getStatusBadgeClass(gatewayRuntime.stateTone || gatewayRuntime.state || "secondary"),
        detail: gatewayRuntime.detail || gatewayRuntime.summary || "Runtime driver diagnostics are not available yet.",
    };
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
        commands: Array,
        metrics: [Object, Boolean],
        gatewayRuntimeSummary: [Object, Boolean],
        logEntries: Array,
    };

    get latestCommandDisplay() {
        const latestCommand = latestGatewayCommand(this.props.commands || []);
        return latestCommand ? normalizeGatewayCommandEntry(latestCommand) : null;
    }

    get statusCards() {
        const latestCommand = this.latestCommandDisplay;
        const latestRuntime = normalizeRuntimeEntry(findLatestRuntimeEntry(this.props.logEntries || []));
        const sharedMetrics = this.props.metrics || {};
        const latestPrintExecution = latestCommand?.printExecutionLabel || null;
        const latestPrintExecutionDetails = latestCommand?.printExecutionDetails || [];
        const gatewayRuntime = this.props.gatewayRuntimeSummary || {};
        const gatewayIssueCounts = gatewayRuntime.issueCounts || {};
        const gatewayDriverCounts = gatewayRuntime.driverCounts || {};
        const edgeReplay = gatewayRuntime.edgeReplay || {};
        const edgeDeadLetter = gatewayRuntime.edgeDeadLetter || {};
        const protocolRuntimeStateCounts = gatewayRuntime.protocolRuntimeStateCounts || gatewayRuntime.protocolRuntime?.stateCounts || {};
        const sharedProtocolRuntimeLabel = sharedMetrics.protocolRuntimeLabel || null;
        const sharedProtocolRuntimeDetail = sharedMetrics.protocolRuntimeDetail || null;
        const sharedProtocolRuntimeTone = sharedMetrics.protocolRuntimeTone || null;
        const sharedProtocolRuntimeAttention =
            sharedMetrics.protocolRuntimeAttention !== null && sharedMetrics.protocolRuntimeAttention !== undefined
                ? Number(sharedMetrics.protocolRuntimeAttention) || 0
                : null;
        const runtimeAttention = buildGatewayRuntimeAttention(gatewayRuntime, sharedMetrics);
        const filterMetaItems = (items) => items.filter(Boolean);
        return [
            {
                label: "API state",
                title: this.props.responseSummary.label || this.props.responseSummary.headline,
                stateLabel: this.props.responseSummary.stateLabel || this.props.responseSummary.state,
                stateClass: getStatusBadgeClass(this.props.responseSummary.stateTone || this.props.responseSummary.state),
                detail: this.props.responseSummary.detail,
                metaItems: filterMetaItems([
                    `Session ${this.props.sessionRef || "n/a"}`,
                    `Last response ${this.props.lastResponse ? "available" : "seed only"}`,
                    this.props.responseSummary.feedbackLabel ? `Feedback ${this.props.responseSummary.feedbackLabel}` : null,
                    this.props.responseSummary.feedbackDetail ? `Detail ${this.props.responseSummary.feedbackDetail}` : null,
                ]),
            },
            {
                label: "Command queue status",
                title: this.props.commandQueueStatus.label,
                stateLabel: this.props.commandQueueStatus.stateLabel || this.props.commandQueueStatus.state,
                stateClass: getStatusBadgeClass(this.props.commandQueueStatus.stateTone || this.props.commandQueueStatus.state),
                detail: this.props.commandQueueStatus.detail,
                metaItems: filterMetaItems([
                    `Total ${this.props.commandQueueStatus.total}`,
                    `Queued ${this.props.commandQueueStatus.queued}`,
                    `Running ${this.props.commandQueueStatus.running}`,
                    `Done ${this.props.commandQueueStatus.done}`,
                    `Failed ${this.props.commandQueueStatus.failed}`,
                    this.props.commandQueueStatus.latestLabel ? `Latest ${this.props.commandQueueStatus.latestLabel}` : null,
                    this.props.commandQueueStatus.latestDetail ? `Latest detail ${this.props.commandQueueStatus.latestDetail}` : null,
                    latestPrintExecution ? `Print ${latestPrintExecution}` : null,
                    ...buildDriverDiagnosticMeta(latestCommand?.printExecution),
                    ...latestPrintExecutionDetails.map((item) => `Print ${item.label}`),
                ]),
            },
            {
                label: "Gateway runtime attention",
                title: runtimeAttention.title,
                stateLabel: runtimeAttention.stateLabel,
                stateClass: runtimeAttention.stateClass,
                detail: runtimeAttention.detail,
                metaItems: filterMetaItems([
                    `Adapters ${gatewayRuntime.adapterCount || 0}`,
                    `Open issues ${gatewayIssueCounts.open || 0}`,
                    `Affected adapters ${gatewayIssueCounts.openAdapters || 0}`,
                    `Ready ${gatewayDriverCounts.ready || 0}`,
                    `Attention ${gatewayDriverCounts.attention || 0}`,
                    `Error ${gatewayDriverCounts.error || 0}`,
                    sharedProtocolRuntimeLabel ? `Protocol summary ${sharedProtocolRuntimeLabel}` : null,
                    sharedProtocolRuntimeDetail ? `Protocol detail ${sharedProtocolRuntimeDetail}` : null,
                    sharedProtocolRuntimeTone ? `Protocol tone ${sharedProtocolRuntimeTone}` : null,
                    sharedProtocolRuntimeAttention !== null ? `Protocol attention ${sharedProtocolRuntimeAttention}` : null,
                    `Edge actions ${gatewayRuntime.edgeActionCounts?.total || 0}`,
                    `Processing ${gatewayRuntime.edgeActionCounts?.processing || 0}`,
                    `Processed ${gatewayRuntime.edgeActionCounts?.processed || 0}`,
                    `Replay pending ${edgeReplay.pending || 0}`,
                    `Replay due ${edgeReplay.due || 0}`,
                    `Replay cooling ${edgeReplay.scheduled || 0}`,
                    `Replay coalesced ${edgeReplay.coalescedCount || 0}`,
                    `Dead letters ${edgeDeadLetter.count || 0}`,
                    `Protocol runtimes ${gatewayRuntime.protocolRuntimeCount || 0}`,
                    `Protocol entries ${gatewayRuntime.protocolRuntimeEntryCount || 0}`,
                    `Protocol ready ${protocolRuntimeStateCounts.ready || 0}`,
                    `Protocol pending ${protocolRuntimeStateCounts.pending || 0}`,
                    `Protocol unavailable ${protocolRuntimeStateCounts.unavailable || 0}`,
                    `Protocol error ${protocolRuntimeStateCounts.error || 0}`,
                    latestRuntime?.title ? `Latest change ${latestRuntime.title}` : null,
                    latestRuntime?.timestamp ? `Changed ${latestRuntime.timestamp}` : null,
                    latestRuntime?.detail ? `Latest detail ${latestRuntime.detail}` : null,
                    gatewayRuntime.summary ? `Summary ${gatewayRuntime.summary}` : null,
                    gatewayRuntime.protocolRuntimeSummary ? `Protocol ${gatewayRuntime.protocolRuntimeSummary}` : null,
                    gatewayRuntime.edgeActionSummary ? `Edge action ${gatewayRuntime.edgeActionSummary}` : null,
                    edgeReplay.lastOutcome ? `Replay outcome ${edgeReplay.lastOutcome}` : null,
                    edgeReplay.lastSummary ? `Replay detail ${edgeReplay.lastSummary}` : null,
                    edgeReplay.summary ? `Replay ${edgeReplay.summary}` : null,
                    edgeDeadLetter.summary ? `Dead letter ${edgeDeadLetter.summary}` : null,
                ]),
            },
        ];
    }
}
