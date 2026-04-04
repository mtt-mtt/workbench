/** @odoo-module **/

import { Component } from "@odoo/owl";
import { feedbackToneClass } from "./shopfloor_status_metrics";

export class ShopfloorFeedbackBar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorFeedbackBar";
    static props = {
        label: String,
        detail: {
            type: String,
            optional: true,
        },
        tone: {
            type: String,
            optional: true,
        },
        actionLabel: {
            type: String,
            optional: true,
        },
        onAction: Function,
        compact: {
            type: Boolean,
            optional: true,
        },
    };

    get noteClass() {
        const classes = ["o_mrp_shopfloor_feedback_bar"];
        if (this.props.compact) {
            classes.push("o_mrp_shopfloor_feedback_bar--compact");
        }
        return classes.join(" ");
    }

    get toneClass() {
        return feedbackToneClass(this.props.tone);
    }

    triggerAction(ev) {
        this.props.onAction?.(ev);
    }
}
