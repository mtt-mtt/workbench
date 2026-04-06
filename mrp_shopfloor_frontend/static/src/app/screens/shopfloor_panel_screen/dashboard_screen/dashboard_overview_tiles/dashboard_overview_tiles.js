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
        gatewayRuntimeSummary: [Object, Boolean],
        metrics: Object,
    };

    get tiles() {
        const gatewayRuntime = this.props.gatewayRuntimeSummary || {};
        const sharedMetrics = this.props.metrics || {};
        const openDriverIssues = gatewayRuntime.issueCounts?.open || 0;
        const openDriverAdapters = gatewayRuntime.issueCounts?.openAdapters || 0;
        const protocolRuntime = gatewayRuntime.protocolRuntime || {};
        const protocolRuntimeCount = gatewayRuntime.protocolRuntimeCount || protocolRuntime.count || 0;
        const protocolRuntimeEntryCount = gatewayRuntime.protocolRuntimeEntryCount || protocolRuntime.entryCount || 0;
        const protocolRuntimeStateCounts = gatewayRuntime.protocolRuntimeStateCounts || protocolRuntime.stateCounts || {};
        const protocolRuntimeSummary = gatewayRuntime.protocolRuntimeSummary || protocolRuntime.summary || null;
        const sharedProtocolRuntimeAttention = sharedMetrics.protocolRuntimeAttention;
        const sharedProtocolRuntimeLabel = sharedMetrics.protocolRuntimeLabel || null;
        const sharedProtocolRuntimeDetail = sharedMetrics.protocolRuntimeDetail || null;
        const sharedProtocolRuntimeTone = sharedMetrics.protocolRuntimeTone || null;
        const hasSharedProtocolRuntimeAttention =
            sharedProtocolRuntimeAttention !== null && sharedProtocolRuntimeAttention !== undefined;
        const protocolRuntimeAttentionCount = hasSharedProtocolRuntimeAttention
            ? Number(sharedProtocolRuntimeAttention) || 0
            : Number(protocolRuntimeStateCounts.error || 0) +
              Number(protocolRuntimeStateCounts.pending || 0) +
              Number(protocolRuntimeStateCounts.unavailable || 0);
        const protocolRuntimeTileLabel =
            sharedProtocolRuntimeLabel ||
            (sharedProtocolRuntimeTone === "danger"
                ? "Protocol runtime error"
                : sharedProtocolRuntimeTone === "warning"
                  ? "Protocol runtime attention"
                  : sharedProtocolRuntimeTone === "success"
                    ? "Protocol runtime ready"
                    : "Protocol runtime");
        const protocolRuntimeTileHint =
            sharedProtocolRuntimeDetail ||
            protocolRuntimeSummary ||
            (protocolRuntimeAttentionCount
                ? `${protocolRuntimeAttentionCount} protocol runtime signal(s) still need follow-up`
                : protocolRuntimeCount || protocolRuntimeEntryCount
                  ? "Protocol runtimes are reporting state."
                  : "No protocol runtime attention detected");
        const edgeActionProcessing = gatewayRuntime.edgeActionCounts?.processing || 0;
        const edgeReplayPending = gatewayRuntime.edgeReplay?.pending || 0;
        const edgeReplayDue = gatewayRuntime.edgeReplay?.due || 0;
        const edgeReplayScheduled = gatewayRuntime.edgeReplay?.scheduled || 0;
        const edgeReplayCoalesced = gatewayRuntime.edgeReplay?.coalescedCount || 0;
        const edgeDeadLetterCount = gatewayRuntime.edgeDeadLetter?.count || 0;
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
            {
                label: "Driver issues",
                value: openDriverIssues,
                hint:
                    gatewayRuntime.summary ||
                    (openDriverAdapters
                        ? `${openDriverAdapters} adapter(s) still need driver follow-up`
                        : "No runtime driver issues detected"),
            },
            {
                label: protocolRuntimeTileLabel,
                value: protocolRuntimeAttentionCount || protocolRuntimeCount || protocolRuntimeEntryCount,
                hint: protocolRuntimeTileHint,
            },
            {
                label: "Edge actions",
                value: edgeActionProcessing,
                hint:
                    gatewayRuntime.edgeDeadLetter?.summary ||
                    gatewayRuntime.edgeReplay?.summary ||
                    gatewayRuntime.edgeActionSummary ||
                    (edgeActionProcessing
                        ? "Some edge actions are being processed right now"
                        : "No edge action is currently processing"),
            },
            {
                label: "Edge replay",
                value: edgeReplayDue || edgeReplayPending,
                hint:
                    gatewayRuntime.edgeReplay?.lastSummary ||
                    gatewayRuntime.edgeReplay?.summary ||
                    (edgeReplayDue
                        ? `Replay due ${edgeReplayDue}, coalesced ${edgeReplayCoalesced}`
                        : edgeReplayScheduled
                          ? `Cooldown active for ${edgeReplayScheduled} item(s)`
                          : edgeReplayPending
                            ? "Offline requests are waiting to replay"
                            : "No replay backlog"),
            },
            {
                label: "Dead letters",
                value: edgeDeadLetterCount,
                hint:
                    gatewayRuntime.edgeDeadLetter?.summary ||
                    (edgeDeadLetterCount ? "Some outbound requests exhausted retry budget" : "No dead-letter backlog"),
            },
        ];
    }
}
