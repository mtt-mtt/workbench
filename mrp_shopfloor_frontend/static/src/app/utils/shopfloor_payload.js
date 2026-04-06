/** @odoo-module **/

import {
    commandStateKey,
    commandStateLabel,
    commandStateTone,
    exceptionSeverityKey,
    exceptionSeverityLabel,
    exceptionSeverityTone,
    exceptionStateKey,
    exceptionStateLabel,
    exceptionStateTone,
} from "../components/shopfloor_status_components/shopfloor_status_metrics";

function isPlainObject(value) {
    return !!value && typeof value === "object" && !Array.isArray(value);
}

function toArray(value) {
    if (Array.isArray(value)) {
        return value.filter((item) => item !== null && item !== undefined);
    }
    if (isPlainObject(value)) {
        return Object.values(value).filter((item) => item !== null && item !== undefined);
    }
    if (value === null || value === undefined || value === "") {
        return [];
    }
    return [value];
}

function firstValue(...values) {
    for (const value of values) {
        if (value !== null && value !== undefined && value !== "") {
            return value;
        }
    }
    return null;
}

function getByPath(source, path) {
    if (!isPlainObject(source) || !path) {
        return undefined;
    }
    return path.split(".").reduce((current, segment) => {
        if (current === null || current === undefined) {
            return undefined;
        }
        return current[segment];
    }, source);
}

function findCollection(sources, paths) {
    for (const source of sources) {
        if (!source) {
            continue;
        }
        for (const path of paths) {
            const value = getByPath(source, path);
            const normalized = toArray(value);
            if (normalized.length) {
                return normalized;
            }
        }
    }
    return [];
}

function findObject(sources, paths) {
    for (const source of sources) {
        if (!source) {
            continue;
        }
        for (const path of paths) {
            const value = getByPath(source, path);
            if (isPlainObject(value)) {
                return value;
            }
        }
    }
    return null;
}

