/** @odoo-module **/

import { reactive } from "@odoo/owl";
import { createShopfloorRouter } from "../router/shopfloor_router";
import { createShopfloorDataService } from "../services/shopfloor_data_service";
import { createShopfloorStateService } from "../services/shopfloor_state_service";
import { createShopfloorSelectionService } from "../services/shopfloor_selection_service";
import { createShopfloorRequestService } from "../services/shopfloor_request_service";

export function createShopfloorStore(env, action = {}, services = {}) {
    const workstationCode = action?.params?.workstation_code || "WS-000";
    const router = services.router || createShopfloorRouter(action?.params?.route || "dashboard");
    const dataService = services.data || createShopfloorDataService();
    const stateService = services.state || createShopfloorStateService();
    const selectionService = services.selection || createShopfloorSelectionService();
    const buildSeedSurfaces = (code) => {
        const responseSummary = stateService.buildIdleResponseSummary();
        const commandQueueStatus = stateService.buildIdleCommandQueueStatus();
        const gatewayRuntimeSummary = stateService.buildIdleGatewayRuntimeSummary();
        const activity = [
            {
                id: `${code}-activity-boot`,
                title: "Frontend shell loaded",
                label: "Frontend shell loaded",
                detail: `Workstation ${code} is using seed state until backend payloads arrive.`,
                kind: "boot",
                status: "info",
                statusKey: "info",
                statusLabel: "Info",
                statusTone: "info",
                timestamp: null,
            },
            {
                id: `${code}-activity-response`,
                title: responseSummary.label || responseSummary.headline || "Awaiting backend payload",
                label: responseSummary.label || responseSummary.headline || "Awaiting backend payload",
                detail: responseSummary.detail || null,
                kind: "seed",
                status: responseSummary.stateKey || responseSummary.state || "secondary",
                statusKey: responseSummary.stateKey || responseSummary.state || "secondary",
                statusLabel: responseSummary.stateLabel || "Idle",
                statusTone: responseSummary.stateTone || responseSummary.state || "secondary",
                timestamp: null,
            },
            {
                id: `${code}-activity-protocol-runtime`,
                title: responseSummary.protocolRuntimeLabel || "Protocol runtime waiting",
                label: responseSummary.protocolRuntimeLabel || "Protocol runtime waiting",
                detail:
                    responseSummary.protocolRuntimeDetail ||
                    gatewayRuntimeSummary.protocolRuntimeSummary ||
                    "Protocol runtime shared summary will appear after backend payloads load.",
                kind: "runtime",
                status: responseSummary.protocolRuntimeStateKey || responseSummary.protocolRuntimeState || "secondary",
                statusKey: responseSummary.protocolRuntimeStateKey || responseSummary.protocolRuntimeState || "secondary",
                statusLabel: responseSummary.protocolRuntimeStateLabel || "Idle",
                statusTone: responseSummary.protocolRuntimeTone || "secondary",
                timestamp: null,
            },
        ];
        return {
            activity,
            timeline: stateService.buildSeedTimelineEntries(code),
            logs: stateService.buildLogEntries(
                {
                    responseSummary,
                    commandQueueStatus,
                    gatewayRuntimeSummary,
                    commands: [],
                    exceptions: [],
                },
                activity
            ),
            responseSummary,
            commandQueueStatus,
            gatewayRuntimeSummary,
        };
    };
    const seedSurfaces = buildSeedSurfaces(workstationCode);

    const state = reactive({
        booted: false,
        loading: false,
        bootError: null,
        activeExecutionTab: "summary",
        workstation: {
            name: action?.params?.workstation_name || "Unassigned workstation",
            code: workstationCode,
            profile: action?.params?.profile_name || "Default profile",
            printer: action?.params?.printer_name || "No printer",
            gateway: action?.params?.gateway_ref || "No gateway",
        },
        currentUser: {
            name: action?.params?.user_name || env.services.user?.name || "Operator",
        },
        sessionRef: action?.params?.session_ref || null,
        connectivity: {
            state: "online",
            tone: "success",
            label: "Live",
            detail: "Execution service connected.",
            canRetry: false,
            recovered: false,
            lastTransitionLabel: "Connected",
        },
        metrics: {
            pendingJobs: 0,
            activeExceptions: 0,
            deviceOnline: true,
            driverIssueOpen: 0,
            driverIssueAdapters: 0,
            protocolRuntimeAttention: 0,
            protocolRuntimeState: "idle",
            protocolRuntimeTone: "secondary",
            protocolRuntimeLabel: null,
            protocolRuntimeDetail: null,
            lastSync: "waiting",
        },
        panels: [
            { key: "dashboard", label: "Dashboard" },
            { key: "queue", label: "Queue" },
            { key: "execution", label: "Execution" },
            { key: "devices", label: "Devices" },
            { key: "exceptions", label: "Exceptions" },
        ],
        activity: seedSurfaces.activity,
        queue: stateService.buildSampleQueue(workstationCode),
        devices: stateService.buildSampleDevices(),
        exceptions: stateService.buildSampleExceptions(),
        commands: [],
        timeline: seedSurfaces.timeline,
        logs: seedSurfaces.logs,
        responseSummary: seedSurfaces.responseSummary,
        commandQueueStatus: seedSurfaces.commandQueueStatus,
        gatewayRuntimeSummary: seedSurfaces.gatewayRuntimeSummary,
        execution: {
            id: null,
            name: "No execution loaded",
            state: "draft",
            action_type: "custom",
            app_code: action?.params?.app_code || "shopfloor",
            workstation_code: workstationCode,
            session_ref: action?.params?.session_ref || null,
            command_key: null,
            idempotency_key: null,
            reference: null,
            note: null,
        },
        lastResponse: null,
        selectedQueueId: null,
        selectedQueueContext: null,
        selectedDeviceCode: null,
    });

    state.selectedQueueId = state.queue[0]?.queue_id || state.queue[0]?.id || null;
    state.selectedQueueContext = stateService.buildQueueContext(state.queue[0] || null);
    state.selectedDeviceCode = state.devices[0]?.code || null;

    const requestService = services.request || createShopfloorRequestService(dataService, router, stateService, selectionService, state);
    let lastProtocolRuntimeActivitySignature = null;

    function pushActivity(message, options = {}) {
        const label = typeof message === "object" && message !== null ? message.label || message.title || null : message;
        if (!label) {
            return;
        }
        const entry =
            typeof message === "object" && message !== null
                ? {
                      id: message.id || `activity-${Date.now()}`,
                      title: message.title || message.label || "Activity",
                      label: message.label || message.title || "Activity",
                      detail: message.detail || null,
                      kind: message.kind || "activity",
                      status: message.status || message.statusKey || options.status || "info",
                      statusKey: message.statusKey || message.status || options.status || "info",
                      statusLabel: message.statusLabel || options.statusLabel || null,
                      statusTone: message.statusTone || message.tone || options.statusTone || message.status || options.status || "info",
                      timestamp: message.timestamp || new Date().toLocaleTimeString(),
                  }
                : {
                      id: `activity-${Date.now()}`,
                      title: String(label),
                      label: String(label),
                      detail: options.detail || null,
                      kind: options.kind || "activity",
                      status: options.status || "info",
                      statusKey: options.statusKey || options.status || "info",
                      statusLabel: options.statusLabel || null,
                      statusTone: options.statusTone || options.status || "info",
                      timestamp: options.timestamp || new Date().toLocaleTimeString(),
                  };
        state.activity = [entry, ...state.activity].slice(0, 6);
        state.logs = [
            {
                ...entry,
            },
            ...state.logs,
        ].slice(0, 12);
        if (options.includeInTimeline) {
            state.timeline = [
                {
                    ...entry,
                },
                ...state.timeline,
            ].slice(0, 12);
        }
    }

    function setMetric(key, value) {
        state.metrics[key] = value;
    }

    function setConnectivity(nextState, detail = null) {
        const currentState = state.connectivity.state;
        const isRecovery = nextState === "online" && currentState !== "online";
        const normalizedState = nextState || "online";
        const labels = {
            online: "Live",
            degraded: "Degraded",
            offline: "Offline",
        };
        const tones = {
            online: "success",
            degraded: "warning",
            offline: "danger",
        };
        const defaultDetails = {
            online: isRecovery ? "Connection restored and state synchronized." : "Execution service connected.",
            degraded: "The workbench is retrying and some data may be stale.",
            offline: "The workbench is using local fallback data until the execution service returns.",
        };
        state.connectivity = {
            state: normalizedState,
            tone: tones[normalizedState] || "secondary",
            label: labels[normalizedState] || "Unknown",
            detail: detail || defaultDetails[normalizedState] || "Connectivity status updated.",
            canRetry: normalizedState !== "online",
            recovered: isRecovery,
            lastTransitionLabel: isRecovery ? "Recovered" : labels[normalizedState] || "Updated",
        };
    }

    function setRoute(route) {
        router.go(route);
        state.activeExecutionTab = route;
    }

    function getGatewayRuntimeAttentionSnapshot(summary) {
        const openDriverIssues = Number(summary?.issueCounts?.open || 0);
        const openDriverAdapters = Number(summary?.issueCounts?.openAdapters || 0);
        const edgeDeadLetterCount = Number(summary?.edgeDeadLetter?.count || 0);
        const edgeDeadLetterAdapters = Number(summary?.edgeDeadLetter?.adapters || 0);
        const edgeReplayPending = Number(summary?.edgeReplay?.pending || 0);
        const edgeReplayDue = Number(summary?.edgeReplay?.due || 0);
        const edgeReplayScheduled = Number(summary?.edgeReplay?.scheduled || 0);
        const edgeReplayAdapters = Number(summary?.edgeReplay?.adapters || 0);
        const edgeReplayOutcome = String(summary?.edgeReplay?.lastOutcome || "").trim().toLowerCase();
        const edgeActionProcessing = Number(summary?.edgeActionCounts?.processing || 0);
        const edgeActionProcessingAdapters = Number(summary?.edgeActionCounts?.processingAdapters || 0);

        if (openDriverIssues > 0) {
            return {
                kind: "driver_issues",
                count: openDriverIssues,
                adapters: openDriverAdapters,
                title: "Driver issues",
                detail: summary?.detail || summary?.summary || null,
                tone: "danger",
                status: "danger",
                statusLabel: "Danger",
                summary: summary?.summary || null,
            };
        }
        if (edgeDeadLetterCount > 0) {
            return {
                kind: "edge_dead_letter",
                count: edgeDeadLetterCount,
                adapters: edgeDeadLetterAdapters,
                title: "Edge dead letters",
                detail:
                    summary?.edgeDeadLetter?.summary ||
                    summary?.detail ||
                    summary?.summary ||
                    "Some outbound requests exhausted retry budget.",
                tone: "danger",
                status: "danger",
                statusLabel: "Danger",
                summary: summary?.edgeDeadLetter?.summary || summary?.summary || null,
            };
        }
        if (edgeReplayDue > 0) {
            return {
                kind: "edge_replay_due",
                count: edgeReplayDue,
                adapters: Number(summary?.edgeReplay?.dueAdapters || edgeReplayAdapters || 0),
                title: "Edge replay due",
                detail:
                    summary?.edgeReplay?.lastSummary ||
                    summary?.edgeReplay?.summary ||
                    summary?.detail ||
                    summary?.summary ||
                    "Some offline requests are ready to replay.",
                tone: "warning",
                status: "warning",
                statusLabel: "Warning",
                summary: summary?.edgeReplay?.lastSummary || summary?.edgeReplay?.summary || summary?.summary || null,
            };
        }
        if (edgeReplayScheduled > 0 && edgeReplayOutcome === "waiting_backoff") {
            return {
                kind: "edge_replay_scheduled",
                count: edgeReplayScheduled,
                adapters: Number(summary?.edgeReplay?.scheduledAdapters || edgeReplayAdapters || 0),
                title: "Edge replay cooling down",
                detail:
                    summary?.edgeReplay?.lastSummary ||
                    summary?.edgeReplay?.summary ||
                    summary?.detail ||
                    summary?.summary ||
                    "Some offline requests are cooling down before the next retry.",
                tone: "info",
                status: "info",
                statusLabel: "Info",
                summary: summary?.edgeReplay?.lastSummary || summary?.edgeReplay?.summary || summary?.summary || null,
            };
        }
        if (edgeReplayPending > 0) {
            return {
                kind: "edge_replay",
                count: edgeReplayPending,
                adapters: edgeReplayAdapters,
                title: "Edge replay pending",
                detail:
                    summary?.edgeReplay?.summary ||
                    summary?.detail ||
                    summary?.summary ||
                    "Some offline requests are still waiting to replay.",
                tone: "warning",
                status: "warning",
                statusLabel: "Warning",
                summary: summary?.edgeReplay?.summary || summary?.summary || null,
            };
        }
        if (edgeActionProcessing > 0) {
            return {
                kind: "edge_actions_processing",
                count: edgeActionProcessing,
                adapters: edgeActionProcessingAdapters,
                title: "Edge actions processing",
                detail:
                    summary?.edgeActionSummary ||
                    summary?.detail ||
                    summary?.summary ||
                    "Edge actions are currently being processed.",
                tone: "info",
                status: "info",
                statusLabel: "Info",
                summary: summary?.edgeActionSummary || summary?.summary || null,
            };
        }
        return null;
    }

    function getProtocolRuntimeAttentionSnapshot(summary) {
        const protocolRuntime = summary?.protocolRuntime || {};
        const protocolRuntimeStateCounts = protocolRuntime.stateCounts || summary?.protocolRuntimeStateCounts || {};
        const protocolRuntimeCount = Number(summary?.protocolRuntimeCount || protocolRuntime.count || 0);
        const protocolRuntimeEntryCount = Number(summary?.protocolRuntimeEntryCount || protocolRuntime.entryCount || 0);
        const protocolRuntimeSummary = summary?.protocolRuntimeSummary || protocolRuntime.summary || null;
        const protocolRuntimeState = String(summary?.protocolRuntimeState || protocolRuntime.state || protocolRuntime.stateKey || "")
            .trim()
            .toLowerCase();
        const protocolErrorCount = Number(protocolRuntimeStateCounts.error || 0);
        const protocolPendingCount = Number(protocolRuntimeStateCounts.pending || 0);
        const protocolUnavailableCount = Number(protocolRuntimeStateCounts.unavailable || 0);
        const protocolReadyCount = Number(protocolRuntimeStateCounts.ready || 0);
        const protocolAttentionCount = protocolErrorCount + protocolPendingCount + protocolUnavailableCount;

        if (!protocolAttentionCount && protocolRuntimeState !== "attention" && protocolRuntimeState !== "error") {
            return null;
        }

        const count = protocolRuntimeCount || protocolRuntimeEntryCount || protocolAttentionCount || protocolReadyCount;
        const adapters = protocolRuntimeEntryCount || protocolRuntimeCount || protocolAttentionCount || protocolReadyCount;

        return {
            kind: "protocol_runtime",
            count,
            adapters,
            title:
                protocolErrorCount > 0
                    ? "Protocol runtimes reporting errors"
                    : protocolPendingCount > 0 || protocolUnavailableCount > 0
                      ? "Protocol runtimes need follow-up"
                      : "Protocol runtime attention",
            detail:
                protocolRuntimeSummary ||
                summary?.detail ||
                summary?.summary ||
                (protocolErrorCount > 0
                    ? "Protocol runtime errors need follow-up."
                    : "Protocol runtime attention is still active."),
            tone: protocolErrorCount > 0 ? "danger" : "warning",
            status: protocolErrorCount > 0 ? "danger" : "warning",
            statusLabel: protocolErrorCount > 0 ? "Danger" : "Warning",
            summary: protocolRuntimeSummary || summary?.summary || null,
        };
    }

    function buildProtocolRuntimeActivitySignature(snapshot, change) {
        if (!snapshot) {
            return null;
        }
        const normalizeText = (value) => String(value || "").replace(/\s+/g, " ").trim().toLowerCase();
        return [
            "protocol_runtime",
            change || "updated",
            snapshot.kind || "",
            snapshot.status || "",
            snapshot.count || 0,
            snapshot.adapters || 0,
            normalizeText(snapshot.title),
            normalizeText(snapshot.detail),
            normalizeText(snapshot.summary),
        ].join("|");
    }

    function buildGatewayRuntimeActivity(snapshot, change = "updated") {
        if (!snapshot) {
            return null;
        }
        const countLabel = snapshot.adapters > 0 ? `${snapshot.count} across ${snapshot.adapters} adapter(s).` : `${snapshot.count}.`;
        const changeTitles = {
            detected: {
                driver_issues: "Driver issues detected",
                edge_dead_letter: "Edge dead letters detected",
                edge_replay_due: "Edge replay due",
                edge_replay_scheduled: "Edge replay cooling down",
                edge_replay: "Edge replay pending",
                edge_actions_processing: "Edge actions processing",
                protocol_runtime: "Protocol runtime attention",
            },
            resolved: {
                driver_issues: "Driver issues resolved",
                edge_dead_letter: "Edge dead letters cleared",
                edge_replay_due: "Edge replay due cleared",
                edge_replay_scheduled: "Edge replay cooldown cleared",
                edge_replay: "Edge replay cleared",
                edge_actions_processing: "Edge actions cleared",
                protocol_runtime: "Protocol runtime attention cleared",
            },
            updated: {
                driver_issues: "Driver issues updated",
                edge_dead_letter: "Edge dead letters updated",
                edge_replay_due: "Edge replay due updated",
                edge_replay_scheduled: "Edge replay cooldown updated",
                edge_replay: "Edge replay updated",
                edge_actions_processing: "Edge actions updated",
                protocol_runtime: "Protocol runtime attention updated",
            },
        };
        const titles = changeTitles[change] || changeTitles.updated;
        let label = snapshot.title;
        if (change === "resolved") {
            label =
                snapshot.kind === "driver_issues"
                    ? "Driver issues resolved. Runtime diagnostics are clear again."
                    : snapshot.kind === "edge_dead_letter"
                      ? "Edge dead letters cleared. No dead-letter backlog remains."
                      : snapshot.kind === "edge_replay_due"
                        ? "Edge replay due cleared. No replay item is waiting to resend."
                        : snapshot.kind === "edge_replay_scheduled"
                          ? "Edge replay cooldown cleared. No retry timer is currently active."
                      : snapshot.kind === "edge_replay"
                        ? "Edge replay cleared. No outbound replay backlog remains."
                        : snapshot.kind === "protocol_runtime"
                          ? "Protocol runtime attention cleared. Protocol runtimes are ready again."
                        : "Edge actions processing cleared. No adapter is currently handling queued edge actions.";
        } else if (change === "detected") {
            label =
                snapshot.kind === "driver_issues"
                    ? `Driver issues detected: ${countLabel}`
                    : snapshot.kind === "edge_dead_letter"
                      ? `Edge dead letters detected: ${countLabel}`
                      : snapshot.kind === "edge_replay_due"
                        ? `Edge replay due: ${countLabel}`
                      : snapshot.kind === "edge_replay_scheduled"
                          ? `Edge replay cooling down: ${countLabel}`
                      : snapshot.kind === "edge_replay"
                        ? `Edge replay pending: ${countLabel}`
                        : snapshot.kind === "protocol_runtime"
                          ? `Protocol runtime attention: ${countLabel}`
                        : `Edge actions processing: ${countLabel}`;
        } else {
            label =
                snapshot.kind === "driver_issues"
                    ? `Driver issues updated: ${countLabel}`
                    : snapshot.kind === "edge_dead_letter"
                      ? `Edge dead letters updated: ${countLabel}`
                      : snapshot.kind === "edge_replay_due"
                        ? `Edge replay due updated: ${countLabel}`
                      : snapshot.kind === "edge_replay_scheduled"
                          ? `Edge replay cooling down updated: ${countLabel}`
                      : snapshot.kind === "edge_replay"
                        ? `Edge replay updated: ${countLabel}`
                        : snapshot.kind === "protocol_runtime"
                          ? `Protocol runtime attention updated: ${countLabel}`
                        : `Edge actions updated: ${countLabel}`;
        }
        return {
            title: titles[snapshot.kind] || snapshot.title,
            label,
            detail: snapshot.detail || snapshot.summary || null,
            kind: "runtime",
            status: snapshot.status,
            statusKey: snapshot.status,
            statusLabel: snapshot.statusLabel,
            statusTone: snapshot.tone,
        };
    }

    function pushGatewayRuntimeActivity(previousSummary, nextSummary) {
        const previousAttention = getGatewayRuntimeAttentionSnapshot(previousSummary);
        const nextAttention = getGatewayRuntimeAttentionSnapshot(nextSummary);

        if (!previousAttention && !nextAttention) {
            return;
        }
        if (!previousAttention && nextAttention) {
            pushActivity(buildGatewayRuntimeActivity(nextAttention, "detected"), { includeInTimeline: true });
            return;
        }
        if (previousAttention && !nextAttention) {
            pushActivity(buildGatewayRuntimeActivity(previousAttention, "resolved"), { includeInTimeline: true });
            return;
        }

        const sameKind = previousAttention.kind === nextAttention.kind;
        const sameCount = previousAttention.count === nextAttention.count;
        const sameAdapters = previousAttention.adapters === nextAttention.adapters;
        const sameDetail = (previousAttention.detail || "") === (nextAttention.detail || "");

        if (sameKind && sameCount && sameAdapters && sameDetail) {
            return;
        }

        pushActivity(
            buildGatewayRuntimeActivity(nextAttention, sameKind ? "updated" : "detected"),
            { includeInTimeline: true }
        );
    }

    function pushProtocolRuntimeActivity(previousSummary, nextSummary) {
        const previousAttention = getProtocolRuntimeAttentionSnapshot(previousSummary);
        const nextAttention = getProtocolRuntimeAttentionSnapshot(nextSummary);

        if (!previousAttention && !nextAttention) {
            return;
        }
        if (!previousAttention && nextAttention) {
            const signature = buildProtocolRuntimeActivitySignature(nextAttention, "detected");
            if (signature && signature === lastProtocolRuntimeActivitySignature) {
                return;
            }
            lastProtocolRuntimeActivitySignature = signature;
            pushActivity(buildGatewayRuntimeActivity(nextAttention, "detected"), { includeInTimeline: true });
            return;
        }
        if (previousAttention && !nextAttention) {
            const signature = buildProtocolRuntimeActivitySignature(previousAttention, "resolved");
            if (signature && signature === lastProtocolRuntimeActivitySignature) {
                return;
            }
            lastProtocolRuntimeActivitySignature = signature;
            pushActivity(buildGatewayRuntimeActivity(previousAttention, "resolved"), { includeInTimeline: true });
            return;
        }

        const sameKind = previousAttention.kind === nextAttention.kind;
        const nextChange = sameKind ? "updated" : "detected";
        const previousSignature = buildProtocolRuntimeActivitySignature(previousAttention, nextChange);
        const nextSignature = buildProtocolRuntimeActivitySignature(nextAttention, nextChange);

        if (nextSignature && nextSignature === previousSignature) {
            return;
        }
        if (nextSignature && nextSignature === lastProtocolRuntimeActivitySignature) {
            return;
        }
        lastProtocolRuntimeActivitySignature = nextSignature;
        pushActivity(buildGatewayRuntimeActivity(nextAttention, nextChange), { includeInTimeline: true });
    }

    async function boot(payload = {}) {
        try {
            const bootPayload = await requestService.boot(payload);
            const previousGatewayRuntimeSummary = state.gatewayRuntimeSummary;
            const normalized = stateService.normalizeShopfloorEnvelope(bootPayload, {
                currentUserName: state.currentUser.name,
                sessionRef: state.sessionRef,
                activity: state.activity,
            });
            stateService.applyNormalizedEnvelope(state, router, normalized);
            selectionService.syncSelectedQueueContext(state);
            setConnectivity("online");
            pushGatewayRuntimeActivity(previousGatewayRuntimeSummary, normalized?.gatewayRuntimeSummary);
            pushProtocolRuntimeActivity(previousGatewayRuntimeSummary, normalized?.gatewayRuntimeSummary);
            pushActivity("Boot payload loaded from execution service");
            state.booted = true;
            state.lastResponse = bootPayload;
            return bootPayload;
        } catch (error) {
            state.bootError = error?.message || "Failed to boot frontend";
            setConnectivity("offline", "Boot failed. The workbench is waiting to reconnect to the execution service.");
            throw error;
        }
    }

    function selectQueueItem(queueId) {
        selectionService.selectQueueItem(state, queueId);
        setRoute("execution");
        pushActivity(`Selected queue item ${state.selectedQueueContext?.reference || queueId}`);
    }

    function selectDevice(deviceCode) {
        selectionService.selectDevice(state, deviceCode);
        setRoute("devices");
        pushActivity(`Selected device ${deviceCode}`);
    }

    function updateFromResponse(response) {
        const previousGatewayRuntimeSummary = state.gatewayRuntimeSummary;
        const normalized = stateService.normalizeShopfloorEnvelope(response, {
            currentUserName: state.currentUser.name,
            sessionRef: state.sessionRef,
            activity: state.activity,
        });
        stateService.applyNormalizedEnvelope(state, router, normalized, state.activity);
        selectionService.syncSelectedQueueContext(state);
        pushGatewayRuntimeActivity(previousGatewayRuntimeSummary, normalized?.gatewayRuntimeSummary);
        pushProtocolRuntimeActivity(previousGatewayRuntimeSummary, normalized?.gatewayRuntimeSummary);
        if (normalized?.messageText) {
            pushActivity(normalized.messageText);
        }
        setConnectivity("online");
        state.lastResponse = response || null;
        return normalized;
    }

    async function refreshState(extra = {}) {
        try {
            const response = await requestService.refreshState(extra);
            updateFromResponse(response);
            pushActivity("State refreshed from execution service");
            return response;
        } catch (error) {
            state.bootError = error?.message || "Failed to refresh Shopfloor state";
            setConnectivity("offline", "Refresh failed. Falling back to the last local workstation snapshot.");
            pushActivity("State refresh failed, keeping current panels");
            throw error;
        }
    }

    async function submitAction(action, extra = {}) {
        const response = await requestService.submitAction(action, extra);
        const normalized = updateFromResponse(response);

        const nextQueueStatus =
            action === "start" ? "in_progress" : action === "pause" ? "paused" : action === "finish" ? "done" : action === "exception" ? "blocked" : null;

        if (!normalized.queue.length && nextQueueStatus && state.selectedQueueId) {
            state.queue = state.queue.map((item) =>
                String(item.id) === String(state.selectedQueueId) || String(item.queue_id) === String(state.selectedQueueId)
                    ? { ...item, status: nextQueueStatus }
                    : item
            );
        }

        if (!normalized.execution?.state) {
            if (action === "start") {
                state.execution.state = "running";
            } else if (action === "pause") {
                state.execution.state = "paused";
            } else if (action === "finish") {
                state.execution.state = "done";
            } else if (action === "exception") {
                state.execution.state = "failed";
            }
        }

        if (action === "exception" && !normalized.exceptions.length) {
            const label = extra.message || "Exception reported";
            state.exceptions = [
                {
                    id: `LOCAL-${Date.now()}`,
                    title: label,
                    severity: extra.severity || "medium",
                    state: extra.state || "new",
                    source: "Operator",
                    details: extra.details || label,
                },
                ...state.exceptions,
            ].slice(0, 8);
        }

        if (!normalized.queue.length && nextQueueStatus) {
            stateService.refreshDerivedState(state);
        }

        if (normalized.queue.length) {
            const matchedSelection = stateService.matchQueueSelection(
                normalized.queue,
                state.selectedQueueContext || selectionService.getSelectedQueueItem(state)
            );
            if (matchedSelection) {
                state.selectedQueueId = matchedSelection.id;
                state.selectedQueueContext = stateService.buildQueueContext(matchedSelection);
            } else {
                selectionService.syncSelectedQueueContext(state);
            }
        }

        return response;
    }

    async function queueDeviceAction(deviceAction = {}, device = null) {
        const selectedDevice = device || state.devices.find((item) => item.code === state.selectedDeviceCode) || null;
        const deviceCode = selectedDevice?.code || deviceAction.deviceCode || deviceAction.device_code || null;
        const gatewayEntryCode = selectedDevice?.entry_code || deviceAction.gateway_entry_code || null;
        const queuedAt = new Date().toISOString();
        const deviceCommand = {
            name: deviceAction.label || deviceAction.name || deviceAction.command || "Device command",
            command_type: deviceAction.command || deviceAction.command_type || deviceAction.key || "custom",
            command_key: deviceAction.command || deviceAction.command_key || deviceAction.key || "custom",
            code: deviceAction.command || deviceAction.command_key || deviceAction.key || "custom",
            device_code: deviceCode,
            signal_code: selectedDevice?.signal || deviceAction.signal_code || null,
            payload: {
                action_key: deviceAction.key || null,
                action_label: deviceAction.label || null,
                device_code: deviceCode,
                device_name: selectedDevice?.name || deviceAction.deviceName || null,
                device_state: selectedDevice?.state || deviceAction.deviceState || null,
                selected_visible: deviceAction.selectedVisible !== false,
                tone: deviceAction.tone || null,
            },
        };

        const response = await submitAction("device", {
            note: deviceAction.detail || deviceAction.label || "Device command queued",
            message: deviceAction.label || "Device command queued",
            command_key: deviceCommand.command_key,
            device_code: deviceCode,
            selected_device_code: deviceCode,
            gateway_entry_code: gatewayEntryCode,
            device_command: deviceCommand,
        });

        if (response?.commands?.length) {
            state.commands = response.commands;
        } else {
            const localCommand = {
                ...deviceCommand,
                id: deviceCommand.command_key || `LOCAL-${Date.now()}`,
                status: "queued",
                state: "queued",
                statusKey: "queued",
                statusLabel: "Queued",
                statusTone: "info",
                tone: "info",
                detail: deviceAction.detail || deviceAction.label || "Device command queued locally",
                note: deviceAction.detail || deviceAction.label || "Device command queued locally",
                createdAt: queuedAt,
                timestamp: queuedAt,
                deviceCode,
                deviceName: selectedDevice?.name || deviceAction.deviceName || null,
                target: deviceCode,
                last_attempt_at: queuedAt,
            };
            state.commands = [localCommand, ...state.commands].slice(0, 12);
            state.commandQueueStatus = stateService.buildCommandQueueStatus(state.commands, {
                label: "Command queue active",
                detail: "Local command receipt prepared while the backend response is being reconciled.",
                latestLabel: localCommand.name,
                latestDetail: localCommand.detail,
                state: "queued",
                stateKey: "queued",
            });
        }

        return response;
    }

    async function startExecution() {
        pushActivity("Start requested");
        return submitAction("start", { note: "Start from Shopfloor frontend" });
    }

    async function pauseExecution() {
        pushActivity("Pause requested");
        return submitAction("pause", { note: "Pause from Shopfloor frontend" });
    }

    async function finishExecution() {
        pushActivity("Finish requested");
        return submitAction("finish", { note: "Finish from Shopfloor frontend" });
    }

    async function reportException(message, severity = "medium", extra = {}) {
        const text = message || "Operator exception";
        pushActivity(`Exception reported: ${text}`);
        return submitAction("exception", {
            ...extra,
            message: text,
            severity,
            exception_type: "process",
            details: text,
            note: text,
        });
    }

    async function refreshPanels() {
        try {
            const refreshed = await refreshState();
            selectionService.syncSelectedQueueContext(state);
            return refreshed;
        } catch {
            const fallbackSeedSurfaces = buildSeedSurfaces(state.workstation.code);
            state.queue = stateService.buildSampleQueue(state.workstation.code);
            state.devices = stateService.buildSampleDevices();
            state.exceptions = stateService.buildSampleExceptions();
            state.commands = [];
            state.activity = fallbackSeedSurfaces.activity;
            state.timeline = fallbackSeedSurfaces.timeline;
            state.logs = fallbackSeedSurfaces.logs;
            state.responseSummary = fallbackSeedSurfaces.responseSummary;
            state.commandQueueStatus = fallbackSeedSurfaces.commandQueueStatus;
            state.gatewayRuntimeSummary = fallbackSeedSurfaces.gatewayRuntimeSummary;
            state.selectedQueueId = state.queue[0]?.queue_id || state.queue[0]?.id || null;
            state.selectedQueueContext = stateService.buildQueueContext(state.queue[0] || null);
            state.selectedDeviceCode = state.devices[0]?.code || null;
            stateService.refreshDerivedState(state);
            setConnectivity("degraded", "Local fallback panels restored while the execution service is unavailable.");
            state.lastResponse = null;
            pushActivity("Local fallback panels restored");
            return null;
        }
    }

    return {
        dataService,
        stateService,
        selectionService,
        requestService,
        state,
        router,
        boot,
        pushActivity,
        setConnectivity,
        setMetric,
        setRoute,
        selectQueueItem,
        selectDevice,
        queueDeviceAction,
        submitAction,
        startExecution,
        pauseExecution,
        finishExecution,
        reportException,
        refreshState,
        refreshPanels,
    };
}
