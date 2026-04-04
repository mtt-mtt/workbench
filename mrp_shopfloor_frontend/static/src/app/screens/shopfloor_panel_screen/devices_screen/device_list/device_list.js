/** @odoo-module **/

import { Component } from "@odoo/owl";
import { ShopfloorDeviceRow } from "../device_row/device_row";

export class ShopfloorDeviceList extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDeviceList";
    static components = {
        ShopfloorDeviceRow,
    };
    static props = {
        groupedDevices: Array,
        selectedDevice: Object,
        summary: Object,
        hasActiveFilters: Boolean,
        selectedDeviceVisible: Boolean,
        onOpenDevice: Function,
        onClearFilters: Function,
    };

    get groups() {
        return Array.isArray(this.props.groupedDevices) ? this.props.groupedDevices : [];
    }

    get hasGroups() {
        return this.groups.length > 0;
    }

    get emptyStateLabel() {
        if (this.hasGroups) {
            return null;
        }
        if (this.props.hasActiveFilters || this.props.summary?.isFiltered) {
            return "No devices match the current filters.";
        }
        return "No devices available.";
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

    openDevice(ev) {
        this.props.onOpenDevice?.(ev);
    }

    clearFilters(ev) {
        this.props.onClearFilters?.(ev);
    }
}
