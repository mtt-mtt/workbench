/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorDashboardSummaryCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardSummaryCard";
    static props = {
        label: String,
        title: String,
        badges: Array,
    };
}
