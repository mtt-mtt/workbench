/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorStatusBadge } from "./shopfloor_status_badge";

export class ShopfloorStatusSummary extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorStatusSummary";
    static components = {
        ShopfloorStatusBadge,
    };
    static props = {
        items: Array,
        title: {
            type: String,
            optional: true,
        },
        subtitle: {
            type: String,
            optional: true,
        },
        compact: {
            type: Boolean,
            optional: true,
        },
        toolbar: {
            type: Boolean,
            optional: true,
        },
    };

    get summaryItems() {
        return Array.isArray(this.props.items) ? this.props.items : [];
    }

    get summaryClass() {
        const classes = ["o_mrp_shopfloor_status_summary"];
        if (this.props.toolbar !== false) {
            classes.push("o_mrp_shopfloor_status_summary--toolbar");
        }
        if (this.props.compact) {
            classes.push("o_mrp_shopfloor_status_summary--compact");
        }
        if (this.props.title || this.props.subtitle) {
            classes.push("o_mrp_shopfloor_status_summary--stacked");
        }
        return classes.join(" ");
    }
}
