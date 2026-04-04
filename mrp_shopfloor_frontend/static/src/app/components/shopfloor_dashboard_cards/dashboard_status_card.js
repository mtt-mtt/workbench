/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorDashboardStatusCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardStatusCard";
    static props = {
        label: String,
        title: String,
        stateLabel: String,
        stateClass: String,
        detail: String,
        metaItems: Array,
    };
}
