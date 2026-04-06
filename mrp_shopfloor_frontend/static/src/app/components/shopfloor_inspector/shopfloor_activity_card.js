/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorFeedbackBar } from "../shopfloor_status_components/shopfloor_feedback_bar";

function buildProtocolRuntimeFeedback(metrics = {}, gatewayRuntimeSummary = null) {
    const sharedAttention = metrics?.protocolRuntimeAttention;
    const attentionCount = sharedAttention === null || sharedAttention === undefined ? null : Number(sharedAttention) || 0;
    const label = metrics?.protocolRuntimeLabel || null;
    const detail =
        metrics?.protocolRuntimeDetail ||
        gatewayRuntimeSummary?.protocolRuntimeSummary ||
        gatewayRuntimeSummary?.protocolRuntime?.summary ||
        null;
    const tone = String(metrics?.protocolRuntimeTone || "").trim().toLowerCase() || null;
    if (!label && !detail && attentionCount === null) {
        return null;
    }
    const resolvedTone =
        tone ||
        (attentionCount !== null ? (attentionCount > 0 ? "warning" : "success") : null) ||
        String(
            gatewayRuntimeSummary?.protocolRuntimeState ||
                gatewayRuntimeSummary?.protocolRuntime?.state ||
                gatewayRuntimeSummary?.protocolRuntime?.stateKey ||
                "secondary",
        )
            .trim()
            .toLowerCase();
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
        tone: resolvedTone || "secondary",
    };
}

export class ShopfloorActivityCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorActivityCard";
    static components = {
        ShopfloorFeedbackBar,
    };
    static props = {
        activity: Array,
        gatewayRuntimeSummary: {
            type: [Object, Boolean],
            optional: true,
        },
        metrics: {
            type: [Object, Boolean],
            optional: true,
        },
    };

    get protocolRuntimeFeedback() {
        return buildProtocolRuntimeFeedback(this.props.metrics || {}, this.props.gatewayRuntimeSummary || null);
    }

    noopFeedbackAction(ev) {
        ev?.preventDefault?.();
    }
}
