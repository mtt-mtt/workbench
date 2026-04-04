/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorDashboardKpiTile extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardKpiTile";
    static props = {
        label: String,
        value: [String, Number],
        hint: String,
    };
}
