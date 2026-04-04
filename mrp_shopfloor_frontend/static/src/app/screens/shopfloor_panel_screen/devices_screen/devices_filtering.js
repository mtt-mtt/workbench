/** @odoo-module **/

const DEVICE_STATE_TONES = {
    ready: 40,
    active: 35,
    degraded: 30,
    offline: 20,
    error: 10,
    unknown: 0,
};

export const DEVICE_GROUP_OPTIONS = [
    { key: "state", label: "State" },
    { key: "kind", label: "Kind" },
    { key: "channel", label: "Channel" },
    { key: "location", label: "Location" },
];

export const DEVICE_STATE_FILTERS = [
    { key: "all", label: "All" },
    { key: "ready", label: "Ready" },
    { key: "active", label: "Active" },
    { key: "attention", label: "Attention" },
    { key: "degraded", label: "Degraded" },
    { key: "offline", label: "Offline" },
    { key: "error", label: "Error" },
    { key: "unknown", label: "Unknown" },
];

function normalizeKey(value, fallback = "unknown") {
    return String(value || fallback).trim().replace(/\s+/g, "_").toLowerCase();
}

function compareText(left, right) {
    return String(left || "").localeCompare(String(right || ""), undefined, {
        numeric: true,
        sensitivity: "base",
    });
}

function deviceStateOrder(device) {
    return DEVICE_STATE_TONES[normalizeKey(device?.state)] ?? 0;
}

export function getDeviceStateKey(device) {
    return normalizeKey(device?.state);
}

export function getDeviceStateLabel(device) {
    return getDeviceStateKey(device).replace(/_/g, " ");
}

export function getDeviceGroupKey(device, groupBy) {
    if (groupBy === "state") {
        return getDeviceStateKey(device);
    }
    return normalizeKey(device?.[groupBy], "unknown");
}

export function getDeviceGroupLabel(device, groupBy, fallbackKey) {
    if (groupBy === "state") {
        return getDeviceStateLabel(device);
    }
    const value = device?.[groupBy];
    return String(value || fallbackKey || "unknown")
        .trim()
        .replace(/\s+/g, " ")
        .replace(/^./, (match) => match.toUpperCase());
}

export function matchesDeviceSearch(device, searchText) {
    if (!searchText) {
        return true;
    }
    const searchable = [
        device?.name,
        device?.code,
        device?.kind,
        device?.signal,
        device?.channel,
        device?.location,
        device?.state,
        device?.value,
        device?.lastSeen,
        device?.message,
    ]
        .filter((value) => value !== null && value !== undefined)
        .join(" ")
        .toLowerCase();
    return searchable.includes(searchText);
}

export function matchesDeviceStateFilter(device, stateFilter) {
    const normalizedFilter = normalizeKey(stateFilter || "all");
    if (!normalizedFilter || normalizedFilter === "all") {
        return true;
    }
    const stateKey = getDeviceStateKey(device);
    if (normalizedFilter === "attention") {
        return ["degraded", "offline", "error"].includes(stateKey);
    }
    if (normalizedFilter === "active") {
        return ["ready", "active"].includes(stateKey);
    }
    return stateKey === normalizedFilter;
}

export function compareDevices(left, right, groupBy = "state") {
    if (groupBy === "state") {
        const stateDelta = deviceStateOrder(right) - deviceStateOrder(left);
        if (stateDelta !== 0) {
            return stateDelta;
        }
    }

    const leftName = left?.name || left?.code || left?.kind;
    const rightName = right?.name || right?.code || right?.kind;
    const nameDelta = compareText(leftName, rightName);
    if (nameDelta !== 0) {
        return nameDelta;
    }

    return compareText(left?.code, right?.code);
}

export function filterDevices(devices, searchText, stateFilter) {
    const list = Array.isArray(devices) ? [...devices] : [];
    const normalizedSearch = String(searchText || "").trim().toLowerCase();
    return list
        .filter((device) => matchesDeviceSearch(device, normalizedSearch))
        .filter((device) => matchesDeviceStateFilter(device, stateFilter))
        .sort((left, right) => compareDevices(left, right));
}

export function groupDevices(devices, groupBy = "state") {
    const list = Array.isArray(devices) ? devices : [];
    const groups = new Map();

    for (const device of list) {
        const key = getDeviceGroupKey(device, groupBy);
        const group = groups.get(key) || {
            key,
            label: getDeviceGroupLabel(device, groupBy, key),
            items: [],
        };
        group.items.push(device);
        groups.set(key, group);
    }

    return Array.from(groups.values())
        .map((group) => ({
            ...group,
            count: group.items.length,
            items: group.items.slice().sort((left, right) =>
                groupBy === "state" ? compareText(left?.name, right?.name) : compareDevices(left, right, groupBy)
            ),
        }))
        .sort((left, right) => {
            if (groupBy === "state") {
                return deviceStateOrder({ state: right.key }) - deviceStateOrder({ state: left.key });
            }
            return compareText(left.label, right.label);
        });
}

export function groupByLabel(groupBy) {
    return DEVICE_GROUP_OPTIONS.find((option) => option.key === groupBy)?.label || "State";
}

export function stateFilterLabel(stateFilter) {
    return DEVICE_STATE_FILTERS.find((option) => option.key === stateFilter)?.label || "All";
}
