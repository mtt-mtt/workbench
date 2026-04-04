/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorExecutionDetailPanel extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionDetailPanel";
    static props = {
        execution: Object,
        selectedQueueContext: Object,
        workstation: Object,
        sessionRef: [String, Boolean],
    };
}
