/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorResponseCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorResponseCard";
    static props = {
        responseSummary: Object,
        lastResponseText: String,
    };
}
