/** @odoo-module **/

import { Component } from "@odoo/owl";
import { getShopfloorRouteMeta, listShopfloorRoutes } from "../../router/shopfloor_router";

export class ShopfloorNavRail extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorNavRail";
    static props = {
        panels: Array,
        currentRoute: String,
        currentUserName: String,
        workstation: Object,
        sessionRef: [String, Boolean],
        metrics: Object,
        gatewayRuntimeSummary: [Object, Boolean],
        booted: Boolean,
        onNavigatePanel: Function,
    };

    get activeRouteMeta() {
        return getShopfloorRouteMeta(this.props.currentRoute);
    }

    get navigationPanels() {
        const panels = Array.isArray(this.props.panels) ? this.props.panels : [];
        const routeOrder = new Map(listShopfloorRoutes().map((route, index) => [route.key, index]));
        return panels
            .map((panel) => ({
                ...panel,
                meta: getShopfloorRouteMeta(panel.key),
            }))
            .sort((left, right) => {
                const leftOrder = routeOrder.has(left.key) ? routeOrder.get(left.key) : Number.MAX_SAFE_INTEGER;
                const rightOrder = routeOrder.has(right.key) ? routeOrder.get(right.key) : Number.MAX_SAFE_INTEGER;
                return leftOrder - rightOrder;
            });
    }

    navigatePanel(ev) {
        this.props.onNavigatePanel?.(ev);
    }

    get gatewayDriverIssueOpen() {
        return this.props.gatewayRuntimeSummary?.issueCounts?.open || 0;
    }

    get gatewayProtocolRuntimeCount() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeCount || this.props.gatewayRuntimeSummary?.protocolRuntime?.count || 0;
    }

    get gatewayProtocolRuntimeEntryCount() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeEntryCount || this.props.gatewayRuntimeSummary?.protocolRuntime?.entryCount || 0;
    }

    get gatewayProtocolRuntimeStateCounts() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeStateCounts || this.props.gatewayRuntimeSummary?.protocolRuntime?.stateCounts || {};
    }

    get gatewayProtocolRuntimeAttentionCount() {
        const sharedAttention = this.props.metrics?.protocolRuntimeAttention;
        if (sharedAttention !== undefined && sharedAttention !== null) {
            return Number(sharedAttention) || 0;
        }
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        return Number(stateCounts.error || 0) + Number(stateCounts.pending || 0) + Number(stateCounts.unavailable || 0);
    }

    get gatewayProtocolRuntimeSummary() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeSummary || this.props.gatewayRuntimeSummary?.protocolRuntime?.summary || null;
    }

    get gatewayProtocolRuntimeLabel() {
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        const attentionCount = this.gatewayProtocolRuntimeAttentionCount;
        const errorCount = stateCounts.error || 0;
        const pendingCount = stateCounts.pending || 0;
        const unavailableCount = stateCounts.unavailable || 0;
        const readyCount = stateCounts.ready || 0;
        if (this.gatewayProtocolRuntimeSummary || this.gatewayProtocolRuntimeCount || this.gatewayProtocolRuntimeEntryCount || attentionCount) {
            if (errorCount > 0) {
                return `Protocol error ${errorCount}`;
            }
            if (pendingCount > 0 || unavailableCount > 0 || attentionCount > 0) {
                return `Protocol attention ${attentionCount || pendingCount + unavailableCount}`;
            }
            if (readyCount > 0) {
                return `Protocol ready ${readyCount}`;
            }
            return `Protocol runtime ${this.gatewayProtocolRuntimeCount || this.gatewayProtocolRuntimeEntryCount || attentionCount}`;
        }
        return null;
    }

    get gatewayProtocolRuntimeTone() {
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        const attentionCount = this.gatewayProtocolRuntimeAttentionCount;
        if ((stateCounts.error || 0) > 0) {
            return "danger";
        }
        if ((stateCounts.pending || 0) > 0 || (stateCounts.unavailable || 0) > 0 || attentionCount > 0) {
            return "warning";
        }
        if ((stateCounts.ready || 0) > 0 || this.gatewayProtocolRuntimeCount || this.gatewayProtocolRuntimeEntryCount) {
            return "success";
        }
        return "secondary";
    }

    get gatewayEdgeActionProcessing() {
        return this.props.gatewayRuntimeSummary?.edgeActionCounts?.processing || 0;
    }

    get gatewayEdgeActionQueued() {
        const pending = this.props.gatewayRuntimeSummary?.edgeActionCounts?.pending || 0;
        return Math.max(pending - this.gatewayEdgeActionProcessing, 0);
    }

    get gatewayEdgeActionProcessed() {
        return this.props.gatewayRuntimeSummary?.edgeActionCounts?.processed || 0;
    }

    get gatewayEdgeActionTotal() {
        return this.props.gatewayRuntimeSummary?.edgeActionCounts?.total || 0;
    }

    get gatewayEdgeReplayPending() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.pending || 0;
    }

    get gatewayEdgeReplayDue() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.due || 0;
    }

    get gatewayEdgeReplayCooling() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.scheduled || 0;
    }

    get gatewayEdgeReplayCoalesced() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.coalescedCount || 0;
    }

    get gatewayEdgeReplayLastOutcome() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.lastOutcome || null;
    }

    get gatewayEdgeReplayLastSummary() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.lastSummary || null;
    }

    get gatewayEdgeDeadLetterCount() {
        return this.props.gatewayRuntimeSummary?.edgeDeadLetter?.count || 0;
    }

    get gatewayRuntimeAttentionLabel() {
        if (this.gatewayDriverIssueOpen) {
            return `Driver issues ${this.gatewayDriverIssueOpen}`;
        }
        if (this.gatewayEdgeDeadLetterCount) {
            return `Dead letters ${this.gatewayEdgeDeadLetterCount}`;
        }
        if (this.gatewayEdgeReplayDue) {
            return `Replay due ${this.gatewayEdgeReplayDue}`;
        }
        if (this.gatewayEdgeReplayCooling && this.gatewayEdgeReplayLastOutcome === "waiting_backoff") {
            return `Replay cooling ${this.gatewayEdgeReplayCooling}`;
        }
        if (this.gatewayEdgeReplayPending) {
            return `Replay pending ${this.gatewayEdgeReplayPending}`;
        }
        if (this.gatewayEdgeActionProcessing) {
            return `Edge actions ${this.gatewayEdgeActionProcessing}`;
        }
        if (this.gatewayProtocolRuntimeLabel) {
            return this.gatewayProtocolRuntimeLabel;
        }
        return null;
    }

    get gatewayDriverSummary() {
        return (
            this.props.gatewayRuntimeSummary?.edgeDeadLetter?.summary ||
            this.gatewayProtocolRuntimeSummary ||
            this.gatewayEdgeReplayLastSummary ||
            this.props.gatewayRuntimeSummary?.edgeReplay?.summary ||
            this.props.gatewayRuntimeSummary?.edgeActionSummary ||
            this.props.gatewayRuntimeSummary?.summary ||
            this.props.gatewayRuntimeSummary?.detail ||
            null
        );
    }

    get gatewayDriverTone() {
        if (this.gatewayDriverIssueOpen) {
            return String(this.props.gatewayRuntimeSummary?.stateTone || this.props.gatewayRuntimeSummary?.state || "danger").toLowerCase();
        }
        if (this.gatewayEdgeDeadLetterCount) {
            return "danger";
        }
        if (this.gatewayEdgeReplayDue) {
            return "warning";
        }
        if (this.gatewayEdgeReplayCooling && this.gatewayEdgeReplayLastOutcome === "waiting_backoff") {
            return "info";
        }
        if (this.gatewayEdgeReplayPending) {
            return "warning";
        }
        if (this.gatewayEdgeActionProcessing) {
            return "info";
        }
        if (this.gatewayProtocolRuntimeLabel) {
            return this.gatewayProtocolRuntimeTone;
        }
        const state = this.props.gatewayRuntimeSummary?.stateTone || this.props.gatewayRuntimeSummary?.state || "secondary";
        return String(state || "secondary").toLowerCase();
    }
}
