import json

from odoo import _
from odoo import fields


class ShopfloorExecutionService:
    ACTION_STATE_MAP = {
        "boot": "ready",
        "start": "running",
        "pause": "paused",
        "resume": "running",
        "finish": "done",
        "fail": "failed",
        "exception": "failed",
        "device": "draft",
        "command": "draft",
        "custom": "draft",
    }

    def __init__(self, env):
        self.env = env

    def _registry_has_model(self, model_name):
        try:
            self.env[model_name]
            return True
        except KeyError:
            return False

    def _model(self, model_name):
        if not self._registry_has_model(model_name):
            return None
        return self.env[model_name].sudo()

    def _resolve_context(self, payload):
        context = dict(self.env.context)
        context.update({k: v for k, v in payload.items() if v is not None})
        return context

    def _json_dumps(self, value):
        return json.dumps(value, ensure_ascii=False, default=str)

    def _maybe_int(self, value):
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def _build_envelope(self, *, data=None, message=None, next_state=None, commands=None, errors=None):
        return {
            "ok": not errors,
            "data": data,
            "next_state": next_state or {},
            "message": message or {},
            "commands": commands or [],
            "errors": errors or [],
        }

    def _get_workstation_model(self):
        return self._model("shopfloor.workstation")

    def _get_workorder_model(self):
        return self._model("mrp.workorder")

    def _get_session_model(self):
        return self._model("shopfloor.session")

    def _get_gateway_entry_model(self):
        return self._model("gateway.entry")

    def _get_gateway_device_model(self):
        return self._model("gateway.device")

    def _get_gateway_signal_model(self):
        return self._model("gateway.signal")

    def _get_gateway_command_model(self):
        return self._model("gateway.command")

    def _get_exception_model(self):
        return self._model("shopfloor.exception")

    def _get_audit_model(self):
        return self._model("shopfloor.audit.log")

    def _priority_label(self, value):
        mapping = {
            "0": "Normal",
            "1": "Low",
            "2": "High",
            "3": "Urgent",
        }
        if value is None:
            return "Normal"
        return mapping.get(str(value), str(value))

    def _serialize_workstation(self, workstation):
        if not workstation:
            return None
        if isinstance(workstation, dict):
            return workstation
        return {
            "id": workstation.id,
            "name": workstation.display_name,
            "code": workstation.code,
            "profile_code": workstation.profile_id.code if workstation.profile_id else None,
            "app_code": workstation.app_id.code if workstation.app_id else None,
            "gateway_ref": workstation.gateway_ref,
            "printer_ref": workstation.default_printer_ref,
            "location_ref": workstation.location_ref,
            "resolved": True,
        }

    def _serialize_workorder(self, workorder):
        if not workorder:
            return None
        return {
            "id": workorder.id,
            "name": workorder.display_name,
            "state": workorder.state,
            "production_id": workorder.production_id.id if workorder.production_id else None,
            "production_name": workorder.production_id.name if workorder.production_id else None,
            "workcenter": workorder.workcenter_id.display_name if workorder.workcenter_id else None,
            "operation": workorder.operation_id.display_name if workorder.operation_id else None,
            "qty_production": workorder.qty_production,
            "qty_produced": workorder.qty_produced,
            "qty_remaining": workorder.qty_remaining,
            "source": "mrp.workorder",
        }

    def _serialize_session(self, session):
        if not session:
            return None
        return {
            "id": session.id,
            "name": session.display_name,
            "code": session.code,
            "state": session.state,
            "workstation_code": session.workstation_id.code if session.workstation_id else None,
            "profile_code": session.profile_id.code if session.profile_id else None,
            "user_name": session.user_id.name if session.user_id else None,
            "start_date": session.start_date,
            "end_date": session.end_date,
            "last_action_at": session.last_action_at,
        }

    def _serialize_execution(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "state": record.state,
            "action_type": record.action_type,
            "app_code": record.app_code,
            "workstation_code": record.workstation_code,
            "gateway_entry_code": record.gateway_entry_code,
            "session_ref": record.session_ref,
            "command_key": record.command_key,
            "gateway_command_code": record.gateway_command_code,
            "exception_code": record.exception_code,
            "idempotency_key": record.idempotency_key,
            "reference": record.reference,
        }

    def _serialize_gateway_command(self, record):
        return {
            "id": record.id,
            "code": record.code,
            "name": record.name,
            "state": record.state,
            "entry_code": record.entry_id.code if record.entry_id else None,
            "device_code": record.device_id.code if record.device_id else None,
            "signal_code": record.signal_id.code if record.signal_id else None,
            "command_type": record.command_type,
            "idempotency_key": record.idempotency_key,
            "attempt_count": record.attempt_count,
        }

    def _serialize_workorder_queue_item(self, record):
        quantity = record.qty_production or (record.production_id.product_qty if record.production_id else 0)
        done = record.qty_produced or 0
        status = {
            "progress": "in_progress",
            "cancel": "cancelled",
        }.get(record.state, record.state)
        return {
            "id": record.id,
            "workorder_id": record.id,
            "production_id": record.production_id.id if record.production_id else None,
            "name": record.production_id.name if record.production_id else record.display_name,
            "product": record.product_id.display_name if record.product_id else None,
            "workorder": record.name,
            "quantity": quantity,
            "done": done,
            "priority": self._priority_label(record.production_id.priority if record.production_id else None),
            "status": status,
            "progress": f"{done} / {quantity}",
            "reference": record.production_id.name if record.production_id else record.name,
            "stage": record.operation_id.display_name if record.operation_id else None,
            "message": record.production_state,
            "source": "mrp.workorder",
        }

    def _serialize_gateway_device(self, record):
        signal = record.signal_ids.sorted(lambda value: (value.sequence, value.id))[:1]
        signal = signal[0] if signal else False
        signal_value = None
        if signal:
            signal_value = signal.value_text
            if signal_value in (None, "") and signal.value_number not in (None, False):
                signal_value = signal.value_number
        channel_parts = [part for part in [record.protocol, record.address] if part]
        return {
            "id": record.id,
            "code": record.code,
            "name": record.name,
            "kind": record.device_type or record.protocol or "Device",
            "state": record.state,
            "signal": signal.technical_key if signal and signal.technical_key else signal.code if signal else None,
            "value": signal_value,
            "last_seen": record.last_seen_at,
            "channel": "/".join(channel_parts) if channel_parts else None,
            "location": record.workstation_ref or record.app_ref,
            "entry_code": record.entry_id.code if record.entry_id else None,
            "source": "gateway.device",
        }

    def _serialize_exception(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "state": record.state,
            "severity": record.severity,
            "exception_type": record.exception_type,
            "message": record.message,
            "details": record.details,
            "resolution_note": record.resolution_note,
            "raised_at": record.raised_at,
            "resolved_at": record.resolved_at,
            "execution_id": record.execution_id.id if record.execution_id else None,
            "app_code": record.app_code,
            "workstation_code": record.workstation_code,
            "gateway_entry_code": record.gateway_entry_code,
            "gateway_command_code": record.gateway_command_code,
            "session_ref": record.session_ref,
        }

    def _normalize_exception_state(self, payload):
        state = str(payload.get("state") or "").strip().lower()
        state_aliases = {
            "acknowledged": "ack",
            "approved": "open",
            "claim": "open",
            "claimed": "open",
            "close": "closed",
            "closed": "closed",
            "cancel": "closed",
            "cancelled": "closed",
            "escalate": "blocked",
            "follow_up": "new",
            "follow-up": "new",
            "open": "open",
            "blocked": "blocked",
            "resolved": "resolved",
            "new": "new",
        }
        if state:
            return state_aliases.get(state, state)
        action = str(payload.get("exception_action") or payload.get("transition") or payload.get("action") or "").strip().lower()
        action_aliases = {
            "claim": "open",
            "close": "closed",
            "escalate": "blocked",
            "follow_up": "new",
            "follow-up": "new",
        }
        return action_aliases.get(action, "new")

    def _exception_terminal_states(self):
        return {"resolved", "closed", "cancelled"}

    def _exception_update_values(self, context, execution, payload, command=None):
        severity = payload.get("severity") or "medium"
        state = self._normalize_exception_state(payload)
        message = payload.get("message") or payload.get("text") or "Execution exception"
        entry_code = payload.get("gateway_entry_code") or context.get("gateway_entry_code") or context.get("gateway_ref")
        command_code = None
        if command:
            command_code = command.code if hasattr(command, "code") else command.get("code")
        elif payload.get("gateway_command_code"):
            command_code = payload.get("gateway_command_code")
        values = {
            "execution_id": execution.id,
            "exception_type": payload.get("exception_type") or payload.get("exception_kind") or "custom",
            "severity": severity,
            "state": state,
            "app_code": context.get("app_code"),
            "workstation_code": context.get("workstation_code"),
            "gateway_entry_code": entry_code,
            "gateway_command_code": command_code,
            "session_ref": context.get("session_ref") or context.get("session_id"),
            "message": message,
            "payload_data": self._json_dumps(payload),
            "details": payload.get("details") or payload.get("reason") or payload.get("note") or "",
            "resolution_note": payload.get("resolution_note") or "",
        }
        if state in self._exception_terminal_states():
            values["resolved_at"] = fields.Datetime.now()
        else:
            values["resolved_at"] = False
        if payload.get("name"):
            values["name"] = payload.get("name")
        return {key: value for key, value in values.items() if value is not None}

    def _search_exception_candidates(self, context, execution, payload, command=None):
        ExceptionModel = self._get_exception_model()
        if ExceptionModel is None:
            return None

        exception_id = self._maybe_int(payload.get("exception_id") or payload.get("exception_record_id"))
        if exception_id:
            return ExceptionModel.browse(exception_id).exists()

        command_code = None
        if command:
            command_code = command.code if hasattr(command, "code") else command.get("code")
        command_code = command_code or payload.get("gateway_command_code") or context.get("gateway_command_code")

        search_domains = []
        if execution and execution.id:
            search_domains.append([("execution_id", "=", execution.id)])
        if command_code:
            search_domains.append([("gateway_command_code", "=", command_code)])

        scoped_domain = []
        if context.get("session_ref") or context.get("session_id"):
            scoped_domain.append(("session_ref", "=", str(context.get("session_ref") or context.get("session_id"))))
        if context.get("workstation_code"):
            scoped_domain.append(("workstation_code", "=", context.get("workstation_code")))
        if context.get("app_code"):
            scoped_domain.append(("app_code", "=", context.get("app_code")))
        if scoped_domain:
            search_domains.append(scoped_domain)

        if payload.get("message"):
            search_domains.append([("message", "=", payload.get("message"))])

        for domain in search_domains:
            records = ExceptionModel.search(domain, order="id desc", limit=5)
            if records:
                for record in records:
                    if record.state not in self._exception_terminal_states():
                        return record
                return records[0]
        return None

    def _audit_exception_transition(self, context, execution, exception, payload, transition_state, created=False):
        event_code_map = {
            "open": "shopfloor.exception.claimed",
            "ack": "shopfloor.exception.acknowledged",
            "blocked": "shopfloor.exception.escalated",
            "resolved": "shopfloor.exception.resolved",
            "closed": "shopfloor.exception.closed",
            "new": "shopfloor.exception.follow_up",
        }
        event_code = event_code_map.get(transition_state, "shopfloor.exception.updated")
        return self._audit(
            event_type="exception",
            event_code=event_code,
            context=context,
            execution=execution,
            result={
                "id": exception.id,
                "state": exception.state,
                "severity": exception.severity,
                "created": created,
            },
            payload=payload,
            severity=exception.severity or payload.get("severity") or "warning",
        )

    def _apply_exception_transition(self, exception, context, execution, payload, command=None):
        values = self._exception_update_values(context, execution, payload, command=command)
        exception.write(values)
        self._audit_exception_transition(
            context,
            execution,
            exception,
            payload,
            values.get("state") or exception.state,
            created=False,
        )
        return exception

    def _serialize_timeline_entry(self, record):
        result_detail = record.result or record.note or record.message
        return {
            "id": record.id,
            "title": record.message or record.event_code or record.name,
            "detail": result_detail,
            "kind": record.event_type,
            "status": record.severity,
            "timestamp": record.event_at,
            "source": "shopfloor.audit.log",
        }

    def _serialize_audit_hint(self, values):
        return {key: values.get(key) for key in values if values.get(key) is not None}

    def _resolve_workstation(self, context):
        workstation_code = context.get("workstation_code")
        if not workstation_code:
            return None
        Workstation = self._get_workstation_model()
        if Workstation is None:
            return {"code": workstation_code, "resolved": False}
        workstation = Workstation.search([("code", "=", workstation_code)], limit=1)
        if not workstation:
            return {"code": workstation_code, "resolved": False}
        return self._serialize_workstation(workstation)

    def _resolve_session(self, context):
        Session = self._get_session_model()
        if Session is None:
            return None
        session_ref = context.get("session_ref") or context.get("session_id")
        workstation_code = context.get("workstation_code")
        domain = []
        if session_ref:
            domain.append(("code", "=", str(session_ref)))
        if workstation_code:
            domain.append(("workstation_id.code", "=", workstation_code))
        session = Session.search(domain, limit=1) if domain else False
        if not session and workstation_code:
            workstation = self._get_workstation_model().search([("code", "=", workstation_code)], limit=1) if self._get_workstation_model() else False
            if workstation and workstation.current_session_id:
                session = workstation.current_session_id
        return self._serialize_session(session) if session else None

    def _latest_execution(self, context):
        Execution = self.env["shopfloor.execution"].sudo()
        domain = []
        workstation_code = context.get("workstation_code")
        session_ref = context.get("session_ref") or context.get("session_id")
        if workstation_code:
            domain.append(("workstation_code", "=", workstation_code))
        if session_ref:
            domain.append(("session_ref", "=", str(session_ref)))
        record = Execution.search(domain, limit=1) if domain else Execution.search([], limit=1)
        return self._serialize_execution(record) if record else None

    def _resolve_workorder(self, context, payload):
        Workorder = self._get_workorder_model()
        if Workorder is None:
            return None

        workorder_id = self._maybe_int(
            payload.get("workorder_id")
            or context.get("workorder_id")
            or payload.get("execution_workorder_id")
        )
        if workorder_id:
            workorder = Workorder.browse(workorder_id).exists()
            if workorder:
                return workorder

        production_id = self._maybe_int(payload.get("production_id") or context.get("production_id"))
        if production_id:
            workorder = Workorder.search([("production_id", "=", production_id)], limit=1, order="sequence, id")
            if workorder:
                return workorder

        candidates = [
            payload.get("workorder_ref"),
            payload.get("reference"),
            context.get("workorder_ref"),
            context.get("reference"),
            payload.get("command_key"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            domain = ["|", ("name", "=", str(candidate)), ("production_id.name", "=", str(candidate))]
            workorder = Workorder.search(domain, limit=1, order="sequence, id")
            if workorder:
                return workorder

        return None

    def _search_workorders(self, context, limit=8):
        Workorder = self._get_workorder_model()
        if Workorder is None:
            return []
        domain = [("state", "in", ["ready", "progress", "blocked"])]
        workorder_id = self._maybe_int(context.get("workorder_id"))
        production_id = self._maybe_int(context.get("production_id"))
        reference = context.get("reference")
        if workorder_id:
            domain.append(("id", "=", workorder_id))
        elif production_id:
            domain.append(("production_id", "=", production_id))
        elif reference:
            domain = ["|", ("production_id.name", "=", str(reference)), ("name", "=", str(reference))] + domain
        records = Workorder.search(domain, limit=limit, order="date_start asc, id asc")
        return [self._serialize_workorder_queue_item(record) for record in records]

    def _apply_workorder_action(self, workorder, action):
        if not workorder:
            return None, "No work order could be resolved for this action."

        workorder = workorder.with_user(self.env.user)
        try:
            if action == "start":
                workorder.button_start()
            elif action == "pause":
                workorder.button_pending()
            elif action == "finish":
                workorder.action_mark_as_done()
            else:
                return None, f"Unsupported work order action: {action}."
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)

        return workorder, None

    def _search_devices(self, context, limit=8):
        Device = self._get_gateway_device_model()
        if Device is None:
            return []
        domain = []
        workstation_code = context.get("workstation_code")
        app_code = context.get("app_code")
        if workstation_code and "workstation_ref" in Device._fields:
            domain.append(("workstation_ref", "=", workstation_code))
        if app_code and "app_ref" in Device._fields:
            domain.append(("app_ref", "=", app_code))
        records = Device.search(domain, limit=limit, order="sequence, id") if domain else Device.search([], limit=limit, order="sequence, id")
        return [self._serialize_gateway_device(record) for record in records]

    def _search_timeline(self, context, limit=12):
        Audit = self._get_audit_model()
        if Audit is None:
            return []
        domain = []
        workstation_code = context.get("workstation_code")
        session_ref = context.get("session_ref") or context.get("session_id")
        if workstation_code:
            domain.append(("workstation_code", "=", workstation_code))
        if session_ref:
            domain.append(("session_ref", "=", str(session_ref)))
        records = Audit.search(domain, limit=limit, order="event_at desc, id desc")
        return [self._serialize_timeline_entry(record) for record in records]

    def _build_metrics(self, queue, devices, exceptions, commands):
        online_states = {"ready", "degraded", "running", "active", "ok", "draft"}
        return {
            "pendingJobs": len([item for item in queue if item.get("status") not in {"done", "cancelled"}]),
            "activeExceptions": len([item for item in exceptions if item.get("state") not in {"resolved", "cancelled", "closed"}]),
            "deviceOnline": len([item for item in devices if item.get("state") in online_states]),
            "commandTotal": len(commands),
        }

    def _build_state_snapshot(self, context):
        queue = self._search_workorders(context)
        devices = self._search_devices(context)
        recent_commands = self._recent_records("gateway.command", context, self._serialize_gateway_command)
        recent_exceptions = self._recent_records("shopfloor.exception", context, self._serialize_exception)
        timeline = self._search_timeline(context)
        metrics = self._build_metrics(queue, devices, recent_exceptions, recent_commands)
        return {
            "queue": queue,
            "devices": devices,
            "exceptions": recent_exceptions,
            "recent_exceptions": recent_exceptions,
            "commands": recent_commands,
            "recent_commands": recent_commands,
            "timeline": timeline,
            "metrics": metrics,
        }

    def _recent_records(self, model_name, context, serializer, limit=5):
        model = self._model(model_name)
        if not model:
            return []
        domain = []
        workstation_code = context.get("workstation_code")
        app_code = context.get("app_code")
        session_ref = context.get("session_ref") or context.get("session_id")
        workstation_field = "workstation_code" if "workstation_code" in model._fields else "workstation_ref" if "workstation_ref" in model._fields else None
        app_field = "app_code" if "app_code" in model._fields else "app_ref" if "app_ref" in model._fields else None
        if workstation_field and workstation_code:
            domain.append((workstation_field, "=", workstation_code))
        if app_field and app_code:
            domain.append((app_field, "=", app_code))
        if "session_ref" in model._fields:
            if session_ref:
                domain.append(("session_ref", "=", str(session_ref)))
        records = model.search(domain, limit=limit, order="id desc")
        return [serializer(record) for record in records]

    def _resolve_gateway_entry(self, context, payload):
        Entry = self._get_gateway_entry_model()
        if Entry is None:
            return None
        candidates = [
            payload.get("gateway_entry_code"),
            context.get("gateway_entry_code"),
            context.get("gateway_ref"),
            context.get("gateway_code"),
            context.get("workstation_code"),
            context.get("app_code"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            entry = Entry.search([("code", "=", str(candidate))], limit=1)
            if entry:
                return entry
            if "workstation_ref" in Entry._fields:
                entry = Entry.search([("workstation_ref", "=", str(candidate))], limit=1)
                if entry:
                    return entry
            if "app_ref" in Entry._fields:
                entry = Entry.search([("app_ref", "=", str(candidate))], limit=1)
                if entry:
                    return entry
        Device = self._get_gateway_device_model()
        if Device is not None:
            for candidate in (
                payload.get("selected_device_code"),
                payload.get("device_code"),
                payload.get("gateway_device_code"),
                context.get("selected_device_code"),
                context.get("device_code"),
            ):
                if not candidate:
                    continue
                device = Device.search([("code", "=", str(candidate))], limit=1)
                if not device and "external_ref" in Device._fields:
                    device = Device.search([("external_ref", "=", str(candidate))], limit=1)
                if device and device.entry_id:
                    return device.entry_id
        return None

    def _resolve_gateway_device(self, entry, payload, request):
        Device = self._get_gateway_device_model()
        if Device is None:
            return None
        candidates = [
            request.get("selected_device_code"),
            request.get("device_code"),
            request.get("device_ref"),
            request.get("external_ref"),
            payload.get("selected_device_code"),
            payload.get("device_code"),
            payload.get("gateway_device_code"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            domain = [("entry_id", "=", entry.id), ("code", "=", str(candidate))]
            device = Device.search(domain, limit=1)
            if device:
                return device
            if "external_ref" in Device._fields:
                device = Device.search([("entry_id", "=", entry.id), ("external_ref", "=", str(candidate))], limit=1)
                if device:
                    return device
        return None

    def _resolve_gateway_signal(self, entry, device, payload, request):
        Signal = self._get_gateway_signal_model()
        if Signal is None:
            return None
        candidates = [
            request.get("signal_code"),
            request.get("signal_ref"),
            request.get("technical_key"),
            payload.get("signal_code"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            domain = [("entry_id", "=", entry.id), ("code", "=", str(candidate))]
            if device:
                domain.append(("device_id", "=", device.id))
            signal = Signal.search(domain, limit=1)
            if signal:
                return signal
            if "technical_key" in Signal._fields:
                domain = [("entry_id", "=", entry.id), ("technical_key", "=", str(candidate))]
                if device:
                    domain.append(("device_id", "=", device.id))
                signal = Signal.search(domain, limit=1)
                if signal:
                    return signal
        return None

    def _normalize_command_request(self, value, fallback_action, payload=None):
        if isinstance(value, str):
            return {
                "name": value,
                "command_type": value,
                "command_key": value,
                "payload": {},
            }
        request = dict(value or {})
        request.setdefault("command_type", request.get("type") or fallback_action or "custom")
        request.setdefault("name", request.get("title") or request["command_type"])
        request.setdefault("command_key", request.get("code") or request["command_type"])
        request.setdefault("payload", request.get("payload") or {})
        if payload:
            request.setdefault(
                "device_code",
                request.get("device_code")
                or request.get("selected_device_code")
                or payload.get("selected_device_code")
                or payload.get("device_code")
                or payload.get("gateway_device_code"),
            )
            request.setdefault(
                "selected_device_code",
                request.get("selected_device_code") or payload.get("selected_device_code") or payload.get("device_code"),
            )
            request.setdefault(
                "entry_code",
                request.get("entry_code") or payload.get("gateway_entry_code") or payload.get("gateway_ref") or payload.get("gateway_code"),
            )
        return request

    def _build_default_device_command_request(self, payload):
        action = (payload.get("action") or payload.get("event") or "device").lower()
        device_code = payload.get("selected_device_code") or payload.get("device_code") or payload.get("gateway_device_code")
        command_key = payload.get("command_key") or payload.get("device_command_key") or f"{action}:{device_code or payload.get('gateway_entry_code') or 'device'}"
        label = payload.get("command_label") or payload.get("label") or payload.get("message") or payload.get("name") or "Device command"
        return {
            "name": label,
            "command_type": payload.get("command_type") or payload.get("device_command_type") or action,
            "command_key": command_key,
            "payload": {
                "action": action,
                "device_code": device_code,
                "selected_device_code": payload.get("selected_device_code"),
                "message": payload.get("message"),
                "details": payload.get("details"),
                "note": payload.get("note"),
            },
            "device_code": device_code,
            "selected_device_code": payload.get("selected_device_code") or device_code,
            "signal_code": payload.get("signal_code") or payload.get("gateway_signal_code"),
            "entry_code": payload.get("gateway_entry_code") or payload.get("gateway_ref") or payload.get("gateway_code"),
            "idempotency_key": payload.get("idempotency_key"),
            "request_text": payload.get("request_text"),
        }

    def _extract_command_requests(self, payload):
        requests = []
        for key in ("commands", "device_commands", "device_actions"):
            value = payload.get(key)
            if isinstance(value, list):
                requests.extend(self._normalize_command_request(item, payload.get("action"), payload) for item in value if item)
            elif isinstance(value, dict):
                requests.append(self._normalize_command_request(value, payload.get("action"), payload))
        for key in ("device_command", "command", "device_action"):
            value = payload.get(key)
            if value:
                requests.append(self._normalize_command_request(value, payload.get("action"), payload))
        if not requests and (payload.get("action") or "").lower() in {"device", "command"}:
            requests.append(self._build_default_device_command_request(payload))
        return requests

    def _make_unique_code(self, model, base_code, suffix_index=0):
        code = str(base_code or "COMMAND").strip()
        if suffix_index:
            code = f"{code}-{suffix_index}"
        candidate = code
        index = suffix_index
        while model.search([("code", "=", candidate)], limit=1):
            index += 1
            candidate = f"{code}-{index}"
        return candidate

    def _create_gateway_command(self, context, execution, request, sequence_index):
        Command = self._get_gateway_command_model()
        if Command is None:
            return None, "gateway.command model is not installed"
        idempotency_key = request.get("idempotency_key") or execution.idempotency_key or context.get("idempotency_key")
        if idempotency_key:
            existing = Command.search([("idempotency_key", "=", str(idempotency_key))], limit=1)
            if existing:
                return existing, None
        entry = self._resolve_gateway_entry(context, request)
        if not entry:
            return None, "No gateway entry found for command request"
        device = self._resolve_gateway_device(entry, context, request)
        signal = self._resolve_gateway_signal(entry, device, context, request)
        base_code = request.get("code") or request.get("command_key") or execution.command_key or execution.reference or execution.name
        code = self._make_unique_code(Command, base_code, sequence_index)
        payload_value = request.get("payload") or {}
        diagnostic_payload = {
            "execution_id": execution.id,
            "execution_name": execution.name,
            "workstation_code": context.get("workstation_code"),
            "session_ref": context.get("session_ref") or context.get("session_id"),
            "request": request,
        }
        values = {
            "name": request.get("name") or request.get("command_type") or code,
            "code": code,
            "state": "queued",
            "entry_id": entry.id,
            "device_id": device.id if device else False,
            "signal_id": signal.id if signal else False,
            "workstation_ref": context.get("workstation_code"),
            "app_ref": context.get("app_code"),
            "command_type": request.get("command_type") or request.get("type") or "custom",
            "idempotency_key": str(idempotency_key) if idempotency_key else False,
            "payload_json": self._json_dumps(payload_value),
            "request_text": request.get("request_text") or self._json_dumps(request),
            "response_text": request.get("response_text") or "",
            "error_message": "",
            "attempt_count": 0,
            "diagnostic_state": self._json_dumps(diagnostic_payload),
        }
        command = Command.create(values)
        self._audit(
            event_type="command",
            event_code="gateway.command.queued",
            context=context,
            execution=execution,
            gateway_command=command,
            result={"state": command.state, "code": command.code},
            payload=request,
            severity="low",
        )
        return command, None

    def _create_exception(self, context, execution, payload, command=None):
        ExceptionModel = self._get_exception_model()
        if ExceptionModel is None:
            return None
        values = self._exception_update_values(context, execution, payload, command=command)
        values["name"] = payload.get("name") or f"{execution.name}-exception"
        exception = ExceptionModel.create(values)
        self._audit_exception_transition(
            context,
            execution,
            exception,
            payload,
            values.get("state") or exception.state,
            created=True,
        )
        return exception

    def _audit(self, event_type, event_code, context, execution=None, gateway_command=None, result=None, payload=None, severity="info"):
        Audit = self._get_audit_model()
        if Audit is None:
            return None
        values = self._serialize_audit_hint(
            {
                "name": event_code,
                "event_type": event_type,
                "event_code": event_code,
                "workstation_code": context.get("workstation_code"),
                "session_ref": context.get("session_ref") or context.get("session_id"),
                "execution_ref": execution.name if execution else context.get("execution_ref"),
                "gateway_command_ref": gateway_command.code if gateway_command else context.get("gateway_command_ref"),
                "actor": self.env.user.name,
                "payload": self._json_dumps(payload if payload is not None else context),
                "result": self._json_dumps(result or {}),
                "severity": severity,
            }
        )
        try:
            return Audit.create(values)
        except Exception:
            return None

    def _action_state(self, action):
        return self.ACTION_STATE_MAP.get(action, "draft")

    def _latest_command_state(self, commands):
        if not commands:
            return None
        return commands[0].get("state") if isinstance(commands[0], dict) else None

    def _latest_command_code(self, commands):
        if not commands:
            return None
        return commands[0].get("code") if isinstance(commands[0], dict) else None

    def _write_execution_result(self, execution, context, payload, commands, exception, errors, response):
        action = (payload.get("action") or payload.get("event") or "custom").lower()
        values = {
            "state": "failed" if (errors or exception) else self._action_state(action),
            "gateway_entry_code": context.get("gateway_entry_code") or context.get("gateway_ref") or context.get("workstation_code"),
            "gateway_command_code": self._latest_command_code(commands),
            "exception_code": exception.name if exception else None,
            "response_data": self._json_dumps(response),
            "note": payload.get("note") or (errors[0]["message"] if errors else None),
        }
        if execution.command_key is None and commands:
            values["command_key"] = self._latest_command_code(commands)
        execution.write({key: value for key, value in values.items() if value is not None})
        return execution

    def boot_payload(self, payload):
        context = self._resolve_context(payload)
        workstation = self._resolve_workstation(context)
        session = self._resolve_session(context)
        execution = self._latest_execution(context)
        workorder = self._resolve_workorder(context, payload)
        snapshot = self._build_state_snapshot(context)
        data = {
            "context": {
                "uid": self.env.user.id,
                "user_name": self.env.user.name,
                "company_id": self.env.company.id,
                "lang": self.env.lang,
                "tz": self.env.user.tz,
                "workstation": workstation,
                "session": session,
                "session_ref": context.get("session_ref") or context.get("session_id"),
            },
            "execution": execution,
            "workorder": self._serialize_workorder(workorder),
            **snapshot,
            "capabilities": {
                "can_create_execution": True,
                "can_report_exception": True,
                "can_print": True,
                "can_queue_gateway_command": bool(self._get_gateway_command_model()),
            },
        }
        response = self._build_envelope(
            data=data,
            message={
                "type": "success",
                "text": "Shopfloor execution boot payload ready",
            },
            next_state={
                "page": payload.get("route") or "dashboard",
                "reload": ["execution", "exceptions", "devices"],
            },
            commands=[],
            errors=[],
        )
        response.update(
            {
                "context": data["context"],
                "execution": execution,
                "workorder": self._serialize_workorder(workorder),
                "capabilities": data["capabilities"],
                **snapshot,
            }
        )
        self._audit(
            event_type="execution",
            event_code="shopfloor.execution.boot",
            context=context,
            execution=None,
            result={"page": response["next_state"]["page"]},
            payload=payload,
            severity="low",
        )
        return response

    def state_payload(self, payload):
        context = self._resolve_context(payload)
        workstation = self._resolve_workstation(context)
        session = self._resolve_session(context)
        execution = self._latest_execution(context)
        workorder = self._resolve_workorder(context, payload)
        snapshot = self._build_state_snapshot(context)
        data = {
            "context": {
                "uid": self.env.user.id,
                "user_name": self.env.user.name,
                "company_id": self.env.company.id,
                "lang": self.env.lang,
                "tz": self.env.user.tz,
                "workstation": workstation,
                "session": session,
                "session_ref": context.get("session_ref") or context.get("session_id"),
            },
            "execution": execution,
            "workorder": self._serialize_workorder(workorder),
            **snapshot,
        }
        response = self._build_envelope(
            data=data,
            message={"type": "success", "text": "Shopfloor state payload ready"},
            next_state={"page": payload.get("route") or "dashboard", "reload": ["queue", "devices", "exceptions", "execution"]},
            commands=snapshot["commands"],
            errors=[],
        )
        response.update(
            {
                "context": data["context"],
                "execution": execution,
                "workorder": self._serialize_workorder(workorder),
                **snapshot,
            }
        )
        return response

    def apply_action(self, payload):
        context = self._resolve_context(payload)
        action = (payload.get("action") or payload.get("event") or "custom").lower()
        workorder = self._resolve_workorder(context, payload)
        action_errors = []
        if action in {"start", "pause", "finish"}:
            workorder, error = self._apply_workorder_action(workorder, action)
            if error:
                action_errors.append({"type": "workorder", "message": error})
        execution = self._create_or_update_execution(context, action, payload)
        if workorder:
            execution.write({
                "workorder_id": workorder.id,
                "production_id": workorder.production_id.id if workorder.production_id else False,
                "reference": workorder.production_id.name if workorder.production_id else workorder.name,
            })
        commands = []
        command_errors = []
        if not action_errors:
            commands, command_errors = self._queue_gateway_commands(context, execution, payload)
        exception = None
        errors = list(action_errors) + list(command_errors)
        if action == "exception" or payload.get("exception"):
            exception, exception_errors = self._report_exception(context, execution, payload, commands)
            errors.extend(exception_errors)
        response = self._build_envelope(
            data=self._serialize_execution(execution),
            message=self._build_message(action, commands, exception, errors),
            next_state=self._build_next_state(action, commands, exception, errors),
            commands=commands,
            errors=errors,
        )
        execution = self._write_execution_result(execution, context, payload, commands, exception, errors, response)
        snapshot = self._build_state_snapshot(context)
        response["data"] = {
            "execution": self._serialize_execution(execution),
            "workorder": self._serialize_workorder(workorder),
            **snapshot,
        }
        response.update(
            {
                "execution": self._serialize_execution(execution),
                "workorder": self._serialize_workorder(workorder),
                "exception": self._serialize_exception(exception) if exception else None,
                **snapshot,
                "context": {
                    "workstation_code": context.get("workstation_code"),
                    "session_ref": context.get("session_ref") or context.get("session_id"),
                    "app_code": context.get("app_code"),
                },
            }
        )
        return response

    def report_exception(self, payload):
        payload = dict(payload or {})
        payload["action"] = "exception"
        payload["exception"] = payload.get("exception") or True
        return self.apply_action(payload)

    def _build_message(self, action, commands, exception, errors):
        if errors:
            return {
                "type": "warning",
                "text": errors[0]["message"],
            }
        if exception:
            return {
                "type": "danger",
                "text": "Exception recorded and linked to the execution.",
            }
        if commands:
            if action in {"device", "command"}:
                return {
                    "type": "success",
                    "text": f"Device action accepted and {len(commands)} gateway command(s) queued.",
                }
            return {
                "type": "success",
                "text": f"Execution {action} accepted and {len(commands)} gateway command(s) queued.",
            }
        if action in {"device", "command"}:
            return {
                "type": "success",
                "text": "Device action accepted.",
            }
        return {
            "type": "success",
            "text": f"Execution {action} accepted.",
        }

    def _build_next_state(self, action, commands, exception, errors):
        if action in {"device", "command"}:
            page = "devices"
        elif exception or action == "exception":
            page = "exceptions"
        else:
            page = "execution"
        if errors and not exception and action not in {"device", "command"}:
            page = "execution"
        reload = ["execution", "exceptions"]
        if action in {"device", "command"}:
            reload.insert(0, "devices")
        if commands:
            reload.append("gateway")
        return {"page": page, "reload": reload}

    def _create_or_update_execution(self, context, action, payload):
        Execution = self.env["shopfloor.execution"].sudo()
        values = {
            "action_type": action,
            "state": self._action_state(action),
            "app_code": context.get("app_code"),
            "workstation_code": context.get("workstation_code"),
            "gateway_entry_code": context.get("gateway_entry_code") or context.get("gateway_ref"),
            "session_ref": context.get("session_ref") or context.get("session_id"),
            "command_key": payload.get("command_key"),
            "idempotency_key": payload.get("idempotency_key"),
            "reference": payload.get("reference") or payload.get("request_ref") or payload.get("command_key"),
            "payload_data": self._json_dumps(payload),
            "response_data": "",
            "note": payload.get("note"),
        }
        production_id = self._maybe_int(payload.get("production_id"))
        workorder_id = self._maybe_int(payload.get("workorder_id"))
        if production_id:
            values["production_id"] = production_id
        if workorder_id:
            values["workorder_id"] = workorder_id
        execution_id = self._maybe_int(payload.get("execution_id"))
        if execution_id:
            execution = Execution.browse(execution_id).exists()
            if execution:
                execution.write({key: value for key, value in values.items() if value is not None})
                return execution
        idempotency_key = values.get("idempotency_key")
        if idempotency_key:
            existing = Execution.search([("idempotency_key", "=", str(idempotency_key))], limit=1)
            if existing:
                existing.write({key: value for key, value in values.items() if value is not None})
                return existing
        if not values.get("name"):
            values["name"] = payload.get("name") or payload.get("reference") or payload.get("command_key") or _("New")
        return Execution.create(values)

    def _queue_gateway_commands(self, context, execution, payload):
        requests = self._extract_command_requests(payload)
        if not requests:
            return [], []
        commands = []
        errors = []
        for index, request in enumerate(requests, start=1):
            command, error = self._create_gateway_command(context, execution, request, index)
            if command:
                commands.append(self._serialize_gateway_command(command))
            if error:
                errors.append({"type": "gateway", "message": error})
        return commands, errors

    def _report_exception(self, context, execution, payload, commands):
        command_record = commands[0] if commands else None
        ExceptionModel = self._get_exception_model()
        if ExceptionModel is None:
            return None, [{"type": "exception", "message": "Exception model is not installed."}]

        exception = self._search_exception_candidates(context, execution, payload, command=command_record)
        if exception:
            exception = self._apply_exception_transition(exception, context, execution, payload, command=command_record)
        else:
            exception = self._create_exception(context, execution, payload, command=command_record)
        if not exception:
            return None, [{"type": "exception", "message": "Exception model is not installed."}]
        return exception, []
