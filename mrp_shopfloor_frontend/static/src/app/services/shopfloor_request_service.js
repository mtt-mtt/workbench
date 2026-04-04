/** @odoo-module **/

export function createShopfloorRequestService(dataService, router, stateService, selectionService, storeState) {
    function buildRequestContext(extra = {}) {
        const selectedQueueItem = selectionService.getSelectedQueueItem(storeState);
        const selectedContext = storeState.selectedQueueContext || stateService.buildQueueContext(selectedQueueItem);
        const selectedRaw = selectedQueueItem?.raw || {};
        return {
            app_code: storeState.execution.app_code,
            workstation_code: storeState.workstation.code,
            session_ref: storeState.sessionRef,
            execution_id: storeState.execution.id,
            route: router.state.route,
            queue_id: extra.queue_id || selectedContext?.queue_id || selectedContext?.id || selectedQueueItem?.queue_id || selectedQueueItem?.id || null,
            workorder_id: extra.workorder_id || selectedContext?.workorder_id || selectedRaw.workorder_id || null,
            production_id: extra.production_id || selectedContext?.production_id || selectedRaw.production_id || null,
            workorder_ref: extra.workorder_ref || selectedContext?.workorder_ref || selectedQueueItem?.workorder_ref || selectedQueueItem?.reference || null,
            production_ref: extra.production_ref || selectedContext?.production_ref || selectedQueueItem?.production_ref || null,
            reference: extra.reference || storeState.execution.reference || selectedContext?.reference || selectedQueueItem?.reference || null,
            selected_device_code: extra.selected_device_code || storeState.selectedDeviceCode || null,
            selection_context: selectedContext ? { ...selectedContext } : null,
        };
    }

    function buildExecutionPayload(extra = {}) {
        const requestContext = buildRequestContext(extra);
        return {
            ...requestContext,
            command_key: extra.command_key || storeState.execution.command_key || `${extra.action || "custom"}-${Date.now()}`,
            idempotency_key: extra.idempotency_key || `${extra.action || "custom"}-${Date.now()}`,
        };
    }

    async function boot(payload = {}) {
        storeState.loading = true;
        storeState.bootError = null;
        try {
            return await dataService.boot({
                ...buildRequestContext(payload),
                ...payload,
            });
        } finally {
            storeState.loading = false;
        }
    }

    async function refreshState(extra = {}) {
        storeState.loading = true;
        storeState.bootError = null;
        try {
            return await dataService.state({
                route: router.state.route,
                ...buildExecutionPayload(extra),
                ...extra,
            });
        } finally {
            storeState.loading = false;
        }
    }

    async function submitAction(action, extra = {}) {
        const payload = {
            action,
            ...buildExecutionPayload({ ...extra, action }),
            note: extra.note || null,
            state: extra.state || null,
            exception_action: extra.exception_action || extra.action || null,
            exception_id: extra.exception_id || null,
            gateway_command_code: extra.gateway_command_code || null,
            exception_type: extra.exception_type || null,
            severity: extra.severity || null,
            details: extra.details || null,
            message: extra.message || null,
        };
        return dataService.action(payload);
    }

    return {
        buildRequestContext,
        buildExecutionPayload,
        boot,
        refreshState,
        submitAction,
    };
}
