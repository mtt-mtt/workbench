/** @odoo-module **/

import { buildQueueContext, matchQueueSelection } from "../utils/shopfloor_payload";

export function createShopfloorSelectionService() {
    function getSelectedQueueItem(state) {
        const byId =
            state.queue.find((item) => String(item.id) === String(state.selectedQueueId)) ||
            state.queue.find((item) => String(item.queue_id) === String(state.selectedQueueId)) ||
            null;
        if (byId) {
            return byId;
        }
        const byContext = state.selectedQueueContext ? matchQueueSelection(state.queue, state.selectedQueueContext) : null;
        return byContext || state.queue[0] || null;
    }

    function syncSelectedQueueContext(state) {
        const selectedQueueItem = getSelectedQueueItem(state);
        state.selectedQueueContext = buildQueueContext(selectedQueueItem);
        if (selectedQueueItem) {
            state.selectedQueueId = selectedQueueItem.id || selectedQueueItem.queue_id || state.selectedQueueId;
        }
        return state.selectedQueueContext;
    }

    function selectQueueItem(state, queueId) {
        state.selectedQueueId = queueId;
        state.selectedQueueContext = buildQueueContext(
            state.queue.find((item) => String(item.id) === String(queueId) || String(item.queue_id) === String(queueId)) || null
        );
        return state.selectedQueueContext;
    }

    function selectDevice(state, deviceCode) {
        state.selectedDeviceCode = deviceCode;
        return state.selectedDeviceCode;
    }

    return {
        getSelectedQueueItem,
        syncSelectedQueueContext,
        selectQueueItem,
        selectDevice,
    };
}
