/** @odoo-module **/

import { getShopfloorRouteMeta, normalizeRoute as normalizeShopfloorRoute } from "../router/shopfloor_router";

export { normalizeShopfloorRoute };

export function getShopfloorRouteLabel(route) {
    return getShopfloorRouteMeta(route).label;
}

export function routeLabel(route) {
    return getShopfloorRouteLabel(route);
}

export function routeMeta(route) {
    return getShopfloorRouteMeta(route);
}

export function createShopfloorShellService(getDocument = () => document) {
    function updateDocumentTitle(workstationCode, route) {
        const doc = getDocument();
        if (!doc) {
            return;
        }
        const workstation = workstationCode || "Shopfloor";
        const meta = routeMeta(route);
        doc.title = `Shopfloor - ${workstation} - ${meta.label}`;
    }

    return {
        routeLabel,
        routeMeta,
        getShopfloorRouteLabel,
        updateDocumentTitle,
    };
}
