/** @odoo-module **/

import { reactive } from "@odoo/owl";

const ROUTE_DEFINITIONS = [
    {
        key: "dashboard",
        label: "Dashboard",
        group: "overview",
        description: "Floor summary and live status",
        order: 10,
    },
    {
        key: "queue",
        label: "Queue",
        group: "work",
        description: "Workorder queue and selection",
        order: 20,
    },
    {
        key: "execution",
        label: "Execution",
        group: "work",
        description: "Action chain and operator flow",
        order: 30,
    },
    {
        key: "devices",
        label: "Devices",
        group: "devices",
        description: "Gateway-linked devices and signals",
        order: 40,
    },
    {
        key: "exceptions",
        label: "Exceptions",
        group: "ops",
        description: "Open issues and backend errors",
        order: 50,
    },
];

const ROUTE_META = Object.fromEntries(ROUTE_DEFINITIONS.map((definition) => [definition.key, definition]));

export function normalizeRoute(route, fallback = "dashboard") {
    const value = String(route || "").trim();
    return value || fallback;
}

export function getShopfloorRouteMeta(route) {
    const key = normalizeRoute(route);
    const definition = ROUTE_META[key];
    if (definition) {
        return {
            ...definition,
            key,
            known: true,
        };
    }

    return {
        key,
        label: key,
        group: "custom",
        description: "Custom route",
        order: Number.MAX_SAFE_INTEGER,
        known: false,
    };
}

export function getShopfloorRouteSummary(route) {
    const meta = getShopfloorRouteMeta(route);
    return {
        key: meta.key,
        label: meta.label,
        group: meta.group,
        description: meta.description,
        known: meta.known,
        order: meta.order,
    };
}

export function listShopfloorRoutes() {
    return ROUTE_DEFINITIONS.map((definition) => ({ ...definition }));
}

export function createShopfloorRouter(initialRoute = "dashboard") {
    const startRoute = normalizeRoute(initialRoute);
    const startMeta = getShopfloorRouteMeta(startRoute);
    const state = reactive({
        route: startRoute,
        current: startRoute,
        previous: null,
        history: [startRoute],
        canGoBack: false,
        label: startMeta.label,
        meta: startMeta,
        routes: listShopfloorRoutes(),
    });

    function syncMeta() {
        const meta = getShopfloorRouteMeta(state.route);
        state.current = state.route;
        state.previous = state.history.length > 1 ? state.history[state.history.length - 2] : null;
        state.canGoBack = state.history.length > 1;
        state.label = meta.label;
        state.meta = meta;
    }

    function push(route) {
        const nextRoute = normalizeRoute(route, state.route);
        if (!nextRoute || nextRoute === state.route) {
            return state.route;
        }
        state.route = nextRoute;
        state.history.push(nextRoute);
        syncMeta();
        return state.route;
    }

    function replace(route) {
        const nextRoute = normalizeRoute(route, state.route);
        if (!nextRoute) {
            return state.route;
        }
        state.route = nextRoute;
        if (state.history.length) {
            state.history[state.history.length - 1] = nextRoute;
        } else {
            state.history.push(nextRoute);
        }
        syncMeta();
        return state.route;
    }

    function back() {
        if (state.history.length <= 1) {
            return state.route;
        }
        state.history.pop();
        state.route = state.history[state.history.length - 1];
        syncMeta();
        return state.route;
    }

    function reset(route = startRoute) {
        const nextRoute = normalizeRoute(route, startRoute);
        state.history.splice(0, state.history.length, nextRoute);
        state.route = nextRoute;
        syncMeta();
        return state.route;
    }

    function go(route, options = {}) {
        if (options.replace) {
            return replace(route);
        }
        return push(route);
    }

    function sync(route) {
        const nextRoute = normalizeRoute(route, state.route);
        if (nextRoute !== state.route) {
            return replace(nextRoute);
        }
        return state.route;
    }

    syncMeta();

    return {
        state,
        go,
        push,
        replace,
        back,
        reset,
        sync,
        normalizeRoute,
        getShopfloorRouteMeta,
        listShopfloorRoutes,
    };
}
