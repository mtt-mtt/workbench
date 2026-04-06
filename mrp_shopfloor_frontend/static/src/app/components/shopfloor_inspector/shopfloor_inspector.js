/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorActivityCard } from "./shopfloor_activity_card";
import { ShopfloorCommandQueueCard } from "./shopfloor_command_queue_card";
import { ShopfloorResponseCard } from "./shopfloor_response_card";
import { ShopfloorTimelineCard } from "./shopfloor_timeline_card";

export class ShopfloorInspector extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorInspector";
    static components = {
        ShopfloorActivityCard,
        ShopfloorCommandQueueCard,
        ShopfloorResponseCard,
        ShopfloorTimelineCard,
    };
    static props = {
        responseSummary: Object,
        commandQueueStatus: Object,
        gatewayRuntimeSummary: [Object, Boolean],
        metrics: [Object, Boolean],
        commands: Array,
        exceptions: Array,
        timelineEntries: Array,
        logEntries: Array,
        activity: Array,
        lastResponseText: String,
    };
}
