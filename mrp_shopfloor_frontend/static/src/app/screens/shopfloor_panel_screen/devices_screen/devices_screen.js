/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { findLatestRuntimeEntry, normalizeRuntimeEntry } from "../../../../utils/shopfloor_runtime_entries";
import { ShopfloorFeedbackBar } from "../../../../components/shopfloor_status_components/shopfloor_feedback_bar";
import { ShopfloorStatusSummary } from "../../../../components/shopfloor_status_components/shopfloor_status_summary";
import {
    deviceStateTone,
    deviceSummaryItems,
    summarizeDevices,
} from "../../../../components/shopfloor_status_components/shopfloor_status_metrics";
import { ShopfloorDeviceActionBar } from "./device_action_bar/device_action_bar";
import { ShopfloorDeviceActionConfirm } from "./device_action_confirm/device_action_confirm";
import { ShopfloorDeviceActionLog } from "./device_action_log/device_action_log";
import { ShopfloorDeviceDetail } from "./device_detail/device_detail";
import { ShopfloorDeviceList } from "./device_list/device_list";
import { ShopfloorDeviceToolbar } from "./device_toolbar/device_toolbar";
import { gatewayCommandFeedback, gatewayCommandSummaryItems, sortGatewayCommands, summarizeGatewayCommands } from "./device_command_status";
import { filterDevices, groupByLabel, groupDevices, stateFilterLabel } from "./devices_filtering";

function normalizeKey(value) {
    return String(value || "").trim().replace(/\s+/g, "_").toLowerCase();
}

function buildDeviceActionCandidates(device) {
    const state = normalizeKey(device?.state);
    const isAttention = ["degraded", "offline", "error"].includes(state);
    const isHealthy = ["ready", "active"].includes(state);

    const actions = [
        {
            key: "probe",
            label: "Probe",
            tone: "secondary",
            detail: "Queue a local health probe in the command shell.",
            command: "probe",
        },
        {
            key: "refresh",
            label: "Refresh snapshot",
            tone: "info",
            detail: "Capture the latest device snapshot without touching the backend.",
            command: "refresh_snapshot",
        },
    ];

    if (isHealthy) {
        actions.push({
            key: "sync",
            label: "Sync snapshot",
            tone: "success",
            detail: "Queue a fresh runtime snapshot for a healthy device.",
            command: "sync_snapshot",
        });
    }

    if (isAttention) {
        actions.push(
            {
                key: "acknowledge",
                label: "Acknowledge",
                tone: "warning",
                detail: "Mark the attention signal as locally acknowledged.",
                command: "acknowledge_attention",
            },
            {
                key: "retry_link",
                label: "Retry link",
                tone: "danger",
                detail: "Queue a reconnect attempt through the local gateway shell.",
                command: "retry_link",
            }
        );
    }

    actions.push({
        key: "note",
        label: "Add note",
        tone: "light",
        detail: "Create a follow-up note without issuing a remote command.",
        command: "create_follow_up",
    });

    return actions;
}

function createActionEntry(device, action) {
    const timestamp = new Date();
    return {
        id: `${timestamp.getTime()}-${action.key}-${normalizeKey(device?.code)}`,
        label: action.label,
        command: action.command,
        tone: action.tone,
        detail: action.detail,
        deviceCode: device?.code || "n/a",
        deviceName: device?.name || "Unknown device",
        deviceState: device?.state || "unknown",
        createdAt: timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        }),
        status: "Queued locally",
    };
}

export class ShopfloorDevicesScreen extends Component {
    static template = "mrp_shopfloor_frontend.ShopfloorDevicesScreen";
    static components = {
        ShopfloorFeedbackBar,
        ShopfloorDeviceActionBar,
        ShopfloorDeviceActionConfirm,
        ShopfloorDeviceActionLog,
        ShopfloorStatusSummary,
        ShopfloorDeviceDetail,
        ShopfloorDeviceList,
        ShopfloorDeviceToolbar,
    };
    static props = {
        devices: Array,
        commands: Array,
        selectedDevice: Object,
        logEntries: Array,
        gatewayRuntimeSummary: [Object, Boolean],
        metrics: [Object, Boolean],
        onOpenDevice: Function,
        onQueueDeviceAction: Function,
    };

    setup() {
        this.state = useState({
            searchText: "",
            groupBy: "state",
            stateFilter: "all",
            actionDraft: null,
            recentActions: [],
        });
    }

    get deviceSummary() {
        return summarizeDevices(this.props.devices, this.props.selectedDevice);
    }

    get deviceSummaryItems() {
        return deviceSummaryItems(this.deviceSummary);
    }

    get visibleDevices() {
        return filterDevices(this.props.devices, this.state.searchText, this.state.stateFilter);
    }

    get groupedDevices() {
        return groupDevices(this.visibleDevices, this.state.groupBy);
    }

    get selectedDeviceVisible() {
        const selectedCode = this.props.selectedDevice?.code;
        if (selectedCode === undefined || selectedCode === null) {
            return null;
        }
        return this.visibleDevices.some((device) => String(device.code) === String(selectedCode));
    }

    get hasActiveFilters() {
        return Boolean(
            String(this.state.searchText || "").trim() ||
                (this.state.groupBy || "state") !== "state" ||
                (this.state.stateFilter || "all") !== "all"
        );
    }

