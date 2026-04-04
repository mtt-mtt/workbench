/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorActivityCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorActivityCard";
    static props = {
        activity: Array,
    };
}
