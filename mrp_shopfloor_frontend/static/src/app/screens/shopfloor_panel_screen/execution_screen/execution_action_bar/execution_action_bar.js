/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorExecutionActionBar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionActionBar";
    static props = {
        execution: Object,
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
