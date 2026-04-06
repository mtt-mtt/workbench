/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorAttentionNote } from "../../../../../components/shopfloor_status_components/shopfloor_attention_note";
import { ShopfloorStatusBadge } from "../../../../../components/shopfloor_status_components/shopfloor_status_badge";
import {
    deviceAttentionLabel,
    deviceStateLabel,
    deviceStateTone,
} from "../../../../../components/shopfloor_status_components/shopfloor_status_metrics";

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

export class ShopfloorDeviceDetail extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceDetail";
    static components = {
        ShopfloorAttentionNote,
        ShopfloorStatusBadge,
    };
    static props = {
        selectedDevice: Object,
        summary: Object,
        selectedDeviceVisible: Boolean,
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

    get stateKey() {
        return String(this.props.selectedDevice?.state || "unknown").trim().replace(/\s+/g, "_").toLowerCase();
    }

    get stateLabel() {
        return deviceStateLabel(this.props.selectedDevice?.state);
    }

    get stateTone() {
        return deviceStateTone(this.props.selectedDevice?.state);
    }

    get attentionLabel() {
        return deviceAttentionLabel(this.props.selectedDevice?.state) ? "Attention required" : null;
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
        if (summary.stateFilterLabel && summary.stateFilter !== "all") {
            parts.push(`State ${summary.stateFilterLabel}`);
        }
        if (summary.groupByLabel && summary.groupBy !== "state") {
            parts.push(`Group ${summary.groupByLabel}`);
        }
        return parts.join(" | ");
    }

    get selectionVisibilityLabel() {
        if (this.props.selectedDevice && this.props.selectedDeviceVisible === false) {
            return "Selected device is hidden by the current filters.";
        }
        return null;
    }

    get showClearFilters() {
        return this.props.selectedDeviceVisible === false || Boolean(this.props.summary?.isFiltered);
    }

    get protocolRuntimeAttentionCount() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (!sharedFeedback) {
            return null;
        }
        return sharedFeedback.attentionCount;
    }

    get protocolRuntimeFeedback() {
        return buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
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
