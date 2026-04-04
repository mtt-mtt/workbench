/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorExecutionActionBar } from "./execution_action_bar/execution_action_bar";
import { ShopfloorExecutionDetailPanel } from "./execution_detail_panel/execution_detail_panel";
import { ShopfloorExecutionExceptionActions } from "./execution_exception_actions/execution_exception_actions";
import { ShopfloorExecutionLogPreview } from "./execution_log_preview/execution_log_preview";

export class ShopfloorExecutionScreen extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionScreen";
    static components = {
        ShopfloorExecutionActionBar,
        ShopfloorExecutionDetailPanel,
        ShopfloorExecutionExceptionActions,
        ShopfloorExecutionLogPreview,
    };
    static props = {
        execution: Object,
        selectedQueueContext: Object,
        selectedQueueItem: Object,
        logEntries: Array,
        workstation: Object,
        sessionRef: [String, Boolean],
        onStartExecution: Function,
        onPauseExecution: Function,
        onFinishExecution: Function,
        onReportException: Function,
    };
}
