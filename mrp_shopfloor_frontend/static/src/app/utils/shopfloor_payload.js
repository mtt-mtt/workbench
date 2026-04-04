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

function buildStateMeta(value, keyFn, labelFn, toneFn, fallbackKey) {
    const key = keyFn(value || fallbackKey);
    return {
        key,
        label: labelFn(key),
        tone: toneFn(key),
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
            raw: item,
        };
    }

    const statusKey = commandStateKey(firstValue(item.status, item.state, "queued"));

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
        lastUpdated: firstValue(source.lastUpdated, source.last_updated, null),
    };
}

export function buildResponseSummary(envelope = {}, commandStatus = null, exceptions = []) {
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
    const ok = envelope?.ok !== false && envelope?.error !== true;
    const headline = ok ? "Backend response received" : "Backend response returned an error";
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
    if (exceptions?.length) {
        fragments.push(`${exceptions.length} exception${exceptions.length === 1 ? "" : "s"}`);
    }

    return {
        headline,
        label: headline,
        detail: fragments.length ? fragments.join(" | ") : "Awaiting backend payload",
        state: ok ? "success" : "warning",
        stateKey: ok ? "success" : "warning",
        stateLabel: ok ? "Success" : "Warning",
        stateTone: ok ? "success" : "warning",
        tone: ok ? "success" : "warning",
        ok,
        message: messageText,
        nextPage,
    };
}

function buildTimelineFallback({ responseSummary, commands = [], exceptions = [], activity = [] } = {}) {
    const entries = [];

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
            detail: `${command.type || "command"} - ${command.statusLabel || command.status || "Queued"}`,
            kind: "command",
            status: command.statusTone || command.status || "queued",
            statusKey: command.statusKey || command.status || "queued",
            statusLabel: command.statusLabel || command.status || "Queued",
            statusTone: command.statusTone || command.status || "queued",
            timestamp: command.createdAt || null,
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

    activity.slice(0, 3).forEach((entry, index) => {
        entries.push({
            id: `timeline-activity-${index}`,
            title: entry,
            label: entry,
            detail: null,
            kind: "activity",
            status: "info",
            statusKey: "info",
            statusLabel: "Info",
            statusTone: "info",
            timestamp: null,
        });
    });

    return entries;
}

export function buildSeedTimelineEntries(workstationCode = "WS-000") {
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
        "log_entries",
        "log_entries.items",
        "logs",
        "logs.items",
    ]).map(normalizeTimelineItem);

    const responseSummary = buildResponseSummary(envelopeRoot, buildCommandQueueStatus(commands), exceptions);
    const fallbackActivity = toArray(fallback.activity);
    const logEntries = timeline.length
        ? timeline
        : buildTimelineFallback({
              responseSummary,
              commands,
              exceptions,
              activity: fallbackActivity,
          });

    return {
        queue,
        devices,
        exceptions,
        commands,
        timeline: logEntries,
        responseSummary,
        commandQueueStatus: buildCommandQueueStatus(commands, envelopeRoot?.command_queue_status || data?.command_queue_status || {}),
        metrics: isPlainObject(envelopeRoot.metrics) ? envelopeRoot.metrics : isPlainObject(data.metrics) ? data.metrics : {},
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
