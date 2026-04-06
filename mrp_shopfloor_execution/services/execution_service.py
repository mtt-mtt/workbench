import json
from datetime import datetime

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

    def _safe_json(self, value):
        if isinstance(value, dict):
            return value
        if not value:
            return {}
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _first_value(self, *values):
        for value in values:
            if value not in (None, "", False):
                return value
        return None

    def _print_execution_summary(self, record):
        request_payload = self._safe_json(record.payload_json)
        request_text_payload = self._safe_json(record.request_text)
        response_payload = self._safe_json(record.response_text)
        diagnostic_state = self._safe_json(record.diagnostic_state)
        print_execution = (
            diagnostic_state.get("print_execution")
            or response_payload.get("print_execution")
            or request_payload.get("print_execution")
            or request_text_payload.get("print_execution")
            or {}
        )
        if not print_execution:
            return {}
        driver_ready = (
            print_execution.get("driver_ready")
            if "driver_ready" in print_execution
            else diagnostic_state.get("driver_ready")
            if "driver_ready" in diagnostic_state
            else response_payload.get("driver_ready")
            if "driver_ready" in response_payload
            else request_payload.get("driver_ready")
            if "driver_ready" in request_payload
            else request_text_payload.get("driver_ready")
            if "driver_ready" in request_text_payload
            else None
        )
        driver_capabilities = self._first_value(
            print_execution.get("driver_capabilities"),
            diagnostic_state.get("driver_capabilities"),
            response_payload.get("driver_capabilities"),
            request_payload.get("driver_capabilities"),
            request_text_payload.get("driver_capabilities"),
        )
        if not isinstance(driver_capabilities, dict):
            driver_capabilities = {}
        return {
            "state": self._first_value(print_execution.get("state"), print_execution.get("execution_state")),
            "execution_state": self._first_value(print_execution.get("execution_state"), print_execution.get("state")),
            "status": self._first_value(print_execution.get("status"), print_execution.get("result")),
            "result": self._first_value(print_execution.get("result"), print_execution.get("status")),
            "service_mode": self._first_value(print_execution.get("service_mode"), print_execution.get("execution_mode")),
            "service_endpoint": self._first_value(print_execution.get("service_endpoint"), print_execution.get("service_url")),
            "service_job_id": print_execution.get("service_job_id"),
            "service_status_code": print_execution.get("service_status_code"),
            "service_error_code": self._first_value(print_execution.get("service_error_code"), response_payload.get("service_error_code")),
            "service_error_detail": self._first_value(print_execution.get("service_error_detail"), response_payload.get("service_error_detail")),
            "service_completed_at": self._first_value(print_execution.get("service_completed_at"), response_payload.get("service_completed_at")),
            "service_accepted_at": self._first_value(print_execution.get("service_accepted_at"), response_payload.get("service_accepted_at")),
            "service_document_url": self._first_value(print_execution.get("service_document_url"), response_payload.get("service_document_url")),
            "service_preview_url": self._first_value(print_execution.get("service_preview_url"), response_payload.get("service_preview_url")),
            "service_printer_code": self._first_value(print_execution.get("service_printer_code"), response_payload.get("service_printer_code")),
            "printer_status": print_execution.get("printer_status"),
            "printed_copies": self._first_value(
                print_execution.get("printed_copies"),
                diagnostic_state.get("printed_copies"),
                response_payload.get("printed_copies"),
                request_payload.get("printed_copies"),
            ),
            "printer_name": self._first_value(print_execution.get("printer_name"), request_payload.get("printer_name")),
            "request_id": self._first_value(print_execution.get("request_id"), request_payload.get("request_id")),
            "result_text": self._first_value(
                print_execution.get("result_text"),
                response_payload.get("response_text"),
                response_payload.get("message"),
                diagnostic_state.get("message"),
            ),
            "service_summary": self._first_value(
                print_execution.get("summary"),
                response_payload.get("summary"),
                diagnostic_state.get("summary"),
            ),
            "error_message": self._first_value(
                print_execution.get("error_message"),
                response_payload.get("error_message"),
                diagnostic_state.get("error_message"),
                response_payload.get("error"),
                response_payload.get("message"),
                diagnostic_state.get("message"),
            ),
            "driver_origin": self._first_value(
                print_execution.get("driver_origin"),
                diagnostic_state.get("driver_origin"),
                response_payload.get("driver_origin"),
                request_payload.get("driver_origin"),
                request_text_payload.get("driver_origin"),
            ),
            "driver_ready": driver_ready,
            "driver_label": self._first_value(
                print_execution.get("driver_label"),
                diagnostic_state.get("driver_label"),
                response_payload.get("driver_label"),
                request_payload.get("driver_label"),
                request_text_payload.get("driver_label"),
            ),
            "driver_type": self._first_value(
                print_execution.get("driver_type"),
                diagnostic_state.get("driver_type"),
                response_payload.get("driver_type"),
                request_payload.get("driver_type"),
                request_text_payload.get("driver_type"),
            ),
            "driver_path": self._first_value(
                print_execution.get("driver_path"),
                diagnostic_state.get("driver_path"),
                response_payload.get("driver_path"),
                request_payload.get("driver_path"),
                request_text_payload.get("driver_path"),
            ),
            "driver_capabilities": driver_capabilities,
            "driver_diagnostics": {
                "origin": self._first_value(
                    print_execution.get("driver_origin"),
                    diagnostic_state.get("driver_origin"),
                    response_payload.get("driver_origin"),
                    request_payload.get("driver_origin"),
                    request_text_payload.get("driver_origin"),
                ),
                "ready": driver_ready,
                "label": self._first_value(
                    print_execution.get("driver_label"),
                    diagnostic_state.get("driver_label"),
                    response_payload.get("driver_label"),
                    request_payload.get("driver_label"),
                    request_text_payload.get("driver_label"),
                ),
                "type": self._first_value(
                    print_execution.get("driver_type"),
                    diagnostic_state.get("driver_type"),
                    response_payload.get("driver_type"),
                    request_payload.get("driver_type"),
                    request_text_payload.get("driver_type"),
                ),
                "path": self._first_value(
                    print_execution.get("driver_path"),
                    diagnostic_state.get("driver_path"),
                    response_payload.get("driver_path"),
                    request_payload.get("driver_path"),
                    request_text_payload.get("driver_path"),
                ),
                "status_polling_supported": driver_capabilities.get("status_polling_supported"),
            },
            "service_request": print_execution.get("service_request") or {},
            "service_response": print_execution.get("service_response") or {},
            "print_plan": self._first_value(
                print_execution.get("print_plan"),
                diagnostic_state.get("print_plan"),
                response_payload.get("print_plan"),
                request_payload.get("print_plan"),
            )
            or {},
            "barcode_validation": self._first_value(
                print_execution.get("barcode_validation"),
                diagnostic_state.get("barcode_validation"),
                response_payload.get("barcode_validation"),
                request_payload.get("barcode_validation"),
            )
            or {},
        }

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

    def _get_gateway_runtime_adapter_model(self):
        return self._model("gateway.runtime.adapter")

    def _get_gateway_runtime_issue_model(self):
        return self._model("gateway.runtime.issue")

    def _get_gateway_runtime_event_model(self):
        return self._model("gateway.runtime.event")

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
        request_payload = self._safe_json(record.payload_json)
        request_summary = self._safe_json(record.request_text)
        response_summary = self._safe_json(record.response_text)
        diagnostic_summary = self._safe_json(record.diagnostic_state)
        print_execution = self._print_execution_summary(record)
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
            "payload_json": request_payload,
            "request_summary": request_summary or request_payload,
            "response_summary": response_summary,
            "diagnostic_summary": diagnostic_summary,
            "print_execution": print_execution,
            "summary": {
                "state": record.state,
                "request_summary": request_summary or request_payload,
                "response_summary": response_summary,
                "diagnostic_summary": diagnostic_summary,
                "print_execution": print_execution,
                "print_plan": print_execution.get("print_plan") or {},
                "barcode_validation": print_execution.get("barcode_validation") or {},
            },
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
        payload = self._safe_json(record.payload)
        result = self._safe_json(record.result)
        summary = result.get("summary") or {}
        print_execution = result.get("print_execution") or summary.get("print_execution") or payload.get("print_execution") or {}
        print_plan = result.get("print_plan") or summary.get("print_plan") or print_execution.get("print_plan") or payload.get("print_plan") or {}
        barcode_validation = (
            result.get("barcode_validation")
            or summary.get("barcode_validation")
            or print_execution.get("barcode_validation")
            or payload.get("barcode_validation")
            or {}
        )
        result_detail = (
            " | ".join(
                        [
                            item
                            for item in [
                                f"mode {print_execution.get('service_mode')}" if print_execution.get("service_mode") else None,
                                f"job {print_execution.get('service_job_id')}" if print_execution.get("service_job_id") else None,
                                f"driver {print_execution.get('driver_origin')}" if print_execution.get("driver_origin") else None,
                                (
                                    f"driver-ready {print_execution.get('driver_ready')}"
                                    if print_execution.get("driver_ready") is not None
                                    else None
                                ),
                                f"printer {print_execution.get('printer_status')}" if print_execution.get("printer_status") else None,
                                f"{print_execution.get('printed_copies')} copies"
                                if print_execution.get("printed_copies") not in (None, "", False)
                                else None,
                            ]
                    if item
                ]
            )
            or record.result
            or record.note
            or record.message
        )
        return {
            "id": record.id,
            "title": record.message or record.event_code or record.name,
            "detail": result_detail,
            "kind": record.event_type,
            "status": record.severity,
            "timestamp": record.event_at,
            "gateway_command_ref": record.gateway_command_ref,
            "print_execution": print_execution,
            "print_plan": print_plan,
            "barcode_validation": barcode_validation,
            "summary": {
                "gateway_command_ref": record.gateway_command_ref,
                "print_execution": print_execution,
                "print_plan": print_plan,
                "barcode_validation": barcode_validation,
                "payload": payload,
                "result": result,
            },
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
        Workstation = self._get_workstation_model()
        domain = []
        if session_ref:
            domain.append(("code", "=", str(session_ref)))
        if workstation_code:
            domain.append(("workstation_id.code", "=", workstation_code))
        session = Session.search(domain, limit=1) if domain else False
        if not session and workstation_code and Workstation is not None:
            workstation = Workstation.search([("code", "=", workstation_code)], limit=1)
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

    def _runtime_issue_status(self, record):
        state = str(getattr(record, "state", "") or "new").strip().lower()
        severity = str(getattr(record, "severity", "") or "medium").strip().lower()
        if state in {"resolved", "closed", "ignored"}:
            return "success", _("Resolved")
        if severity in {"critical", "high"} or state in {"blocked"}:
            return "danger", _("Danger")
        if state in {"open", "new", "in_progress"}:
            return "warning", _("Warning")
        return "info", _("Info")

    def _serialize_runtime_issue_activity(self, record):
        status, status_label = self._runtime_issue_status(record)
        detail_parts = [
            record.detail or None,
            record.payload_summary or None,
            record.repair_summary or None,
            f"adapter {record.adapter_code}" if record.adapter_code else None,
            f"action {record.recommended_action_key}" if record.recommended_action_key else None,
        ]
        detail = " | ".join(part for part in detail_parts if part) or record.message or record.name
        timestamp = record.resolved_at or record.last_seen_at or False
        return {
            "id": f"runtime-issue-{record.id}",
            "title": record.message or record.name or _("Runtime issue"),
            "label": record.message or record.name or _("Runtime issue"),
            "detail": detail,
            "kind": "runtime",
            "status": status,
            "statusKey": status,
            "statusLabel": status_label,
            "statusTone": status,
            "timestamp": timestamp,
            "summary": {
                "issue_id": record.id,
                "issue_key": record.issue_key,
                "state": record.state,
                "severity": record.severity,
                "adapter_code": record.adapter_code,
                "adapter_type": record.adapter_type,
                "recommended_action_key": record.recommended_action_key,
                "payload_summary": record.payload_summary,
                "repair_summary": record.repair_summary,
                "resolved_at": record.resolved_at,
                "last_seen_at": record.last_seen_at,
            },
            "source": "gateway.runtime.issue",
        }

    def _runtime_edge_action_snapshot(self, record):
        payload = self._safe_json(record.normalized_json) or self._safe_json(record.payload_json)
        if not isinstance(payload, dict):
            payload = {}
        note = self._safe_json(getattr(record, "note", None))
        if not isinstance(note, dict):
            note = {}
        signal_kind = str(payload.get("signal_kind") or "").strip().lower()
        source_signal = str(getattr(record, "source_signal", "") or "").strip().lower()
        if signal_kind != "edge_cache_action" and "edge_cache_action" not in source_signal:
            return None
        action_name = str(payload.get("edge_cache_action") or getattr(record, "registry_action", "") or "").strip().lower()
        issue_key = str(payload.get("issue_key") or "").strip() or None
        if not action_name:
            if issue_key and issue_key.endswith(":edge_dead_letter"):
                action_name = "review_dead_letter"
            elif issue_key and issue_key.endswith(":edge_replay"):
                action_name = "replay"
        if action_name not in {"replay", "review_dead_letter"}:
            return None
        return {
            "action_name": action_name,
            "issue_key": issue_key,
            "source_payload_id": getattr(record, "source_payload_id", None) or payload.get("source_payload_id"),
            "edge_fetch_count": int(getattr(record, "edge_fetch_count", 0) or 0),
            "last_edge_fetch_at": getattr(record, "last_edge_fetch_at", False) or payload.get("last_edge_fetch_at"),
            "payload": payload,
            "note": note,
        }

    def _runtime_edge_action_title(self, record, snapshot):
        state = str(getattr(record, "state", "") or "new").strip().lower()
        action_name = snapshot.get("action_name")
        action_label = _("Edge replay") if action_name == "replay" else _("Dead-letter review")
        if state == "processed":
            return _("%s processed") % action_label
        if state == "processing":
            return _("%s processing") % action_label
        if state == "failed":
            return _("%s failed") % action_label
        if state == "cancelled":
            return _("%s cancelled") % action_label
        return _("%s requested") % action_label

    def _runtime_event_status(self, record):
        edge_action = self._runtime_edge_action_snapshot(record)
        state = str(getattr(record, "state", "") or "new").strip().lower()
        severity = str(getattr(record, "severity", "") or "medium").strip().lower()
        event_kind = str(getattr(record, "event_kind", "") or "custom").strip().lower()
        if edge_action:
            if state == "failed":
                return "danger", _("Failed")
            if state == "processed":
                return "success", _("Processed")
            if state == "processing":
                return "info", _("Processing")
            if state == "cancelled":
                return "info", _("Cancelled")
            if edge_action.get("action_name") == "review_dead_letter":
                return "warning", _("Pending")
            return "info", _("Pending")
        if state == "failed":
            return "danger", _("Failed")
        if severity in {"critical", "high"}:
            return "danger", _("Danger")
        if event_kind in {"alarm", "diagnostic"}:
            return "warning", _("Warning")
        if state == "processed":
            return "success", _("Processed")
        if state == "cancelled":
            return "info", _("Cancelled")
        return "info", _("Info")

    def _runtime_protocol_runtime_snapshot(self, record):
        def _as_dict(value):
            payload = self._safe_json(value)
            return payload if isinstance(payload, dict) else {}

        def _has_runtime_markers(value):
            if not isinstance(value, dict) or not value:
                return False
            return any(
                key in value
                for key in (
                    "state",
                    "summary",
                    "count",
                    "entry_count",
                    "detail",
                    "state_counts",
                    "kind_counts",
                    "protocol_runtime_state",
                    "protocol_runtime_summary",
                    "protocol_runtime_count",
                    "protocol_runtime_entry_count",
                    "protocol_runtime_state_counts",
                    "protocol_runtime_kind_counts",
                )
            )

        def _format_counts(counts):
            if not isinstance(counts, dict) or not counts:
                return ""
            parts = []
            for key in sorted(counts):
                value = counts.get(key)
                if value in (None, "", False):
                    continue
                parts.append(f"{key}={value}")
            return ", ".join(parts)

        payload = _as_dict(record.normalized_json) or _as_dict(record.payload_json)
        if not payload:
            return None

        candidates = []
        for key in ("protocol_runtime", "edge_protocol_runtime"):
            candidate = _as_dict(payload.get(key))
            if _has_runtime_markers(candidate):
                candidates.append((key, candidate))

        edge_diagnostics = _as_dict(payload.get("edge_diagnostics"))
        if edge_diagnostics:
            if _has_runtime_markers(edge_diagnostics):
                candidates.append(("edge_diagnostics", edge_diagnostics))
            candidate = _as_dict(edge_diagnostics.get("protocol_runtime"))
            if _has_runtime_markers(candidate):
                candidates.append(("edge_diagnostics.protocol_runtime", candidate))

        for key in ("summary", "data", "diagnostic_summary", "diagnostic_state"):
            container = _as_dict(payload.get(key))
            if not container:
                continue
            if _has_runtime_markers(container):
                candidates.append((key, container))
            for nested_key in ("protocol_runtime", "edge_protocol_runtime"):
                candidate = _as_dict(container.get(nested_key))
                if _has_runtime_markers(candidate):
                    candidates.append((f"{key}.{nested_key}", candidate))

        if _has_runtime_markers(payload):
            candidates.append(("payload", payload))

        runtime_source = None
        runtime = None
        for source, candidate in candidates:
            runtime_source = source
            runtime = candidate
            break
        if not runtime:
            return None

        state = str(runtime.get("state") or runtime.get("protocol_runtime_state") or "unknown").strip().lower() or "unknown"
        summary = runtime.get("summary") or runtime.get("protocol_runtime_summary") or _("No protocol runtime data")
        detail = runtime.get("detail") or runtime.get("protocol_runtime_detail") or summary
        count = int(runtime.get("count") or runtime.get("protocol_runtime_count") or 0)
        entry_count = int(runtime.get("entry_count") or runtime.get("protocol_runtime_entry_count") or 0)
        state_counts = self._safe_json(runtime.get("state_counts") or runtime.get("protocol_runtime_state_counts"))
        kind_counts = self._safe_json(runtime.get("kind_counts") or runtime.get("protocol_runtime_kind_counts"))
        state_counts_summary = (
            runtime.get("state_counts_summary")
            or runtime.get("protocol_runtime_state_counts_summary")
            or _format_counts(state_counts)
        )
        kind_counts_summary = (
            runtime.get("kind_counts_summary")
            or runtime.get("protocol_runtime_kind_counts_summary")
            or _format_counts(kind_counts)
        )
        if state in {"error", "failed"}:
            status = "danger"
            status_label = _("Error")
            title = _("Protocol runtime error")
        elif state in {"attention", "warning"}:
            status = "warning"
            status_label = _("Attention")
            title = _("Protocol runtime attention")
        elif state in {"ready", "healthy", "ok"}:
            status = "success"
            status_label = _("Ready")
            title = _("Protocol runtime ready")
        else:
            status = "info"
            status_label = _("Info")
            title = _("Protocol runtime update")
        detail_parts = [
            detail if detail != title else None,
            _("state %s") % state if state else None,
            _("items %s") % count if count else None,
            _("entries %s") % entry_count if entry_count else None,
            _("state counts %s") % state_counts_summary if state_counts_summary else None,
            _("kind counts %s") % kind_counts_summary if kind_counts_summary else None,
        ]
        detail = " | ".join(str(part) for part in detail_parts if part) or summary or title
        return {
            "source": runtime_source,
            "state": state,
            "summary": summary,
            "detail": detail,
            "count": count,
            "entry_count": entry_count,
            "state_counts_summary": state_counts_summary,
            "kind_counts_summary": kind_counts_summary,
            "status": status,
            "status_label": status_label,
            "title": title,
        }

    def _serialize_runtime_event_activity(self, record):
        status, status_label = self._runtime_event_status(record)
        edge_action = self._runtime_edge_action_snapshot(record)
        protocol_runtime = self._runtime_protocol_runtime_snapshot(record)
        payload = self._safe_json(record.normalized_json) or self._safe_json(record.payload_json)
        payload_bits = []
        if isinstance(payload, dict):
            payload_bits.extend(
                [
                    payload.get("summary"),
                    payload.get("message"),
                    payload.get("signal"),
                    payload.get("ui_refresh_hint"),
                ]
            )
        title = record.message or record.name or _("Runtime event")
        if protocol_runtime:
            status = protocol_runtime.get("status") or status
            status_label = protocol_runtime.get("status_label") or status_label
            title = protocol_runtime.get("title") or title
            payload_bits = [
                protocol_runtime.get("summary"),
                protocol_runtime.get("detail") if protocol_runtime.get("detail") != protocol_runtime.get("summary") else None,
                _("state %s") % protocol_runtime.get("state") if protocol_runtime.get("state") else None,
                _("items %s") % protocol_runtime.get("count") if protocol_runtime.get("count") else None,
                _("entries %s") % protocol_runtime.get("entry_count") if protocol_runtime.get("entry_count") else None,
                _("state counts %s") % protocol_runtime.get("state_counts_summary") if protocol_runtime.get("state_counts_summary") else None,
                _("kind counts %s") % protocol_runtime.get("kind_counts_summary") if protocol_runtime.get("kind_counts_summary") else None,
            ]
        if edge_action:
            title = self._runtime_edge_action_title(record, edge_action)
            fetch_count = edge_action.get("edge_fetch_count") or 0
            note_summary = edge_action.get("note", {}).get("summary")
            payload_bits = [
                _("state %s") % (record.state or _("new")),
                _("result %s") % (record.result or _("pending")),
                note_summary if isinstance(note_summary, str) else json.dumps(note_summary, ensure_ascii=False) if note_summary else None,
                _("fetches %s") % fetch_count,
                _("trace %s") % edge_action.get("source_payload_id") if edge_action.get("source_payload_id") else None,
                _("issue %s") % edge_action.get("issue_key") if edge_action.get("issue_key") else None,
                _("last fetch %s") % edge_action.get("last_edge_fetch_at") if edge_action.get("last_edge_fetch_at") else None,
            ]
        message_text = record.message or None
        if protocol_runtime and message_text and message_text.strip().lower() in {"runtime event", "runtime"}:
            message_text = None
        detail_parts = [
            None if edge_action else message_text,
            None if edge_action else record.result or None,
            f"{record.event_kind} / {record.change_kind}" if record.event_kind or record.change_kind else None,
            record.discovery_state or None,
            record.source_signal or None,
            record.ui_refresh_hint or None,
            f"adapter {record.adapter_id.code}" if record.adapter_id else None,
            f"command {record.command_id.code}" if record.command_id else None,
        ]
        detail_parts.extend(bit for bit in payload_bits if bit)
        detail = " | ".join(str(part) for part in detail_parts if part) or record.name or _("Runtime event")
        timestamp = (
            record.processed_at or edge_action.get("last_edge_fetch_at") or record.occurred_at or False
            if edge_action
            else record.occurred_at or record.processed_at or False
        )
        protocol_runtime_merge_key = self._protocol_runtime_timeline_dedupe_key(record, protocol_runtime)
        return {
            "id": f"runtime-event-{record.id}",
            "title": title,
            "label": title,
            "detail": detail,
            "kind": "runtime",
            "status": status,
            "statusKey": status,
            "statusLabel": status_label,
            "statusTone": status,
            "timestamp": timestamp,
            "summary": {
                "event_id": record.id,
                "event_code": record.code,
                "event_kind": record.event_kind,
                "severity": record.severity,
                "state": record.state,
                "change_kind": record.change_kind,
                "discovery_state": record.discovery_state,
                "source_signal": record.source_signal,
                "result": record.result,
                "adapter_code": record.adapter_id.code if record.adapter_id else None,
                "entry_code": record.entry_id.code if record.entry_id else None,
                "device_code": record.device_id.code if record.device_id else None,
                "command_code": record.command_id.code if record.command_id else None,
                "occurred_at": record.occurred_at,
                "processed_at": record.processed_at,
                "registry_action": record.registry_action,
                "source_payload_id": record.source_payload_id,
                "edge_fetch_count": record.edge_fetch_count,
                "last_edge_fetch_at": record.last_edge_fetch_at,
                "protocol_runtime_source": protocol_runtime.get("source") if protocol_runtime else None,
                "protocol_runtime_state": protocol_runtime.get("state") if protocol_runtime else None,
                "protocol_runtime_summary": protocol_runtime.get("summary") if protocol_runtime else None,
                "protocol_runtime_detail": protocol_runtime.get("detail") if protocol_runtime else None,
                "protocol_runtime_count": protocol_runtime.get("count") if protocol_runtime else None,
                "protocol_runtime_entry_count": protocol_runtime.get("entry_count") if protocol_runtime else None,
                "protocol_runtime_state_counts_summary": protocol_runtime.get("state_counts_summary") if protocol_runtime else None,
                "protocol_runtime_kind_counts_summary": protocol_runtime.get("kind_counts_summary") if protocol_runtime else None,
                "protocol_runtime_merge_key": protocol_runtime_merge_key,
                "protocol_runtime_dedupe_key": protocol_runtime_merge_key,
                "issue_key": edge_action.get("issue_key") if edge_action else None,
                "edge_cache_action": edge_action.get("action_name") if edge_action else None,
            },
            "source": "gateway.runtime.event",
        }

    def _adapter_matches_context(self, adapter, context):
        if not adapter:
            return False
        workstation_code = context.get("workstation_code")
        app_code = context.get("app_code")
        entry_code = context.get("gateway_entry_code") or context.get("gateway_ref") or context.get("gateway_code")
        adapter_entry = getattr(adapter, "entry_id", None)
        if entry_code and (not adapter_entry or str(adapter_entry.code) != str(entry_code)):
            return False
        if workstation_code:
            workstation_match = bool(
                (getattr(adapter, "workstation_id", None) and str(adapter.workstation_id.code) == str(workstation_code))
                or (adapter_entry and getattr(adapter_entry, "workstation_ref", None) and str(adapter_entry.workstation_ref) == str(workstation_code))
            )
            if not workstation_match:
                return False
        if app_code:
            app_match = bool(
                (getattr(adapter, "app_id", None) and str(adapter.app_id.code) == str(app_code))
                or (adapter_entry and getattr(adapter_entry, "app_ref", None) and str(adapter_entry.app_ref) == str(app_code))
            )
            if not app_match:
                return False
        return True

    def _runtime_event_matches_context(self, record, context):
        workstation_code = context.get("workstation_code")
        app_code = context.get("app_code")
        entry_code = context.get("gateway_entry_code") or context.get("gateway_ref") or context.get("gateway_code")
        session_ref = context.get("session_ref") or context.get("session_id")
        entry = getattr(record, "entry_id", None)
        if entry_code and (not entry or str(entry.code) != str(entry_code)):
            return False
        if workstation_code:
            workstation_match = bool(
                (getattr(record, "workstation_id", None) and str(record.workstation_id.code) == str(workstation_code))
                or (entry and getattr(entry, "workstation_ref", None) and str(entry.workstation_ref) == str(workstation_code))
            )
            if not workstation_match:
                return False
        if app_code:
            app_match = bool(
                (getattr(record, "app_id", None) and str(record.app_id.code) == str(app_code))
                or (entry and getattr(entry, "app_ref", None) and str(entry.app_ref) == str(app_code))
            )
            if not app_match:
                return False
        if session_ref and getattr(record, "session_ref", None) and str(record.session_ref) != str(session_ref):
            return False
        return True

    def _search_runtime_issue_activity(self, context, limit=6):
        Issue = self._get_gateway_runtime_issue_model()
        if Issue is None:
            return []
        records = Issue.search([], limit=max(limit * 6, 24), order="last_seen_at desc, id desc")
        result = []
        for record in records:
            if self._adapter_matches_context(getattr(record, "adapter_id", None), context):
                result.append(self._serialize_runtime_issue_activity(record))
            if len(result) >= limit:
                break
        return result

    def _search_runtime_event_activity(self, context, limit=6):
        Event = self._get_gateway_runtime_event_model()
        if Event is None:
            return []
        records = Event.search([], limit=max(limit * 6, 24), order="occurred_at desc, id desc")
        result = []
        seen_keys = set()
        for record in records:
            if self._runtime_event_matches_context(record, context):
                entry = self._serialize_runtime_event_activity(record)
                dedupe_key = self._timeline_entry_dedupe_key(entry)
                if dedupe_key and dedupe_key in seen_keys:
                    continue
                if dedupe_key:
                    seen_keys.add(dedupe_key)
                result.append(entry)
            if len(result) >= limit:
                break
        return result

    def _normalize_timeline_dedupe_token(self, value):
        if value in (None, False):
            return ""
        if isinstance(value, dict):
            value = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
        elif isinstance(value, (list, tuple, set)):
            value = json.dumps(list(value), sort_keys=True, ensure_ascii=False, default=str)
        else:
            value = str(value)
        return " ".join(value.split()).strip().lower()

    def _protocol_runtime_timeline_dedupe_key(self, record_or_summary, protocol_runtime=None):
        summary = protocol_runtime if isinstance(protocol_runtime, dict) else record_or_summary if isinstance(record_or_summary, dict) else {}
        if not isinstance(summary, dict) or not summary:
            return None
        adapter_code = self._normalize_timeline_dedupe_token(summary.get("adapter_code"))
        entry_code = self._normalize_timeline_dedupe_token(summary.get("entry_code"))
        runtime_source = self._normalize_timeline_dedupe_token(summary.get("protocol_runtime_source"))
        runtime_state = self._normalize_timeline_dedupe_token(summary.get("protocol_runtime_state"))
        runtime_summary = self._normalize_timeline_dedupe_token(
            summary.get("protocol_runtime_summary") or summary.get("protocol_runtime_detail")
        )
        runtime_count = self._normalize_timeline_dedupe_token(summary.get("protocol_runtime_count"))
        runtime_entry_count = self._normalize_timeline_dedupe_token(summary.get("protocol_runtime_entry_count"))
        state_counts_summary = self._normalize_timeline_dedupe_token(summary.get("protocol_runtime_state_counts_summary"))
        kind_counts_summary = self._normalize_timeline_dedupe_token(summary.get("protocol_runtime_kind_counts_summary"))
        if not adapter_code and record_or_summary is not None and protocol_runtime is not None:
            adapter = getattr(record_or_summary, "adapter_id", None)
            entry = getattr(record_or_summary, "entry_id", None)
            adapter_code = self._normalize_timeline_dedupe_token(adapter.code if adapter else None)
            entry_code = self._normalize_timeline_dedupe_token(entry.code if entry else None)
            runtime_source = runtime_source or self._normalize_timeline_dedupe_token("gateway.runtime.event")
        if not any(
            (
                adapter_code,
                entry_code,
                runtime_source,
                runtime_state,
                runtime_summary,
                runtime_count,
                runtime_entry_count,
                state_counts_summary,
                kind_counts_summary,
            )
        ):
            return None
        parts = [
            "protocol-runtime",
            f"adapter:{adapter_code or 'any'}",
        ]
        if entry_code:
            parts.append(f"entry:{entry_code}")
        if runtime_source:
            parts.append(f"source:{runtime_source}")
        parts.append(f"state:{runtime_state or 'unknown'}")
        if runtime_summary:
            parts.append(f"summary:{runtime_summary}")
        parts.append(f"count:{runtime_count or '0'}")
        parts.append(f"entries:{runtime_entry_count or '0'}")
        if state_counts_summary:
            parts.append(f"states:{state_counts_summary}")
        if kind_counts_summary:
            parts.append(f"kinds:{kind_counts_summary}")
        return "|".join(parts)

    def _timeline_entry_sort_key(self, entry):
        raw_value = entry.get("timestamp") or entry.get("createdAt") or entry.get("created_at")
        try:
            value = fields.Datetime.to_datetime(raw_value) if raw_value else None
        except Exception:
            value = None
        return value or datetime.min

    def _timeline_entry_dedupe_key(self, entry):
        if not isinstance(entry, dict):
            return None
        if entry.get("source") != "gateway.runtime.event":
            return entry.get("id")
        summary = entry.get("summary") or {}
        edge_cache_action = summary.get("edge_cache_action")
        source_payload_id = summary.get("source_payload_id")
        state = summary.get("state")
        if edge_cache_action and source_payload_id and state:
            return f"runtime-edge-action:{source_payload_id}:{edge_cache_action}:{state}"
        protocol_runtime_key = summary.get("protocol_runtime_dedupe_key") or summary.get("protocol_runtime_merge_key")
        if not protocol_runtime_key:
            protocol_runtime_key = self._protocol_runtime_timeline_dedupe_key(summary)
        if protocol_runtime_key:
            return protocol_runtime_key
        return entry.get("id")

    def _merge_timeline_entries(self, *groups, limit=12):
        merged = []
        for group in groups:
            for entry in group or []:
                merged.append(entry)
        merged.sort(key=self._timeline_entry_sort_key, reverse=True)
        result = []
        seen_keys = set()
        for entry in merged:
            dedupe_key = self._timeline_entry_dedupe_key(entry)
            if dedupe_key and dedupe_key in seen_keys:
                continue
            if dedupe_key:
                seen_keys.add(dedupe_key)
            result.append(entry)
            if len(result) >= limit:
                break
        return result

    def _build_metrics(self, queue, devices, exceptions, commands):
        online_states = {"ready", "degraded", "running", "active", "ok", "draft"}
        return {
            "pendingJobs": len([item for item in queue if item.get("status") not in {"done", "cancelled"}]),
            "activeExceptions": len([item for item in exceptions if item.get("state") not in {"resolved", "cancelled", "closed"}]),
            "deviceOnline": len([item for item in devices if item.get("state") in online_states]),
            "commandTotal": len(commands),
        }

    def _build_gateway_runtime_summary(self, context):
        Adapter = self._get_gateway_runtime_adapter_model()
        if Adapter is None:
            return {}
        adapters = Adapter.search([], order="sequence, id").filtered(lambda record: self._adapter_matches_context(record, context))
        adapter_count = len(adapters)
        issue_total = sum(adapters.mapped("driver_issue_count"))
        issue_open = sum(adapters.mapped("open_driver_issue_count"))
        issue_adapters = len(adapters.filtered(lambda record: record.driver_issue_count))
        open_issue_adapters = len(adapters.filtered(lambda record: record.open_driver_issue_count))
        driver_ready = len(adapters.filtered(lambda record: record.driver_diagnostic_state == "ready"))
        driver_attention = len(adapters.filtered(lambda record: record.driver_diagnostic_state == "attention"))
        driver_error = len(adapters.filtered(lambda record: record.driver_diagnostic_state == "error"))
        driver_unknown = len(adapters.filtered(lambda record: record.driver_diagnostic_state in (False, None, "unknown")))
        replay_pending = sum(adapters.mapped("edge_replay_pending_count"))
        replay_due = sum(adapters.mapped("edge_replay_due_count"))
        replay_scheduled = sum(adapters.mapped("edge_replay_scheduled_count"))
        replay_coalesced = sum(adapters.mapped("edge_replay_coalesced_count"))
        dead_letter_total = sum(adapters.mapped("edge_dead_letter_count"))
        replay_adapters = len(adapters.filtered(lambda record: record.edge_replay_pending_count))
        replay_due_adapters = len(adapters.filtered(lambda record: record.edge_replay_due_count))
        replay_scheduled_adapters = len(adapters.filtered(lambda record: record.edge_replay_scheduled_count))
        dead_letter_adapters = len(adapters.filtered(lambda record: record.edge_dead_letter_count))
        edge_action_total = sum(adapters.mapped("edge_action_count"))
        edge_action_pending = sum(adapters.mapped("pending_edge_action_count"))
        edge_action_processing = sum(adapters.mapped("processing_edge_action_count"))
        edge_action_processed = sum(adapters.mapped("processed_edge_action_count"))
        edge_action_adapters = len(adapters.filtered(lambda record: record.edge_action_count))
        edge_action_processing_adapters = len(adapters.filtered(lambda record: record.processing_edge_action_count))
        replay_summaries = [summary for summary in adapters.mapped("edge_replay_summary") if summary and "pending_count=0" not in summary]
        replay_last_summaries = [summary for summary in adapters.mapped("edge_last_replay_summary") if summary]
        replay_outcomes = [outcome for outcome in adapters.mapped("edge_last_replay_outcome") if outcome]
        dead_letter_summaries = [summary for summary in adapters.mapped("edge_dead_letter_summary") if summary and "dead_letter_count=0" not in summary]
        replay_summary_text = (
            replay_last_summaries[0]
            if replay_last_summaries and replay_pending
            else replay_summaries[0]
            if replay_summaries
            else (_("pending_count=%s, kinds=none") % replay_pending)
        )
        if dead_letter_total:
            state = "danger"
            label = _("Edge dead letters present")
            detail = _("%(total)s dead letter(s) across %(adapters)s adapter(s).") % {
                "total": dead_letter_total,
                "adapters": dead_letter_adapters or adapter_count,
            }
        elif issue_open:
            state = "danger"
            label = _("Driver issues open")
            detail = _("%(open)s open issue(s) across %(adapters)s adapter(s).") % {
                "open": issue_open,
                "adapters": open_issue_adapters or issue_adapters or adapter_count,
            }
        elif replay_due:
            state = "warning"
            label = _("Edge replay due")
            detail = _("%(due)s replay item(s) are ready to resend across %(adapters)s adapter(s); %(coalesced)s duplicate request(s) already coalesced.") % {
                "due": replay_due,
                "adapters": replay_due_adapters or replay_adapters or adapter_count,
                "coalesced": replay_coalesced,
            }
        elif replay_scheduled and set(replay_outcomes) == {"waiting_backoff"}:
            state = "info"
            label = _("Edge replay cooling down")
            detail = _("%(scheduled)s replay item(s) are waiting for retry across %(adapters)s adapter(s); %(coalesced)s duplicate request(s) already coalesced.") % {
                "scheduled": replay_scheduled,
                "adapters": replay_scheduled_adapters or replay_adapters or adapter_count,
                "coalesced": replay_coalesced,
            }
        elif edge_action_processing:
            state = "info"
            label = _("Edge actions processing")
            detail = _("%(processing)s action(s) processing across %(adapters)s adapter(s).") % {
                "processing": edge_action_processing,
                "adapters": edge_action_processing_adapters or edge_action_adapters or adapter_count,
            }
        elif replay_pending:
            state = "warning"
            label = _("Edge replay pending")
            detail = _("%(pending)s replay item(s) pending across %(adapters)s adapter(s); %(coalesced)s duplicate request(s) already coalesced.") % {
                "pending": replay_pending,
                "adapters": replay_adapters or adapter_count,
                "coalesced": replay_coalesced,
            }
        elif adapter_count:
            state = "success" if not (driver_attention or driver_error) else "warning"
            label = _("Driver diagnostics clear") if state == "success" else _("Driver diagnostics need review")
            detail = _("%(ready)s ready, %(attention)s attention, %(error)s error.") % {
                "ready": driver_ready,
                "attention": driver_attention,
                "error": driver_error,
            }
        else:
            state = "secondary"
            label = _("Driver diagnostics unavailable")
            detail = _("No runtime adapters matched the current workstation context.")
        summaries = [summary for summary in adapters.mapped("driver_issue_summary") if summary]
        edge_action_summaries = [summary for summary in adapters.mapped("edge_action_summary") if summary and not summary.startswith("0 action(s), 0 pending")]
        recent_issues = self._search_runtime_issue_activity(context, limit=3)
        recent_events = self._search_runtime_event_activity(context, limit=3)
        recent_activity = self._merge_timeline_entries(recent_events, recent_issues, limit=6)
        summary = (
            dead_letter_summaries[0]
            if dead_letter_summaries
            else replay_last_summaries[0]
            if replay_last_summaries and replay_pending
            else replay_summaries[0]
            if replay_summaries
            else edge_action_summaries[0]
            if edge_action_summaries
            else summaries[0]
            if summaries
            else detail
        )
        return {
            "state": state,
            "label": label,
            "detail": detail,
            "summary": summary,
            "adapter_count": adapter_count,
            "driver_issue_counts": {
                "total": issue_total,
                "open": issue_open,
                "resolved": max(issue_total - issue_open, 0),
                "adapters": issue_adapters,
                "open_adapters": open_issue_adapters,
            },
            "driver_counts": {
                "ready": driver_ready,
                "attention": driver_attention,
                "error": driver_error,
                "unknown": driver_unknown,
            },
            "edge_replay": {
                "pending": replay_pending,
                "due": replay_due,
                "scheduled": replay_scheduled,
                "adapters": replay_adapters,
                "due_adapters": replay_due_adapters,
                "scheduled_adapters": replay_scheduled_adapters,
                "coalesced_count": replay_coalesced,
                "last_outcome": replay_outcomes[0] if replay_outcomes else None,
                "last_summary": replay_last_summaries[0] if replay_last_summaries else None,
                "summary": replay_summary_text,
            },
            "edge_action_counts": {
                "total": edge_action_total,
                "pending": edge_action_pending,
                "processing": edge_action_processing,
                "processed": edge_action_processed,
                "adapters": edge_action_adapters,
                "processing_adapters": edge_action_processing_adapters,
            },
            "edge_action_summary": edge_action_summaries[0]
            if edge_action_summaries
            else (_("%(total)s action(s), %(pending)s pending, %(processing)s processing, %(processed)s processed") % {
                "total": edge_action_total,
                "pending": edge_action_pending,
                "processing": edge_action_processing,
                "processed": edge_action_processed,
            }),
            "edge_dead_letter": {
                "count": dead_letter_total,
                "adapters": dead_letter_adapters,
                "summary": dead_letter_summaries[0] if dead_letter_summaries else (_("dead_letter_count=%s, kinds=none") % dead_letter_total),
            },
            "recent_activity": recent_activity,
            "recent_events": recent_events,
            "recent_issues": recent_issues,
        }

    def _build_state_snapshot(self, context):
        queue = self._search_workorders(context)
        devices = self._search_devices(context)
        recent_commands = self._recent_records("gateway.command", context, self._serialize_gateway_command)
        recent_exceptions = self._recent_records("shopfloor.exception", context, self._serialize_exception)
        runtime_events = self._search_runtime_event_activity(context)
        runtime_issues = self._search_runtime_issue_activity(context)
        runtime_activity = self._merge_timeline_entries(runtime_events, runtime_issues)
        timeline = self._merge_timeline_entries(self._search_timeline(context), runtime_events, runtime_issues)
        gateway_runtime = self._build_gateway_runtime_summary(context)
        metrics = self._build_metrics(queue, devices, recent_exceptions, recent_commands)
        if gateway_runtime:
            metrics.update(
                {
                    "driverIssueOpen": (gateway_runtime.get("driver_issue_counts") or {}).get("open", 0),
                    "driverIssueAdapters": (gateway_runtime.get("driver_issue_counts") or {}).get("open_adapters", 0),
                    "edgeActionProcessing": (gateway_runtime.get("edge_action_counts") or {}).get("processing", 0),
                    "edgeReplayPending": (gateway_runtime.get("edge_replay") or {}).get("pending", 0),
                    "edgeDeadLetterCount": (gateway_runtime.get("edge_dead_letter") or {}).get("count", 0),
                }
            )
        return {
            "queue": queue,
            "devices": devices,
            "exceptions": recent_exceptions,
            "recent_exceptions": recent_exceptions,
            "commands": recent_commands,
            "recent_commands": recent_commands,
            "timeline": timeline,
            "activity": runtime_activity,
            "recent_runtime_activity": runtime_activity,
            "recent_runtime_events": runtime_events,
            "recent_runtime_issues": runtime_issues,
            "metrics": metrics,
            "gateway_runtime": gateway_runtime,
        }

    def _recent_records(self, model_name, context, serializer, limit=5):
        model = self._model(model_name)
        if model is None:
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
                "can_queue_gateway_command": self._registry_has_model("gateway.command"),
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
