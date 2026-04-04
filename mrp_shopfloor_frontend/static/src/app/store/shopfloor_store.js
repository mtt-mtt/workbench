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
        metrics: {
            pendingJobs: 0,
            activeExceptions: 0,
            deviceOnline: true,
            lastSync: "waiting",
        },
        panels: [
            { key: "dashboard", label: "Dashboard" },
            { key: "queue", label: "Queue" },
            { key: "execution", label: "Execution" },
            { key: "devices", label: "Devices" },
            { key: "exceptions", label: "Exceptions" },
        ],
        activity: [
            "Frontend shell loaded",
            "Waiting for core API wiring",
            "Router and store are ready",
        ],
        queue: stateService.buildSampleQueue(workstationCode),
        devices: stateService.buildSampleDevices(),
        exceptions: stateService.buildSampleExceptions(),
        commands: [],
        timeline: stateService.buildSeedTimelineEntries(workstationCode),
        logs: stateService.buildSampleLogs(workstationCode),
        responseSummary: stateService.buildIdleResponseSummary(),
        commandQueueStatus: stateService.buildIdleCommandQueueStatus(),
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

    function pushActivity(message) {
        if (!message) {
            return;
        }
        state.activity = [message, ...state.activity].slice(0, 6);
        state.logs = [
            {
                id: `activity-${Date.now()}`,
                title: message,
                detail: null,
                kind: "activity",
                status: "info",
                timestamp: new Date().toLocaleTimeString(),
            },
            ...state.logs,
        ].slice(0, 12);
    }

    function setMetric(key, value) {
        state.metrics[key] = value;
    }

    function setRoute(route) {
        router.go(route);
        state.activeExecutionTab = route;
    }

    async function boot(payload = {}) {
        try {
            const bootPayload = await requestService.boot(payload);
            const normalized = stateService.normalizeShopfloorEnvelope(bootPayload, {
                currentUserName: state.currentUser.name,
                sessionRef: state.sessionRef,
                activity: state.activity,
            });
            stateService.applyNormalizedEnvelope(state, router, normalized);
            selectionService.syncSelectedQueueContext(state);
            pushActivity("Boot payload loaded from execution service");
            state.booted = true;
            state.lastResponse = bootPayload;
            return bootPayload;
        } catch (error) {
            state.bootError = error?.message || "Failed to boot frontend";
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
        const normalized = stateService.normalizeShopfloorEnvelope(response, {
            currentUserName: state.currentUser.name,
            sessionRef: state.sessionRef,
            activity: state.activity,
        });
        stateService.applyNormalizedEnvelope(state, router, normalized, state.activity);
        selectionService.syncSelectedQueueContext(state);
        if (normalized?.messageText) {
            pushActivity(normalized.messageText);
        }
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
            state.queue = stateService.buildSampleQueue(state.workstation.code);
            state.devices = stateService.buildSampleDevices();
            state.exceptions = stateService.buildSampleExceptions();
            state.commands = [];
            state.timeline = stateService.buildSeedTimelineEntries(state.workstation.code);
            state.logs = stateService.buildSampleLogs(state.workstation.code);
            state.responseSummary = stateService.buildIdleResponseSummary();
            state.commandQueueStatus = stateService.buildIdleCommandQueueStatus();
            state.selectedQueueId = state.queue[0]?.queue_id || state.queue[0]?.id || null;
            state.selectedQueueContext = stateService.buildQueueContext(state.queue[0] || null);
            state.selectedDeviceCode = state.devices[0]?.code || null;
            stateService.refreshDerivedState(state);
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
