/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ShopfloorResponseCard extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorResponseCard";
    static props = {
        responseSummary: Object,
        gatewayRuntimeSummary: [Object, Boolean],
        metrics: [Object, Boolean],
        exceptions: Array,
        lastResponseText: String,
    };

    get feedbackLabel() {
        return this.props.responseSummary.feedbackLabel || this.props.responseSummary.label || "Backend response";
    }

    get feedbackDetail() {
        return this.props.responseSummary.feedbackDetail || this.props.responseSummary.detail || "Awaiting backend payload";
    }

    _parseRawResponse() {
        const rawText = this.props.lastResponseText;
        if (!rawText || typeof rawText !== "string") {
            return null;
        }
        try {
            return JSON.parse(rawText);
        } catch {
            return null;
        }
    }

    get responsePrintExecution() {
        const summary = this.props.responseSummary || {};
        const raw = summary.raw || summary.payload || summary.result || this._parseRawResponse() || null;
        const execution =
            summary.printExecution ||
            summary.print_execution ||
            summary.latestPrintExecution ||
            summary.latest_print_execution ||
            raw?.print_execution ||
            raw?.printExecution ||
            raw?.data?.print_execution ||
            raw?.data?.printExecution ||
            raw?.result?.print_execution ||
            raw?.result?.printExecution ||
            null;
        if (!execution || typeof execution !== "object") {
            return null;
        }
        return {
            executionState: execution.execution_state || execution.executionState || summary.executionState || summary.execution_state || null,
            serviceMode: execution.service_mode || execution.serviceMode || summary.serviceMode || summary.service_mode || null,
            executionMode: execution.execution_mode || execution.executionMode || summary.executionMode || summary.execution_mode || null,
            serviceJobId: execution.service_job_id || execution.serviceJobId || summary.serviceJobId || summary.service_job_id || null,
            serviceStatusCode:
                execution.service_status_code || execution.serviceStatusCode || summary.serviceStatusCode || summary.service_status_code || null,
            serviceErrorCode: execution.service_error_code || execution.serviceErrorCode || summary.serviceErrorCode || summary.service_error_code || null,
            serviceErrorDetail: execution.service_error_detail || execution.serviceErrorDetail || summary.serviceErrorDetail || summary.service_error_detail || null,
            serviceAcceptedAt: execution.service_accepted_at || execution.serviceAcceptedAt || summary.serviceAcceptedAt || summary.service_accepted_at || null,
            serviceCompletedAt: execution.service_completed_at || execution.serviceCompletedAt || summary.serviceCompletedAt || summary.service_completed_at || null,
            serviceStatusUrl: execution.service_status_url || execution.serviceStatusUrl || summary.serviceStatusUrl || summary.service_status_url || null,
            serviceCheckedAt: execution.service_checked_at || execution.serviceCheckedAt || summary.serviceCheckedAt || summary.service_checked_at || null,
            serviceDocumentUrl: execution.service_document_url || execution.serviceDocumentUrl || summary.serviceDocumentUrl || summary.service_document_url || null,
            servicePreviewUrl: execution.service_preview_url || execution.servicePreviewUrl || summary.servicePreviewUrl || summary.service_preview_url || null,
            servicePrinterCode: execution.service_printer_code || execution.servicePrinterCode || summary.servicePrinterCode || summary.service_printer_code || null,
            driverOrigin: execution.driver_origin || execution.driverOrigin || summary.driverOrigin || summary.driver_origin || null,
            driverReady: execution.driver_ready ?? execution.driverReady ?? summary.driverReady ?? summary.driver_ready ?? null,
            driverLabel: execution.driver_label || execution.driverLabel || summary.driverLabel || summary.driver_label || null,
            driverType: execution.driver_type || execution.driverType || summary.driverType || summary.driver_type || null,
            driverPath: execution.driver_path || execution.driverPath || summary.driverPath || summary.driver_path || null,
            driverCapabilities:
                execution.driver_capabilities || execution.driverCapabilities || summary.driverCapabilities || summary.driver_capabilities || {},
            printerStatus: execution.printer_status || execution.printerStatus || summary.printer_status || summary.printerStatus || null,
            printedCopies: execution.printed_copies || execution.printedCopies || summary.printed_copies || summary.printedCopies || null,
            completed: execution.completed ?? summary.completed ?? null,
            terminal: execution.terminal ?? summary.terminal ?? null,
            serviceSummary: execution.service_summary || execution.serviceSummary || summary.serviceSummary || summary.service_summary || null,
            result: execution.result || null,
        };
    }

    get responsePrintExecutionTone() {
        const execution = this.responsePrintExecution;
        if (!execution) {
            return "info";
        }
        const state = String(execution.executionState || execution.result || "").trim().toLowerCase();
        if (["failed", "error", "rejected"].includes(state)) {
            return "danger";
        }
        if (["submitted", "acknowledged", "accepted", "queued", "pending", "processing", "running"].includes(state)) {
            return "warning";
        }
        if (["done", "completed", "success", "printed"].includes(state)) {
            return "success";
        }
        return "info";
    }

    get responsePrintExecutionLabel() {
        const execution = this.responsePrintExecution;
        if (!execution) {
            return null;
        }
        const parts = [
            execution.executionState ? `state ${execution.executionState}` : null,
            execution.serviceMode ? `mode ${execution.serviceMode}` : null,
            execution.executionMode ? `execution ${execution.executionMode}` : null,
            execution.driverOrigin ? `driver ${execution.driverOrigin}` : null,
            execution.driverReady === true ? "driver ready" : execution.driverReady === false ? "driver not ready" : null,
            execution.serviceJobId ? `job ${execution.serviceJobId}` : null,
            execution.serviceStatusCode !== null && execution.serviceStatusCode !== undefined ? `code ${execution.serviceStatusCode}` : null,
            execution.serviceErrorCode ? `error ${execution.serviceErrorCode}` : null,
            execution.completed === true ? "completed" : execution.completed === false ? "pending" : null,
            execution.terminal === true ? "terminal" : execution.terminal === false ? "non-terminal" : null,
            execution.printerStatus ? `printer ${execution.printerStatus}` : null,
            execution.servicePrinterCode ? `device ${execution.servicePrinterCode}` : null,
            execution.printedCopies !== null && execution.printedCopies !== undefined ? `${execution.printedCopies} copies` : null,
        ].filter(Boolean);
        return parts.length ? parts.join(" | ") : null;
    }

    get responsePrintExecutionDetails() {
        const execution = this.responsePrintExecution;
        if (!execution) {
            return [];
        }
        return [
            execution.executionState ? `state ${execution.executionState}` : null,
            execution.serviceMode ? `mode ${execution.serviceMode}` : null,
            execution.driverOrigin ? `driver ${execution.driverOrigin}` : null,
            execution.driverLabel ? `label ${execution.driverLabel}` : null,
            execution.driverType ? `type ${execution.driverType}` : null,
            execution.driverReady === true ? "driver ready" : execution.driverReady === false ? "driver not ready" : null,
            execution.driverCapabilities?.supportsRefreshStatus === true ||
            execution.driverCapabilities?.supports_refresh_status === true
                ? "refresh-status supported"
                : execution.driverCapabilities?.supportsRefreshStatus === false ||
                    execution.driverCapabilities?.supports_refresh_status === false
                  ? "refresh-status unavailable"
                  : null,
            execution.driverCapabilities?.statusPollingSupported === true ||
            execution.driverCapabilities?.status_polling_supported === true
                ? "polling ready"
                : execution.driverCapabilities?.statusPollingSupported === false ||
                    execution.driverCapabilities?.status_polling_supported === false
                  ? "polling limited"
                  : null,
            execution.serviceJobId ? `job ${execution.serviceJobId}` : null,
            execution.serviceStatusCode !== null && execution.serviceStatusCode !== undefined ? `code ${execution.serviceStatusCode}` : null,
            execution.serviceErrorCode ? `error ${execution.serviceErrorCode}` : null,
            execution.serviceErrorDetail ? execution.serviceErrorDetail : null,
            execution.serviceAcceptedAt ? `accepted ${execution.serviceAcceptedAt}` : null,
            execution.serviceCompletedAt ? `completed ${execution.serviceCompletedAt}` : null,
            execution.serviceCheckedAt ? `checked ${execution.serviceCheckedAt}` : null,
            execution.serviceSummary ? execution.serviceSummary : null,
            execution.printerStatus ? `printer ${execution.printerStatus}` : null,
            execution.servicePrinterCode ? `device ${execution.servicePrinterCode}` : null,
            execution.serviceDocumentUrl ? "document ready" : null,
            execution.servicePreviewUrl ? "preview ready" : null,
            execution.serviceStatusUrl ? `status ${execution.serviceStatusUrl}` : null,
            execution.printedCopies !== null && execution.printedCopies !== undefined ? `${execution.printedCopies} copies` : null,
        ]
            .filter(Boolean)
            .map((label, index) => ({
                key: `${index}-${label}`,
                label,
            }));
    }

    get payloadAvailabilityLabel() {
        return this.props.lastResponseText ? "raw payload available" : "seed only";
    }

    get exceptionCount() {
        return Array.isArray(this.props.exceptions) ? this.props.exceptions.length : 0;
    }

    get gatewayDriverIssueOpen() {
        return this.props.gatewayRuntimeSummary?.issueCounts?.open || 0;
    }

    get gatewayEdgeDeadLetterCount() {
        return this.props.gatewayRuntimeSummary?.edgeDeadLetter?.count || 0;
    }

    get gatewayEdgeReplayPending() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.pending || 0;
    }

    get gatewayEdgeReplayDue() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.due || 0;
    }

    get gatewayEdgeReplayCooling() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.scheduled || 0;
    }

    get gatewayEdgeReplayLastOutcome() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.lastOutcome || null;
    }

    get gatewayEdgeReplayLastSummary() {
        return this.props.gatewayRuntimeSummary?.edgeReplay?.lastSummary || null;
    }

    get gatewayDriverSummary() {
        return (
            this.props.gatewayRuntimeSummary?.edgeDeadLetter?.summary ||
            this.gatewayEdgeReplayLastSummary ||
            this.props.gatewayRuntimeSummary?.edgeReplay?.summary ||
            this.props.gatewayRuntimeSummary?.summary ||
            this.props.gatewayRuntimeSummary?.detail ||
            null
        );
    }

    get gatewayDriverTone() {
        return String(this.props.gatewayRuntimeSummary?.stateTone || this.props.gatewayRuntimeSummary?.state || "secondary").toLowerCase();
    }

    get gatewayProtocolRuntimeCount() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeCount || this.props.gatewayRuntimeSummary?.protocolRuntime?.count || 0;
    }

    get gatewayProtocolRuntimeEntryCount() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeEntryCount || this.props.gatewayRuntimeSummary?.protocolRuntime?.entryCount || 0;
    }

    get gatewayProtocolRuntimeStateCounts() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeStateCounts || this.props.gatewayRuntimeSummary?.protocolRuntime?.stateCounts || {};
    }

    get sharedProtocolRuntimeSummary() {
        const responseSummary = this.props.responseSummary || {};
        const metrics = this.props.metrics || {};
        const pickValue = (...values) => {
            for (const value of values) {
                if (value === null || value === undefined) {
                    continue;
                }
                if (typeof value === "string" && !value.trim()) {
                    continue;
                }
                return value;
            }
            return null;
        };
        const label = pickValue(
            responseSummary.protocolRuntimeLabel,
            responseSummary.protocolRuntimeHeadline,
            responseSummary.protocolRuntimeTitle,
            metrics.protocolRuntimeLabel,
            metrics.protocolRuntimeHeadline,
            metrics.protocolRuntimeTitle,
        );
        const detail = pickValue(
            responseSummary.protocolRuntimeDetail,
            responseSummary.protocolRuntimeStateSummary,
            responseSummary.protocolRuntimeStateDetail,
            metrics.protocolRuntimeDetail,
            metrics.protocolRuntimeStateSummary,
            metrics.protocolRuntimeStateDetail,
        );
        const tone = String(
            pickValue(
                responseSummary.protocolRuntimeTone,
                responseSummary.protocolRuntimeStateTone,
                metrics.protocolRuntimeTone,
                metrics.protocolRuntimeStateTone,
            ) || "",
        )
            .trim()
            .toLowerCase() || null;
        const attention =
            responseSummary.protocolRuntimeAttention !== null && responseSummary.protocolRuntimeAttention !== undefined
                ? Number(responseSummary.protocolRuntimeAttention) || 0
                : metrics.protocolRuntimeAttention !== null && metrics.protocolRuntimeAttention !== undefined
                  ? Number(metrics.protocolRuntimeAttention) || 0
                  : null;
        if (!label && !detail && attention === null && !tone) {
            return null;
        }
        return {
            label,
            detail,
            tone,
            attention,
        };
    }

    get gatewayProtocolRuntimeSharedAttentionCount() {
        const sharedSummary = this.sharedProtocolRuntimeSummary;
        if (sharedSummary && sharedSummary.attention !== null) {
            return sharedSummary.attention;
        }
        return null;
    }

    get gatewayProtocolRuntimeAttentionCount() {
        const sharedAttention = this.gatewayProtocolRuntimeSharedAttentionCount;
        if (sharedAttention !== null) {
            return sharedAttention;
        }
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        const errorCount = Number(stateCounts.error || 0);
        const pendingCount = Number(stateCounts.pending || 0);
        const unavailableCount = Number(stateCounts.unavailable || 0);
        return Math.max(errorCount, pendingCount + unavailableCount);
    }

    get gatewayProtocolRuntimeSummary() {
        return this.props.gatewayRuntimeSummary?.protocolRuntimeSummary || this.props.gatewayRuntimeSummary?.protocolRuntime?.summary || null;
    }

    get gatewayProtocolRuntimeTone() {
        const sharedSummary = this.sharedProtocolRuntimeSummary;
        if (sharedSummary) {
            if (sharedSummary.tone) {
                return sharedSummary.tone;
            }
            if (sharedSummary.label || sharedSummary.detail) {
                return "secondary";
            }
        }
        const stateTone = String(this.props.gatewayRuntimeSummary?.protocolRuntimeStateTone || this.props.gatewayRuntimeSummary?.protocolRuntime?.stateTone || "").toLowerCase();
        if (stateTone) {
            return stateTone;
        }
        const attentionCount = this.gatewayProtocolRuntimeAttentionCount;
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        const errorCount = Number(stateCounts.error || 0);
        const pendingCount = Number(stateCounts.pending || 0);
        const unavailableCount = Number(stateCounts.unavailable || 0);
        if (attentionCount > 0 && errorCount > 0) {
            return "danger";
        }
        if (attentionCount > 0 && (pendingCount > 0 || unavailableCount > 0)) {
            return "warning";
        }
        if (attentionCount > 0) {
            return "warning";
        }
        return "secondary";
    }

    get gatewayProtocolRuntimeLabel() {
        const sharedSummary = this.sharedProtocolRuntimeSummary;
        if (sharedSummary) {
            if (sharedSummary.label) {
                return sharedSummary.label;
            }
            if (sharedSummary.detail) {
                return sharedSummary.detail;
            }
            if (sharedSummary.tone === "danger") {
                return "Protocol runtime error";
            }
            if (sharedSummary.tone === "warning") {
                return "Protocol runtime attention";
            }
            if (sharedSummary.tone === "success") {
                return "Protocol runtime ready";
            }
            if (sharedSummary.attention !== null) {
                if (sharedSummary.attention > 0) {
                    return `Protocol runtime attention ${sharedSummary.attention}`;
                }
                return "Protocol runtime ready";
            }
        }
        const count = this.gatewayProtocolRuntimeAttentionCount || this.gatewayProtocolRuntimeCount || this.gatewayProtocolRuntimeEntryCount;
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        const errorCount = Number(stateCounts.error || 0);
        const pendingCount = Number(stateCounts.pending || 0);
        const unavailableCount = Number(stateCounts.unavailable || 0);
        if (count > 0 && errorCount > 0) {
            return `Protocol runtime errors ${count}`;
        }
        if (count > 0 && (pendingCount > 0 || unavailableCount > 0)) {
            return `Protocol runtime attention ${count}`;
        }
        if (count > 0) {
            return `Protocol runtimes ${count}`;
        }
        return null;
    }

    get gatewayProtocolRuntimeDetail() {
        const stateCounts = this.gatewayProtocolRuntimeStateCounts;
        const sharedSummary = this.sharedProtocolRuntimeSummary;
        if (sharedSummary) {
            const sharedParts = [
                sharedSummary.detail || sharedSummary.label || null,
                sharedSummary.tone ? `tone ${sharedSummary.tone}` : null,
                sharedSummary.attention !== null && sharedSummary.attention !== undefined
                    ? `attention ${sharedSummary.attention}`
                    : null,
            ].filter(Boolean);
            if (sharedParts.length) {
                return sharedParts.join(" | ");
            }
        }
        const attentionCount = this.gatewayProtocolRuntimeAttentionCount || this.gatewayProtocolRuntimeCount || this.gatewayProtocolRuntimeEntryCount;
        const parts = [
            this.gatewayProtocolRuntimeSummary,
            attentionCount || this.gatewayProtocolRuntimeCount || this.gatewayProtocolRuntimeEntryCount
                ? `${this.gatewayProtocolRuntimeCount || 0} runtime(s), ${this.gatewayProtocolRuntimeEntryCount || 0} entry(ies)`
                : null,
            Number(stateCounts.ready || 0) ? `ready ${stateCounts.ready}` : null,
            Number(stateCounts.pending || 0) ? `pending ${stateCounts.pending}` : null,
            Number(stateCounts.unavailable || 0) ? `unavailable ${stateCounts.unavailable}` : null,
            Number(stateCounts.error || 0) ? `error ${stateCounts.error}` : null,
        ].filter(Boolean);
        return parts.length ? parts.join(" | ") : null;
    }

    get attentionLabel() {
        if (this.exceptionCount > 0) {
            return `${this.exceptionCount} active exception${this.exceptionCount > 1 ? "s" : ""}`;
        }
        if (this.gatewayDriverIssueOpen > 0) {
            return `${this.gatewayDriverIssueOpen} open driver issue${this.gatewayDriverIssueOpen > 1 ? "s" : ""}`;
        }
        if (this.gatewayProtocolRuntimeLabel) {
            return this.gatewayProtocolRuntimeLabel;
        }
        if (this.gatewayEdgeDeadLetterCount > 0) {
            return `${this.gatewayEdgeDeadLetterCount} dead letter${this.gatewayEdgeDeadLetterCount > 1 ? "s" : ""}`;
        }
        if (this.gatewayEdgeReplayDue > 0) {
            return `${this.gatewayEdgeReplayDue} replay item${this.gatewayEdgeReplayDue > 1 ? "s" : ""} due`;
        }
        if (this.gatewayEdgeReplayCooling > 0 && this.gatewayEdgeReplayLastOutcome === "waiting_backoff") {
            return `${this.gatewayEdgeReplayCooling} replay item${this.gatewayEdgeReplayCooling > 1 ? "s" : ""} cooling`;
        }
        if (this.gatewayEdgeReplayPending > 0) {
            return `${this.gatewayEdgeReplayPending} replay item${this.gatewayEdgeReplayPending > 1 ? "s" : ""} pending`;
        }
        const processing = this.props.gatewayRuntimeSummary?.edgeActionCounts?.processing || 0;
        if (processing > 0) {
            return `${processing} edge action${processing > 1 ? "s" : ""} processing`;
        }
        return this.props.responseSummary.nextPage || null;
    }
}
