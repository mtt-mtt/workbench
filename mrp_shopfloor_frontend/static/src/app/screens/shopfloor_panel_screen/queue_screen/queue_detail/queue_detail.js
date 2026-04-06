/** @odoo-module **/

import { Component } from "@odoo/owl";

function normalizeTone(value) {
    const normalized = String(value || "secondary").trim().toLowerCase();
    if (normalized === "success" || normalized === "done") {
        return "success";
    }
    if (normalized === "warning" || normalized === "queued" || normalized === "submitted" || normalized === "acknowledged") {
        return "warning";
    }
    if (normalized === "danger" || normalized === "failed" || normalized === "error" || normalized === "attention") {
        return "danger";
    }
    if (normalized === "info" || normalized === "active" || normalized === "runtime") {
        return "info";
    }
    return "secondary";
}

function buildSharedProtocolRuntimeFeedback(metrics = {}) {
    const sharedAttention = metrics?.protocolRuntimeAttention;
    const attentionCount = sharedAttention === null || sharedAttention === undefined ? null : Number(sharedAttention) || 0;
    const label = metrics?.protocolRuntimeLabel || null;
    const detail = metrics?.protocolRuntimeDetail || null;
    const tone = String(metrics?.protocolRuntimeTone || "").trim().toLowerCase() || null;
    if (!label && !detail && !tone && attentionCount === null) {
        return null;
    }
    const resolvedTone =
        tone ||
        (attentionCount !== null ? (attentionCount > 0 ? "warning" : "success") : null) ||
        "secondary";
    const resolvedLabel =
        label ||
        (attentionCount !== null
            ? attentionCount > 0
                ? `Protocol runtime attention ${attentionCount}`
                : "Protocol runtime ready"
            : resolvedTone === "danger"
              ? "Protocol runtime error"
              : resolvedTone === "warning"
                ? "Protocol runtime attention"
                : resolvedTone === "success"
                  ? "Protocol runtime ready"
                  : "Protocol runtime");
    const resolvedDetail =
        detail ||
        (attentionCount !== null
            ? attentionCount > 0
                ? `${attentionCount} protocol runtime(s) need follow-up.`
                : "Protocol runtime attention is clear."
            : `${resolvedLabel} reported.`);
    return {
        label: resolvedLabel,
        detail: resolvedDetail,
        tone: resolvedTone,
        attentionCount,
    };
}

export class ShopfloorQueueDetail extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorQueueDetail";
    static props = {
        selectedQueueItem: Object,
        summary: Object,
        selectedQueueContext: Object,
        selectedQueueVisible: Boolean,
        latestRuntimeEntry: {
            type: Object,
            optional: true,
        },
        gatewayRuntimeSummary: {
            type: [Object, Boolean],
            optional: true,
        },
        metrics: {
            type: [Object, Boolean],
            optional: true,
        },
        onClearFilters: Function,
    };

    get statusKey() {
        return String(this.props.selectedQueueItem?.status || "unknown").trim().replace(/\s+/g, "_").toLowerCase();
    }

    get statusLabel() {
        return this.statusKey.replace(/_/g, " ");
    }

    get statusToneClass() {
        const map = {
            done: "text-bg-success",
            ready: "text-bg-success",
            in_progress: "text-bg-info",
            running: "text-bg-info",
            paused: "text-bg-warning",
            waiting: "text-bg-secondary",
            blocked: "text-bg-danger",
            error: "text-bg-danger",
            rejected: "text-bg-danger",
            draft: "text-bg-light",
        };
        return map[this.statusKey] || "text-bg-light";
    }

    get priorityLabel() {
        return String(this.props.selectedQueueItem?.priority || "Normal");
    }

    get priorityToneClass() {
        const key = this.priorityLabel.trim().toLowerCase();
        if (["high", "urgent", "critical"].includes(key)) {
            return "text-bg-warning";
        }
        return "text-bg-secondary";
    }

    get progressLabel() {
        const done = this.props.selectedQueueItem?.done ?? 0;
        const quantity = this.props.selectedQueueItem?.quantity ?? 0;
        return this.props.selectedQueueItem?.progress || `${done} / ${quantity}`;
    }

    get attentionLabel() {
        return ["blocked", "error", "rejected"].includes(this.statusKey) ? "Attention required" : null;
    }

    get hasSelectedQueueItem() {
        return Boolean(this.props.selectedQueueItem);
    }

    get filterSummaryLabel() {
        const summary = this.props.summary || {};
        if (!summary.isFiltered) {
            return null;
        }
        const parts = [];
        if (summary.searchText) {
            parts.push(`Search "${summary.searchText}"`);
        }
        if (summary.statusFilterLabel && summary.statusFilter !== "all") {
            parts.push(`Status ${summary.statusFilterLabel}`);
        }
        if (summary.sortLabel) {
            parts.push(`Sort ${summary.sortLabel}`);
        }
        return parts.join(" | ");
    }

    get selectionVisibilityLabel() {
        if (this.props.selectedQueueVisible === false) {
            return "Selected item is hidden by the current filters.";
        }
        return null;
    }

    get selectedContextReference() {
        return this.props.selectedQueueContext?.reference || this.props.selectedQueueItem?.reference || "n/a";
    }

    get selectedContextWorkorderRef() {
        return this.props.selectedQueueContext?.workorder_ref || this.props.selectedQueueItem?.workorder_ref || "n/a";
    }

    get selectedContextProductionRef() {
        return this.props.selectedQueueContext?.production_ref || this.props.selectedQueueItem?.production_ref || "n/a";
    }

    get protocolRuntimeAttentionCount() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (!sharedFeedback) {
            return null;
        }
        return sharedFeedback.attentionCount;
    }

    get protocolRuntimeFeedback() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (!sharedFeedback) {
            return null;
        }
        return sharedFeedback;
    }

    get runtimeSummary() {
        return this.props.gatewayRuntimeSummary || null;
    }

    get runtimeFeedback() {
        if (this.protocolRuntimeFeedback) {
            return this.protocolRuntimeFeedback;
        }
        const runtimeEntry = this.props.latestRuntimeEntry || null;
        if (runtimeEntry) {
            return {
                label:
                    runtimeEntry.protocolRuntimeLabel ||
                    runtimeEntry.title ||
                    runtimeEntry.label ||
                    (runtimeEntry.kind === "protocol_runtime" || runtimeEntry.kind === "protocol-runtime"
                        ? "Protocol runtime diagnostics"
                        : "Driver diagnostics"),
                detail:
                    [
                        runtimeEntry.protocolRuntimeDetail ||
                            runtimeEntry.detail ||
                            runtimeEntry.protocolRuntimeStateSummary,
                        runtimeEntry.timestamp ? `Changed ${runtimeEntry.timestamp}` : null,
                    ]
                        .filter(Boolean)
                        .join(" | ") || "Runtime event recorded.",
                tone: runtimeEntry.protocolRuntimeTone || runtimeEntry.statusTone || runtimeEntry.status || "info",
            };
        }
        const runtimeSummary = this.runtimeSummary;
        if (runtimeSummary) {
            return {
                label: runtimeSummary.label || "Driver diagnostics",
                detail: runtimeSummary.detail || runtimeSummary.summary || "Runtime diagnostics available.",
                tone: runtimeSummary.stateTone || runtimeSummary.state || "secondary",
            };
        }
        return null;
    }

    get runtimeStateClass() {
        return `badge rounded-pill text-bg-${normalizeTone(this.runtimeFeedback?.tone || "secondary")}`;
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