    get visibleDeviceSummary() {
        const summary = summarizeDevices(this.visibleDevices, this.props.selectedDevice);
        return {
            ...summary,
            baseTotal: this.deviceSummary.total,
            baseAttentionCount: this.deviceSummary.attentionCount,
            searchText: String(this.state.searchText || "").trim(),
            stateFilter: this.state.stateFilter || "all",
            stateFilterLabel: stateFilterLabel(this.state.stateFilter || "all"),
            groupBy: this.state.groupBy || "state",
            groupByLabel: groupByLabel(this.state.groupBy || "state"),
            isFiltered: this.hasActiveFilters,
            selectedVisible: this.selectedDeviceVisible,
        };
    }

    get visibleSummaryItems() {
        return deviceSummaryItems(this.visibleDeviceSummary);
    }

    get deviceFeedback() {
        const selectedDevice = this.props.selectedDevice;
        const draft = this.actionDraft;
        if (draft) {
            return {
                label: `Draft ${draft.label || "device action"}`,
                detail: `${draft.deviceName || "Device"} | ${draft.command || "custom"} | ${draft.deviceState || "unknown"}`,
                tone: draft.tone || "info",
            };
        }

        if (this.commandSummary?.total) {
            const feedback = gatewayCommandFeedback(this.commandSummary);
            return {
                label: feedback.label,
                detail: feedback.detail,
                tone: feedback.tone,
            };
        }

        if (selectedDevice && selectedDevice.code !== "DEVICE-EMPTY") {
            return {
                label: selectedDevice.name || "Selected device",
                detail: `${selectedDevice.kind || "Device"} | ${selectedDevice.state || "unknown"} | ${selectedDevice.signal || "no signal"}`,
                tone: deviceStateTone(selectedDevice.state || "unknown"),
            };
        }

        return {
            label: "Device actions",
            detail: "Select a device to preview a local command draft.",
            tone: "secondary",
        };
    }

    get latestRuntimeEntry() {
        return normalizeRuntimeEntry(findLatestRuntimeEntry(this.props.logEntries || []));
    }

    get selectedDeviceActionCandidates() {
        const selectedDevice = this.props.selectedDevice;
        if (!selectedDevice || selectedDevice.code === "DEVICE-EMPTY") {
            return [];
        }
        return buildDeviceActionCandidates(selectedDevice);
    }

    get actionDraft() {
        const draft = this.state.actionDraft;
        if (!draft) {
            return null;
        }
        const selectedCode = this.props.selectedDevice?.code;
        if (selectedCode === undefined || selectedCode === null) {
            return null;
        }
        return String(draft.deviceCode) === String(selectedCode) ? draft : null;
    }

    get recentActions() {
        const selectedCode = this.props.selectedDevice?.code || null;
        if (Array.isArray(this.props.commands) && this.props.commands.length) {
            const orderedCommands = sortGatewayCommands(this.props.commands);
            const matchingCommands = selectedCode
                ? orderedCommands.filter(
                      (item) =>
                          String(item.deviceCode || item.device_code || item.target || "") === String(selectedCode)
                  )
                : orderedCommands;
            return matchingCommands.length ? matchingCommands : orderedCommands;
        }
        return sortGatewayCommands(this.state.recentActions);
    }

    get recentActionCount() {
        return this.recentActions.length;
    }

    get commandSummary() {
        return summarizeGatewayCommands(this.recentActions);
    }

    get commandSummaryItems() {
        return gatewayCommandSummaryItems(this.commandSummary);
    }

    openDevice(ev) {
        this.props.onOpenDevice?.(ev);
    }

    onSearchTextChange(ev) {
        this.state.searchText = typeof ev === "string" ? ev : ev?.target?.value || "";
    }

    onGroupByChange(ev) {
        this.state.groupBy = typeof ev === "string" ? ev : ev?.currentTarget?.dataset?.groupBy || "state";
    }

    onStateFilterChange(ev) {
        this.state.stateFilter =
            typeof ev === "string" ? ev : ev?.currentTarget?.dataset?.stateFilter || "all";
    }

    clearFilters(ev) {
        ev?.preventDefault?.();
        this.state.searchText = "";
        this.state.groupBy = "state";
        this.state.stateFilter = "all";
    }

    selectDeviceAction(action) {
        const selectedDevice = this.props.selectedDevice;
        if (!selectedDevice || selectedDevice.code === "DEVICE-EMPTY" || !action) {
            return;
        }
        this.state.actionDraft = {
            ...action,
            deviceCode: selectedDevice.code || "n/a",
            deviceName: selectedDevice.name || "Unknown device",
            deviceState: selectedDevice.state || "unknown",
            gatewayEntryCode: selectedDevice.entry_code || selectedDevice.entryCode || null,
            selectedVisible: this.selectedDeviceVisible !== false,
            createdAt: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
            }),
        };
    }

    clearDeviceActionDraft(ev) {
        ev?.preventDefault?.();
        this.state.actionDraft = null;
    }

    async confirmDeviceAction(ev) {
        ev?.preventDefault?.();
        const draft = this.actionDraft;
        const selectedDevice = this.props.selectedDevice;
        if (!draft || !selectedDevice || selectedDevice.code === "DEVICE-EMPTY") {
            return;
        }
        if (this.props.onQueueDeviceAction) {
            await this.props.onQueueDeviceAction({
                ...draft,
                deviceCode: draft.deviceCode,
                gatewayEntryCode: draft.gatewayEntryCode,
            });
        } else {
            const entry = createActionEntry(this.props.selectedDevice, draft);
            this.state.recentActions = [entry, ...this.recentActions].slice(0, 5);
        }
        this.state.actionDraft = null;
    }
}
