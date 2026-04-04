/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorWorkspaceShell extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorWorkspaceShell";
    static props = {
        currentPanel: String,
        workstation: Object,
        metrics: Object,
        commandQueueStatus: Object,
        sessionRef: [String, Boolean],
        lastResponse: [Object, Boolean],
    };

    get backendStateLabel() {
        return this.props.lastResponse ? "Booted" : "Seed";
    }

    get sessionLabel() {
        return this.props.sessionRef || "n/a";
    }
}
