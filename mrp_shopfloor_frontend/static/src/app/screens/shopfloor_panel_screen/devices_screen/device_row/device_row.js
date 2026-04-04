/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorAttentionNote } from "../../../../../components/shopfloor_status_components/shopfloor_attention_note";
import { ShopfloorStatusBadge } from "../../../../../components/shopfloor_status_components/shopfloor_status_badge";
import {
    deviceAttentionLabel,
    deviceStateLabel,
    deviceStateTone,
} from "../../../../../components/shopfloor_status_components/shopfloor_status_metrics";

export class ShopfloorDeviceRow extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceRow";
    static components = {
        ShopfloorAttentionNote,
        ShopfloorStatusBadge,
    };
    static props = {
        device: Object,
        selected: Boolean,
        onOpenDevice: Function,
    };

    get stateKey() {
        return String(this.props.device?.state || "unknown").trim().replace(/\s+/g, "_").toLowerCase();
    }

    get stateLabel() {
        return deviceStateLabel(this.props.device?.state);
    }

    get stateTone() {
        return deviceStateTone(this.props.device?.state);
    }

    get rowClass() {
        const classes = ["o_mrp_shopfloor_list_item"];
        if (this.props.selected) {
            classes.push("is-selected", "border", "border-primary");
        } else if (["degraded", "error"].includes(this.stateKey)) {
            classes.push("border", "border-warning");
        } else if (this.stateKey === "offline") {
            classes.push("border", "border-secondary");
        }
        return classes.join(" ");
    }

    get attentionLabel() {
        return deviceAttentionLabel(this.props.device?.state) ? "Attention" : null;
    }

    openDevice(ev) {
        this.props.onOpenDevice?.(ev);
    }
}
