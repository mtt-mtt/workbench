/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorAttentionNote } from "../../../../../components/shopfloor_status_components/shopfloor_attention_note";
import { ShopfloorStatusBadge } from "../../../../../components/shopfloor_status_components/shopfloor_status_badge";
import {
    deviceAttentionLabel,
    deviceStateLabel,
    deviceStateTone,
} from "../../../../../components/shopfloor_status_components/shopfloor_status_metrics";

export class ShopfloorDeviceDetail extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceDetail";
    static components = {
        ShopfloorAttentionNote,
        ShopfloorStatusBadge,
    };
    static props = {
        selectedDevice: Object,
        summary: Object,
        selectedDeviceVisible: Boolean,
        onClearFilters: Function,
    };

    get stateKey() {
        return String(this.props.selectedDevice?.state || "unknown").trim().replace(/\s+/g, "_").toLowerCase();
    }

    get stateLabel() {
        return deviceStateLabel(this.props.selectedDevice?.state);
    }

    get stateTone() {
        return deviceStateTone(this.props.selectedDevice?.state);
    }

    get attentionLabel() {
        return deviceAttentionLabel(this.props.selectedDevice?.state) ? "Attention required" : null;
    }

    get filterSummaryLabel() {
        const summary = this.props.summary || {};
        if (!summary.isFiltered) {
            return null;
        }
        const parts = [];
        if (summary.searchText) {
            parts.push(`Search "${summary.searchText}"`);
        }
        if (summary.stateFilterLabel && summary.stateFilter !== "all") {
            parts.push(`State ${summary.stateFilterLabel}`);
        }
        if (summary.groupByLabel && summary.groupBy !== "state") {
            parts.push(`Group ${summary.groupByLabel}`);
        }
        return parts.join(" | ");
    }

    get selectionVisibilityLabel() {
        if (this.props.selectedDevice && this.props.selectedDeviceVisible === false) {
            return "Selected device is hidden by the current filters.";
        }
        return null;
    }

    get showClearFilters() {
        return this.props.selectedDeviceVisible === false || Boolean(this.props.summary?.isFiltered);
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
