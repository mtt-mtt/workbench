/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

const SHOPFLOOR_ENDPOINTS = {
    action: "/mrp_shopfloor_execution/action",
    boot: "/mrp_shopfloor_execution/boot",
    state: "/mrp_shopfloor_execution/state",
};

export function createShopfloorDataService() {
    async function request(endpoint, payload = {}) {
        const route = SHOPFLOOR_ENDPOINTS[endpoint] || endpoint;
        return rpc(route, payload);
    }

    return {
        request,
        boot(payload = {}) {
            return request("boot", payload);
        },
        state(payload = {}) {
            return request("state", payload);
        },
        action(payload = {}) {
            return request("action", payload);
        },
    };
}