function toInteger(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeStatus(value, fallback = "unknown") {
    return String(firstValue(value, fallback))
        .trim()
        .replace(/_/g, " ");
}

function labelizeKey(value, fallback = "Unknown") {
    const normalized = String(value || fallback)
        .trim()
        .replace(/\s+/g, "_")
        .toLowerCase();
    return normalized.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function toneForKey(key, map, fallback = "secondary") {
    return map?.[key] || fallback;
}

function normalizeCountMap(value) {
    if (!isPlainObject(value)) {
        return {};
    }
    return Object.fromEntries(Object.entries(value).map(([key, count]) => [key, toInteger(count, 0)]));
}

function normalizeProtocolRuntimeEntry(item, index = 0) {
    if (!isPlainObject(item)) {
        const label = String(item || `Protocol runtime ${index + 1}`);
        return {
            id: `protocol-runtime-${index}`,
            code: label,
            label,
            kind: "runtime",
            state: "unknown",
            stateKey: "unknown",
            stateLabel: "Unknown",
            stateTone: "secondary",
            detail: null,
            summary: null,
            loaded: null,
            error: null,
            runtimeState: "unknown",
            raw: item,
        };
    }
    const runtimeState = firstValue(item.protocol_runtime_state, item.runtime_state, item.state, "unknown");
    const stateKey = String(firstValue(runtimeState, "unknown"))
        .trim()
        .replace(/\s+/g, "_")
        .toLowerCase();
    return {
        id: firstValue(item.id, item.code, `protocol-runtime-${index}`),
        code: firstValue(item.code, item.adapter_code, item.name, item.id, `protocol-runtime-${index}`),
        label: firstValue(item.label, item.title, item.name, item.code, `Protocol runtime ${index + 1}`),
        kind: firstValue(item.kind, item.adapter_type, item.type, "runtime"),
        state: stateKey,
        stateKey,
        stateLabel: firstValue(
            item.state_label,
            item.protocol_runtime_state_label,
            item.runtime_state_label,
            labelizeKey(stateKey, "Unknown")
        ),
        stateTone: firstValue(item.state_tone, item.protocol_runtime_state_tone, item.runtime_state_tone, "secondary"),
        detail: firstValue(item.detail, item.summary, item.runtime_summary, null),
        summary: firstValue(item.summary, item.runtime_summary, item.detail, null),
        loaded:
            typeof item.protocol_runtime_loaded === "boolean"
                ? item.protocol_runtime_loaded
                : typeof item.loaded === "boolean"
                  ? item.loaded
                  : null,
        error: firstValue(item.protocol_runtime_error, item.runtime_error, item.error, null),
        runtimeState: runtimeState,
        raw: item,
    };
}

function summarizeProtocolRuntime(protocolRuntimeCount, protocolRuntimeEntryCount, stateCounts = {}) {
    const readyCount = toInteger(firstValue(stateCounts.ready, 0));
    const pendingCount = toInteger(firstValue(stateCounts.pending, 0));
    const unavailableCount = toInteger(firstValue(stateCounts.unavailable, 0));
    const stoppedCount = toInteger(firstValue(stateCounts.stopped, 0));
    const errorCount = toInteger(firstValue(stateCounts.error, 0));
    const loadedCount = toInteger(firstValue(stateCounts.loaded, 0));
    const activeCount = protocolRuntimeEntryCount || protocolRuntimeCount || readyCount || pendingCount || unavailableCount || stoppedCount || errorCount || loadedCount;
    const stateKey =
        errorCount > 0
            ? "danger"
            : pendingCount > 0 || unavailableCount > 0
              ? "warning"
              : readyCount > 0 || activeCount > 0
                ? "success"
                : stoppedCount > 0
                  ? "info"
                  : "secondary";
    const detailParts = [
        protocolRuntimeCount ? `${protocolRuntimeCount} runtime${protocolRuntimeCount === 1 ? "" : "s"}` : null,
        protocolRuntimeEntryCount && protocolRuntimeEntryCount !== protocolRuntimeCount
            ? `${protocolRuntimeEntryCount} entries`
            : null,
        readyCount ? `ready ${readyCount}` : null,
        pendingCount ? `pending ${pendingCount}` : null,
        unavailableCount ? `unavailable ${unavailableCount}` : null,
        stoppedCount ? `stopped ${stoppedCount}` : null,
        errorCount ? `error ${errorCount}` : null,
        loadedCount ? `loaded ${loadedCount}` : null,
    ].filter(Boolean);
    return {
        stateKey,
        stateLabel: labelizeKey(stateKey, "Secondary"),
        stateTone: toneForKey(stateKey, { danger: "danger", warning: "warning", success: "success", info: "info" }, "secondary"),
        detail: detailParts.join(" | ") || null,
    };
}

function normalizeProtocolRuntimeSummaryState(value, fallback = "secondary") {
    const normalized = String(value || fallback)
        .trim()
        .replace(/\s+/g, "_")
        .toLowerCase();
    if (["danger", "error", "failed"].includes(normalized)) {
        return "danger";
    }
    if (["warning", "attention", "pending", "unavailable"].includes(normalized)) {
        return "warning";
    }
    if (["success", "ready", "loaded"].includes(normalized)) {
        return "success";
    }
    if (["info", "stopped", "active"].includes(normalized)) {
        return "info";
    }
    return fallback;
}

function buildProtocolRuntimeSharedSummary(source = {}) {
    const protocolRuntime = isPlainObject(source?.protocolRuntime) ? source.protocolRuntime : {};
    const protocolRuntimeCount = toInteger(firstValue(source?.protocolRuntimeCount, protocolRuntime.count, 0));
    const protocolRuntimeEntryCount = toInteger(firstValue(source?.protocolRuntimeEntryCount, protocolRuntime.entryCount, 0));
    const protocolRuntimeStateCounts = normalizeCountMap(
        firstValue(source?.protocolRuntimeStateCounts, protocolRuntime.stateCounts, {})
    );
    const protocolRuntimeSummary = firstValue(
        source?.protocolRuntimeSummary,
        protocolRuntime.summary,
        protocolRuntime.detail,
        null
    );
    const protocolRuntimeStateSummary = summarizeProtocolRuntime(
        protocolRuntimeCount,
        protocolRuntimeEntryCount,
        protocolRuntimeStateCounts
    );
    const protocolRuntimeState = normalizeProtocolRuntimeSummaryState(
        firstValue(
            source?.protocolRuntimeStateKey,
            source?.protocolRuntimeState,
            protocolRuntime.stateKey,
            protocolRuntime.state,
            protocolRuntimeStateSummary.stateKey,
            "secondary"
        ),
        protocolRuntimeStateSummary.stateKey
    );
    const errorCount = toInteger(firstValue(protocolRuntimeStateCounts.error, 0));
    const pendingCount = toInteger(firstValue(protocolRuntimeStateCounts.pending, 0));
    const unavailableCount = toInteger(firstValue(protocolRuntimeStateCounts.unavailable, 0));
    const readyCount = toInteger(firstValue(protocolRuntimeStateCounts.ready, 0));
    const attentionCount = Math.max(
        errorCount + pendingCount + unavailableCount,
        ["danger", "warning"].includes(protocolRuntimeState)
            ? toInteger(firstValue(protocolRuntimeCount, protocolRuntimeEntryCount, 0))
            : 0
    );
    const primaryCount =
        attentionCount || readyCount || protocolRuntimeCount || protocolRuntimeEntryCount || 0;
    const headline =
        protocolRuntimeState === "danger"
            ? "Protocol runtime error"
            : protocolRuntimeState === "warning"
              ? "Protocol runtime attention"
              : protocolRuntimeState === "success"
                ? "Protocol runtime ready"
                : null;
    const label =
        protocolRuntimeState === "danger"
            ? `Protocol error ${errorCount || primaryCount}`
            : protocolRuntimeState === "warning"
              ? `Protocol attention ${attentionCount || primaryCount}`
              : protocolRuntimeState === "success"
                ? `Protocol ready ${readyCount || protocolRuntimeCount || protocolRuntimeEntryCount}`
                : null;
    const detail =
        protocolRuntimeSummary ||
        (protocolRuntimeState === "danger"
            ? `${errorCount || primaryCount} protocol runtime(s) are reporting errors.`
            : protocolRuntimeState === "warning"
              ? `${attentionCount || primaryCount} protocol runtime(s) need follow-up.`
              : protocolRuntimeState === "success"
                ? `${readyCount || protocolRuntimeCount || protocolRuntimeEntryCount} protocol runtime(s) reported ready.`
                : protocolRuntimeStateSummary.detail);
    return {
        stateKey: protocolRuntimeState,
        stateLabel: labelizeKey(protocolRuntimeState, "Secondary"),
        stateTone: toneForKey(
            protocolRuntimeState,
            { danger: "danger", warning: "warning", success: "success", info: "info" },
            "secondary"
        ),
        headline,
        label,
        detail,
        summary: protocolRuntimeSummary || protocolRuntimeStateSummary.detail,
        attentionCount,
        primaryCount,
        count: protocolRuntimeCount,
        entryCount: protocolRuntimeEntryCount,
        stateCounts: protocolRuntimeStateCounts,
        hasSignal: Boolean(protocolRuntimeSummary || primaryCount || protocolRuntimeStateSummary.detail),
    };
}

function buildStateMeta(value, keyFn, labelFn, toneFn, fallbackKey) {
    const key = keyFn(value || fallbackKey);
    return {
        key,
        label: labelFn(key),
        tone: toneFn(key),
    };
}

function normalizePrintExecution(value) {
    if (!isPlainObject(value)) {
        return null;
    }
    const driverCapabilities = isPlainObject(value.driver_capabilities) ? value.driver_capabilities : {};
    const driverDiagnostics = isPlainObject(value.driver_diagnostics) ? value.driver_diagnostics : {};
    return {
        state: firstValue(value.state, value.execution_state, null),
        executionState: firstValue(value.execution_state, value.state, null),
        status: firstValue(value.status, value.result, null),
        serviceMode: firstValue(value.service_mode, value.execution_mode, null),
        serviceEndpoint: firstValue(value.service_endpoint, value.service_url, null),
        serviceJobId: firstValue(value.service_job_id, null),
        serviceStatusCode: firstValue(value.service_status_code, null),
        serviceErrorCode: firstValue(value.service_error_code, null),
        serviceErrorDetail: firstValue(value.service_error_detail, null),
        serviceCompletedAt: firstValue(value.service_completed_at, null),
        serviceAcceptedAt: firstValue(value.service_accepted_at, null),
        serviceStatusUrl: firstValue(value.service_status_url, value.service_url, null),
        serviceCheckedAt: firstValue(value.service_checked_at, null),
        serviceDocumentUrl: firstValue(value.service_document_url, null),
        servicePreviewUrl: firstValue(value.service_preview_url, null),
        servicePrinterCode: firstValue(value.service_printer_code, null),
        printerStatus: firstValue(value.printer_status, null),
        printedCopies: toInteger(firstValue(value.printed_copies, 0)),
        printerName: firstValue(value.printer_name, null),
        requestId: firstValue(value.request_id, null),
        resultText: firstValue(value.result_text, null),
        serviceSummary: firstValue(value.service_summary, value.summary, null),
        errorMessage: firstValue(value.error_message, null),
        driverOrigin: firstValue(value.driver_origin, driverDiagnostics.origin, null),
        driverReady:
            Object.prototype.hasOwnProperty.call(value, "driver_ready") && typeof value.driver_ready === "boolean"
                ? value.driver_ready
                : Object.prototype.hasOwnProperty.call(driverDiagnostics, "ready") && typeof driverDiagnostics.ready === "boolean"
                  ? driverDiagnostics.ready
                : null,
        driverLabel: firstValue(value.driver_label, driverDiagnostics.label, null),
        driverType: firstValue(value.driver_type, driverDiagnostics.type, null),
        driverPath: firstValue(value.driver_path, driverDiagnostics.path, null),
        driverCapabilities,
        driverDiagnostics,
        serviceRequest: isPlainObject(value.service_request) ? value.service_request : {},
        serviceResponse: isPlainObject(value.service_response) ? value.service_response : {},
        printPlan: isPlainObject(value.print_plan) ? value.print_plan : {},
        barcodeValidation: isPlainObject(value.barcode_validation) ? value.barcode_validation : {},
        raw: value,
    };
}

function buildPrintExecutionDetailItems(printExecution) {
    if (!printExecution) {
        return [];
    }
    return [
        printExecution.state ? `state ${printExecution.state}` : null,
        printExecution.executionState ? `execution ${printExecution.executionState}` : null,
        printExecution.serviceAcceptedAt ? `accepted ${printExecution.serviceAcceptedAt}` : null,
        printExecution.serviceCompletedAt ? `completed ${printExecution.serviceCompletedAt}` : null,
        printExecution.serviceCheckedAt ? `checked ${printExecution.serviceCheckedAt}` : null,
        printExecution.serviceMode ? `mode ${printExecution.serviceMode}` : null,
        printExecution.serviceJobId ? `job ${printExecution.serviceJobId}` : null,
        printExecution.serviceStatusCode !== null && printExecution.serviceStatusCode !== undefined
            ? `code ${printExecution.serviceStatusCode}`
            : null,
        printExecution.serviceStatusUrl ? `status ${printExecution.serviceStatusUrl}` : null,
        printExecution.serviceErrorCode ? `error ${printExecution.serviceErrorCode}` : null,
        printExecution.printerStatus ? `printer ${printExecution.printerStatus}` : null,
        printExecution.servicePrinterCode ? `device ${printExecution.servicePrinterCode}` : null,
        printExecution.driverOrigin ? `driver ${printExecution.driverOrigin}` : null,
        printExecution.driverReady === true ? "driver ready" : null,
        printExecution.driverReady === false ? "driver error" : null,
        printExecution.driverLabel ? `label ${printExecution.driverLabel}` : null,
        printExecution.driverCapabilities?.status_polling_supported === true ? "polling ready" : null,
        printExecution.driverCapabilities &&
        Object.prototype.hasOwnProperty.call(printExecution.driverCapabilities, "status_polling_supported") &&
        printExecution.driverCapabilities.status_polling_supported === false
            ? "polling limited"
            : null,
        printExecution.driverCapabilities?.supports_refresh_status === true ? "refresh-status supported" : null,
        printExecution.driverCapabilities &&
        Object.prototype.hasOwnProperty.call(printExecution.driverCapabilities, "supports_refresh_status") &&
        printExecution.driverCapabilities.supports_refresh_status === false
            ? "refresh-status unavailable"
            : null,
        printExecution.driverCapabilities?.supports_status_endpoint === true ? "status endpoint ready" : null,
        printExecution.driverCapabilities?.has_status_endpoint_method === true &&
        printExecution.driverCapabilities?.supports_status_endpoint !== true
            ? "status endpoint empty"
            : null,
        printExecution.printedCopies !== null && printExecution.printedCopies !== undefined
            ? `${printExecution.printedCopies} copies`
            : null,
        printExecution.serviceDocumentUrl ? "document ready" : null,
        printExecution.servicePreviewUrl ? "preview ready" : null,
    ]
        .filter(Boolean)
        .map((label, index) => ({
            key: `${index}-${label}`,
            label,
        }));
}

function buildPrintExecutionBadge(printExecution) {
    const items = buildPrintExecutionDetailItems(printExecution);
    return items.length ? items.map((item) => item.label).join(" | ") : null;
}

export function normalizeActivityEntry(item, index = 0) {
    if (!isPlainObject(item)) {
        const label = String(item || "Activity");
        return {
            id: `activity-${index}`,
            title: label,
            label,
            detail: null,
            kind: "activity",
            status: "info",
            statusKey: "info",
            statusLabel: "Info",
            statusTone: "info",
            timestamp: null,
            raw: item,
        };
    }
    const statusKey = normalizeStatus(firstValue(item.statusKey, item.status, item.state, "info"))
        .trim()
        .replace(/\s+/g, "_")
        .toLowerCase();
    return {
        id: firstValue(item.id, `activity-${index}`),
        title: firstValue(item.title, item.label, item.message, "Activity"),
        label: firstValue(item.label, item.title, item.message, "Activity"),
        detail: firstValue(item.detail, item.description, null),
        kind: firstValue(item.kind, "activity"),
        status: statusKey,
        statusKey,
        statusLabel: firstValue(item.statusLabel, labelizeKey(statusKey, "Info")),
        statusTone: firstValue(item.statusTone, item.tone, statusKey),
        timestamp: firstValue(item.timestamp, item.createdAt, item.created_at, null),
        raw: item,
    };
}

function normalizeGatewayRuntimeSummary(value) {
    if (!isPlainObject(value)) {
        return null;
    }
    const issueCounts = isPlainObject(value.driver_issue_counts) ? value.driver_issue_counts : {};
    const driverCounts = isPlainObject(value.driver_counts) ? value.driver_counts : {};
    const edgeActionCounts = isPlainObject(value.edge_action_counts) ? value.edge_action_counts : {};
    const edgeReplay = isPlainObject(value.edge_replay) ? value.edge_replay : {};
    const edgeDeadLetter = isPlainObject(value.edge_dead_letter) ? value.edge_dead_letter : {};
    const protocolRuntime = isPlainObject(value.edge_protocol_runtime) ? value.edge_protocol_runtime : isPlainObject(value.protocol_runtime) ? value.protocol_runtime : {};
    const protocolRuntimeStateCounts = normalizeCountMap(
        firstValue(
            value.edge_protocol_runtime_state_counts,
            value.protocol_runtime_state_counts,
            protocolRuntime.state_counts,
            protocolRuntime.protocol_runtime_state_counts,
            {}
        )
    );
    const protocolRuntimeKindCounts = normalizeCountMap(
        firstValue(
            value.edge_protocol_runtime_kind_counts,
            value.protocol_runtime_kind_counts,
            protocolRuntime.kind_counts,
            protocolRuntime.protocol_runtime_kind_counts,
            {}
        )
    );
    const protocolRuntimes = [
        ...toArray(value.edge_protocol_runtimes),
        ...toArray(value.protocol_runtimes),
        ...toArray(protocolRuntime.runtimes),
        ...toArray(protocolRuntime.protocol_runtimes),
    ].map((item, index) => normalizeProtocolRuntimeEntry(item, index));
    const protocolRuntimeCount = toInteger(
        firstValue(value.edge_protocol_runtime_count, value.protocol_runtime_count, protocolRuntime.count, protocolRuntime.protocol_runtime_count, protocolRuntimes.length)
    );
    const protocolRuntimeEntryCount = toInteger(
        firstValue(
            value.edge_protocol_runtime_entry_count,
            value.protocol_runtime_entry_count,
            protocolRuntime.entry_count,
            protocolRuntime.protocol_runtime_entry_count,
            protocolRuntimes.length
        )
    );
    const protocolRuntimeState = firstValue(
        value.edge_protocol_runtime_state,
        value.protocol_runtime_state,
        protocolRuntime.state,
        protocolRuntime.runtime_state,
        null
    );
    const protocolRuntimeStateSummary = summarizeProtocolRuntime(protocolRuntimeCount, protocolRuntimeEntryCount, protocolRuntimeStateCounts);
    const protocolRuntimeResolvedState = firstValue(protocolRuntimeState, protocolRuntimeStateSummary.stateKey, "secondary");
    const protocolRuntimeResolvedStateKey = String(protocolRuntimeResolvedState || "secondary")
        .trim()
        .replace(/\s+/g, "_")
        .toLowerCase();
    const protocolRuntimeSharedSummary = buildProtocolRuntimeSharedSummary({
        protocolRuntimeSummary: firstValue(
            value.edge_protocol_runtime_summary,
            value.protocol_runtime_summary,
            protocolRuntime.summary,
            protocolRuntime.detail,
            protocolRuntimeStateSummary.detail,
            null
        ),
        protocolRuntimeCount,
        protocolRuntimeEntryCount,
        protocolRuntimeState: protocolRuntimeResolvedStateKey,
        protocolRuntimeStateKey: protocolRuntimeResolvedStateKey,
        protocolRuntimeStateCounts,
        protocolRuntime: {
            summary: firstValue(
                value.edge_protocol_runtime_summary,
                value.protocol_runtime_summary,
                protocolRuntime.summary,
                protocolRuntime.detail,
                protocolRuntimeStateSummary.detail,
                null
            ),
            count: protocolRuntimeCount,
            entryCount: protocolRuntimeEntryCount,
            state: protocolRuntimeResolvedStateKey,
            stateKey: protocolRuntimeResolvedStateKey,
            stateCounts: protocolRuntimeStateCounts,
        },
    });
    const stateKey = String(firstValue(value.state, issueCounts.open ? "danger" : "secondary")).toLowerCase();
    return {
        state: stateKey,
        stateKey,
        stateLabel: labelizeKey(stateKey, "Info"),
        stateTone: stateKey,
        label: firstValue(value.label, "Driver diagnostics"),
        detail: firstValue(value.detail, value.summary, null),
        summary: firstValue(value.summary, value.detail, null),
        adapterCount: toInteger(firstValue(value.adapter_count, 0)),
        issueCounts: {
            total: toInteger(firstValue(issueCounts.total, 0)),
            open: toInteger(firstValue(issueCounts.open, 0)),
            resolved: toInteger(firstValue(issueCounts.resolved, 0)),
            adapters: toInteger(firstValue(issueCounts.adapters, 0)),
            openAdapters: toInteger(firstValue(issueCounts.open_adapters, 0)),
        },
        driverCounts: {
            ready: toInteger(firstValue(driverCounts.ready, 0)),
            attention: toInteger(firstValue(driverCounts.attention, 0)),
            error: toInteger(firstValue(driverCounts.error, 0)),
            unknown: toInteger(firstValue(driverCounts.unknown, 0)),
        },
        edgeActionCounts: {
            total: toInteger(firstValue(edgeActionCounts.total, 0)),
            pending: toInteger(firstValue(edgeActionCounts.pending, 0)),
            processing: toInteger(firstValue(edgeActionCounts.processing, 0)),
            processed: toInteger(firstValue(edgeActionCounts.processed, 0)),
            adapters: toInteger(firstValue(edgeActionCounts.adapters, 0)),
            processingAdapters: toInteger(firstValue(edgeActionCounts.processing_adapters, 0)),
        },
        edgeActionSummary: firstValue(value.edge_action_summary, null),
        edgeReplay: {
            pending: toInteger(firstValue(edgeReplay.pending, 0)),
            due: toInteger(firstValue(edgeReplay.due, 0)),
            scheduled: toInteger(firstValue(edgeReplay.scheduled, 0)),
            adapters: toInteger(firstValue(edgeReplay.adapters, 0)),
            dueAdapters: toInteger(firstValue(edgeReplay.due_adapters, edgeReplay.dueAdapters, 0)),
            scheduledAdapters: toInteger(firstValue(edgeReplay.scheduled_adapters, edgeReplay.scheduledAdapters, 0)),
            coalescedCount: toInteger(firstValue(edgeReplay.coalesced_count, edgeReplay.coalescedCount, 0)),
            historyCount: toInteger(firstValue(edgeReplay.history_count, edgeReplay.historyCount, 0)),
            lastOutcome: firstValue(edgeReplay.last_outcome, edgeReplay.lastOutcome, null),
            lastSummary: firstValue(edgeReplay.last_summary, edgeReplay.lastSummary, null),
            nextRetryAt: firstValue(edgeReplay.next_retry_at, edgeReplay.nextRetryAt, null),
            latestCoalescedAt: firstValue(edgeReplay.latest_coalesced_at, edgeReplay.latestCoalescedAt, null),
            summary: firstValue(edgeReplay.summary, null),
        },
        edgeDeadLetter: {
            count: toInteger(firstValue(edgeDeadLetter.count, 0)),
            adapters: toInteger(firstValue(edgeDeadLetter.adapters, 0)),
            summary: firstValue(edgeDeadLetter.summary, null),
        },
        protocolRuntime: {
            summary: firstValue(
                value.edge_protocol_runtime_summary,
                value.protocol_runtime_summary,
                protocolRuntime.summary,
                protocolRuntime.detail,
                protocolRuntimeStateSummary.detail,
                null
            ),
            count: protocolRuntimeCount,
            entryCount: protocolRuntimeEntryCount,
            state: protocolRuntimeResolvedStateKey,
            stateKey: protocolRuntimeResolvedStateKey,
            stateLabel: labelizeKey(protocolRuntimeResolvedState, "Secondary"),
            stateTone: protocolRuntimeStateSummary.stateTone,
            stateCounts: protocolRuntimeStateCounts,
            kindCounts: protocolRuntimeKindCounts,
            runtimes: protocolRuntimes,
            detail: protocolRuntimeStateSummary.detail,
            headline: protocolRuntimeSharedSummary.headline,
            label: protocolRuntimeSharedSummary.label,
            tone: protocolRuntimeSharedSummary.stateTone,
            attentionCount: protocolRuntimeSharedSummary.attentionCount,
        },
        protocolRuntimeSummary: firstValue(
            value.edge_protocol_runtime_summary,
            value.protocol_runtime_summary,
            protocolRuntime.summary,
            protocolRuntime.detail,
            protocolRuntimeStateSummary.detail,
            null
        ),
        protocolRuntimeCount,
        protocolRuntimeEntryCount,
        protocolRuntimeState: protocolRuntimeResolvedStateKey,
        protocolRuntimeStateKey: protocolRuntimeResolvedStateKey,
        protocolRuntimeStateLabel: labelizeKey(protocolRuntimeResolvedState, "Secondary"),
        protocolRuntimeStateTone: protocolRuntimeStateSummary.stateTone,
        protocolRuntimeStateCounts,
        protocolRuntimeKindCounts,
        protocolRuntimes,
        protocolRuntimeHeadline: protocolRuntimeSharedSummary.headline,
        protocolRuntimeLabel: protocolRuntimeSharedSummary.label,
        protocolRuntimeDetail: protocolRuntimeSharedSummary.detail,
        protocolRuntimeTone: protocolRuntimeSharedSummary.stateTone,
        protocolRuntimeAttention: protocolRuntimeSharedSummary.attentionCount,
        raw: value,
    };
}

export function buildQueueContext(item) {
    if (!item) {
        return null;
    }

    const raw = item.raw || item;
    return {
        id: firstValue(item.id, raw.id, null),
        queue_id: firstValue(item.queue_id, raw.queue_id, item.id, raw.id, null),
        workorder_id: firstValue(item.workorder_id, raw.workorder_id, raw.workorder?.id, null),
        production_id: firstValue(item.production_id, raw.production_id, raw.production?.id, null),
        reference: firstValue(item.reference, raw.reference, raw.order_ref, null),
        workorder_ref: firstValue(item.workorder_ref, raw.workorder_ref, raw.workorder_reference, raw.workorder_code, null),
        production_ref: firstValue(item.production_ref, raw.production_ref, raw.production_reference, raw.production_code, null),
        name: firstValue(item.name, raw.name, raw.display_name, null),
        workorder: firstValue(item.workorder, raw.workorder, raw.workorder_name, raw.operation, null),
        product: firstValue(item.product, raw.product, raw.product_name, raw.product_display_name, null),
    };
}

export function getQueueSelectionKeys(item) {
    const context = buildQueueContext(item);
    if (!context) {
        return [];
    }

    return [
        context.id,
        context.queue_id,
        context.reference,
        context.workorder_ref,
        context.production_ref,
        context.workorder_id,
        context.production_id,
    ].filter((value) => value !== null && value !== undefined && value !== "");
}

export function matchQueueSelection(queue, selection) {
    if (!selection || !queue?.length) {
        return null;
    }

    const selectionContext = buildQueueContext(selection);
    const selectionValues = new Set(
        [
            selectionContext?.id,
            selectionContext?.queue_id,
            selectionContext?.reference,
            selectionContext?.workorder_ref,
            selectionContext?.production_ref,
            selectionContext?.workorder_id,
            selectionContext?.production_id,
        ]
            .filter((value) => value !== null && value !== undefined && value !== "")
            .map(String)
    );

    if (!selectionValues.size) {
        return null;
    }

    return queue.find((item) => getQueueSelectionKeys(item).some((candidate) => selectionValues.has(String(candidate)))) || null;
}

function normalizeQueueItem(item, index = 0) {
    if (!isPlainObject(item)) {
        const title = String(item || "Queue item");
        return {
            id: `QUEUE-${index + 1}`,
            queue_id: `QUEUE-${index + 1}`,
            workorder_id: null,
            production_id: null,
            name: title,
            product: "-",
            workorder: "-",
            quantity: 0,
            done: 0,
            priority: "Normal",
            status: "waiting",
            progress: "0 / 0",
            reference: null,
            stage: null,
            message: null,
            source: "backend",
        };
    }
    const quantity = toInteger(
        firstValue(
            item.quantity,
            item.qty,
            item.total_quantity,
            item.total,
            item.planned_quantity,
            item.target_quantity
        )
    );
    const done = toInteger(
        firstValue(item.done, item.completed, item.quantity_done, item.progress_done, item.actual_quantity)
    );
    const status = normalizeStatus(
        firstValue(
            item.status,
            item.state,
            quantity && done >= quantity ? "done" : null,
            "waiting"
        )
    );

    return {
        id: firstValue(item.id, item.queue_id, item.workorder_id, item.reference, `QUEUE-${index + 1}`),
        queue_id: firstValue(item.queue_id, item.id, item.workorder_id, item.reference, `QUEUE-${index + 1}`),
        workorder_id: firstValue(item.workorder_id, item.workorderId, item.workorder_id?.id, null),
        production_id: firstValue(item.production_id, item.productionId, item.production_id?.id, null),
        name: firstValue(item.name, item.display_name, item.title, item.workorder, "Queue item"),
        product: firstValue(item.product, item.product_name, item.product_display_name, item.item_name, "-"),
        workorder: firstValue(item.workorder, item.workorder_name, item.operation, item.stage, "-"),
        workorder_ref: firstValue(item.workorder_ref, item.workorder_reference, item.workorder_code, item.reference, null),
        production_ref: firstValue(item.production_ref, item.production_reference, item.production_code, null),
        quantity,
        done,
        priority: firstValue(item.priority, item.priority_label, item.priority_name, "Normal"),
        status,
        progress: item.progress || `${done} / ${quantity}`,
        reference: firstValue(item.reference, item.order_ref, item.workorder_ref, null),
        stage: firstValue(item.stage, item.operation, null),
        message: firstValue(item.message, item.note, null),
        source: firstValue(item.source, item.origin, "backend"),
        raw: item,
    };
}

function normalizeDeviceItem(item, index = 0) {
    if (!isPlainObject(item)) {
        const title = String(item || "Device");
        return {
            code: `DEVICE-${index + 1}`,
            name: title,
            kind: "Device",
            state: "offline",
            signal: "-",
            value: "-",
            lastSeen: "-",
            channel: null,
            location: null,
            raw: item,
        };
    }

    return {
        code: firstValue(item.code, item.device_code, item.id, `DEVICE-${index + 1}`),
        name: firstValue(item.name, item.display_name, item.title, item.label, "Device"),
        kind: firstValue(item.kind, item.device_type, item.type, item.category, "Device"),
        state: normalizeStatus(firstValue(item.state, item.status, item.connection_state, "offline")),
        signal: firstValue(item.signal, item.topic, item.address, item.endpoint, "-"),
        value: firstValue(item.value, item.reading, item.state_value, item.payload, "-"),
        lastSeen: firstValue(item.lastSeen, item.last_seen, item.updated_at, item.synced_at, "-"),
        channel: firstValue(item.channel, item.port, item.connection, null),
        location: firstValue(item.location, item.room, item.area, null),
        entry_code: firstValue(item.entry_code, item.entryCode, item.gateway_entry_code, null),
        raw: item,
    };
}

function normalizeExceptionItem(item, index = 0) {
    if (!isPlainObject(item)) {
        const title = String(item || "Exception");
        const severityKey = exceptionSeverityKey("medium");
        const stateKey = exceptionStateKey("new");
        return {
            id: `EXC-${index + 1}`,
            title,
            label: title,
            severity: severityKey,
            severityKey,
            severityLabel: exceptionSeverityLabel(severityKey),
            severityTone: exceptionSeverityTone(severityKey),
            severityMeta: buildStateMeta(severityKey, exceptionSeverityKey, exceptionSeverityLabel, exceptionSeverityTone, "medium"),
            state: stateKey,
            stateKey,
            stateLabel: exceptionStateLabel(stateKey),
            stateTone: exceptionStateTone(stateKey),
            tone: exceptionStateTone(stateKey),
            source: "Backend",
            details: null,
            reference: null,
            createdAt: null,
            raw: item,
        };
    }

    const severityKey = exceptionSeverityKey(firstValue(item.severity, item.level, "medium"));
    const stateKey = exceptionStateKey(firstValue(item.state, item.status, "new"));

    return {
        id: firstValue(item.id, item.exception_id, item.code, `EXC-${index + 1}`),
        title: firstValue(item.title, item.message, item.name, item.text, "Exception"),
        label: firstValue(item.label, item.title, item.message, item.name, item.text, "Exception"),
        severity: severityKey,
        severityKey,
        severityLabel: exceptionSeverityLabel(severityKey),
        severityTone: exceptionSeverityTone(severityKey),
        severityMeta: buildStateMeta(severityKey, exceptionSeverityKey, exceptionSeverityLabel, exceptionSeverityTone, "medium"),
        state: stateKey,
        stateKey,
        stateLabel: exceptionStateLabel(stateKey),
        stateTone: exceptionStateTone(stateKey),
        tone: exceptionStateTone(stateKey),
        source: firstValue(item.source, item.origin, item.actor, "Backend"),
        details: firstValue(item.details, item.description, item.note, null),
        resolutionNote: firstValue(item.resolution_note, item.resolutionNote, null),
        reference: firstValue(item.reference, item.command_key, item.gateway_command_code, item.execution_id, null),
        gatewayCommandCode: firstValue(item.gateway_command_code, item.gatewayCommandCode, null),
        createdAt: firstValue(item.createdAt, item.created_at, item.raised_at, item.time, item.timestamp, null),
        resolvedAt: firstValue(item.resolved_at, item.resolvedAt, null),
        raw: item,
    };
}

function normalizeCommandItem(item, index = 0) {
    if (!isPlainObject(item)) {
        const title = String(item || "Command");
        const statusKey = commandStateKey("queued");
        return {
            id: `CMD-${index + 1}`,
            name: title,
            label: title,
            type: "gateway_write",
            status: statusKey,
            statusKey,
            statusLabel: commandStateLabel(statusKey),
            statusTone: commandStateTone(statusKey),
            tone: commandStateTone(statusKey),
            target: null,
            note: null,
            createdAt: null,
            printExecution: null,
            raw: item,
        };
    }

    const statusKey = commandStateKey(firstValue(item.status, item.state, "queued"));
    const printExecution =
        (isPlainObject(item.print_execution) && item.print_execution) ||
        (isPlainObject(item.printExecution) && item.printExecution) ||
        (isPlainObject(item.summary?.print_execution) && item.summary.print_execution) ||
        null;
    const printPlan =
        (isPlainObject(item.print_plan) && item.print_plan) ||
        (isPlainObject(item.printPlan) && item.printPlan) ||
        (isPlainObject(item.summary?.print_plan) && item.summary.print_plan) ||
        {};
    const barcodeValidation =
        (isPlainObject(item.barcode_validation) && item.barcode_validation) ||
        (isPlainObject(item.barcodeValidation) && item.barcodeValidation) ||
        (isPlainObject(item.summary?.barcode_validation) && item.summary.barcode_validation) ||
        {};
    const normalizedPrintExecution = normalizePrintExecution(printExecution);

    return {
        id: firstValue(item.command_id, item.id, item.code, `CMD-${index + 1}`),
        code: firstValue(item.code, item.command_key, item.id, `CMD-${index + 1}`),
        name: firstValue(item.name, item.title, item.label, item.command_type, "Command"),
        label: firstValue(item.label, item.title, item.name, item.command_type, "Command"),
        type: firstValue(item.type, item.command_type, item.action_type, "gateway_write"),
        status: statusKey,
        statusKey,
        statusLabel: commandStateLabel(statusKey),
        statusTone: commandStateTone(statusKey),
        tone: commandStateTone(statusKey),
        state: statusKey,
        target: firstValue(item.target, item.device_code, item.signal_code, item.signal, item.reference, null),
        deviceCode: firstValue(item.deviceCode, item.device_code, item.target, null),
        entryCode: firstValue(item.entryCode, item.entry_code, null),
        signalCode: firstValue(item.signalCode, item.signal_code, null),
        idempotencyKey: firstValue(item.idempotencyKey, item.idempotency_key, null),
        attemptCount: toInteger(firstValue(item.attemptCount, item.attempt_count, 0)),
        note: firstValue(item.note, item.message, item.details, null),
        createdAt: firstValue(item.createdAt, item.last_attempt_at, item.processed_at, item.created_at, item.timestamp, null),
        printExecution: normalizedPrintExecution,
        printPlan,
        barcodeValidation,
        printExecutionLabel: buildPrintExecutionBadge(normalizedPrintExecution),
        printExecutionDetails: buildPrintExecutionDetailItems(normalizedPrintExecution),
        raw: item,
    };
}

function normalizeTimelineItem(item, index = 0) {
    if (!isPlainObject(item)) {
        const text = String(item || "Timeline event");
        return {
            id: `TIMELINE-${index + 1}`,
            title: text,
            label: text,
            detail: null,
            kind: "event",
            status: "info",
            statusKey: "info",
            statusLabel: "Info",
            statusTone: "info",
            timestamp: null,
            raw: item,
        };
    }

    const statusKey = normalizeStatus(firstValue(item.status, item.level, item.severity, "info"))
        .trim()
        .replace(/\s+/g, "_")
        .toLowerCase();
    const printExecution = normalizePrintExecution(
        (isPlainObject(item.print_execution) && item.print_execution) ||
            (isPlainObject(item.printExecution) && item.printExecution) ||
            (isPlainObject(item.summary?.print_execution) && item.summary.print_execution) ||
            null
    );
    const printPlan =
        (isPlainObject(item.print_plan) && item.print_plan) ||
        (isPlainObject(item.printPlan) && item.printPlan) ||
        (isPlainObject(item.summary?.print_plan) && item.summary.print_plan) ||
        {};
    const barcodeValidation =
        (isPlainObject(item.barcode_validation) && item.barcode_validation) ||
        (isPlainObject(item.barcodeValidation) && item.barcodeValidation) ||
        (isPlainObject(item.summary?.barcode_validation) && item.summary.barcode_validation) ||
        {};

    return {
        id: firstValue(item.id, item.key, `TIMELINE-${index + 1}`),
        title: firstValue(item.title, item.name, item.label, item.message, item.event, "Timeline event"),
        label: firstValue(item.label, item.title, item.name, item.message, item.event, "Timeline event"),
        detail: firstValue(item.detail, item.description, item.note, null),
        kind: firstValue(item.kind, item.type, "event"),
        status: normalizeStatus(firstValue(item.status, item.level, item.severity, "info")),
        statusKey,
        statusLabel: labelizeKey(statusKey, "Info"),
        statusTone: toneForKey(
            statusKey,
            {
                info: "info",
                success: "success",
                warning: "warning",
                danger: "danger",
                secondary: "secondary",
            },
            "info"
        ),
        timestamp: firstValue(item.timestamp, item.time, item.created_at, item.date, null),
        printExecution,
        printPlan,
        barcodeValidation,
        printExecutionLabel: buildPrintExecutionBadge(printExecution),
        printExecutionDetails: buildPrintExecutionDetailItems(printExecution),
        raw: item,
    };
}

export function buildCommandQueueStatus(commands = [], source = {}) {
    const counts = commands.reduce(
        (acc, command) => {
            const status = commandStateKey(command?.statusKey || command?.status || command?.state || "queued");
            acc.total += 1;
            acc[status] = (acc[status] || 0) + 1;
            return acc;
        },
        {
            total: 0,
            queued: 0,
            pending: 0,
            waiting: 0,
            draft: 0,
            sent: 0,
            received: 0,
            accepted: 0,
            acknowledged: 0,
            running: 0,
            in_progress: 0,
            processing: 0,
            done: 0,
            completed: 0,
            success: 0,
            failed: 0,
            error: 0,
            rejected: 0,
            cancelled: 0,
            canceled: 0,
        }
    );

    const queued = counts.queued + counts.pending + counts.waiting + counts.draft;
    const running = counts.running + counts.in_progress + counts.processing + counts.sent + counts.received + counts.accepted + counts.acknowledged;
    const done = counts.done + counts.completed + counts.success;
    const failed = counts.failed + counts.error + counts.rejected;
    const total = counts.total;
    const state = commandStateKey(firstValue(source.stateKey, source.state, failed ? "attention" : running ? "active" : queued ? "queued" : "idle"));
    const latestCommand = commands[0] || null;
    const latestPrintExecution = latestCommand?.printExecution || null;
    const latestPrintExecutionBadge = buildPrintExecutionBadge(latestPrintExecution);
    const latestPrintExecutionDetails = buildPrintExecutionDetailItems(latestPrintExecution);
    const latestLabel = firstValue(
        source.latestLabel,
        source.latest_label,
        latestCommand?.label,
        latestCommand?.name,
        null
    );
    const latestDetail = firstValue(
        source.latestDetail,
        source.latest_detail,
        latestCommand?.note,
        latestCommand?.detail,
        latestCommand?.message,
        null
    );
    const headline = firstValue(source.label, total ? "Command queue active" : "Command queue idle");
    const detail = firstValue(
        source.detail,
        total
            ? `${queued} queued, ${running} running, ${done} done${failed ? `, ${failed} failed` : ""}`
            : "No commands returned yet"
    );

    return {
        label: headline,
        detail,
        state,
        stateLabel: commandStateLabel(state),
        stateTone: commandStateTone(state),
        total,
        queued,
        running,
        done,
        failed,
        attentionCount: failed + running,
        latestLabel,
        latestDetail,
        latestTone: commandStateTone(state),
        latestPrintExecution,
        latestPrintExecutionBadge,
        latestPrintExecutionDetails,
        latestPrintPlan: latestCommand?.printPlan || {},
        latestBarcodeValidation: latestCommand?.barcodeValidation || {},
        lastUpdated: firstValue(source.lastUpdated, source.last_updated, null),
    };
}

export function buildResponseSummary(envelope = {}, commandStatus = null, exceptions = [], gatewayRuntimeSummary = null) {
    const messageText = firstValue(
        envelope?.message?.text,
        envelope?.message?.body,
        envelope?.message,
        envelope?.data?.message?.text,
        envelope?.data?.message?.body,
        envelope?.data?.message,
        null
    );
    const nextPage = firstValue(envelope?.next_state?.page, envelope?.data?.next_state?.page, null);
    const criticalExceptions = exceptions.filter((item) => item?.severityKey === "critical");
    const openExceptions = exceptions.filter((item) => ["new", "open", "blocked", "ack"].includes(item?.stateKey));
    const commandFailed = Number(commandStatus?.failed || 0) > 0;
    const commandRunning = Number(commandStatus?.running || 0) > 0;
    const latestPrintExecution = commandStatus?.latestPrintExecution || null;
    const latestPrintExecutionBadge = commandStatus?.latestPrintExecutionBadge || null;
    const latestPrintPlan = commandStatus?.latestPrintPlan || {};
    const latestBarcodeValidation = commandStatus?.latestBarcodeValidation || {};
    const barcodeStatus = firstValue(latestBarcodeValidation?.status, latestBarcodeValidation?.result, null);
    const openDriverIssues = toInteger(firstValue(gatewayRuntimeSummary?.issueCounts?.open, 0));
    const edgeReplayPending = toInteger(firstValue(gatewayRuntimeSummary?.edgeReplay?.pending, 0));
    const edgeReplayDue = toInteger(firstValue(gatewayRuntimeSummary?.edgeReplay?.due, 0));
    const edgeReplayScheduled = toInteger(firstValue(gatewayRuntimeSummary?.edgeReplay?.scheduled, 0));
    const edgeReplayCoalesced = toInteger(firstValue(gatewayRuntimeSummary?.edgeReplay?.coalescedCount, 0));
    const edgeReplayOutcome = firstValue(gatewayRuntimeSummary?.edgeReplay?.lastOutcome, null);
    const edgeDeadLetterCount = toInteger(firstValue(gatewayRuntimeSummary?.edgeDeadLetter?.count, 0));
    const edgeActionProcessing = toInteger(firstValue(gatewayRuntimeSummary?.edgeActionCounts?.processing, 0));
    const protocolRuntimeSharedSummary = buildProtocolRuntimeSharedSummary(gatewayRuntimeSummary || {});
    const protocolRuntimeSummary = protocolRuntimeSharedSummary.summary;
    const protocolRuntimeCount = protocolRuntimeSharedSummary.count;
    const protocolRuntimeEntryCount = protocolRuntimeSharedSummary.entryCount;
    const protocolRuntimeStateSummary = {
        stateKey: protocolRuntimeSharedSummary.stateKey,
        stateTone: protocolRuntimeSharedSummary.stateTone,
        detail: protocolRuntimeSharedSummary.detail,
    };
    const protocolRuntimeHeadline = protocolRuntimeSharedSummary.headline;
    const ok = envelope?.ok !== false && envelope?.error !== true && !commandFailed;
    let headline = ok ? "Backend response received" : "Backend response returned an error";
    let stateKey = ok ? "success" : "warning";
    if (commandFailed || criticalExceptions.length) {
        headline = criticalExceptions.length ? "Attention required" : "Command failure detected";
        stateKey = "danger";
    } else if (openDriverIssues > 0) {
        headline = "Driver issues open";
        stateKey = "danger";
    } else if (edgeDeadLetterCount > 0) {
        headline = "Edge dead letters present";
        stateKey = "danger";
    } else if (edgeReplayPending > 0 && edgeReplayOutcome === "waiting_backoff" && edgeReplayDue === 0 && edgeReplayScheduled > 0) {
        headline = "Edge replay cooling down";
        stateKey = "info";
    } else if (edgeReplayPending > 0) {
        headline = "Edge replay pending";
        stateKey = "warning";
    } else if (edgeActionProcessing > 0) {
        headline = "Edge actions processing";
        stateKey = "info";
    } else if (openExceptions.length || commandRunning) {
        headline = "Operator follow-up pending";
        stateKey = "warning";
    } else if (protocolRuntimeHeadline) {
        headline = protocolRuntimeHeadline;
        stateKey = protocolRuntimeStateSummary.stateKey;
    } else if (latestPrintExecutionBadge) {
        headline = "Print receipt received";
    }
    const fragments = [];

    if (messageText) {
        fragments.push(messageText);
    }
    if (nextPage) {
        fragments.push(`next: ${nextPage}`);
    }
    if (commandStatus?.detail) {
        fragments.push(commandStatus.detail);
    }
    if (latestPrintExecutionBadge) {
        fragments.push(`print: ${latestPrintExecutionBadge}`);
    }
    if (latestPrintExecution?.serviceSummary) {
        fragments.push(latestPrintExecution.serviceSummary);
    }
    if (latestPrintExecution?.errorMessage) {
        fragments.push(`print error: ${latestPrintExecution.errorMessage}`);
    }
    if (barcodeStatus) {
        fragments.push(`barcode: ${barcodeStatus}`);
    }
    if (latestPrintPlan?.label_template) {
        fragments.push(`label: ${latestPrintPlan.label_template}`);
    }
    if (exceptions?.length) {
        fragments.push(`${exceptions.length} exception${exceptions.length === 1 ? "" : "s"}`);
    }
    if (gatewayRuntimeSummary?.summary) {
        fragments.push(`driver: ${gatewayRuntimeSummary.summary}`);
    }
    if (protocolRuntimeSharedSummary.detail) {
        fragments.push(`protocol: ${protocolRuntimeSharedSummary.detail}`);
    } else if (protocolRuntimeCount || protocolRuntimeEntryCount) {
        fragments.push(`protocol: ${protocolRuntimeCount || 0} runtime${protocolRuntimeCount === 1 ? "" : "s"}`);
    }

    const feedbackLabel = criticalExceptions.length
        ? criticalExceptions[0]?.title || "Critical exception"
        : openDriverIssues > 0
          ? "Driver issues open"
          : edgeDeadLetterCount > 0
            ? "Edge dead letters present"
            : edgeReplayPending > 0 && edgeReplayOutcome === "waiting_backoff" && edgeReplayDue === 0 && edgeReplayScheduled > 0
              ? "Edge replay cooling down"
            : edgeReplayPending > 0
              ? "Edge replay pending"
              : edgeActionProcessing > 0
                ? "Edge actions processing"
          : commandFailed
          ? commandStatus?.latestLabel || "Command failed"
          : openExceptions.length
            ? openExceptions[0]?.title || "Exception pending"
            : commandRunning
              ? commandStatus?.latestLabel || "Command running"
              : protocolRuntimeHeadline
                ? protocolRuntimeSharedSummary.label || protocolRuntimeHeadline
                : latestPrintExecutionBadge
                  ? "Print receipt received"
                  : messageText || "Backend response received";

    const feedbackDetail = criticalExceptions.length
        ? criticalExceptions[0]?.details || criticalExceptions[0]?.stateLabel || "Critical issue requires attention."
        : openDriverIssues > 0
          ? gatewayRuntimeSummary?.summary || gatewayRuntimeSummary?.detail || "Runtime driver issues still need follow-up."
          : edgeDeadLetterCount > 0
            ? gatewayRuntimeSummary?.edgeDeadLetter?.summary ||
              gatewayRuntimeSummary?.detail ||
              gatewayRuntimeSummary?.summary ||
              "Some outbound requests exhausted retry budget."
            : edgeReplayPending > 0 && edgeReplayOutcome === "waiting_backoff" && edgeReplayDue === 0 && edgeReplayScheduled > 0
              ? gatewayRuntimeSummary?.edgeReplay?.lastSummary ||
                gatewayRuntimeSummary?.edgeReplay?.summary ||
                gatewayRuntimeSummary?.detail ||
                gatewayRuntimeSummary?.summary ||
                `Replay cooldown active for ${edgeReplayScheduled} item(s); ${edgeReplayCoalesced} duplicate request(s) already coalesced.`
            : edgeReplayPending > 0
              ? gatewayRuntimeSummary?.edgeReplay?.lastSummary ||
                gatewayRuntimeSummary?.edgeReplay?.summary ||
                gatewayRuntimeSummary?.detail ||
                gatewayRuntimeSummary?.summary ||
                "Some offline requests are still waiting to replay."
            : edgeActionProcessing > 0
                ? gatewayRuntimeSummary?.edgeActionSummary ||
                  gatewayRuntimeSummary?.detail ||
                  gatewayRuntimeSummary?.summary ||
                  "Some edge actions are still being processed."
          : commandFailed
          ? commandStatus?.latestDetail || commandStatus?.detail || "The latest gateway command ended in a failed state."
          : openExceptions.length
            ? openExceptions[0]?.details || openExceptions[0]?.stateLabel || "An exception is still waiting for follow-up."
            : commandRunning
              ? commandStatus?.latestDetail || commandStatus?.detail || "A gateway command is still moving through the queue."
              : protocolRuntimeHeadline
                ? protocolRuntimeSharedSummary.detail ||
                  `${protocolRuntimeCount || protocolRuntimeEntryCount || 0} protocol runtime${protocolRuntimeCount + protocolRuntimeEntryCount === 1 ? "" : "s"}`
                : latestPrintExecutionBadge
                  ? [
                        latestPrintExecutionBadge,
                        latestPrintExecution?.serviceSummary || null,
                        latestPrintExecution?.errorMessage ? `print error ${latestPrintExecution.errorMessage}` : null,
                        barcodeStatus ? `barcode ${barcodeStatus}` : null,
                    ]
                        .filter(Boolean)
                        .join(" | ")
                  : messageText || "Backend payload is available.";

    return {
        headline,
        label: headline,
        detail: fragments.length ? fragments.join(" | ") : "Awaiting backend payload",
        state: stateKey,
        stateKey,
        stateLabel: labelizeKey(stateKey, "Info"),
        stateTone: stateKey,
        tone: stateKey,
        ok,
        message: messageText,
        nextPage,
        feedbackLabel,
        feedbackDetail,
        printExecution: latestPrintExecution,
        latestPrintExecution,
        latestPrintExecutionBadge,
        latestPrintExecutionDetails: commandStatus?.latestPrintExecutionDetails || [],
        latestPrintPlan,
        latestBarcodeValidation,
        latestCommandLabel: commandStatus?.latestLabel || null,
        latestCommandDetail: commandStatus?.latestDetail || null,
        protocolRuntimeHeadline,
        protocolRuntimeLabel: protocolRuntimeSharedSummary.label,
        protocolRuntimeDetail: protocolRuntimeSharedSummary.detail,
        protocolRuntimeTone: protocolRuntimeSharedSummary.stateTone,
        protocolRuntimeAttention: protocolRuntimeSharedSummary.attentionCount,
        protocolRuntimeStateSummary: protocolRuntimeStateSummary.detail,
        protocolRuntimeStateKey: protocolRuntimeStateSummary.stateKey,
        openExceptionCount: openExceptions.length,
        criticalExceptionCount: criticalExceptions.length,
        gatewayRuntimeSummary,
    };
}

function buildTimelineFallback({ responseSummary, commands = [], exceptions = [], activity = [], gatewayRuntimeSummary = null } = {}) {
    const entries = [];
    const protocolRuntimeSharedSummary = buildProtocolRuntimeSharedSummary(gatewayRuntimeSummary || {});

    if (responseSummary?.headline || responseSummary?.detail) {
        entries.push({
            id: "timeline-response",
            title: responseSummary.headline || "Backend response",
            label: responseSummary.label || responseSummary.headline || "Backend response",
            detail: responseSummary.detail || null,
            kind: "response",
            status: responseSummary.state || "info",
            statusKey: responseSummary.stateKey || responseSummary.state || "info",
            statusLabel: responseSummary.stateLabel || responseSummary.state || "Info",
            statusTone: responseSummary.stateTone || responseSummary.state || "info",
            timestamp: null,
        });
    }

    commands.slice(0, 5).forEach((command, index) => {
        entries.push({
            id: `timeline-command-${index}`,
            title: command.name || "Command",
            label: command.label || command.name || "Command",
            detail: command.printExecutionLabel || `${command.type || "command"} - ${command.statusLabel || command.status || "Queued"}`,
            kind: "command",
            status: command.statusTone || command.status || "queued",
            statusKey: command.statusKey || command.status || "queued",
            statusLabel: command.statusLabel || command.status || "Queued",
            statusTone: command.statusTone || command.status || "queued",
            timestamp: command.createdAt || null,
            printExecution: command.printExecution || null,
            printPlan: command.printPlan || {},
            barcodeValidation: command.barcodeValidation || {},
            printExecutionLabel: command.printExecutionLabel || buildPrintExecutionBadge(command.printExecution || null),
            printExecutionDetails: command.printExecutionDetails || buildPrintExecutionDetailItems(command.printExecution || null),
        });
    });

    exceptions.slice(0, 3).forEach((exception, index) => {
        entries.push({
            id: `timeline-exception-${index}`,
            title: exception.title || "Exception",
            label: exception.label || exception.title || "Exception",
            detail: `${exception.severityLabel || exception.severity || "Medium"} - ${exception.stateLabel || exception.state || "New"}`,
            kind: "exception",
            status: exception.severityTone || exception.severity || "medium",
            statusKey: exception.stateKey || exception.state || "new",
            statusLabel: exception.stateLabel || exception.state || "New",
            statusTone: exception.stateTone || exception.state || "warning",
            timestamp: exception.createdAt || null,
        });
    });

    if (gatewayRuntimeSummary?.summary || gatewayRuntimeSummary?.detail) {
        entries.push({
            id: "timeline-runtime-driver",
            title: gatewayRuntimeSummary.label || "Driver diagnostics",
            label: gatewayRuntimeSummary.label || "Driver diagnostics",
            detail: gatewayRuntimeSummary.detail || gatewayRuntimeSummary.summary || null,
            kind: "runtime",
            status: gatewayRuntimeSummary.stateTone || gatewayRuntimeSummary.state || "info",
            statusKey: gatewayRuntimeSummary.stateKey || gatewayRuntimeSummary.state || "info",
            statusLabel: gatewayRuntimeSummary.stateLabel || gatewayRuntimeSummary.state || "Info",
            statusTone: gatewayRuntimeSummary.stateTone || gatewayRuntimeSummary.state || "info",
            timestamp: null,
        });
    }
    if (protocolRuntimeSharedSummary.hasSignal) {
        entries.push({
            id: "timeline-runtime-protocol",
            title: protocolRuntimeSharedSummary.label || protocolRuntimeSharedSummary.headline || "Protocol runtime",
            label: protocolRuntimeSharedSummary.label || protocolRuntimeSharedSummary.headline || "Protocol runtime",
            detail:
                protocolRuntimeSharedSummary.detail ||
                `${protocolRuntimeSharedSummary.count || 0} runtime${protocolRuntimeSharedSummary.count === 1 ? "" : "s"}`,
            kind: "runtime",
            status: protocolRuntimeSharedSummary.stateTone || protocolRuntimeSharedSummary.stateKey || "info",
            statusKey: protocolRuntimeSharedSummary.stateKey || "info",
            statusLabel: protocolRuntimeSharedSummary.stateLabel || "Info",
            statusTone: protocolRuntimeSharedSummary.stateTone || protocolRuntimeSharedSummary.stateKey || "info",
            timestamp: null,
        });
    }

    activity.slice(0, 3).forEach((entry, index) => {
        const normalizedActivity = normalizeActivityEntry(entry, index);
        entries.push({
            id: normalizedActivity.id || `timeline-activity-${index}`,
            title: normalizedActivity.title,
            label: normalizedActivity.label,
            detail: normalizedActivity.detail,
            kind: normalizedActivity.kind || "activity",
            status: normalizedActivity.status || "info",
            statusKey: normalizedActivity.statusKey || normalizedActivity.status || "info",
            statusLabel: normalizedActivity.statusLabel || normalizedActivity.status || "Info",
            statusTone: normalizedActivity.statusTone || normalizedActivity.status || "info",
            timestamp: normalizedActivity.timestamp || null,
        });
    });

    return entries;
}

export function buildSeedTimelineEntries(workstationCode = "WS-000") {
    const protocolRuntimeSharedSummary = buildProtocolRuntimeSharedSummary({
        protocolRuntimeState: "secondary",
        protocolRuntimeSummary: "Protocol runtime shared summary will appear after backend payloads load.",
        protocolRuntimeCount: 0,
        protocolRuntimeEntryCount: 0,
        protocolRuntimeStateCounts: {},
    });
    return [
        {
            id: `${workstationCode}-BOOT`,
            title: "Frontend shell ready",
            detail: `Workstation ${workstationCode} is using seed state`,
            kind: "boot",
            status: "info",
            timestamp: null,
        },
        {
            id: `${workstationCode}-QUEUE`,
            title: "Seed queue available",
            detail: "Queue, devices, and exceptions will be replaced when backend data arrives",
            kind: "seed",
            status: "info",
            timestamp: null,
        },
        {
            id: `${workstationCode}-PROTOCOL-RUNTIME`,
            title: protocolRuntimeSharedSummary.label || "Protocol runtime waiting",
            detail: protocolRuntimeSharedSummary.detail,
            kind: "runtime",
            status: protocolRuntimeSharedSummary.stateTone || "secondary",
            statusKey: protocolRuntimeSharedSummary.stateKey || "secondary",
            statusLabel: protocolRuntimeSharedSummary.stateLabel || "Secondary",
            statusTone: protocolRuntimeSharedSummary.stateTone || "secondary",
            timestamp: null,
        },
    ];
}

export function normalizeShopfloorEnvelope(envelope = {}, fallback = {}) {
    const envelopeRoot = isPlainObject(envelope) ? envelope : {};
    const data = isPlainObject(envelopeRoot.data) ? envelopeRoot.data : {};
    const context = isPlainObject(envelopeRoot.context) ? envelopeRoot.context : {};
    const execution = isPlainObject(envelopeRoot.execution) ? envelopeRoot.execution : {};
    const payload = isPlainObject(envelopeRoot.payload) ? envelopeRoot.payload : {};
    const sources = [envelopeRoot, data, payload, context, execution];

    const queue = findCollection(sources, [
        "queue",
        "queue.items",
        "work_queue",
        "work_queue.items",
        "workorders",
        "workorders.items",
        "tasks",
        "tasks.items",
        "jobs",
        "jobs.items",
        "items",
    ]).map(normalizeQueueItem);

    const devices = findCollection(sources, [
        "devices",
        "devices.items",
        "equipment",
        "equipment.items",
        "gateway.devices",
        "gateway.devices.items",
        "signals",
        "signals.items",
    ]).map(normalizeDeviceItem);

    const exceptions = findCollection(sources, [
        "exceptions",
        "exceptions.items",
        "errors",
        "errors.items",
        "recent_exceptions",
        "recent_exceptions.items",
        "alerts",
        "alerts.items",
    ]).map(normalizeExceptionItem);

    const commands = findCollection(sources, [
        "commands",
        "commands.items",
        "recent_commands",
        "recent_commands.items",
        "command_queue",
        "command_queue.items",
    ]).map(normalizeCommandItem);

    const timeline = findCollection(sources, [
        "timeline",
        "timeline.items",
        "events",
        "events.items",
        "gateway_runtime.recent_activity",
        "gateway_runtime.recent_activity.items",
        "gateway.runtime.recent_activity",
        "gateway.runtime.recent_activity.items",
        "log_entries",
        "log_entries.items",
        "logs",
        "logs.items",
    ]).map(normalizeTimelineItem);
    const activity = findCollection(sources, [
        "activity",
        "activity.items",
        "recent_activity",
        "recent_activity.items",
        "recent_runtime_activity",
        "recent_runtime_activity.items",
        "recent_runtime_events",
        "recent_runtime_events.items",
        "recent_runtime_issues",
        "recent_runtime_issues.items",
        "gateway_runtime.recent_activity",
        "gateway_runtime.recent_activity.items",
        "gateway_runtime.recent_events",
        "gateway_runtime.recent_events.items",
        "gateway_runtime.recent_issues",
        "gateway_runtime.recent_issues.items",
        "gateway.runtime.recent_activity",
        "gateway.runtime.recent_activity.items",
        "gateway.runtime.recent_events",
        "gateway.runtime.recent_events.items",
        "gateway.runtime.recent_issues",
        "gateway.runtime.recent_issues.items",
    ]).map(normalizeActivityEntry);
    const gatewayRuntimeSummary = normalizeGatewayRuntimeSummary(
        findObject(sources, [
            "gateway_runtime",
            "gateway_runtime.summary",
            "gateway.runtime",
            "runtime_summary",
            "runtime.summary",
        ])
    );

    const responseSummary = buildResponseSummary(envelopeRoot, buildCommandQueueStatus(commands), exceptions, gatewayRuntimeSummary);
    const fallbackActivity = activity.length ? activity : toArray(fallback.activity);
    const logEntries = timeline.length
        ? timeline
        : buildTimelineFallback({
              responseSummary,
              commands,
              exceptions,
              activity: fallbackActivity,
              gatewayRuntimeSummary,
          });

    return {
        queue,
        devices,
        exceptions,
        commands,
        timeline: logEntries,
        activity: fallbackActivity,
        responseSummary,
        commandQueueStatus: buildCommandQueueStatus(commands, envelopeRoot?.command_queue_status || data?.command_queue_status || {}),
        metrics: isPlainObject(envelopeRoot.metrics) ? envelopeRoot.metrics : isPlainObject(data.metrics) ? data.metrics : {},
        gatewayRuntimeSummary,
        workstation: context.workstation || data.workstation || envelopeRoot.workstation || null,
        currentUserName:
            firstValue(context.user_name, data.user_name, envelopeRoot.user_name, fallback.currentUserName, null),
        sessionRef: firstValue(context.session_ref, data.session_ref, envelopeRoot.session_ref, fallback.sessionRef, null),
        execution: isPlainObject(execution)
            ? execution
            : isPlainObject(data.execution)
              ? data.execution
              : null,
        nextState: envelopeRoot.next_state || data.next_state || null,
        messageText: responseSummary.message,
        raw: envelopeRoot,
    };
}
