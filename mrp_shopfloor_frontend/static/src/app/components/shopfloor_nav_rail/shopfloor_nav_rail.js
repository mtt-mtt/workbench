/** @odoo-module **/

import { Component } from "@odoo/owl";
import { getShopfloorRouteMeta, listShopfloorRoutes } from "../../router/shopfloor_router";

export class ShopfloorNavRail extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorNavRail";
    static props = {
        panels: Array,
        currentRoute: String,
        currentUserName: String,
        workstation: Object,
        sessionRef: [String, Boolean],
        metrics: Object,
        booted: Boolean,
        onNavigatePanel: Function,
    };

    get activeRouteMeta() {
        return getShopfloorRouteMeta(this.props.currentRoute);
    }

    get navigationPanels() {
        const panels = Array.isArray(this.props.panels) ? this.props.panels : [];
        const routeOrder = new Map(listShopfloorRoutes().map((route, index) => [route.key, index]));
        return panels
            .map((panel) => ({
                ...panel,
                meta: getShopfloorRouteMeta(panel.key),
            }))
            .sort((left, right) => {
                const leftOrder = routeOrder.has(left.key) ? routeOrder.get(left.key) : Number.MAX_SAFE_INTEGER;
                const rightOrder = routeOrder.has(right.key) ? routeOrder.get(right.key) : Number.MAX_SAFE_INTEGER;
                return leftOrder - rightOrder;
            });
    }

    navigatePanel(ev) {
        this.props.onNavigatePanel?.(ev);
    }
}
