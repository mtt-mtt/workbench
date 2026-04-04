/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorCommandQueueCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorCommandQueueCard";
    static props = {
        commandQueueStatus: Object,
        commands: Array,
    };
}
