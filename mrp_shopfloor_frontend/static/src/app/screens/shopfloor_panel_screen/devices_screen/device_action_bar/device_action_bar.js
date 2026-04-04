/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorDeviceActionBar extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceActionBar";
    static props = {
        selectedDevice: Object,
        selectedDeviceVisible: Boolean,
        actionCandidates: Array,
        onSelectAction: Function,
    };

    get actions() {
        return Array.isArray(this.props.actionCandidates) ? this.props.actionCandidates : [];
    }

    get hasDevice() {
        return Boolean(this.props.selectedDevice && this.props.selectedDevice.code !== "DEVICE-EMPTY");
    }

    get stateLabel() {
        return String(this.props.selectedDevice?.state || "unknown").replace(/_/g, " ");
    }

    get visibilityLabel() {
        if (!this.props.selectedDevice) {
            return "Select a device to build a local command draft.";
        }
        if (this.props.selectedDeviceVisible === false) {
            return "This device is hidden by the current filters. Actions still preview locally.";
        }
        return "Choose a local action to preview and confirm.";
    }

    buttonClass(action) {
        const tone = String(action?.tone || "secondary").toLowerCase();
        const map = {
            success: "btn-outline-success",
            warning: "btn-outline-warning",
            danger: "btn-outline-danger",
            info: "btn-outline-info",
            light: "btn-outline-light",
            secondary: "btn-outline-secondary",
        };
        return map[tone] || map.secondary;
    }

    selectAction(ev) {
        const actionKey = ev.currentTarget.dataset.actionKey;
        const action = this.actions.find((candidate) => candidate.key === actionKey);
        if (action) {
            this.props.onSelectAction?.(action);
        }
    }
}
