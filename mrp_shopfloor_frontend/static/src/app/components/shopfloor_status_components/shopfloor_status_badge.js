/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorStatusBadge extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorStatusBadge";
    static props = {
        label: String,
        tone: {
            type: String,
            optional: true,
        },
        detail: {
            type: String,
            optional: true,
        },
        compact: {
            type: Boolean,
            optional: true,
        },
        pill: {
            type: Boolean,
            optional: true,
        },
    };

    get toneClass() {
        const tone = String(this.props.tone || "secondary").trim().toLowerCase();
        const map = {
            success: "text-bg-success",
            warning: "text-bg-warning",
            danger: "text-bg-danger",
            info: "text-bg-info",
            secondary: "text-bg-secondary",
            light: "text-bg-light",
        };
        return map[tone] || map.secondary;
    }

    get badgeClass() {
        const classes = [this.props.pill === false ? "badge" : "badge rounded-pill", "o_mrp_shopfloor_status_chip"];
        if (this.props.compact) {
            classes.push("o_mrp_shopfloor_status_chip--compact");
        }
        return classes.join(" ");
    }
}
