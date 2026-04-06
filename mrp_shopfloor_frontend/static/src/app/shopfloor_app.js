/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ShopfloorInspector } from "./components/shopfloor_inspector/shopfloor_inspector";
import { ShopfloorNavRail } from "./components/shopfloor_nav_rail/shopfloor_nav_rail";
import { createShopfloorRouter } from "./router/shopfloor_router";
import { createShopfloorDataService } from "./services/shopfloor_data_service";
import {
    createShopfloorShellService,
    normalizeShopfloorRoute,
    routeLabel,
} from "./services/shopfloor_shell_service";
import { createShopfloorStore } from "./store/shopfloor_store";
import { ShopfloorPanelScreen } from "./screens/shopfloor_panel_screen/shopfloor_panel_screen";

export class ShopfloorFrontendAction extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorApp";
    static components = {
        ShopfloorInspector,
        ShopfloorNavRail,
        ShopfloorPanelScreen,
    };

    setup() {
        this._scannerBuffer = "";
        this._scannerTimer = null;
        this._lastScannerKeyAt = 0;
        this._boundKeydown = this.onWindowKeydown.bind(this);
        this._boundFullscreenChange = this.onFullscreenChange.bind(this);
        this.notification = useService("notification");
        const action = this.props.action || {};
        this.routerService = createShopfloorRouter(action?.params?.route || "dashboard");
        this.dataService = createShopfloorDataService();
        this.shellService = createShopfloorShellService();
        this.store = createShopfloorStore(this.env, action, {
            router: this.routerService,
            data: this.dataService,
        });
        this.state = useState({
            ready: false,
            loadError: null,
            fullscreen: false,
            focusMode: true,
            lastScannerCode: null,
            scannerHint: "Ready for scanner input",
        });

        onWillStart(async () => {
            try {
                await this.store.boot({
                    workstation_code: action?.params?.workstation_code || null,
                    session_ref: action?.params?.session_ref || null,
                    route: action?.params?.route || "dashboard",
                });
                this.state.ready = true;
                this.updateDocumentTitle();
            } catch (error) {
                this.state.loadError = error.message || "Failed to boot Shopfloor frontend.";
                this.notification.add(this.state.loadError, { type: "danger" });
            }
        });

        onMounted(() => {
            document.body.classList.add("o_shopfloor_frontend");
            window.addEventListener("keydown", this._boundKeydown);
            document.addEventListener("fullscreenchange", this._boundFullscreenChange);
            this.onFullscreenChange();
            this.updateDocumentTitle();
        });

        onWillUnmount(() => {
            document.body.classList.remove("o_shopfloor_frontend");
            window.removeEventListener("keydown", this._boundKeydown);
            document.removeEventListener("fullscreenchange", this._boundFullscreenChange);
            this.clearScannerBuffer();
        });
    }

    get router() {
        return this.routerService;
    }

    get shellRoute() {
        return this.router.state.current || this.router.state.route;
    }

    get uiState() {
        return {
            fullscreen: this.state.fullscreen,
            focusMode: this.state.focusMode,
            lastScannerCode: this.state.lastScannerCode,
            scannerHint: this.state.scannerHint,
            shortcutSummary: "Alt+1-5 panels · F2/F3/F4 run control · F8 refresh · Ctrl+Shift+F fullscreen",
        };
    }

    updateDocumentTitle(route = this.shellRoute) {
        const workstation = this.workstation?.code || "Shopfloor";
        this.shellService.updateDocumentTitle(workstation, route);
    }

    setRoute(route, options = {}) {
        const nextRoute = normalizeShopfloorRoute(route, this.shellRoute);
        if (options.replace) {
            this.router.replace(nextRoute);
        } else {
            this.router.go(nextRoute);
        }
        this.store.state.activeExecutionTab = nextRoute;
        this.updateDocumentTitle(nextRoute);
        return nextRoute;
    }

    buildRefreshPayload(extra = {}) {
        const queueContext = this.selectedQueueContext || {};
        const selectedDevice = this.selectedDevice || {};
        return {
            route: extra.route || this.shellRoute,
            queue_id: extra.queue_id || queueContext.id || null,
            workorder_id: extra.workorder_id || queueContext.workorder_id || null,
            production_id: extra.production_id || queueContext.production_id || null,
            workorder_ref: extra.workorder_ref || queueContext.workorder_ref || null,
            production_ref: extra.production_ref || queueContext.production_ref || null,
            device_code: extra.device_code || selectedDevice.code || null,
        };
    }

    async refreshCurrentContext(extra = {}) {
        try {
            return await this.store.refreshState(this.buildRefreshPayload(extra));
        } catch (error) {
            const fallback = await this.store.refreshPanels();
            if (!fallback) {
                throw error;
            }
            return fallback;
        }
    }

    async navigate(route, options = {}) {
        const nextRoute = this.setRoute(route, options);
        this.store.pushActivity(`Navigated to ${routeLabel(nextRoute)}`);
        if (options.refresh !== false) {
            try {
                await this.refreshCurrentContext({ route: nextRoute });
            } catch (error) {
                this.notification.add(error.message || "Failed to refresh the current view", { type: "warning" });
            }
        }
    }

    async navigatePanel(ev) {
        ev?.preventDefault?.();
        await this.navigate(ev.currentTarget.dataset.route);
    }

    async goBack() {
        if (this.router.state.canGoBack) {
            this.router.back();
        } else {
            this.router.replace("dashboard");
        }
        this.store.state.activeExecutionTab = this.shellRoute;
        this.updateDocumentTitle();
        this.store.pushActivity("Returned to the previous Shopfloor view");
        try {
            await this.refreshCurrentContext({ route: this.shellRoute });
        } catch (error) {
            this.notification.add(error.message || "Failed to refresh after navigation", { type: "warning" });
        }
    }

    async refreshDemoMetrics() {
        try {
            await this.refreshCurrentContext();
            this.notification.add("Current view refreshed", { type: "info" });
        } catch (error) {
            this.notification.add(error.message || "Failed to refresh panels", { type: "warning" });
        }
    }

    onFullscreenChange() {
        this.state.fullscreen = Boolean(document.fullscreenElement);
    }

    clearScannerBuffer() {
        if (this._scannerTimer) {
            clearTimeout(this._scannerTimer);
            this._scannerTimer = null;
        }
        this._scannerBuffer = "";
        this._lastScannerKeyAt = 0;
    }

    scheduleScannerReset() {
        if (this._scannerTimer) {
            clearTimeout(this._scannerTimer);
        }
        this._scannerTimer = setTimeout(() => {
            this.clearScannerBuffer();
        }, 180);
    }

    isEditableTarget(target) {
        if (!target) {
            return false;
        }
        const tagName = String(target.tagName || "").toLowerCase();
        return (
            tagName === "input" ||
            tagName === "textarea" ||
            tagName === "select" ||
            target.isContentEditable === true
        );
    }

    async toggleFullscreen() {
        try {
            if (document.fullscreenElement) {
                await document.exitFullscreen();
            } else {
                await document.documentElement.requestFullscreen();
            }
        } catch (error) {
            this.notification.add(error.message || "Fullscreen request failed", { type: "warning" });
        }
    }

    toggleFocusMode() {
        this.state.focusMode = !this.state.focusMode;
        this.store.pushActivity(this.state.focusMode ? "Focus mode enabled" : "Focus mode disabled");
    }

    matchScannerTarget(code) {
        const normalizedCode = String(code || "").trim().toLowerCase();
        if (!normalizedCode) {
            return null;
        }
        const queueItem = (this.queue || []).find((item) =>
            [
                item?.reference,
                item?.workorder_ref,
                item?.production_ref,
                item?.name,
            ]
                .filter(Boolean)
                .some((value) => String(value).trim().toLowerCase() === normalizedCode)
        );
        if (queueItem) {
            return {
                type: "queue",
                value: queueItem,
            };
        }
        const device = (this.devices || []).find((item) =>
            [item?.code, item?.name, item?.signal, item?.value]
                .filter(Boolean)
                .some((value) => String(value).trim().toLowerCase() === normalizedCode)
        );
        if (device) {
            return {
                type: "device",
                value: device,
            };
        }
        return null;
    }

    async handleScannerCode(code) {
        const trimmedCode = String(code || "").trim();
        if (!trimmedCode) {
            return;
        }
        this.state.lastScannerCode = trimmedCode;
        const target = this.matchScannerTarget(trimmedCode);
        if (!target) {
            this.state.scannerHint = `Scanned ${trimmedCode} but found no matching queue or device`;
            this.notification.add(this.state.scannerHint, { type: "warning" });
            this.store.pushActivity(`Scanner miss ${trimmedCode}`);
            return;
        }
        this.state.focusMode = true;
        if (target.type === "queue") {
            this.state.scannerHint = `Scanned ${trimmedCode} and opened queue ${target.value.reference || target.value.name}`;
            this.notification.add(this.state.scannerHint, { type: "success" });
            const queueId = target.value.queue_id || target.value.id;
            await this.openQueueItem({
                currentTarget: {
                    dataset: {
                        queueId,
                    },
                },
                preventDefault() {},
            });
            return;
        }
        this.state.scannerHint = `Scanned ${trimmedCode} and opened device ${target.value.code || target.value.name}`;
        this.notification.add(this.state.scannerHint, { type: "success" });
        await this.openDevice({
            currentTarget: {
                dataset: {
                    deviceCode: target.value.code,
                },
            },
            preventDefault() {},
        });
    }

    async onWindowKeydown(ev) {
        if (ev.defaultPrevented) {
            return;
        }
        const editable = this.isEditableTarget(ev.target);
        if (ev.ctrlKey && ev.shiftKey && (ev.key === "F" || ev.key === "f")) {
            ev.preventDefault();
            await this.toggleFullscreen();
            return;
        }
        if (ev.ctrlKey && ev.shiftKey && (ev.key === "M" || ev.key === "m")) {
            ev.preventDefault();
            this.toggleFocusMode();
            return;
        }
        if (editable) {
            return;
        }
        if (ev.altKey && ["1", "2", "3", "4", "5"].includes(ev.key)) {
            ev.preventDefault();
            const routes = {
                1: "dashboard",
                2: "queue",
                3: "execution",
                4: "devices",
                5: "exceptions",
            };
            await this.navigate(routes[ev.key], { replace: true });
            return;
        }
        if (ev.key === "F2") {
            ev.preventDefault();
            await this.startExecution();
            return;
        }
        if (ev.key === "F3") {
            ev.preventDefault();
            await this.pauseExecution();
            return;
        }
        if (ev.key === "F4") {
            ev.preventDefault();
            await this.finishExecution();
            return;
        }
        if (ev.key === "F8") {
            ev.preventDefault();
            await this.refreshDemoMetrics();
            return;
        }
        if (ev.key === "Escape" && this.state.focusMode) {
            ev.preventDefault();
            this.state.focusMode = false;
            this.state.scannerHint = "Focus mode dismissed";
            return;
        }
        if (ev.ctrlKey || ev.metaKey || ev.altKey) {
            return;
        }
        if (ev.key === "Enter") {
            const scannedCode = this._scannerBuffer;
            this.clearScannerBuffer();
            if (scannedCode.length >= 3) {
                ev.preventDefault();
                await this.handleScannerCode(scannedCode);
            }
            return;
        }
        if (ev.key.length !== 1) {
            return;
        }
        const now = Date.now();
        if (!this._lastScannerKeyAt || now - this._lastScannerKeyAt > 80) {
            this._scannerBuffer = "";
        }
        this._lastScannerKeyAt = now;
        this._scannerBuffer += ev.key;
        this.state.scannerHint = `Scanner buffer ${this._scannerBuffer}`;
        this.scheduleScannerReset();
    }

    async openQueueItem(ev) {
        const queueId = ev.currentTarget.dataset.queueId;
        this.store.selectQueueItem(queueId);
        this.setRoute("execution", { replace: true });
        this.store.pushActivity(`Selected queue item ${this.selectedQueueContext?.reference || queueId}`);
        try {
            await this.refreshCurrentContext({
                route: "execution",
                queue_id: queueId,
                ...this.selectedQueueContext,
            });
        } catch (error) {
            this.notification.add(error.message || "Failed to load execution context", { type: "warning" });
        }
    }

    async openDevice(ev) {
        const deviceCode = ev.currentTarget.dataset.deviceCode;
        this.store.selectDevice(deviceCode);
        this.setRoute("devices", { replace: true });
        this.store.pushActivity(`Selected device ${deviceCode}`);
        try {
            await this.refreshCurrentContext({
                route: "devices",
                device_code: deviceCode,
            });
        } catch (error) {
            this.notification.add(error.message || "Failed to load device context", { type: "warning" });
        }
    }

    async queueDeviceAction(deviceAction = {}) {
        const selectedDevice = this.selectedDevice;
        if (!selectedDevice || selectedDevice.code === "DEVICE-EMPTY") {
            this.notification.add("Select a real device before queuing a command.", { type: "warning" });
            return;
        }
        const actionLabel = deviceAction.label || "Device action";
        const commandName = deviceAction.command || deviceAction.command_key || deviceAction.key || actionLabel;
        try {
            await this.store.queueDeviceAction(deviceAction, selectedDevice);
            this.setRoute("devices", { replace: true });
            await this.refreshCurrentContext({
                route: "devices",
                device_code: selectedDevice?.code || null,
            });
            this.notification.add(`${actionLabel} queued for ${selectedDevice?.name || selectedDevice?.code || "device"}`, {
                type: "success",
            });
            this.store.pushActivity(`Queued device command ${commandName}`);
        } catch (error) {
            this.notification.add(error.message || "Failed to queue device action", { type: "danger" });
        }
    }

    async startExecution() {
        try {
            await this.store.startExecution();
            this.setRoute("execution", { replace: true });
            await this.refreshCurrentContext({ route: "execution" });
            this.notification.add("Execution started", { type: "success" });
        } catch (error) {
            this.notification.add(error.message || "Failed to start execution", { type: "danger" });
        }
    }

    async pauseExecution() {
        try {
            await this.store.pauseExecution();
            this.setRoute("execution", { replace: true });
            await this.refreshCurrentContext({ route: "execution" });
            this.notification.add("Execution paused", { type: "warning" });
        } catch (error) {
            this.notification.add(error.message || "Failed to pause execution", { type: "danger" });
        }
    }

    async finishExecution() {
        try {
            await this.store.finishExecution();
            this.setRoute("queue");
            await this.refreshCurrentContext({ route: "queue" });
            this.notification.add("Execution finished", { type: "success" });
        } catch (error) {
            this.notification.add(error.message || "Failed to finish execution", { type: "danger" });
        }
    }

    async reportException(ev) {
        const severity = ev.currentTarget.dataset.severity || "medium";
        const nextState = ev.currentTarget.dataset.state || "new";
        const actionKey = ev.currentTarget.dataset.action || null;
        const exceptionId = ev.currentTarget.dataset.exceptionId || null;
        const gatewayCommandCode = ev.currentTarget.dataset.gatewayCommandCode || null;
        const message = ev.currentTarget.dataset.message || "Operator exception";
        try {
            await this.store.reportException(message, severity, {
                state: nextState,
                action: actionKey,
                exception_id: exceptionId,
                gateway_command_code: gatewayCommandCode,
            });
            this.setRoute("exceptions", { replace: true });
            await this.refreshCurrentContext({ route: "exceptions" });
            this.notification.add("Exception reported", { type: "warning" });
        } catch (error) {
            this.notification.add(error.message || "Failed to report exception", { type: "danger" });
        }
    }

    get currentPanel() {
        return this.shellRoute;
    }

    get currentRoute() {
        return this.shellRoute;
    }

    get shellTitle() {
        return `${this.workstation?.name || "Shopfloor"} - ${routeLabel(this.shellRoute)}`;
    }

    get workstation() {
        return this.store.state.workstation;
    }

    get panels() {
        return this.store.state.panels;
    }

    get activity() {
        return this.store.state.activity;
    }

    get timelineEntries() {
        return this.store.state.timeline;
    }

    get logEntries() {
        return this.store.state.logs;
    }

    get metrics() {
        return this.store.state.metrics;
    }

    get connectivity() {
        return this.store.state.connectivity;
    }

    get currentUserName() {
        return this.store.state.currentUser.name;
    }

    get sessionRef() {
        return this.store.state.sessionRef;
    }

    get loading() {
        return this.store.state.loading;
    }

    get loadError() {
        return this.store.state.bootError;
    }

    get queue() {
        return this.store.state.queue;
    }

    get selectedQueueItem() {
        return (
            this.store.state.queue.find((item) => String(item.id) === String(this.store.state.selectedQueueId)) ||
            this.store.state.queue[0] || {
                id: "QUEUE-EMPTY",
                name: "No queue item",
                workorder: "-",
                quantity: 0,
                done: 0,
                priority: "-",
            }
        );
    }

    get selectedQueueContext() {
        return this.store.state.selectedQueueContext || {
            id: this.selectedQueueItem.id,
            workorder_id: this.selectedQueueItem.workorder_id || null,
            production_id: this.selectedQueueItem.production_id || null,
            reference: this.selectedQueueItem.reference || null,
            workorder_ref: this.selectedQueueItem.workorder_ref || this.selectedQueueItem.reference || null,
            production_ref: this.selectedQueueItem.production_ref || null,
        };
    }

    get devices() {
        return this.store.state.devices;
    }

    get selectedDevice() {
        return (
            this.store.state.devices.find((item) => item.code === this.store.state.selectedDeviceCode) ||
            this.store.state.devices[0] || {
                code: "DEVICE-EMPTY",
                name: "No device selected",
                kind: "-",
                state: "offline",
                signal: "-",
                value: "-",
                lastSeen: "-",
            }
        );
    }

    get exceptions() {
        return this.store.state.exceptions;
    }

    get execution() {
        return this.store.state.execution;
    }

    get commands() {
        return this.store.state.commands;
    }

    get commandQueueStatus() {
        return this.store.state.commandQueueStatus;
    }

    get gatewayRuntimeSummary() {
        return this.store.state.gatewayRuntimeSummary;
    }

    get responseSummary() {
        return this.store.state.responseSummary;
    }

    get lastResponse() {
        return this.store.state.lastResponse;
    }

    get lastResponseText() {
        return JSON.stringify(this.lastResponse || {}, null, 2);
    }

    get booted() {
        return this.store.state.booted;
    }
}
