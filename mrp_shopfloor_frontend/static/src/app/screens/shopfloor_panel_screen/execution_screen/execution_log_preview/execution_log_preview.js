/** @odoo-module **/

import { Component } from "@odoo/owl";
import {
    findLatestRuntimeEntry,
    isProtocolRuntimeEntry,
    normalizeRuntimeEntry,
} from "../../../../utils/shopfloor_runtime_entries";

function normalizeStatusTone(value) {
    const normalized = String(value || "secondary").trim().toLowerCase();
    if (normalized === "success" || normalized === "done") {
        return "success";
    }
    if (normalized === "warning" || normalized === "queued" || normalized === "submitted" || normalized === "acknowledged") {
        return "warning";
    }
    if (normalized === "danger" || normalized === "failed" || normalized === "error" || normalized === "attention") {
        return "danger";
    }
    if (normalized === "info" || normalized === "active" || normalized === "runtime") {
        return "info";
    }
    return "secondary";
}

export class ShopfloorExecutionLogPreview extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorExecutionLogPreview";
    static props = {
        logEntries: Array,
    };

    get latestRuntimeEntry() {
        return normalizeRuntimeEntry(findLatestRuntimeEntry(this.props.logEntries || []));
    }

    entryStatusClass(entry) {
        return `badge rounded-pill text-bg-${normalizeStatusTone(entry?.statusTone || entry?.status || "secondary")}`;
    }

    entryKindClass(entry) {
        return entry?.kind === "runtime" || entry?.kind === "protocol_runtime" || entry?.kind === "protocol-runtime"
            ? "badge rounded-pill text-bg-info"
            : "badge rounded-pill text-bg-secondary";
    }
}
