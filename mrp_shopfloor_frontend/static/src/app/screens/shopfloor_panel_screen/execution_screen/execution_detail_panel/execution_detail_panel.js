/** @odoo-module **/

import { Component } from "@odoo/owl";
import { findLatestRuntimeEntry, normalizeRuntimeEntry } from "../../../../utils/shopfloor_runtime_entries";

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

export class ShopfloorExecutionDetailPanel extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionDetailPanel";
    static props = {
        execution: Object,
        selectedQueueContext: Object,
        logEntries: Array,
        gatewayRuntimeSummary: [Object, Boolean],
        metrics: [Object, Boolean],
        workstation: Object,
        sessionRef: [String, Boolean],
    };

    get latestRuntimeEntry() {
        return normalizeRuntimeEntry(findLatestRuntimeEntry(this.props.logEntries || []));
    }

    get runtimeSummary() {
        return this.props.gatewayRuntimeSummary || null;
    }

    get sharedProtocolRuntimeAttentionCount() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (!sharedFeedback) {
            return null;
        }
        return sharedFeedback.attentionCount;
    }

    get runtimeAttentionCount() {
        const sharedAttention = this.sharedProtocolRuntimeAttentionCount;
        if (sharedAttention !== null) {
            return sharedAttention;
        }
        const stateCounts = this.runtimeSummary?.protocolRuntimeStateCounts || this.runtimeSummary?.protocolRuntime?.stateCounts || {};
        return Number(stateCounts.error || 0) + Number(stateCounts.pending || 0) + Number(stateCounts.unavailable || 0);
    }

    get runtimeAttentionLabel() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (sharedFeedback) {
            return sharedFeedback.label;
        }
        return (
            this.latestRuntimeEntry?.protocolRuntimeLabel ||
            this.latestRuntimeEntry?.statusLabel ||
            this.latestRuntimeEntry?.label ||
            this.runtimeSummary?.stateLabel ||
            "Runtime"
        );
    }

    get runtimeAttentionDetail() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (sharedFeedback) {
            return sharedFeedback.detail || this.runtimeSummary?.summary || this.runtimeSummary?.detail;
        }
        return (
            this.latestRuntimeEntry?.protocolRuntimeDetail ||
            this.latestRuntimeEntry?.detail ||
            this.latestRuntimeEntry?.protocolRuntimeStateSummary ||
            this.runtimeSummary?.detail ||
            this.runtimeSummary?.summary ||
            "No runtime change details yet."
        );
    }

    get runtimeFeedbackTitle() {
        if (buildSharedProtocolRuntimeFeedback(this.props.metrics || {})) {
            return this.runtimeAttentionLabel;
        }
        return (
            this.latestRuntimeEntry?.protocolRuntimeLabel ||
            this.latestRuntimeEntry?.title ||
            this.latestRuntimeEntry?.label ||
            this.runtimeSummary?.label ||
            (this.latestRuntimeEntry?.kind === "protocol_runtime" || this.latestRuntimeEntry?.kind === "protocol-runtime"
                ? "Protocol runtime diagnostics"
                : "Driver diagnostics")
        );
    }

    get runtimeStateClass() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (sharedFeedback) {
            return `badge rounded-pill text-bg-${normalizeTone(sharedFeedback.tone || "secondary")}`;
        }
        const tone = normalizeTone(
            this.latestRuntimeEntry?.protocolRuntimeTone ||
                this.latestRuntimeEntry?.statusTone ||
                this.latestRuntimeEntry?.status ||
                this.runtimeSummary?.stateTone ||
                this.runtimeSummary?.state ||
                "secondary"
        );
        return `badge rounded-pill text-bg-${tone}`;
    }
}
