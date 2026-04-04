/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorAttentionNote extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorAttentionNote";
    static props = {
        label: String,
        detail: {
            type: String,
            optional: true,
        },
        tone: {
            type: String,
            optional: true,
        },
        compact: {
            type: Boolean,
            optional: true,
        },
    };

    get toneClass() {
        const tone = String(this.props.tone || "warning").trim().toLowerCase();
        const map = {
            warning: "text-bg-warning",
            danger: "text-bg-danger",
            info: "text-bg-info",
            secondary: "text-bg-secondary",
        };
        return map[tone] || map.warning;
    }

    get noteClass() {
        const classes = ["o_mrp_shopfloor_attention_note"];
        if (this.props.compact) {
            classes.push("o_mrp_shopfloor_attention_note--compact");
        }
        return classes.join(" ");
    }
}
