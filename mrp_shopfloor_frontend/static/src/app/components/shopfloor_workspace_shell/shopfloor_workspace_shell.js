/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorWorkspaceShell extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorWorkspaceShell";
    static props = {
        currentPanel: String,
        workstation: Object,
        metrics: Object,
        commandQueueStatus: Object,
        gatewayRuntimeSummary: [Object, Boolean],
        sessionRef: [String, Boolean],
        lastResponse: [Object, Boolean],
        ui: {
            type: [Object, Boolean],
            optional: true,
        },
        onStartExecution: {
            type: Function,
            optional: true,
        },
        onPauseExecution: {
            type: Function,
            optional: true,
        },
        onFinishExecution: {
            type: Function,
            optional: true,
        },
        onReportException: {
            type: Function,
            optional: true,
        },
        onRefreshQueue: {
            type: Function,
            optional: true,
        },
        onToggleFullscreen: {
            type: Function,
            optional: true,
        },
        onToggleFocusMode: {
            type: Function,
            optional: true,
        },
    };

    get backendStateLabel() {
        return this.props.lastResponse ? "Booted" : "Seed";
    }

    get ui() {
        return this.props.ui || {};
    }

    get fullscreenLabel() {
        return this.ui.fullscreen ? "Exit fullscreen" : "Fullscreen";
    }

    get focusLabel() {
        return this.ui.focusMode ? "Exit focus" : "Focus";
    }

    get sessionLabel() {
        return this.props.sessionRef || "n/a";
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

    get gatewayRuntimeAttentionTone() {
        const state = this.props.gatewayRuntimeSummary?.stateTone || this.props.gatewayRuntimeSummary?.state || "secondary";
        return String(state || "secondary").toLowerCase();
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

    get gatewayRuntimeAttentionSummary() {
        return (
            this.props.gatewayRuntimeSummary?.edgeDeadLetter?.summary ||
            this.gatewayProtocolRuntimeSummary ||
            this.gatewayEdgeReplayLastSummary ||
            this.props.gatewayRuntimeSummary?.edgeReplay?.summary ||
            this.props.gatewayRuntimeSummary?.edgeActionSummary ||
            this.props.gatewayRuntimeSummary?.detail ||
            this.props.gatewayRuntimeSummary?.summary ||
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
        return this.gatewayRuntimeAttentionTone;
    }

    get summaryClassName() {
        return this.ui.focusMode
            ? "o_mrp_shopfloor_card o_mrp_shopfloor_card--summary o_mrp_shopfloor_workspace_metrics is-focused"
            : "o_mrp_shopfloor_card o_mrp_shopfloor_card--summary o_mrp_shopfloor_workspace_metrics";
    }

    get taskDeckLabel() {
        const labels = {
            dashboard: "Monitor line health and keep the workstation synced",
            queue: "Pick the next unit of work and scan into execution",
            execution: "Run the current work order with large primary controls",
            devices: "Confirm device state and queue device-side actions",
            exceptions: "Resolve or escalate blocked work quickly",
        };
        return labels[this.props.currentPanel] || "Keep the workstation focused on the next operator action";
    }

    get taskDeckMeta() {
        const parts = [
            this.ui.lastScannerCode ? `Last scan ${this.ui.lastScannerCode}` : null,
            this.ui.scannerHint || null,
            this.ui.shortcutSummary || null,
        ].filter(Boolean);
        return parts.join(" · ");
    }

    get taskActions() {
        if (this.props.currentPanel === "execution") {
            return [
                { key: "start", label: "Start", hint: "F2", tone: "btn-primary", handler: "startExecution" },
                { key: "pause", label: "Pause", hint: "F3", tone: "btn-outline-warning", handler: "pauseExecution" },
                { key: "finish", label: "Finish", hint: "F4", tone: "btn-outline-success", handler: "finishExecution" },
                { key: "exception", label: "Raise exception", hint: "Escalate flow", tone: "btn-outline-danger", handler: "raiseException" },
            ];
        }
        return [
            { key: "refresh", label: "Refresh state", hint: "F8", tone: "btn-light", handler: "refreshQueue" },
            { key: "focus", label: this.focusLabel, hint: "Ctrl+Shift+M", tone: "btn-outline-light", handler: "toggleFocusMode" },
            { key: "fullscreen", label: this.fullscreenLabel, hint: "Ctrl+Shift+F", tone: "btn-outline-light", handler: "toggleFullscreen" },
            { key: "exception", label: "Raise exception", hint: "Quick operator note", tone: "btn-outline-danger", handler: "raiseException" },
        ];
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

    refreshQueue(ev) {
        this.props.onRefreshQueue?.(ev);
    }

    toggleFullscreen(ev) {
        this.props.onToggleFullscreen?.(ev);
    }

    toggleFocusMode(ev) {
        this.props.onToggleFocusMode?.(ev);
    }

    raiseException() {
        this.props.onReportException?.({
            currentTarget: {
                dataset: {
                    severity: "medium",
                    state: "new",
                    action: "follow_up",
                    message: "Operator quick exception",
                },
            },
            preventDefault() {},
        });
    }

    runTaskAction(ev) {
        const handler = ev?.currentTarget?.dataset?.handler || null;
        if (handler === "startExecution") {
            this.startExecution(ev);
            return;
        }
        if (handler === "pauseExecution") {
            this.pauseExecution(ev);
            return;
        }
        if (handler === "finishExecution") {
            this.finishExecution(ev);
            return;
        }
        if (handler === "refreshQueue") {
            this.refreshQueue(ev);
            return;
        }
        if (handler === "toggleFocusMode") {
            this.toggleFocusMode(ev);
            return;
        }
        if (handler === "toggleFullscreen") {
            this.toggleFullscreen(ev);
            return;
        }
        this.raiseException();
    }
}
