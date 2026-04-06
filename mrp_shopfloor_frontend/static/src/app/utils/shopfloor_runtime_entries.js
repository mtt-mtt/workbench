/** @odoo-module **/

function normalizedKind(entry) {
    return String(entry?.kind || "").trim().toLowerCase();
}

function titleTokens(entry) {
    return String(entry?.title || entry?.label || "").toLowerCase();
}

export function isProtocolRuntimeEntry(entry) {
    const kind = normalizedKind(entry);
    if (kind === "protocol-runtime" || kind === "protocol_runtime") {
        return true;
    }
    if (
        entry?.protocolRuntimeLabel !== undefined ||
        entry?.protocolRuntimeDetail !== undefined ||
        entry?.protocolRuntimeTone !== undefined ||
        entry?.protocolRuntimeAttention !== undefined
    ) {
        return true;
    }
    return titleTokens(entry).includes("protocol runtime");
}

export function isGenericRuntimeEntry(entry) {
    const kind = normalizedKind(entry);
    if (kind === "runtime") {
        return true;
    }
    return ["driver issues", "dead letters", "replay pending", "edge actions"].some((token) =>
        titleTokens(entry).includes(token)
    );
}

export function findLatestRuntimeEntry(entries = []) {
    const normalizedEntries = Array.isArray(entries) ? entries : [];
    return normalizedEntries.find(isProtocolRuntimeEntry) || normalizedEntries.find(isGenericRuntimeEntry) || null;
}

export function normalizeRuntimeEntry(entry) {
    if (!entry) {
        return null;
    }
    const protocolRuntime = isProtocolRuntimeEntry(entry);
    const label =
        entry.protocolRuntimeLabel ||
        entry.label ||
        entry.title ||
        (protocolRuntime ? "Protocol runtime diagnostics" : "Runtime diagnostics");
    const detail = entry.protocolRuntimeDetail || entry.detail || entry.protocolRuntimeStateSummary || null;
    const statusTone =
        String(entry.protocolRuntimeTone || entry.statusTone || entry.status || "")
            .trim()
            .toLowerCase() || "info";
    const statusLabel =
        entry.statusLabel ||
        (statusTone === "success"
            ? "Success"
            : statusTone === "warning"
              ? "Warning"
              : statusTone === "danger"
                ? "Danger"
                : "Info");
    return {
        ...entry,
        title: label,
        label,
        detail,
        statusTone,
        statusLabel,
        status: entry.status || statusTone,
    };
}
