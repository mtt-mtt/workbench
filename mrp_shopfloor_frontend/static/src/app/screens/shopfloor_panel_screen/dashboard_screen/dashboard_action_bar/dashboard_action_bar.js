/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorDashboardActionBar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDashboardActionBar";
    static props = {
        onStartExecution: Function,
        onPauseExecution: Function,
        onFinishExecution: Function,
    };

    startExecution(ev) {
        this.props.onStartExecution?.(ev);
    }

    pauseExecution(ev) {
        this.props.onPauseExecution?.(ev);
    }

    finishExecution(ev) {
        this.props.onFinishExecution?.(ev);
    }
}
