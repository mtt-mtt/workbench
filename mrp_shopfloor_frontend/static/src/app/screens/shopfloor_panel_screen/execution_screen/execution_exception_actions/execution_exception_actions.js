/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorExecutionExceptionActions extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionExceptionActions";
    static props = {
        onReportException: Function,
    };

    reportException(ev) {
        this.props.onReportException?.(ev);
    }
}
