/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorQueueRow extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorQueueRow";
    static props = {
        item: Object,
        selected: Boolean,
        onOpenQueueItem: Function,
    };

    get statusKey() {
        return String(this.props.item?.status || "unknown").trim().replace(/\s+/g, "_").toLowerCase();
    }

    get statusLabel() {
        return this.statusKey.replace(/_/g, " ");
    }

    get statusToneClass() {
        const map = {
            done: "text-bg-success",
            ready: "text-bg-success",
            in_progress: "text-bg-info",
            running: "text-bg-info",
            paused: "text-bg-warning",
            waiting: "text-bg-secondary",
            blocked: "text-bg-danger",
            error: "text-bg-danger",
            rejected: "text-bg-danger",
            draft: "text-bg-light",
        };
        return map[this.statusKey] || "text-bg-light";
    }

    get priorityLabel() {
        return String(this.props.item?.priority || "Normal");
    }

    get priorityToneClass() {
        const key = this.priorityLabel.trim().toLowerCase();
        if (["high", "urgent", "critical"].includes(key)) {
            return "text-bg-warning";
        }
        return "text-bg-secondary";
    }

    get progressLabel() {
        const done = this.props.item?.done ?? 0;
        const quantity = this.props.item?.quantity ?? 0;
        return this.props.item?.progress || `${done} / ${quantity}`;
    }

    get rowClass() {
        const classes = ["o_mrp_shopfloor_list_item"];
        if (this.props.selected) {
            classes.push("is-selected", "border", "border-primary");
        } else if (["blocked", "error", "rejected"].includes(this.statusKey)) {
            classes.push("border", "border-danger");
        } else if (["paused", "waiting"].includes(this.statusKey)) {
            classes.push("border", "border-warning");
        }
        return classes.join(" ");
    }

    get attentionLabel() {
        return ["blocked", "error", "rejected"].includes(this.statusKey) ? "Attention required" : null;
    }

    openQueueItem(ev) {
        this.props.onOpenQueueItem?.(ev);
    }
}
