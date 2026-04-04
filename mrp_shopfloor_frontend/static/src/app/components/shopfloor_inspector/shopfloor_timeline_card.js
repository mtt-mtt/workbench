/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorTimelineCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorTimelineCard";
    static props = {
        title: String,
        entries: Array,
        emptyMessage: String,
        compact: { type: Boolean, optional: true },
    };
}
