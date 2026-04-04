/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorStatusSummary } from "./shopfloor_status_summary";
import { buildActionDescriptors } from "./shopfloor_status_metrics";

export class ShopfloorActionBar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorActionBar";
    static components = {
        ShopfloorStatusSummary,
    };
    static props = {
        title: {
            type: String,
            optional: true,
        },
        subtitle: {
            type: String,
            optional: true,
        },
        summaryItems: {
            type: Array,
            optional: true,
        },
        primaryActions: {
            type: Array,
            optional: true,
        },
        secondaryActions: {
            type: Array,
            optional: true,
        },
        onAction: Function,
    };

    get primaryActionItems() {
        return buildActionDescriptors(this.props.primaryActions);
    }

    get secondaryActionItems() {
        return buildActionDescriptors(this.props.secondaryActions);
    }

    get summaryItems() {
        return Array.isArray(this.props.summaryItems) ? this.props.summaryItems : [];
    }

    get hasSecondaryActions() {
        return this.secondaryActionItems.length > 0;
    }

    triggerAction(ev) {
        this.props.onAction?.(ev);
    }
}
