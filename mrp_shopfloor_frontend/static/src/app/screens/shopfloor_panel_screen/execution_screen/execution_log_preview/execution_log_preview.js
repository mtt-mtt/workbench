/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorExecutionLogPreview extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionLogPreview";
    static props = {
        logEntries: Array,
    };
}
