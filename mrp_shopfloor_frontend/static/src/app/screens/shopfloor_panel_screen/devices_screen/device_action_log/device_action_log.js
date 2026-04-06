/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorFeedbackBar } from "../../../../../components/shopfloor_status_components/shopfloor_feedback_bar";
import { ShopfloorStatusSummary } from "../../../../../components/shopfloor_status_components/shopfloor_status_summary";
import {
    gatewayCommandFeedback,
    gatewayCommandSummaryItems,
    normalizeGatewayCommandEntry,
    sortGatewayCommands,
    summarizeGatewayCommands,
} from "../device_command_status";

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

export class ShopfloorDeviceActionLog extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceActionLog";
    static components = {
        ShopfloorFeedbackBar,
        ShopfloorStatusSummary,
    };
    static props = {
        recentActions: Array,
        commands: Array,
        commandSummary: {
            type: Object,
            optional: true,
        },
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
    };

    get entries() {
        if (Array.isArray(this.props.commands) && this.props.commands.length) {
            return sortGatewayCommands(this.props.commands);
        }
        return sortGatewayCommands(this.props.recentActions);
    }

    get displayEntries() {
        return this.entries.map((entry) => normalizeGatewayCommandEntry(entry));
    }

    get commandSummary() {
        return this.props.commandSummary || summarizeGatewayCommands(this.entries);
    }

    get commandSummaryItems() {
        return gatewayCommandSummaryItems(this.commandSummary);
    }

    get commandFeedback() {
        return gatewayCommandFeedback(this.commandSummary);
    }

    get commandStateSteps() {
        const latest = String(this.commandSummary?.latestState || "").toLowerCase();
        return [
            { key: "queued", label: "Queued", active: ["queued", "draft"].includes(latest) },
            { key: "sent", label: "Sent", active: latest === "sent" },
            { key: "acknowledged", label: "Acknowledged", active: latest === "acknowledged" },
            { key: "done", label: "Done", active: latest === "done" },
            { key: "failed", label: "Failed", active: latest === "failed" },
        ];
    }

    get commandStateLabel() {
        return this.commandSummary?.latestStateLabel || "Queued";
    }

    get commandStateDetail() {
        if (!this.commandSummary?.total) {
            return "No command response yet.";
        }
        return this.commandSummary?.latestCommandDetail || this.commandFeedback.detail;
    }

    get latestPrintExecutionLabel() {
        return this.commandSummary?.latestPrintExecutionBadge || null;
    }

    get latestPrintExecutionDetails() {
        return this.commandSummary?.latestPrintExecutionDetails || [];
    }

    get runtimeFeedback() {
        const sharedFeedback = buildSharedProtocolRuntimeFeedback(this.props.metrics || {});
        if (sharedFeedback) {
            return sharedFeedback;
        }
        const runtimeEntry = this.props.latestRuntimeEntry || null;
        const runtimeSummary = this.props.gatewayRuntimeSummary || null;
        if (runtimeEntry) {
            return {
                label: runtimeEntry.title || runtimeEntry.label || "Driver diagnostics",
                detail:
                    [runtimeEntry.detail, runtimeEntry.timestamp ? `Changed ${runtimeEntry.timestamp}` : null]
                        .filter(Boolean)
                        .join(" | ") || "Runtime event recorded.",
                tone: runtimeEntry.statusTone || runtimeEntry.status || "info",
            };
        }
        if (runtimeSummary) {
            return {
                label: runtimeSummary.label || "Driver diagnostics",
                detail: runtimeSummary.detail || runtimeSummary.summary || "Runtime diagnostics available.",
                tone: runtimeSummary.stateTone || runtimeSummary.state || "secondary",
            };
        }
        return null;
    }

    noopFeedbackAction(ev) {
        ev?.preventDefault?.();
    }
}
