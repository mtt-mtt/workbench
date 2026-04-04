import hashlib
import json

from odoo import fields


class GatewayRuntimeService:
    def __init__(self, env):
        self.env = env

    def _registry_has_model(self, model_name):
        return model_name in self.env.registry.models

    def _model_has_field(self, model_name, field_name):
        return self._registry_has_model(model_name) and field_name in self.env[model_name]._fields

    def _as_dict(self, payload):
        if isinstance(payload, dict):
            return dict(payload)
        if not payload:
            return {}
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                return parsed if isinstance(parsed, dict) else {"payload": parsed}
            except Exception:
                return {"payload": payload}
        return {"payload": payload}

    def _now(self):
        return fields.Datetime.now()

    def _parse_json(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            return dict(value)
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _json_dumps(self, value):
        return json.dumps(value, ensure_ascii=False, default=str)

    def _fingerprint_payload(self, payload):
        payload = self._as_dict(payload)
        if not payload:
            return None
        return hashlib.sha1(
            self._json_dumps(payload).encode("utf-8", errors="ignore")
        ).hexdigest()[:16]

    def _payload_bool(self, payload, key, default=False):
        value = payload.get(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return default

    def _extract_payload_config(self, payload):
        payload = self._as_dict(payload)
        config = self._parse_json(payload.get("config_json"))
        coordinator = self._as_dict(config.get("coordinator"))
        capability = self._as_dict(config.get("capability"))
        protocol = self._as_dict(config.get("protocol"))
        for key, value in payload.items():
            if key.startswith("supports_"):
                capability[key] = self._payload_bool(payload, key, False)
        for key in (
            "transport",
            "broker_url",
            "endpoint_url",
            "host",
            "port",
            "serial_port",
            "baudrate",
            "parity",
            "stop_bits",
            "unit_id",
            "rack",
            "slot",
            "cpu",
            "client_id",
            "base_topic",
            "qos",
            "retain_default",
            "namespace_uri",
            "security_policy",
            "security_mode",
            "auth_mode",
            "username",
            "poll_interval_seconds",
            "timeout_seconds",
            "retry_limit",
        ):
            if payload.get(key) is not None:
                protocol[key] = payload.get(key)
        for key in (
            "refresh_interval",
            "update_interval_seconds",
            "retry_after",
            "retry_after_seconds",
            "always_update",
            "first_refresh_required",
        ):
            if payload.get(key) is not None:
                coordinator[key] = payload.get(key)
        return {"config": config, "coordinator": coordinator, "capability": capability, "protocol": protocol}

    def _capability_defaults(self, adapter_type, payload=None):
        payload = self._as_dict(payload)
        extracted = self._extract_payload_config(payload)
        capability = extracted["capability"]
        protocol = extracted["protocol"]
        defaults = {
            "supports_push": False,
            "supports_poll": True,
            "supports_read": True,
            "supports_write": True,
            "supports_subscribe": False,
            "supports_discovery": False,
            "supports_ack": True,
            "supports_diagnostics": True,
            "supports_repair": True,
            "supports_reload": True,
            "supports_load": True,
            "supports_unload": True,
            "supports_dispatch": True,
        }
        type_defaults = {
            "mock": {"supports_push": True, "supports_subscribe": True, "supports_discovery": True},
            "mqtt": {"supports_push": True, "supports_poll": True, "supports_subscribe": True, "supports_discovery": True},
            "modbus": {"supports_push": False, "supports_poll": True, "supports_subscribe": False, "supports_discovery": False},
            "opcua": {"supports_push": True, "supports_poll": True, "supports_subscribe": True, "supports_discovery": True},
            "ads": {"supports_push": True, "supports_poll": True, "supports_subscribe": True, "supports_discovery": False},
            "s7": {"supports_push": False, "supports_poll": True, "supports_subscribe": False, "supports_discovery": False},
            "http": {"supports_push": True, "supports_poll": False, "supports_read": False, "supports_subscribe": False},
            "print": {"supports_push": True, "supports_poll": False, "supports_read": False, "supports_subscribe": False, "supports_write": True},
            "scale": {"supports_push": False, "supports_poll": True, "supports_read": True, "supports_write": False},
            "generic": {},
        }
        defaults.update(type_defaults.get(adapter_type or "generic", {}))
        if protocol.get("transport") == "mock":
            defaults["supports_discovery"] = True
        for key in list(defaults):
            if key in capability:
                defaults[key] = self._payload_bool(capability, key, defaults[key])
        return defaults

    def _protocol_summary(self, adapter_type, payload=None):
        payload = self._as_dict(payload)
        extracted = self._extract_payload_config(payload)
        protocol = extracted["protocol"]
        if adapter_type == "mqtt":
            return {
                "broker_url": payload.get("broker_url") or protocol.get("broker_url") or payload.get("connection_target"),
                "client_id": payload.get("client_id") or protocol.get("client_id"),
                "base_topic": payload.get("base_topic") or protocol.get("base_topic"),
                "qos": self._maybe_int(payload.get("qos"), self._maybe_int(protocol.get("qos"), 0)),
            }
        if adapter_type == "modbus":
            return {
                "transport": payload.get("transport") or protocol.get("transport") or "tcp",
                "host": payload.get("host") or protocol.get("host"),
                "port": self._maybe_int(payload.get("port"), self._maybe_int(protocol.get("port"), 502)),
                "unit_id": self._maybe_int(payload.get("unit_id"), self._maybe_int(protocol.get("unit_id"), 1)),
            }
        if adapter_type == "opcua":
            return {
                "endpoint_url": payload.get("endpoint_url") or protocol.get("endpoint_url") or payload.get("connection_target"),
                "security_policy": payload.get("security_policy") or protocol.get("security_policy") or "none",
                "security_mode": payload.get("security_mode") or protocol.get("security_mode") or "none",
            }
        if adapter_type == "s7":
            return {
                "host": payload.get("host") or protocol.get("host"),
                "port": self._maybe_int(payload.get("port"), self._maybe_int(protocol.get("port"), 102)),
                "rack": self._maybe_int(payload.get("rack"), self._maybe_int(protocol.get("rack"), 0)),
                "slot": self._maybe_int(payload.get("slot"), self._maybe_int(protocol.get("slot"), 1)),
            }
        return protocol

    def _coordinator_contract(self, adapter=None, payload=None, refresh_reason=None):
        payload = self._as_dict(payload)
        extracted = self._extract_payload_config(payload)
        coordinator = extracted["coordinator"]
        refresh_interval = self._maybe_int(
            payload.get("refresh_interval"),
            self._maybe_int(
                payload.get("update_interval_seconds"),
                self._maybe_int(
                    coordinator.get("refresh_interval"),
                    self._maybe_int(
                        coordinator.get("update_interval_seconds"),
                        self._maybe_int(payload.get("poll_interval_seconds"), self._adapter_timeout_seconds(adapter) if adapter else 30),
                    ),
                ),
            ),
        )
        retry_after = self._maybe_int(
            payload.get("retry_after"),
            self._maybe_int(payload.get("retry_after_seconds"), self._maybe_int(coordinator.get("retry_after"), self._maybe_int(coordinator.get("retry_after_seconds"), 0))),
        )
        supports_push = self._payload_bool(coordinator, "supports_push", bool(adapter and adapter.supports_push))
        supports_poll = self._payload_bool(coordinator, "supports_poll", bool(adapter.supports_poll) if adapter else True)
        return {
            "mode": coordinator.get("mode") or (adapter.coordinator_mode if adapter else "hybrid" if supports_push and supports_poll else "push" if supports_push else "poll"),
            "refresh_interval": max(1, refresh_interval or 30),
            "retry_after": max(0, retry_after or 0),
            "always_update": self._payload_bool(coordinator, "always_update", bool(adapter.always_update) if adapter else False),
            "first_refresh_required": self._payload_bool(coordinator, "first_refresh_required", bool(adapter.first_refresh_required) if adapter else True),
            "last_exception": payload.get("last_exception") or (adapter.last_exception_message if adapter else None),
            "refresh_reason": refresh_reason or payload.get("reason"),
        }

    def _maybe_int(self, value, default=None):
        try:
            if value is None:
                return default
            return int(value)
        except Exception:
            return default

    def _adapter_timeout_seconds(self, adapter):
        if not adapter:
            return 30
        return max(1, int(adapter.timeout_seconds or 30))

    def _adapter_heartbeat_timeout_seconds(self, adapter):
        if not adapter:
            return 60
        return max(1, int(adapter.heartbeat_timeout_seconds or adapter.timeout_seconds or 60))

    def _datetime_age_seconds(self, when_value):
        if not when_value:
            return None
        delta = fields.Datetime.now() - when_value
        return int(delta.total_seconds())

    def _adapter_health_from_adapter(self, adapter):
        if not adapter:
            return {
                "health_state": "unknown",
                "health_score": 0,
                "health_detail": "Adapter not found",
                "diagnostic_summary": json.dumps({"missing": True}, ensure_ascii=False),
            }

        diag = self._parse_json(adapter.diagnostic_state)
        timeout_seconds = self._adapter_heartbeat_timeout_seconds(adapter)
        age_seconds = self._datetime_age_seconds(adapter.last_heartbeat_at)
        stale = age_seconds is not None and age_seconds > timeout_seconds
        reconnect_blocked = (adapter.reconnect_policy or "auto") == "off"
        reconnect_budget = max(0, int(adapter.max_reconnect_attempts or 0) - int(adapter.reconnect_attempts or 0))

        if adapter.state == "disabled":
            health_state = "offline"
            health_score = 0
            health_detail = "Adapter is disabled"
        elif stale:
            health_state = "offline" if reconnect_blocked or reconnect_budget <= 0 else "degraded"
            health_score = 20 if health_state == "degraded" else 0
            health_detail = f"Heartbeat stale for {age_seconds} seconds"
        elif adapter.last_failure_at:
            health_state = "warning"
            health_score = 45
            health_detail = adapter.last_error or "Recent failure recorded"
        elif adapter.last_heartbeat_at or adapter.last_success_at:
            health_state = "healthy"
            health_score = 90
            health_detail = "Heartbeat fresh"
        else:
            health_state = "unknown"
            health_score = 25
            health_detail = "Awaiting heartbeat"

        summary = {
            "code": adapter.code,
            "adapter_type": adapter.adapter_type,
            "state": adapter.state,
            "health_state": health_state,
            "health_score": health_score,
            "health_detail": health_detail,
            "timeout_seconds": self._adapter_timeout_seconds(adapter),
            "heartbeat_timeout_seconds": timeout_seconds,
            "reconnect_policy": adapter.reconnect_policy,
            "reconnect_delay_seconds": adapter.reconnect_delay_seconds,
            "max_reconnect_attempts": adapter.max_reconnect_attempts,
            "reconnect_attempts": adapter.reconnect_attempts,
            "reconnect_budget": reconnect_budget,
            "last_heartbeat_at": adapter.last_heartbeat_at,
            "last_success_at": adapter.last_success_at,
            "last_failure_at": adapter.last_failure_at,
            "last_reconnect_at": adapter.last_reconnect_at,
            "last_error": adapter.last_error,
            "diagnostic": diag,
            "stale": stale,
            "age_seconds": age_seconds,
        }
        return {
            "health_state": health_state,
            "health_score": health_score,
            "health_detail": health_detail,
            "diagnostic_summary": json.dumps(summary, ensure_ascii=False, default=str),
            "diagnostic_state": json.dumps(summary, ensure_ascii=False, default=str),
            "summary": summary,
        }

    def _apply_adapter_health(self, adapter, *, health_state=None, health_detail=None, diagnostic_state=None, mark_success=False, mark_failure=False):
        values = {}
        if health_state:
            values["health_state"] = health_state
        if health_detail is not None:
            values["health_detail"] = health_detail
        if diagnostic_state is not None:
            values["diagnostic_state"] = diagnostic_state
            values["diagnostic_summary"] = diagnostic_state
        if mark_success:
            values["last_success_at"] = self._now()
            values["health_state"] = health_state or "healthy"
            values["health_score"] = 90
            values["last_error"] = False
        if mark_failure:
            values["last_failure_at"] = self._now()
            values["health_state"] = health_state or "warning"
            values["health_score"] = 40 if values.get("health_state") == "warning" else 10
        if values:
            adapter.write(values)
        return adapter

    def _issue_model(self):
        if not self._registry_has_model("gateway.runtime.issue"):
            return None
        return self.env["gateway.runtime.issue"].sudo()

    def _issue_has_field(self, field_name):
        model = self._issue_model()
        return bool(model and field_name in model._fields)

    def _issue_selection_value(self, field_name, preferred, fallback=None):
        model = self._issue_model()
        if not model or field_name not in model._fields:
            return fallback if fallback is not None else (preferred[0] if preferred else None)
        field = model._fields[field_name]
        selection = field.selection
        if not selection:
            return fallback if fallback is not None else (preferred[0] if preferred else None)
        if callable(selection):
            selection = selection(model.env)
        allowed = {item[0] for item in selection}
        for candidate in preferred:
            if candidate in allowed:
                return candidate
        return fallback if fallback in allowed else next(iter(allowed), fallback)

    def _issue_kind_value(self, preferred):
        preferences = {
            "repair": ["repair", "diagnostic"],
            "connectivity": ["connectivity", "health", "diagnostic"],
            "configuration": ["configuration", "diagnostic"],
            "discovery": ["discovery", "diagnostic"],
            "health": ["health", "diagnostic"],
            "cleanup": ["cleanup", "diagnostic"],
            "alarm": ["diagnostic"],
            "protocol_event": ["diagnostic"],
            "command_failure": ["diagnostic"],
        }
        return self._issue_selection_value("issue_kind", preferences.get(preferred, [preferred, "diagnostic"]), "diagnostic")

    def _issue_state_open_value(self):
        return self._issue_selection_value("state", ["open", "new", "active", "pending", "reported"], "open")

    def _issue_state_progress_value(self):
        return self._issue_selection_value("state", ["in_progress", "ack", "open", "processing"], self._issue_state_open_value())

    def _issue_state_resolved_value(self):
        return self._issue_selection_value("state", ["resolved", "closed", "done", "cancelled"], "resolved")

    def _issue_is_resolved(self, issue):
        state = getattr(issue, "state", None)
        return state in {"resolved", "closed", "done", "cancelled", "ignored"}

    def _find_runtime_issue(self, adapter, issue_kind=None, include_resolved=False):
        Issue = self._issue_model()
        if Issue is None or not adapter:
            return None
        issue_key = f"runtime:{adapter.code}:{issue_kind}" if adapter and issue_kind else None
        domain = [("adapter_id", "=", adapter.id)] if self._issue_has_field("adapter_id") else []
        if issue_key and self._issue_has_field("issue_key"):
            domain = [("issue_key", "=", issue_key)]
        elif issue_kind and self._issue_has_field("issue_kind"):
            domain.append(("issue_kind", "=", self._issue_kind_value(issue_kind)))
        issues = Issue.search(domain, order="last_seen_at desc, id desc")
        if include_resolved:
            return issues[:1]
        for issue in issues:
            if not self._issue_is_resolved(issue):
                return issue
        return issues[:1]

    def _upsert_runtime_issue(self, adapter, *, issue_kind, severity="medium", message="", detail=None, payload=None, recommended_action=None, state=None):
        Issue = self._issue_model()
        if Issue is None or not adapter:
            return None
        issue = self._find_runtime_issue(adapter, issue_kind=issue_kind)
        values = {}
        if self._issue_has_field("name"):
            values["name"] = f"{adapter.code}:{issue_kind}"
        if self._issue_has_field("issue_key"):
            values["issue_key"] = f"runtime:{adapter.code}:{issue_kind}"
        if self._issue_has_field("adapter_id"):
            values["adapter_id"] = adapter.id
        if self._issue_has_field("entry_id") and getattr(adapter, "entry_id", None):
            values["entry_id"] = adapter.entry_id.id
        if self._issue_has_field("issue_kind"):
            values["issue_kind"] = self._issue_kind_value(issue_kind)
        if self._issue_has_field("recommended_action_key"):
            values["recommended_action_key"] = self._issue_selection_value(
                "recommended_action_key",
                [recommended_action, "review_runtime"],
                "review_runtime",
            )
        if self._issue_has_field("is_fixable"):
            values["is_fixable"] = (recommended_action or "") in {
                "refresh_runtime",
                "repair_runtime",
                "reload_runtime",
                "load_runtime",
                "unload_runtime",
            }
        if self._issue_has_field("severity"):
            values["severity"] = self._issue_selection_value("severity", [severity, "medium", "high", "low"], severity)
        if self._issue_has_field("state"):
            values["state"] = state or self._issue_state_open_value()
        if self._issue_has_field("message"):
            values["message"] = message or f"{issue_kind} issue"
        if self._issue_has_field("detail"):
            values["detail"] = detail or message or f"{issue_kind} issue"
        if self._issue_has_field("recommended_action"):
            values["recommended_action"] = recommended_action or "review_runtime"
        if self._issue_has_field("payload_json"):
            values["payload_json"] = self._json_dumps(self._as_dict(payload))
        if self._issue_has_field("last_seen_at"):
            values["last_seen_at"] = self._now()
        if self._issue_has_field("resolved_at"):
            values["resolved_at"] = False
        if issue:
            issue.write(values)
            return issue
        return Issue.create(values)

    def _resolve_runtime_issue(self, adapter, *, issue_kind, detail=None, payload=None):
        issue = self._find_runtime_issue(adapter, issue_kind=issue_kind)
        if not issue or self._issue_is_resolved(issue):
            return issue
        values = {}
        if self._issue_has_field("state"):
            values["state"] = self._issue_state_resolved_value()
        if self._issue_has_field("resolved_at"):
            values["resolved_at"] = self._now()
        if self._issue_has_field("last_seen_at"):
            values["last_seen_at"] = self._now()
        if detail is not None and self._issue_has_field("detail"):
            values["detail"] = detail
        if payload is not None and self._issue_has_field("payload_json"):
            values["payload_json"] = self._json_dumps(self._as_dict(payload))
        if values:
            issue.write(values)
        return issue

    def _runtime_issue_summary(self, adapter):
        Issue = self._issue_model()
        if Issue is None or not adapter:
            return {"total": 0, "open": 0, "resolved": 0, "fixable": 0, "open_fixable": 0, "by_severity": {}}
        domain = [("adapter_id", "=", adapter.id)] if self._issue_has_field("adapter_id") else []
        issues = Issue.search(domain)
        summary = {"total": len(issues), "open": 0, "resolved": 0, "fixable": 0, "open_fixable": 0, "by_severity": {}}
        for issue in issues:
            severity = getattr(issue, "severity", "unknown") or "unknown"
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            if getattr(issue, "is_fixable", False):
                summary["fixable"] += 1
            if self._issue_is_resolved(issue):
                summary["resolved"] += 1
            else:
                summary["open"] += 1
                if getattr(issue, "is_fixable", False):
                    summary["open_fixable"] += 1
        return summary

    def _sync_configuration_issue(self, adapter, payload=None):
        if not adapter:
            return None
        payload = self._as_dict(payload)
        config_missing = not (adapter.connection_target or adapter.config_json or payload.get("connection_target") or payload.get("config_json"))
        if config_missing:
            return self._upsert_runtime_issue(
                adapter,
                issue_kind="configuration",
                severity="medium",
                message="Adapter configuration is incomplete",
                detail="Connection target or protocol configuration is required before runtime activation.",
                payload=payload,
                recommended_action="configure_adapter",
            )
        return self._resolve_runtime_issue(adapter, issue_kind="configuration", detail="Configuration available", payload=payload)

    def _sync_connectivity_issue(self, adapter, health, payload=None):
        if not adapter:
            return None
        summary = health.get("summary", {}) if isinstance(health, dict) else {}
        state = health.get("health_state")
        detail = health.get("health_detail") or summary.get("health_detail")
        if state in {"healthy", "unknown"} and not summary.get("stale"):
            return self._resolve_runtime_issue(adapter, issue_kind="connectivity", detail=detail or "Adapter connectivity recovered", payload=payload)
        severity = "high" if state in {"offline", "degraded"} else "medium"
        recommended = "repair_runtime" if summary.get("stale") or state in {"offline", "degraded"} else "refresh_runtime"
        return self._upsert_runtime_issue(
            adapter,
            issue_kind="connectivity",
            severity=severity,
            message=detail or "Adapter connectivity degraded",
            detail=detail or "Runtime health indicates connectivity issues.",
            payload=payload or summary,
            recommended_action=recommended,
        )

    def _resolve_entry(self, entry_code):
        if not entry_code or not self._registry_has_model("gateway.entry"):
            return None
        return self.env["gateway.entry"].sudo().search([("code", "=", entry_code)], limit=1)

    def _resolve_device(self, device_code):
        if not device_code or not self._registry_has_model("gateway.device"):
            return None
        return self.env["gateway.device"].sudo().search([("code", "=", device_code)], limit=1)

    def _resolve_device_from_payload(self, payload=None):
        data = self._as_dict(payload)
        device = self._resolve_device(data.get("device_code"))
        if device:
            return device
        if self._registry_has_model("gateway.device") and self._model_has_field("gateway.device", "device_uid"):
            device_uid = data.get("device_uid")
            if device_uid:
                device = self.env["gateway.device"].sudo().search([("device_uid", "=", device_uid)], limit=1)
                if device:
                    return device
        external_ref = data.get("external_ref")
        if external_ref and self._registry_has_model("gateway.device"):
            return self.env["gateway.device"].sudo().search([("external_ref", "=", external_ref)], limit=1)
        return None

    def _resolve_parent_device_from_payload(self, payload=None):
        data = self._as_dict(payload)
        parent_code = (
            data.get("parent_device_code")
            or data.get("via_device_code")
            or data.get("parent_code")
        )
        if parent_code:
            return self._resolve_device(parent_code)
        parent_uid = data.get("parent_device_uid") or data.get("via_device_uid")
        if parent_uid and self._registry_has_model("gateway.device") and self._model_has_field("gateway.device", "device_uid"):
            return self.env["gateway.device"].sudo().search([("device_uid", "=", parent_uid)], limit=1)
        return None

    def _resolve_adapter(self, adapter_code):
        if not adapter_code or not self._registry_has_model("gateway.runtime.adapter"):
            return None
        return self.env["gateway.runtime.adapter"].sudo().search([("code", "=", adapter_code)], limit=1)

    def _resolve_app(self, app_code):
        if not app_code or not self._registry_has_model("shopfloor.app"):
            return None
        return self.env["shopfloor.app"].sudo().search([("code", "=", app_code)], limit=1)

    def _resolve_workstation(self, workstation_code):
        if not workstation_code or not self._registry_has_model("shopfloor.workstation"):
            return None
        return self.env["shopfloor.workstation"].sudo().search([("code", "=", workstation_code)], limit=1)

    def _resolve_command(self, payload):
        if not self._registry_has_model("gateway.command"):
            return None
        command_id = payload.get("command_id")
        command_code = payload.get("command_code")
        Command = self.env["gateway.command"].sudo()
        if command_id:
            return Command.browse(int(command_id)).exists()
        if command_code:
            return Command.search([("code", "=", command_code)], limit=1)
        return None

    def _probe_session_model(self):
        if not self._registry_has_model("gateway.runtime.probe.session"):
            return None
        return self.env["gateway.runtime.probe.session"].sudo()

    def _resolve_probe_session(self, session):
        Session = self._probe_session_model()
        if Session is None:
            return None
        if hasattr(session, "_name") and getattr(session, "_name", None) == "gateway.runtime.probe.session":
            return session.exists()
        if isinstance(session, int):
            return Session.browse(session).exists()
        if isinstance(session, dict):
            if session.get("session_id"):
                return Session.browse(int(session["session_id"])).exists()
            if session.get("code"):
                return Session.search([("code", "=", session["code"])], limit=1)
        return None

    def _resolve_runtime_context(self, payload=None):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        entry = self._resolve_entry(data.get("entry_code")) or (adapter.entry_id if adapter and adapter.entry_id else None)
        device = self._resolve_device_from_payload(data)
        workstation = self._resolve_workstation(data.get("workstation_code")) or (
            adapter.workstation_id if adapter and adapter.workstation_id else None
        )
        app = self._resolve_app(data.get("app_code")) or (adapter.app_id if adapter and adapter.app_id else None)
        if not device and adapter and adapter.device_code:
            device = self._resolve_device(adapter.device_code)
        return {
            "payload": data,
            "adapter": adapter,
            "entry": entry,
            "device": device,
            "workstation": workstation,
            "app": app,
        }

    def _device_registry_values(self, payload=None, *, adapter=None, entry=None, workstation=None, app=None, now=None):
        data = self._as_dict(payload)
        device_code = data.get("device_code") or (adapter.device_code if adapter else None)
        if not device_code or not entry:
            return None
        now = now or self._now()
        status = data.get("status") or data.get("state")
        state_map = {
            "ok": "ready",
            "warn": "degraded",
            "error": "degraded",
            "offline": "offline",
            "ready": "ready",
            "degraded": "degraded",
            "disabled": "disabled",
            "offline_state": "offline",
        }
        state = state_map.get(status, "ready")
        values = {
            "name": data.get("device_name") or device_code,
            "code": device_code,
            "entry_id": entry.id,
            "state": state,
            "device_type": data.get("device_type") or data.get("kind") or (adapter.adapter_type if adapter else None),
            "workstation_ref": data.get("workstation_code") or (workstation.code if workstation else None),
            "app_ref": data.get("app_code") or (app.code if app else None),
            "external_ref": data.get("external_ref") or data.get("device_uid"),
            "protocol": data.get("protocol") or (adapter.adapter_type if adapter else None),
            "address": data.get("address") or data.get("connection_target") or (adapter.connection_target if adapter else None),
            "last_seen_at": now,
        }
        parent_device = self._resolve_parent_device_from_payload(data)
        if self._model_has_field("gateway.device", "parent_device_id"):
            values["parent_device_id"] = parent_device.id if parent_device else False
        if self._model_has_field("gateway.device", "device_uid"):
            values["device_uid"] = data.get("device_uid") or device_code
        if self._model_has_field("gateway.device", "identifiers_json"):
            values["identifiers_json"] = self._json_dumps(
                data.get("identifiers")
                or {
                    "device_code": device_code,
                    "entry_code": entry.code,
                    "adapter_code": adapter.code if adapter else None,
                }
            )
        if self._model_has_field("gateway.device", "connections_json"):
            values["connections_json"] = self._json_dumps(
                data.get("connections")
                or {
                    "address": values["address"],
                    "protocol": values["protocol"],
                }
            )
        if self._model_has_field("gateway.device", "adapter_instance_id"):
            values["adapter_instance_id"] = adapter.id if adapter else False
        if self._model_has_field("gateway.device", "lifecycle_state"):
            values["lifecycle_state"] = {
                "draft": "draft",
                "ready": "ready",
                "degraded": "degraded",
                "offline": "offline",
                "disabled": "disabled",
            }.get(state, "bound")
        if self._model_has_field("gateway.device", "disabled_by"):
            values["disabled_by"] = "runtime" if state == "disabled" else False
        if self._model_has_field("gateway.device", "config_binding"):
            values["config_binding"] = entry.code
        if self._model_has_field("gateway.device", "workstation_binding"):
            values["workstation_binding"] = workstation.code if workstation else data.get("workstation_code")
        if self._model_has_field("gateway.device", "change_kind"):
            values["change_kind"] = self._change_kind(data)
        if self._model_has_field("gateway.device", "discovery_state"):
            values["discovery_state"] = self._discovery_state(data)
        if self._model_has_field("gateway.device", "capability_state"):
            values["capability_state"] = data.get("capability_state") or ("ready" if data.get("capability_ready") else "partial" if data.get("identifiers") else "unknown")
        if self._model_has_field("gateway.device", "point_sync_state"):
            values["point_sync_state"] = data.get("point_sync_state") or ("synced" if data.get("point_sync_ready") else "pending")
        if self._model_has_field("gateway.device", "subscription_state"):
            values["subscription_state"] = data.get("subscription_state") or ("subscribed" if self._payload_bool(data, "subscribed", False) else "requested" if self._payload_bool(data, "subscription_requested", False) else "idle")
        if self._model_has_field("gateway.device", "probe_ready"):
            values["probe_ready"] = self._payload_bool(data, "probe_ready", bool(data.get("probe_session_id") or self._change_kind(data) == "probe"))
        if self._model_has_field("gateway.device", "source_signal"):
            values["source_signal"] = data.get("signal") or data.get("source_signal")
        if self._model_has_field("gateway.device", "source_payload_id"):
            values["source_payload_id"] = data.get("source_payload_id") or self._fingerprint_payload(data)
        if self._model_has_field("gateway.device", "probe_session_id"):
            values["probe_session_id"] = data.get("probe_session_id")
        if self._model_has_field("gateway.device", "last_transition_at"):
            values["last_transition_at"] = now
        return values

    def _upsert_gateway_device(self, payload=None, *, adapter=None, entry=None, workstation=None, app=None, now=None):
        if not self._registry_has_model("gateway.device"):
            return None, "missing_model"
        values = self._device_registry_values(
            payload,
            adapter=adapter,
            entry=entry,
            workstation=workstation,
            app=app,
            now=now,
        )
        if not values:
            return None, "skipped"
        Device = self.env["gateway.device"].sudo()
        device = Device.search([("code", "=", values["code"])], limit=1)
        action = "update" if device else "create"
        if device:
            changed_fields = []
            for field_name, new_value in values.items():
                if field_name not in device._fields:
                    continue
                old_value = device[field_name]
                if getattr(old_value, "id", old_value) != getattr(new_value, "id", new_value):
                    changed_fields.append(field_name)
            if self._model_has_field("gateway.device", "changed_fields_json"):
                values["changed_fields_json"] = self._json_dumps(changed_fields)
            if self._model_has_field("gateway.device", "state_version"):
                values["state_version"] = int(device.state_version or 0) + (1 if changed_fields else 0)
            device.write(values)
        else:
            if self._model_has_field("gateway.device", "changed_fields_json"):
                values["changed_fields_json"] = self._json_dumps(sorted(values.keys()))
            if self._model_has_field("gateway.device", "state_version"):
                values["state_version"] = 1
            device = Device.create(values)
        return device, action

    def _normalize_payload(self, payload):
        data = self._as_dict(payload)
        status = data.get("status") or data.get("state") or "ok"
        if status not in {"ok", "warn", "error", "offline"}:
            status = "ok"
        severity = data.get("severity") or {
            "ok": "low",
            "warn": "medium",
            "error": "high",
            "offline": "high",
        }.get(status, "medium")
        normalized = {
            "name": data.get("name") or data.get("code") or "Runtime Message",
            "code": data.get("code") or data.get("adapter_code") or data.get("event_code"),
            "adapter_code": data.get("adapter_code") or data.get("code"),
            "entry_code": data.get("entry_code"),
            "device_code": data.get("device_code"),
            "workstation_code": data.get("workstation_code"),
            "app_code": data.get("app_code"),
            "session_ref": data.get("session_ref"),
            "status": status,
            "severity": severity,
            "message": data.get("message") or data.get("note") or "",
            "payload_json": json.dumps(data, ensure_ascii=False, default=str),
        }
        normalized["normalized_json"] = json.dumps(normalized, ensure_ascii=False, default=str)
        return normalized

    def _coalesce_codes(self, payload):
        data = self._as_dict(payload)
        return {
            "adapter_code": data.get("adapter_code") or data.get("code"),
            "entry_code": data.get("entry_code"),
            "device_code": data.get("device_code"),
            "workstation_code": data.get("workstation_code"),
            "app_code": data.get("app_code"),
        }

    def _signal_name(self, kind, adapter_code=None, entry_code=None):
        scope = adapter_code or entry_code or "*"
        kind = (kind or "runtime").replace(" ", "_").lower()
        return f"mrp_gateway_runtime.{kind}.{scope}"

    def _change_kind(self, payload=None, default="state"):
        data = self._as_dict(payload)
        change_kind = data.get("change_kind")
        if change_kind in {"identity", "topology", "state", "probe"}:
            return change_kind
        event_kind = data.get("event_kind")
        if event_kind in {"discovery", "inventory", "topology"}:
            return "topology"
        if event_kind in {"diagnostic", "probe"}:
            return "probe"
        return default

    def _discovery_state(self, payload=None, *, default="bound"):
        data = self._as_dict(payload)
        discovery_state = data.get("discovery_state")
        if discovery_state in {"discovered", "bound", "enriched", "ready", "removed"}:
            return discovery_state
        change_kind = self._change_kind(data, default="state")
        if change_kind == "topology":
            return "enriched"
        if change_kind == "probe":
            return "discovered"
        status = data.get("status") or data.get("state")
        if status in {"ok", "ready"}:
            return "ready"
        return default

    def _capability_defaults(self, adapter_type, payload=None):
        payload = self._as_dict(payload)
        adapter_type = adapter_type or "generic"
        subscribe = adapter_type in {"mqtt", "opcua"}
        push = adapter_type in {"mqtt", "http", "print", "mock"}
        poll = adapter_type not in {"print"}
        read = adapter_type not in {"print"}
        write = adapter_type not in {"scale"}
        defaults = {
            "supports_push": push,
            "supports_poll": poll,
            "supports_read": read,
            "supports_write": write,
            "supports_subscribe": subscribe,
            "supports_discovery": adapter_type in {"mqtt", "opcua", "http"},
            "supports_ack": adapter_type in {"modbus", "opcua", "s7", "mqtt", "http"},
            "supports_diagnostics": True,
            "supports_repair": True,
            "supports_reload": True,
            "supports_load": True,
            "supports_unload": True,
            "supports_dispatch": True,
        }
        for key in list(defaults):
            if key in payload:
                defaults[key] = bool(payload.get(key))
        return defaults

    def _coordinator_state_payload(self, adapter=None, payload=None, *, refresh_reason=None):
        payload = self._as_dict(payload)
        adapter = adapter or self._resolve_adapter(payload.get("adapter_code") or payload.get("code"))
        health = self._adapter_health_from_adapter(adapter)
        summary = health.get("summary", {})
        stale = bool(summary.get("stale"))
        contract = self._coordinator_contract(adapter=adapter, payload=payload, refresh_reason=refresh_reason)
        retry_after = contract["retry_after"]
        if retry_after <= 0:
            if adapter and adapter.reconnect_policy == "auto" and stale:
                retry_after = max(1, int(adapter.reconnect_delay_seconds or 5))
            elif adapter and adapter.last_failure_at:
                retry_after = max(1, int(adapter.reconnect_delay_seconds or 5))
        refresh_interval = contract["refresh_interval"]
        listener_count = 0
        if adapter:
            listener_count = int(adapter.heartbeat_count or 0) + int(adapter.event_count or 0)
        coordinator = {
            "adapter_code": adapter.code if adapter else payload.get("adapter_code") or payload.get("code"),
            "entry_code": adapter.entry_id.code if adapter and adapter.entry_id else payload.get("entry_code"),
            "workstation_code": adapter.workstation_id.code if adapter and adapter.workstation_id else payload.get("workstation_code"),
            "state": adapter.state if adapter else "unknown",
            "health_state": health["health_state"],
            "health_score": health["health_score"],
            "health_detail": health["health_detail"],
            "diagnostic_summary": health["summary"],
            "mode": contract["mode"],
            "refresh_interval": refresh_interval,
            "retry_after": retry_after,
            "last_update_success": bool(adapter.last_update_success) if adapter else False,
            "last_exception": adapter.last_exception_message if adapter else None,
            "last_exception_class": adapter.last_exception_class if adapter else None,
            "last_refresh_at": adapter.last_poll_at if adapter else None,
            "last_update_started_at": adapter.last_update_started_at if adapter else None,
            "last_update_finished_at": adapter.last_update_finished_at if adapter else None,
            "last_update_success_at": adapter.last_update_success_at if adapter else None,
            "last_update_failure_at": adapter.last_update_failure_at if adapter else None,
            "last_heartbeat_at": adapter.last_heartbeat_at if adapter else None,
            "last_repair_at": adapter.last_repair_at if adapter else None,
            "supports_refresh": bool(adapter.supports_poll or adapter.supports_push) if adapter else True,
            "supports_repair": bool(adapter.supports_repair) if adapter else True,
            "supports_reload": bool(adapter.supports_reload) if adapter else True,
            "supports_load": bool(adapter.supports_load) if adapter else True,
            "supports_unload": bool(adapter.supports_unload) if adapter else True,
            "supports_dispatch": bool(adapter.supports_dispatch) if adapter else True,
            "always_update": contract["always_update"],
            "first_refresh_required": contract["first_refresh_required"],
            "listener_count": int(adapter.listener_count) if adapter else listener_count,
            "refresh_reason": contract["refresh_reason"],
            "signal": self._signal_name("coordinator_refresh", adapter.code if adapter else payload.get("adapter_code"), payload.get("entry_code")),
        }
        coordinator["signal_payload"] = {
            "signal": coordinator["signal"],
            "adapter_code": coordinator["adapter_code"],
            "entry_code": coordinator["entry_code"],
            "state": coordinator["state"],
            "health_state": coordinator["health_state"],
            "health_score": coordinator["health_score"],
            "reason": refresh_reason,
        }
        return coordinator

    def build_capability_payload(self, payload=None, adapter=None):
        data = self._as_dict(payload)
        adapter = adapter or self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        adapter_type = adapter.adapter_type if adapter else data.get("adapter_type") or "mock"
        transport = data.get("transport") or adapter_type
        coordinator = self._coordinator_state_payload(adapter=adapter, payload=data)
        supports = self._capability_defaults(adapter_type, payload=data)
        if adapter:
            supports.update(
                {
                    "supports_push": bool(adapter.supports_push),
                    "supports_poll": bool(adapter.supports_poll),
                    "supports_read": bool(adapter.supports_read),
                    "supports_write": bool(adapter.supports_write),
                    "supports_subscribe": bool(adapter.supports_subscribe),
                    "supports_discovery": bool(adapter.supports_discovery),
                    "supports_ack": bool(adapter.supports_ack),
                    "supports_diagnostics": bool(adapter.supports_diagnostics),
                    "supports_repair": bool(adapter.supports_repair),
                    "supports_reload": bool(adapter.supports_reload),
                    "supports_load": bool(adapter.supports_load),
                    "supports_unload": bool(adapter.supports_unload),
                    "supports_dispatch": bool(adapter.supports_dispatch),
                }
            )
        capability = {
            "adapter_code": adapter.code if adapter else data.get("adapter_code") or data.get("code"),
            "entry_code": adapter.entry_id.code if adapter and adapter.entry_id else data.get("entry_code"),
            "device_code": adapter.device_code if adapter else data.get("device_code"),
            "workstation_code": adapter.workstation_id.code if adapter and adapter.workstation_id else data.get("workstation_code"),
            "app_code": adapter.app_id.code if adapter and adapter.app_id else data.get("app_code"),
            "adapter_type": adapter_type,
            "transport": transport,
            "state": adapter.state if adapter else data.get("state") or "unknown",
            "health_state": coordinator["health_state"],
            "health_score": coordinator["health_score"],
            "health_detail": coordinator["health_detail"],
            "supports": {
                "read": supports["supports_read"],
                "write": supports["supports_write"],
                "poll": supports["supports_poll"],
                "push": supports["supports_push"],
                "subscribe": supports["supports_subscribe"],
                "discovery": supports["supports_discovery"],
                "ack": supports["supports_ack"],
                "diagnostic": supports["supports_diagnostics"],
                "repair": supports["supports_repair"],
                "reload": supports["supports_reload"],
                "load": supports["supports_load"],
                "unload": supports["supports_unload"],
                "dispatch": supports["supports_dispatch"],
            },
            "protocol": self._protocol_summary(adapter_type, payload=data),
            "coordinator": coordinator,
            "lifecycle": {
                "state": adapter.state if adapter else data.get("state") or "unknown",
                "unique_id": adapter.runtime_unique_id if adapter else data.get("runtime_unique_id"),
                "can_refresh": supports["supports_poll"] or supports["supports_push"],
                "can_repair": supports["supports_repair"],
                "can_reload": supports["supports_reload"],
                "can_load": supports["supports_load"],
                "can_unload": supports["supports_unload"],
            },
        }
        capability["capability_json"] = self._json_dumps(capability)
        return capability

    def upsert_registry_then_dispatch(self, payload=None, *, change_kind=None, discovery_state=None, event_kind=None, signal_kind=None):
        context = self._resolve_runtime_context(payload)
        data = context["payload"]
        adapter = context["adapter"]
        entry = context["entry"]
        workstation = context["workstation"]
        app = context["app"]
        now = self._now()
        device, registry_action = self._upsert_gateway_device(
            data,
            adapter=adapter,
            entry=entry,
            workstation=workstation,
            app=app,
            now=now,
        )
        change_kind = change_kind or self._change_kind(data)
        discovery_state = discovery_state or self._discovery_state(data)
        signal = self.dispatch_runtime_signal(
            {
                **data,
                "adapter_code": adapter.code if adapter else data.get("adapter_code") or data.get("code"),
                "entry_code": entry.code if entry else data.get("entry_code"),
                "device_code": device.code if device else data.get("device_code"),
                "workstation_code": workstation.code if workstation else data.get("workstation_code"),
                "app_code": app.code if app else data.get("app_code"),
                "signal_kind": signal_kind or data.get("signal_kind") or "device_update",
                "change_kind": change_kind,
                "discovery_state": discovery_state,
                "registry_action": registry_action,
            },
            log_event=False,
        )
        event = self._log_runtime_event(
            {
                **data,
                "name": data.get("name") or data.get("code") or f"{change_kind.title()} update",
                "event_kind": event_kind or data.get("event_kind") or "status",
                "adapter_code": adapter.code if adapter else data.get("adapter_code") or data.get("code"),
                "entry_code": entry.code if entry else data.get("entry_code"),
                "device_code": device.code if device else data.get("device_code"),
                "workstation_code": workstation.code if workstation else data.get("workstation_code"),
                "app_code": app.code if app else data.get("app_code"),
                "change_kind": change_kind,
                "discovery_state": discovery_state,
                "source_signal": signal.get("signal"),
                "source_payload_id": self._fingerprint_payload(data),
                "probe_session_id": data.get("probe_session_id"),
                "state_version": self._fingerprint_payload(
                    {
                        "adapter_code": adapter.code if adapter else data.get("adapter_code") or data.get("code"),
                        "device_code": device.code if device else data.get("device_code"),
                        "status": data.get("status") or data.get("state"),
                        "change_kind": change_kind,
                        "discovery_state": discovery_state,
                    }
                ),
                "registry_action": registry_action,
                "ui_refresh_hint": data.get("ui_refresh_hint") or "device_panel",
                "message": data.get("message") or data.get("reason") or f"{change_kind.title()} update dispatched",
                "result": data.get("result") or discovery_state,
            }
        )
        return {
            "ok": True,
            "device": device,
            "registry_action": registry_action,
            "signal": signal,
            "event": event,
        }

    def dispatch_state_only(self, payload=None):
        return self.upsert_registry_then_dispatch(
            payload,
            change_kind="state",
            discovery_state=self._discovery_state(payload, default="bound"),
            event_kind="status",
            signal_kind="device_update",
        )

    def dispatch_topology_change(self, payload=None):
        return self.upsert_registry_then_dispatch(
            payload,
            change_kind="topology",
            discovery_state=self._discovery_state(payload, default="enriched"),
            event_kind="custom",
            signal_kind="topology_change",
        )

    def dispatch_runtime_signal(self, payload=None, *, signal=None, kind=None, log_event=True):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        entry = self._resolve_entry(data.get("entry_code"))
        signal_name = signal or data.get("signal") or self._signal_name(
            kind or data.get("signal_kind") or "runtime",
            adapter.code if adapter else data.get("adapter_code"),
            data.get("entry_code"),
        )
        signal_payload = {
            "signal": signal_name,
            "kind": kind or data.get("signal_kind") or "runtime",
            "adapter_code": adapter.code if adapter else data.get("adapter_code") or data.get("code"),
            "entry_code": entry.code if entry else data.get("entry_code"),
            "device_code": data.get("device_code") or (adapter.device_code if adapter else None),
            "workstation_code": data.get("workstation_code") or (adapter.workstation_id.code if adapter and adapter.workstation_id else None),
            "payload": data,
        }
        event = None
        if log_event:
            event = self._log_runtime_event(
                {
                    "event_kind": "signal",
                    "name": signal_name,
                    "adapter_code": signal_payload["adapter_code"],
                    "entry_code": signal_payload["entry_code"],
                    "device_code": signal_payload["device_code"],
                    "workstation_code": signal_payload["workstation_code"],
                    "change_kind": data.get("change_kind") or "state",
                    "discovery_state": data.get("discovery_state") or "bound",
                    "source_signal": signal_name,
                    "source_payload_id": self._fingerprint_payload(data),
                    "probe_session_id": data.get("probe_session_id"),
                    "state_version": data.get("state_version") or self._fingerprint_payload(signal_payload),
                    "registry_action": data.get("registry_action"),
                    "ui_refresh_hint": data.get("ui_refresh_hint"),
                    "message": data.get("message") or data.get("reason") or signal_name,
                    "severity": data.get("severity") or "low",
                    "result": data.get("result") or data.get("state") or "dispatched",
                }
            )
        return {
            "ok": True,
            "signal": signal_name,
            "data": signal_payload,
            "event_id": event.id if event else None,
            "message": {"type": "success", "text": f"Signal dispatched: {signal_name}"},
        }

    def refresh_runtime(self, payload=None):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        health = self._adapter_health_from_adapter(adapter)
        adapter.write(
            {
                "last_update_started_at": self._now(),
                "last_poll_at": self._now(),
                "state": adapter.state if adapter.state in {"ready", "degraded", "offline"} else "ready",
                "health_state": health["health_state"],
                "health_score": health["health_score"],
                "health_detail": health["health_detail"],
                "retry_after_seconds": 0,
                "last_update_success": health["health_state"] in {"healthy", "warning"},
                "last_update_finished_at": self._now(),
                "last_update_success_at": self._now() if health["health_state"] in {"healthy", "warning"} else adapter.last_update_success_at,
                "last_update_failure_at": self._now() if health["health_state"] not in {"healthy", "warning"} else adapter.last_update_failure_at,
                "last_exception_class": False if health["health_state"] in {"healthy", "warning"} else "RuntimeRefreshError",
                "last_exception_message": False if health["health_state"] in {"healthy", "warning"} else health["health_detail"],
                "first_refresh_required": False,
                "diagnostic_state": health["diagnostic_state"],
                "diagnostic_summary": health["diagnostic_summary"],
            }
        )
        self._sync_configuration_issue(adapter, data)
        self._sync_connectivity_issue(adapter, health, data)
        signal = self.dispatch_runtime_signal(
            {
                **data,
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "signal_kind": "coordinator_refresh",
                "reason": data.get("reason") or "manual_refresh",
                "result": "refreshed",
            }
        )
        return {
            "ok": True,
            "data": {
                "adapter": self._serialize_adapter(adapter),
                "capability": self.build_capability_payload(adapter=adapter, payload=data),
                "coordinator": self._coordinator_state_payload(adapter=adapter, payload=data, refresh_reason=data.get("reason") or "manual_refresh"),
                "signal": signal,
            },
            "message": {"type": "success", "text": "Runtime refreshed"},
        }

    def repair_runtime(self, payload=None):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        health = self._adapter_health_from_adapter(adapter)
        summary = health.get("summary", {})
        stale = bool(summary.get("stale"))
        if stale:
            adapter.write(
                {
                    "reconnect_attempts": adapter.reconnect_attempts + 1,
                    "last_reconnect_at": self._now(),
                    "last_repair_at": self._now(),
                    "health_state": "degraded",
                    "health_score": 25,
                    "health_detail": data.get("reason") or "Repair requested for stale adapter",
                    "retry_after_seconds": max(1, int(adapter.reconnect_delay_seconds or 5)),
                    "last_exception_class": "RuntimeRepairRequested",
                    "last_exception_message": data.get("reason") or "Repair requested for stale adapter",
                    "diagnostic_state": health["diagnostic_state"],
                    "diagnostic_summary": health["diagnostic_summary"],
                }
            )
        else:
            adapter.write(
                {
                    "last_reconnect_at": self._now(),
                    "last_repair_at": self._now(),
                    "health_state": health["health_state"],
                    "health_score": health["health_score"],
                    "health_detail": data.get("reason") or health["health_detail"],
                    "retry_after_seconds": max(0, int(adapter.retry_after_seconds or 0)),
                    "last_exception_class": "RuntimeRepairRequested",
                    "last_exception_message": data.get("reason") or health["health_detail"],
                    "diagnostic_state": health["diagnostic_state"],
                    "diagnostic_summary": health["diagnostic_summary"],
                }
            )
        self._upsert_runtime_issue(
            adapter,
            issue_kind="repair",
            severity="high" if stale else "medium",
            message=data.get("reason") or ("Repair requested for stale adapter" if stale else "Manual runtime repair requested"),
            detail=data.get("reason") or ("Heartbeat stale, reconnect workflow requested." if stale else "Runtime repair requested by operator."),
            payload={**data, "stale": stale, "health": summary},
            recommended_action="reload_runtime" if stale else "repair_runtime",
            state=self._issue_state_progress_value(),
        )
        signal = self.dispatch_runtime_signal(
            {
                **data,
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "signal_kind": "repair",
                "reason": data.get("reason") or ("stale_adapter" if stale else "manual_repair"),
                "result": "repair_requested",
            }
        )
        return {
            "ok": True,
            "data": {
                "adapter": self._serialize_adapter(adapter),
                "capability": self.build_capability_payload(adapter=adapter, payload=data),
                "coordinator": self._coordinator_state_payload(adapter=adapter, payload=data, refresh_reason=data.get("reason") or "repair"),
                "signal": signal,
                "repaired": True,
            },
            "message": {"type": "success", "text": "Runtime repair requested"},
        }

    def load_runtime(self, payload=None):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        adapter.write(
            {
                "state": "ready",
                "health_state": "healthy",
                "health_score": 80,
                "health_detail": data.get("reason") or "Runtime loaded",
                "last_success_at": self._now(),
                "last_update_success": True,
                "last_update_started_at": self._now(),
                "last_update_finished_at": self._now(),
                "last_update_success_at": self._now(),
                "retry_after_seconds": 0,
                "first_refresh_required": False,
                "last_exception_class": False,
                "last_exception_message": False,
                "diagnostic_state": json.dumps({"loaded": True, "reason": data.get("reason")}, ensure_ascii=False),
                "diagnostic_summary": json.dumps({"loaded": True, "state": "ready"}, ensure_ascii=False),
            }
        )
        self._sync_configuration_issue(adapter, data)
        self._resolve_runtime_issue(adapter, issue_kind="repair", detail="Runtime load completed", payload=data)
        self._sync_connectivity_issue(adapter, self._adapter_health_from_adapter(adapter), data)
        signal = self.dispatch_runtime_signal(
            {
                **data,
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "signal_kind": "load",
                "reason": data.get("reason") or "runtime_loaded",
                "result": "loaded",
            }
        )
        return {
            "ok": True,
            "data": {
                "adapter": self._serialize_adapter(adapter),
                "capability": self.build_capability_payload(adapter=adapter, payload=data),
                "coordinator": self._coordinator_state_payload(adapter=adapter, payload=data, refresh_reason="load"),
                "signal": signal,
            },
            "message": {"type": "success", "text": "Runtime loaded"},
        }

    def unload_runtime(self, payload=None):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        adapter.write(
            {
                "state": "disabled",
                "health_state": "offline",
                "health_score": 0,
                "health_detail": data.get("reason") or "Runtime unloaded",
                "last_failure_at": self._now(),
                "last_error": data.get("reason") or adapter.last_error,
                "last_update_success": False,
                "last_update_finished_at": self._now(),
                "last_update_failure_at": self._now(),
                "last_exception_class": "RuntimeUnloaded",
                "last_exception_message": data.get("reason") or "Runtime unloaded",
            }
        )
        self._upsert_runtime_issue(
            adapter,
            issue_kind="connectivity",
            severity="medium",
            message=data.get("reason") or "Runtime unloaded",
            detail=data.get("reason") or "Runtime adapter was unloaded and is currently offline.",
            payload=data,
            recommended_action="load_runtime",
        )
        signal = self.dispatch_runtime_signal(
            {
                **data,
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "signal_kind": "unload",
                "reason": data.get("reason") or "runtime_unloaded",
                "result": "unloaded",
            }
        )
        return {
            "ok": True,
            "data": {
                "adapter": self._serialize_adapter(adapter),
                "capability": self.build_capability_payload(adapter=adapter, payload=data),
                "coordinator": self._coordinator_state_payload(adapter=adapter, payload=data, refresh_reason="unload"),
                "signal": signal,
            },
            "message": {"type": "success", "text": "Runtime unloaded"},
        }

    def reload_runtime(self, payload=None):
        data = self._as_dict(payload)
        adapter = self._resolve_adapter(data.get("adapter_code") or data.get("code"))
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        unload_result = self.unload_runtime(data)
        if not unload_result.get("ok"):
            return unload_result
        repair_result = self.repair_runtime(data)
        load_result = self.load_runtime(data)
        signal = self.dispatch_runtime_signal(
            {
                **data,
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "signal_kind": "reload",
                "reason": data.get("reason") or "runtime_reloaded",
                "result": "reloaded",
            }
        )
        return {
            "ok": True,
            "data": {
                "adapter": self._serialize_adapter(adapter),
                "capability": self.build_capability_payload(adapter=adapter, payload=data),
                "coordinator": self._coordinator_state_payload(adapter=adapter, payload=data, refresh_reason="reload"),
                "signal": signal,
                "steps": {
                    "unload": unload_result,
                    "repair": repair_result,
                    "load": load_result,
                },
            },
            "message": {"type": "success", "text": "Runtime reloaded"},
        }

    def normalize_status_payload(self, payload):
        return self._normalize_payload(payload)

    def register_adapter_definition(self, payload):
        payload = self._as_dict(payload)
        normalized = self._normalize_payload(payload)
        Adapter = self.env["gateway.runtime.adapter"].sudo()
        adapter_code = normalized["adapter_code"] or normalized["name"]
        if not adapter_code:
            return {"ok": False, "errors": ["Adapter code is required"]}
        adapter = Adapter.search([("code", "=", adapter_code)], limit=1)
        entry = self._resolve_entry(normalized["entry_code"])
        workstation = self._resolve_workstation(normalized["workstation_code"])
        app = self._resolve_app(normalized["app_code"])
        contract = self.build_capability_payload(payload=payload, adapter=adapter)
        coordinator = contract["coordinator"]
        config_payload = self._extract_payload_config(payload)
        merged_config = dict(config_payload["config"])
        merged_config.update(
            {
                "capability": contract["supports"],
                "coordinator": {
                    "mode": coordinator["mode"],
                    "refresh_interval": coordinator["refresh_interval"],
                    "retry_after": coordinator["retry_after"],
                    "always_update": coordinator["always_update"],
                    "first_refresh_required": coordinator["first_refresh_required"],
                },
                "protocol": contract["protocol"],
            }
        )
        values = {
            "name": normalized["name"],
            "adapter_type": payload.get("adapter_type") or "mock",
            "entry_id": entry.id if entry else False,
            "app_id": app.id if app else False,
            "workstation_id": workstation.id if workstation else False,
            "device_code": normalized["device_code"],
            "runtime_unique_id": payload.get("runtime_unique_id") or f"{payload.get('adapter_type') or 'generic'}:{adapter_code}",
            "connection_target": payload.get("connection_target"),
            "config_json": self._json_dumps(merged_config),
            "config_text": payload.get("config_text"),
            "state": "ready",
            "health_state": "healthy",
            "health_score": 80,
            "health_detail": "Adapter registered",
            "coordinator_mode": coordinator["mode"],
            "update_interval_seconds": coordinator["refresh_interval"],
            "retry_after_seconds": coordinator["retry_after"],
            "last_update_success": False,
            "first_refresh_required": coordinator["first_refresh_required"],
            "always_update": coordinator["always_update"],
            "timeout_seconds": self._maybe_int(payload.get("timeout_seconds"), coordinator["refresh_interval"]),
            "heartbeat_timeout_seconds": self._maybe_int(payload.get("heartbeat_timeout_seconds"), max(60, coordinator["refresh_interval"] * 2)),
            "supports_push": contract["supports"]["push"],
            "supports_poll": contract["supports"]["poll"],
            "supports_read": contract["supports"]["read"],
            "supports_write": contract["supports"]["write"],
            "supports_subscribe": contract["supports"]["subscribe"],
            "supports_discovery": contract["supports"]["discovery"],
            "supports_ack": contract["supports"]["ack"],
            "supports_diagnostics": contract["supports"]["diagnostic"],
            "supports_repair": contract["supports"]["repair"],
            "supports_reload": contract["supports"]["reload"],
            "supports_load": contract["supports"]["load"],
            "supports_unload": contract["supports"]["unload"],
            "supports_dispatch": contract["supports"]["dispatch"],
            "reconnect_policy": payload.get("reconnect_policy") or "auto",
            "reconnect_delay_seconds": self._maybe_int(payload.get("reconnect_delay_seconds"), 5),
            "max_reconnect_attempts": self._maybe_int(payload.get("max_reconnect_attempts"), 3),
            "diagnostic_state": self._json_dumps({"registered": True, "protocol": contract["protocol"]}),
            "diagnostic_summary": self._json_dumps(
                {
                    "registered": True,
                    "adapter_type": payload.get("adapter_type") or "mock",
                    "capability": contract["supports"],
                    "coordinator": {
                        "mode": coordinator["mode"],
                        "refresh_interval": coordinator["refresh_interval"],
                        "retry_after": coordinator["retry_after"],
                    },
                }
            ),
        }
        if adapter:
            adapter.write(values)
        else:
            values["code"] = adapter_code
            adapter = Adapter.create(values)
        entry = adapter.entry_id if adapter.entry_id else entry
        workstation = adapter.workstation_id if adapter.workstation_id else workstation
        app = adapter.app_id if adapter.app_id else app
        self._upsert_gateway_device(
            payload,
            adapter=adapter,
            entry=entry,
            workstation=workstation,
            app=app,
        )
        self._sync_configuration_issue(adapter, payload)
        return {
            "ok": True,
            "data": self._serialize_adapter(adapter),
            "capability": self.build_capability_payload(adapter=adapter, payload=payload),
            "coordinator": self._coordinator_state_payload(adapter=adapter, payload=payload, refresh_reason="registration"),
            "message": {"type": "success", "text": "Runtime adapter registered"},
        }

    def create_probe_session(self, payload):
        payload = self._as_dict(payload)
        context = self._resolve_runtime_context(payload)
        adapter = context["adapter"]
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        Session = self._probe_session_model()
        if Session is None:
            return {"ok": False, "errors": ["Probe session model not available"]}
        now = self._now()
        probe_kind = payload.get("probe_kind") or "summary"
        request_json = {
            "adapter_code": adapter.code,
            "entry_code": context["entry"].code if context["entry"] else payload.get("entry_code"),
            "device_code": context["device"].code if context["device"] else payload.get("device_code"),
            "workstation_code": context["workstation"].code if context["workstation"] else payload.get("workstation_code"),
            "app_code": context["app"].code if context["app"] else payload.get("app_code"),
            "probe_kind": probe_kind,
            "change_kind": payload.get("change_kind") or "probe",
            "discovery_state": payload.get("discovery_state") or "discovered",
            "ui_refresh_hint": payload.get("ui_refresh_hint") or "probe_sessions",
            "signal": payload.get("signal") or self._signal_name("probe", adapter.code, context["entry"].code if context["entry"] else None),
            "source_payload": payload,
        }
        session = Session.create(
            {
                "name": payload.get("name") or f"{adapter.code} {probe_kind} probe",
                "session_key": payload.get("session_key") or f"{adapter.code}:{probe_kind}:{now.strftime('%Y%m%d%H%M%S%f')}",
                "adapter_id": adapter.id,
                "entry_id": context["entry"].id if context["entry"] else False,
                "device_id": context["device"].id if context["device"] else False,
                "app_id": context["app"].id if context["app"] else False,
                "workstation_id": context["workstation"].id if context["workstation"] else False,
                "protocol": payload.get("protocol") or adapter.adapter_type,
                "trigger_kind": payload.get("trigger_kind") or "probe",
                "capability": payload.get("capability") or adapter.capability_summary if hasattr(adapter, "capability_summary") else payload.get("capability"),
                "probe_kind": probe_kind,
                "target_ref": payload.get("target_ref") or (context["device"].code if context["device"] else payload.get("device_code") or adapter.code),
                "change_kind": payload.get("change_kind") or "probe",
                "discovery_state": payload.get("discovery_state") or "discovered",
                "state": payload.get("state") or "running",
                "result_state": payload.get("result_state") or "pending",
                "source_signal": request_json["signal"],
                "source_payload_id": self._fingerprint_payload(payload),
                "state_version": self._fingerprint_payload(request_json),
                "ui_refresh_hint": request_json["ui_refresh_hint"],
                "request_json": self._json_dumps(request_json),
                "payload_json": self._json_dumps(payload),
                "normalized_json": self._json_dumps({"request": request_json, "adapter": adapter.code}),
                "message": payload.get("message") or _("Probe session started"),
                "summary": payload.get("message") or _("Probe session started"),
                "started_at": now,
            }
        )
        signal = self.dispatch_runtime_signal(
            {
                "adapter_code": adapter.code,
                "entry_code": context["entry"].code if context["entry"] else payload.get("entry_code"),
                "device_code": context["device"].code if context["device"] else payload.get("device_code"),
                "workstation_code": context["workstation"].code if context["workstation"] else payload.get("workstation_code"),
                "app_code": context["app"].code if context["app"] else payload.get("app_code"),
                "signal_kind": "probe",
                "change_kind": "probe",
                "discovery_state": session.discovery_state,
                "probe_session_id": session.code,
                "source_signal": session.source_signal,
                "source_payload_id": session.source_payload_id,
                "state_version": session.state_version,
                "ui_refresh_hint": session.ui_refresh_hint,
                "message": session.message,
                "result": session.result_state,
            }
        )
        if signal.get("event_id"):
            session.write({"runtime_event_id": signal["event_id"]})
        return {
            "ok": True,
            "data": self._serialize_probe_session(session),
            "signal": signal,
            "message": {"type": "success", "text": "Probe session created"},
        }

    def complete_probe_session(self, session, payload=None, *, state=None, result_state=None, response=None, message=None, last_error=None):
        Session = self._probe_session_model()
        if Session is None:
            return {"ok": False, "errors": ["Probe session model not available"]}
        session = self._resolve_probe_session(session)
        if not session:
            return {"ok": False, "errors": ["Probe session not found"]}
        payload = self._as_dict(payload)
        result_state = result_state or payload.get("result_state") or payload.get("state") or session.result_state
        state = state or payload.get("state")
        if not state:
            state = "done" if result_state in {"ok", "warning"} else "failed" if result_state == "error" else "cancelled" if result_state == "cancelled" else "running"
        values = {
            "state": state,
            "result_state": result_state,
            "message": message or payload.get("message") or session.message,
            "summary": message or payload.get("message") or session.summary,
            "last_error": last_error or payload.get("last_error") or session.last_error,
            "ui_refresh_hint": payload.get("ui_refresh_hint") or session.ui_refresh_hint,
        }
        if response is not None:
            values["response_json"] = self._json_dumps(response)
        if state in {"done", "failed", "cancelled"}:
            values["finished_at"] = self._now()
            if session.started_at:
                values["latency_ms"] = int(max(0, (values["finished_at"] - session.started_at).total_seconds() * 1000))
        session.write(values)
        signal = self.dispatch_runtime_signal(
            {
                "adapter_code": session.adapter_id.code if session.adapter_id else payload.get("adapter_code"),
                "entry_code": session.entry_id.code if session.entry_id else payload.get("entry_code"),
                "device_code": session.device_id.code if session.device_id else payload.get("device_code"),
                "workstation_code": session.workstation_id.code if session.workstation_id else payload.get("workstation_code"),
                "app_code": session.app_id.code if session.app_id else payload.get("app_code"),
                "signal_kind": "probe",
                "change_kind": "probe",
                "discovery_state": session.discovery_state,
                "probe_session_id": session.code,
                "source_signal": session.source_signal,
                "source_payload_id": session.source_payload_id,
                "state_version": session.state_version,
                "ui_refresh_hint": session.ui_refresh_hint,
                "message": session.message or message,
                "result": session.result_state,
            }
        )
        if signal.get("event_id"):
            session.write({"runtime_event_id": signal["event_id"]})
        return {
            "ok": True,
            "data": self._serialize_probe_session(session),
            "signal": signal,
            "message": {"type": "success", "text": "Probe session updated"},
        }

    def ingest_heartbeat(self, payload):
        normalized = self._normalize_payload(payload)
        context = self._resolve_runtime_context(normalized)
        adapter = context["adapter"]
        entry = context["entry"]
        workstation = context["workstation"]
        app = context["app"]
        device, registry_action = self._upsert_gateway_device(
            normalized,
            adapter=adapter,
            entry=entry,
            workstation=workstation,
            app=app,
        )
        heartbeat = self.env["gateway.runtime.heartbeat"].sudo().create(
            {
                "name": normalized["name"],
                "adapter_id": adapter.id if adapter else False,
                "entry_id": entry.id if entry else False,
                "device_id": device.id if device else False,
                "app_id": app.id if app else False,
                "workstation_id": workstation.id if workstation else False,
                "status": normalized["status"],
                "payload_json": normalized["payload_json"],
                "normalized_json": normalized["normalized_json"],
                "message": normalized["message"],
                "latency_ms": int(payload.get("latency_ms") or 0),
                "state": "processed",
                "processed_at": self._now(),
            }
        )
        if adapter:
            heartbeat_summary = {
                "code": adapter.code,
                "adapter_type": adapter.adapter_type,
                "status": normalized["status"],
                "health_state": "healthy" if normalized["status"] == "ok" else "warning" if normalized["status"] == "warn" else "degraded" if normalized["status"] == "error" else "offline",
                "health_score": 90 if normalized["status"] == "ok" else 60 if normalized["status"] == "warn" else 30 if normalized["status"] == "error" else 0,
                "health_detail": f"Heartbeat {normalized['status']}",
                "timeout_seconds": self._adapter_timeout_seconds(adapter),
                "heartbeat_timeout_seconds": self._adapter_heartbeat_timeout_seconds(adapter),
                "received_at": heartbeat.received_at,
                "latency_ms": heartbeat.latency_ms,
                "message": heartbeat.message,
                "reconnect_policy": adapter.reconnect_policy,
            }
            adapter.write(
                {
                    "last_heartbeat_at": heartbeat.received_at,
                    "state": "ready" if normalized["status"] == "ok" else "degraded",
                    "heartbeat_count": adapter.heartbeat_count + 1,
                    "listener_count": (adapter.heartbeat_count or 0) + (adapter.event_count or 0) + 1,
                    "last_success_at": heartbeat.received_at if normalized["status"] == "ok" else adapter.last_success_at,
                    "last_failure_at": heartbeat.received_at if normalized["status"] != "ok" else adapter.last_failure_at,
                    "last_error": None if normalized["status"] == "ok" else normalized["message"] or adapter.last_error,
                    "reconnect_attempts": 0 if normalized["status"] == "ok" else adapter.reconnect_attempts,
                    "last_update_success": normalized["status"] in {"ok", "warn"},
                    "last_update_started_at": heartbeat.received_at,
                    "last_update_finished_at": heartbeat.received_at,
                    "last_update_success_at": heartbeat.received_at if normalized["status"] in {"ok", "warn"} else adapter.last_update_success_at,
                    "last_update_failure_at": heartbeat.received_at if normalized["status"] not in {"ok", "warn"} else adapter.last_update_failure_at,
                    "last_exception_class": False if normalized["status"] in {"ok", "warn"} else "RuntimeHeartbeatError",
                    "last_exception_message": False if normalized["status"] in {"ok", "warn"} else normalized["message"],
                    "first_refresh_required": False,
                    "health_state": "healthy" if normalized["status"] == "ok" else "warning" if normalized["status"] == "warn" else "degraded" if normalized["status"] == "error" else "offline",
                    "health_score": 90 if normalized["status"] == "ok" else 60 if normalized["status"] == "warn" else 30 if normalized["status"] == "error" else 0,
                    "diagnostic_state": heartbeat.normalized_json,
                    "diagnostic_summary": json.dumps(heartbeat_summary, ensure_ascii=False, default=str),
                }
            )
            self._sync_connectivity_issue(adapter, self._adapter_health_from_adapter(adapter), payload)
            if normalized["status"] == "ok":
                self._resolve_runtime_issue(adapter, issue_kind="repair", detail="Heartbeat healthy after repair", payload=payload)
        if entry:
            entry.write({"last_seen_at": heartbeat.received_at})
        self.dispatch_state_only(
            {
                **normalized,
                "adapter_code": adapter.code if adapter else normalized["adapter_code"],
                "entry_code": entry.code if entry else normalized["entry_code"],
                "device_code": device.code if device else normalized["device_code"],
                "workstation_code": workstation.code if workstation else normalized["workstation_code"],
                "app_code": app.code if app else normalized["app_code"],
                "message": normalized["message"] or "Heartbeat state update",
                "result": normalized["status"],
                "registry_action": registry_action,
                "ui_refresh_hint": "device_status",
            }
        )
        return {
            "ok": True,
            "data": self._serialize_heartbeat(heartbeat),
            "message": {"type": "success", "text": "Heartbeat ingested"},
        }

    def ingest_event(self, payload):
        normalized = self._normalize_payload(payload)
        context = self._resolve_runtime_context(normalized)
        adapter = context["adapter"]
        entry = context["entry"]
        workstation = context["workstation"]
        app = context["app"]
        device, registry_action = self._upsert_gateway_device(
            normalized,
            adapter=adapter,
            entry=entry,
            workstation=workstation,
            app=app,
        )
        command = self._resolve_command(payload)
        event = self.env["gateway.runtime.event"].sudo().create(
            {
                "name": normalized["name"],
                "adapter_id": adapter.id if adapter else False,
                "entry_id": entry.id if entry else False,
                "device_id": device.id if device else False,
                "command_id": command.id if command else False,
                "event_kind": payload.get("event_kind") or "custom",
                "change_kind": self._change_kind(payload),
                "discovery_state": self._discovery_state(payload),
                "severity": normalized["severity"],
                "state": "processed",
                "app_id": app.id if app else False,
                "workstation_id": workstation.id if workstation else False,
                "session_ref": normalized["session_ref"],
                "source_signal": payload.get("signal"),
                "source_payload_id": self._fingerprint_payload(payload),
                "probe_session_id": payload.get("probe_session_id"),
                "state_version": self._fingerprint_payload(
                    {
                        "adapter_code": normalized["adapter_code"],
                        "device_code": device.code if device else normalized["device_code"],
                        "event_kind": payload.get("event_kind") or "custom",
                        "result": payload.get("result"),
                    }
                ),
                "registry_action": registry_action,
                "ui_refresh_hint": payload.get("ui_refresh_hint") or "events",
                "payload_json": normalized["payload_json"],
                "normalized_json": normalized["normalized_json"],
                "message": normalized["message"],
                "result": payload.get("result"),
                "processed_at": self._now(),
            }
        )
        if adapter:
            adapter.write({"event_count": adapter.event_count + 1, "listener_count": int(adapter.heartbeat_count or 0) + int(adapter.event_count or 0) + 1})
            if normalized["severity"] in {"high", "critical"}:
                event_summary = {
                    "code": adapter.code,
                    "adapter_type": adapter.adapter_type,
                    "severity": normalized["severity"],
                    "health_state": "warning" if normalized["severity"] == "high" else "degraded",
                    "health_score": 55 if normalized["severity"] == "high" else 35,
                    "last_event_kind": event.event_kind,
                    "last_event_message": normalized["message"] or payload.get("result"),
                    "last_event_at": event.occurred_at,
                }
                adapter.write(
                    {
                        "last_failure_at": event.occurred_at,
                        "last_error": normalized["message"] or payload.get("result") or adapter.last_error,
                        "last_update_success": False,
                        "last_update_failure_at": event.occurred_at,
                        "last_exception_class": "RuntimeEventError",
                        "last_exception_message": normalized["message"] or payload.get("result"),
                        "health_state": "warning" if normalized["severity"] == "high" else "degraded",
                        "health_score": 55 if normalized["severity"] == "high" else 35,
                        "diagnostic_summary": json.dumps(event_summary, ensure_ascii=False, default=str),
                    }
                )
                self._upsert_runtime_issue(
                    adapter,
                    issue_kind="alarm" if event.event_kind == "alarm" else "protocol_event",
                    severity=normalized["severity"],
                    message=normalized["message"] or payload.get("result") or f"{event.event_kind} event requires attention",
                    detail=f"Runtime event kind={event.event_kind}, severity={normalized['severity']}",
                    payload=payload,
                    recommended_action="review_runtime_events",
                )
        if command and payload.get("command_result"):
            self.queue_command_execution_result(command, payload.get("command_result"))
        dispatcher = self.dispatch_topology_change if self._change_kind(payload) == "topology" else self.dispatch_state_only
        dispatcher(
            {
                **normalized,
                "adapter_code": adapter.code if adapter else normalized["adapter_code"],
                "entry_code": entry.code if entry else normalized["entry_code"],
                "device_code": device.code if device else normalized["device_code"],
                "workstation_code": workstation.code if workstation else normalized["workstation_code"],
                "app_code": app.code if app else normalized["app_code"],
                "message": normalized["message"] or payload.get("result") or "Runtime event update",
                "result": payload.get("result") or event.event_kind,
                "change_kind": self._change_kind(payload),
                "discovery_state": self._discovery_state(payload),
                "registry_action": registry_action,
                "probe_session_id": payload.get("probe_session_id"),
                "ui_refresh_hint": payload.get("ui_refresh_hint") or "events",
            }
        )
        return {
            "ok": True,
            "data": self._serialize_event(event),
            "message": {"type": "success", "text": "Event ingested"},
        }

    def simulate_coordinator_poll(self, adapter_code=None, limit=20):
        Adapter = self.env["gateway.runtime.adapter"].sudo()
        domain = [("active", "=", True)]
        if adapter_code:
            domain.append(("code", "=", adapter_code))
        adapters = Adapter.search(domain, limit=limit)
        snapshots = []
        for adapter in adapters:
            bucket = sum(ord(ch) for ch in (adapter.code or "")) % 4
            status = ["ok", "warn", "error", "offline"][bucket]
            adapter_state = "ready" if status == "ok" else "degraded" if status in {"warn", "error"} else "offline"
            payload = {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else None,
                "device_code": adapter.device_code,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
                "app_code": adapter.app_id.code if adapter.app_id else None,
                "status": status,
                "message": f"Simulated poll for {adapter.code}",
                "latency_ms": 10 + bucket * 5,
            }
            snapshots.append(self.ingest_heartbeat(payload)["data"])
            adapter.write({"last_poll_at": self._now(), "state": adapter_state})
        return {
            "ok": True,
            "data": snapshots,
            "message": {"type": "success", "text": "Coordinator poll simulated"},
        }

    def process_queued_commands(self, limit=50):
        if not self._registry_has_model("gateway.command"):
            return {"ok": True, "data": [], "message": {"type": "warning", "text": "No gateway.command model"}}
        commands = self.env["gateway.command"].sudo().search([("state", "in", ["draft", "queued"])], limit=limit)
        results = []
        for command in commands:
            command.write(
                {
                    "state": "sent",
                    "attempt_count": command.attempt_count + 1,
                    "last_attempt_at": self._now(),
                    "request_text": command.request_text or self._format_command_request(command),
                }
            )
            results.append(self.queue_command_execution_result(command, self._demo_command_outcome(command)))
        return {
            "ok": True,
            "data": results,
            "message": {"type": "success", "text": f"Processed {len(results)} gateway commands"},
        }

    def refresh_adapter_diagnostics(self, adapter_code=None, limit=200):
        if not self._registry_has_model("gateway.runtime.adapter"):
            return {"ok": True, "data": [], "message": {"type": "warning", "text": "No runtime adapter model"}}
        Adapter = self.env["gateway.runtime.adapter"].sudo()
        domain = []
        if adapter_code:
            domain.append(("code", "=", adapter_code))
        adapters = Adapter.search(domain, limit=limit)
        payload = []
        for adapter in adapters:
            health = self._adapter_health_from_adapter(adapter)
            adapter.write(
                {
                    "health_state": health["health_state"],
                    "health_score": health["health_score"],
                    "health_detail": health["health_detail"],
                    "diagnostic_state": health["diagnostic_state"],
                    "diagnostic_summary": health["diagnostic_summary"],
                }
            )
            payload.append(
                {
                    **self._serialize_adapter(adapter),
                    "health_state": health["health_state"],
                    "health_score": health["health_score"],
                    "health_detail": health["health_detail"],
                    "diagnostic_summary": health["summary"],
                }
            )
        return {
            "ok": True,
            "data": payload,
            "summary": self.build_runtime_summary(adapter_code=adapter_code, adapters=adapters),
            "message": {"type": "success", "text": "Runtime diagnostics refreshed"},
        }

    def repair_stale_adapters(self, limit=200):
        if not self._registry_has_model("gateway.runtime.adapter"):
            return {"ok": True, "data": [], "message": {"type": "warning", "text": "No runtime adapter model"}}
        Adapter = self.env["gateway.runtime.adapter"].sudo()
        adapters = Adapter.search([("active", "=", True)], limit=limit)
        repaired = []
        for adapter in adapters:
            health = self._adapter_health_from_adapter(adapter)
            summary = health["summary"]
            stale = summary.get("stale")
            reconnect_policy = adapter.reconnect_policy or "auto"
            reconnect_budget = max(0, int(adapter.max_reconnect_attempts or 0) - int(adapter.reconnect_attempts or 0))
            values = {
                "health_state": health["health_state"],
                "health_score": health["health_score"],
                "health_detail": health["health_detail"],
                "diagnostic_state": health["diagnostic_state"],
                "diagnostic_summary": health["diagnostic_summary"],
            }
            if stale and reconnect_policy == "auto" and reconnect_budget > 0:
                values.update(
                    {
                        "reconnect_attempts": adapter.reconnect_attempts + 1,
                        "last_reconnect_at": self._now(),
                        "health_state": "degraded",
                        "health_score": 25,
                        "health_detail": f"Reconnect attempt {adapter.reconnect_attempts + 1} queued",
                    }
                )
                self._upsert_runtime_issue(
                    adapter,
                    issue_kind="repair",
                    severity="high",
                    message=f"Reconnect attempt {adapter.reconnect_attempts + 1} queued",
                    detail="Adapter heartbeat is stale and auto-repair has been queued.",
                    payload=summary,
                    recommended_action="reload_runtime",
                    state=self._issue_state_progress_value(),
                )
            elif stale:
                values.update(
                    {
                        "state": "offline",
                        "health_state": "offline",
                        "health_score": 0,
                    }
                )
                self._upsert_runtime_issue(
                    adapter,
                    issue_kind="connectivity",
                    severity="high",
                    message="Adapter heartbeat is stale and reconnect budget is exhausted",
                    detail="Runtime marked adapter offline after stale heartbeat evaluation.",
                    payload=summary,
                    recommended_action="repair_runtime",
                )
            adapter.write(values)
            repaired.append(self._serialize_adapter(adapter))
        return {
            "ok": True,
            "data": repaired,
            "summary": self.build_runtime_summary(adapters=adapters),
            "message": {"type": "success", "text": "Stale adapters evaluated"},
        }

    def request_adapter_reconnect(self, adapter_code=None, limit=1):
        if not self._registry_has_model("gateway.runtime.adapter"):
            return {"ok": False, "errors": ["No runtime adapter model"]}
        Adapter = self.env["gateway.runtime.adapter"].sudo()
        domain = [("active", "=", True)]
        if adapter_code:
            domain.append(("code", "=", adapter_code))
        adapters = Adapter.search(domain, limit=limit)
        results = []
        for adapter in adapters:
            adapter.write(
                {
                    "reconnect_attempts": adapter.reconnect_attempts + 1,
                    "last_reconnect_at": self._now(),
                    "health_state": "warning",
                    "health_score": 40,
                    "health_detail": f"Reconnect requested for {adapter.code}",
                }
            )
            self._upsert_runtime_issue(
                adapter,
                issue_kind="repair",
                severity="medium",
                message=f"Reconnect requested for {adapter.code}",
                detail="Manual reconnect was requested for this runtime adapter.",
                payload={"adapter_code": adapter.code, "reconnect_attempts": adapter.reconnect_attempts + 1},
                recommended_action="reload_runtime",
                state=self._issue_state_progress_value(),
            )
            self._log_runtime_event(
                {
                    "event_kind": "diagnostic",
                    "name": f"Reconnect requested: {adapter.code}",
                    "adapter_code": adapter.code,
                    "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
                    "app_code": adapter.app_id.code if adapter.app_id else None,
                    "message": f"Reconnect requested for {adapter.code}",
                    "severity": "medium",
                    "result": "reconnect_requested",
                }
            )
            results.append(self._serialize_adapter(adapter))
        return {
            "ok": True,
            "data": results,
            "summary": self.build_runtime_summary(adapter_code=adapter_code, adapters=adapters),
            "message": {"type": "success", "text": "Reconnect requested"},
        }

    def build_runtime_summary(self, adapter_code=None, adapters=None):
        Adapter = self.env["gateway.runtime.adapter"].sudo() if self._registry_has_model("gateway.runtime.adapter") else None
        if adapters is None and Adapter is not None:
            domain = [("active", "=", True)]
            if adapter_code:
                domain.append(("code", "=", adapter_code))
            adapters = Adapter.search(domain, limit=200)
        adapters = adapters or []
        counts = {
            "total": len(adapters),
            "healthy": 0,
            "warning": 0,
            "degraded": 0,
            "offline": 0,
            "unknown": 0,
            "stale": 0,
            "auto_reconnect": 0,
            "manual_reconnect": 0,
        }
        issue_counts = {"total": 0, "open": 0, "resolved": 0, "fixable": 0, "open_fixable": 0}
        adapter_payload = []
        for adapter in adapters:
            health = self._adapter_health_from_adapter(adapter)
            summary = health["summary"]
            issue_summary = self._runtime_issue_summary(adapter)
            counts[health["health_state"]] = counts.get(health["health_state"], 0) + 1
            if summary.get("stale"):
                counts["stale"] += 1
            if adapter.reconnect_policy == "auto":
                counts["auto_reconnect"] += 1
            if adapter.reconnect_policy == "manual":
                counts["manual_reconnect"] += 1
            issue_counts["total"] += issue_summary["total"]
            issue_counts["open"] += issue_summary["open"]
            issue_counts["resolved"] += issue_summary["resolved"]
            issue_counts["fixable"] += issue_summary["fixable"]
            issue_counts["open_fixable"] += issue_summary["open_fixable"]
            adapter_payload.append(
                {
                    **self._serialize_adapter(adapter),
                    "health_state": health["health_state"],
                    "health_score": health["health_score"],
                    "health_detail": health["health_detail"],
                    "diagnostic_summary": health["summary"],
                    "issue_summary": issue_summary,
                }
            )
        return {
            "generated_at": self._now(),
            "counts": counts,
            "issues": issue_counts,
            "adapters": adapter_payload,
        }

    def runtime_diagnostics(self, payload=None):
        payload = self._as_dict(payload)
        adapter_code = payload.get("adapter_code")
        summary = self.build_runtime_summary(adapter_code=adapter_code)
        return {
            "ok": True,
            "data": summary,
            "message": {"type": "success", "text": "Runtime diagnostics ready"},
        }

    def queue_command_execution_result(self, command, outcome):
        if isinstance(command, int):
            command = self.env["gateway.command"].sudo().browse(command).exists()
        elif hasattr(command, "exists"):
            command = command.exists()
        if not command:
            return {"ok": False, "errors": ["Command not found"]}
        if isinstance(outcome, dict):
            final_state = outcome.get("state") or outcome.get("result") or "done"
            response_text = outcome.get("response_text") or json.dumps(outcome, ensure_ascii=False, default=str)
            error_message = outcome.get("error_message")
            diagnostic_state = outcome.get("diagnostic_state") or response_text
        else:
            final_state = outcome
            response_text = str(outcome)
            error_message = None
            diagnostic_state = response_text
        if final_state not in {"done", "failed"}:
            final_state = "done"
        values = {
            "state": final_state,
            "response_text": response_text if final_state == "done" else command.response_text,
            "error_message": error_message if final_state == "failed" else command.error_message,
            "diagnostic_state": diagnostic_state,
            "processed_at": self._now(),
        }
        if final_state == "failed" and not values["error_message"]:
            values["error_message"] = "Gateway runtime mock failure"
        command.write(values)
        runtime_adapter = self._resolve_adapter_for_command(command)
        if runtime_adapter:
            adapter_values = {"command_count": runtime_adapter.command_count + 1}
            if final_state == "done":
                adapter_summary = {
                    "code": runtime_adapter.code,
                    "adapter_type": runtime_adapter.adapter_type,
                    "health_state": "healthy",
                    "health_score": 90,
                    "last_command_state": final_state,
                    "last_command_code": command.code,
                    "last_command_at": values["processed_at"],
                }
                adapter_values.update(
                    {
                        "last_success_at": values["processed_at"],
                        "health_state": "healthy",
                        "health_score": 90,
                        "last_error": False,
                        "diagnostic_summary": json.dumps(adapter_summary, ensure_ascii=False, default=str),
                    }
                )
            else:
                adapter_summary = {
                    "code": runtime_adapter.code,
                    "adapter_type": runtime_adapter.adapter_type,
                    "health_state": "warning",
                    "health_score": 45,
                    "last_command_state": final_state,
                    "last_command_code": command.code,
                    "last_command_at": values["processed_at"],
                    "error_message": values["error_message"],
                }
                adapter_values.update(
                    {
                        "last_failure_at": values["processed_at"],
                        "last_error": values["error_message"],
                        "health_state": "warning",
                        "health_score": 45,
                        "diagnostic_summary": json.dumps(adapter_summary, ensure_ascii=False, default=str),
                    }
                )
            runtime_adapter.write(adapter_values)
            if final_state == "done":
                self._resolve_runtime_issue(runtime_adapter, issue_kind="command_failure", detail="Latest command completed successfully", payload={"command_code": command.code})
            else:
                self._upsert_runtime_issue(
                    runtime_adapter,
                    issue_kind="command_failure",
                    severity="high",
                    message=values["error_message"] or "Gateway command failed",
                    detail=f"Command {command.code} failed during runtime execution.",
                    payload={"command_code": command.code, "diagnostic_state": diagnostic_state},
                    recommended_action="review_runtime_events",
                )
        self._log_runtime_event(
            {
                "event_kind": "command",
                "name": f"Command {command.code} {final_state}",
                "command_id": command.id,
                "entry_id": command.entry_id.id if command.entry_id else False,
                "device_id": command.device_id.id if command.device_id else False,
                "message": values.get("error_message") if final_state == "failed" else "Command processed",
                "severity": "high" if final_state == "failed" else "low",
                "result": final_state,
            }
        )
        return self._serialize_command(command)

    def _resolve_adapter_for_command(self, command):
        if not self._registry_has_model("gateway.runtime.adapter") or not command.entry_id:
            return None
        domain = [("entry_id", "=", command.entry_id.id)]
        if command.device_id and self._registry_has_model("shopfloor.workstation"):
            domain.append(("device_code", "=", command.device_id.code))
        return self.env["gateway.runtime.adapter"].sudo().search(domain, limit=1)

    def _log_runtime_event(self, payload):
        if not self._registry_has_model("gateway.runtime.event"):
            return None
        normalized = self._normalize_payload(payload)
        context = self._resolve_runtime_context(payload)
        adapter = context["adapter"]
        entry = context["entry"]
        device = context["device"]
        workstation = context["workstation"]
        app = context["app"]
        command = self._resolve_command(payload)
        return self.env["gateway.runtime.event"].sudo().create(
            {
                "name": normalized["name"],
                "event_kind": payload.get("event_kind") or "custom",
                "adapter_id": adapter.id if adapter else False,
                "entry_id": entry.id if entry else False,
                "device_id": device.id if device else False,
                "command_id": command.id if command else False,
                "app_id": app.id if app else False,
                "workstation_id": workstation.id if workstation else False,
                "session_ref": normalized["session_ref"],
                "change_kind": payload.get("change_kind") or self._change_kind(payload),
                "discovery_state": payload.get("discovery_state") or self._discovery_state(payload),
                "source_signal": payload.get("source_signal") or payload.get("signal"),
                "source_payload_id": payload.get("source_payload_id") or self._fingerprint_payload(payload),
                "probe_session_id": payload.get("probe_session_id"),
                "state_version": payload.get("state_version"),
                "registry_action": payload.get("registry_action"),
                "ui_refresh_hint": payload.get("ui_refresh_hint"),
                "severity": normalized["severity"],
                "message": normalized["message"] or payload.get("result") or "Runtime event",
                "payload_json": normalized["payload_json"],
                "normalized_json": normalized["normalized_json"],
                "result": payload.get("result"),
                "processed_at": self._now(),
                "state": "processed",
            }
        )

    def _demo_command_outcome(self, command):
        payload = self._safe_json(command.payload_json)
        if payload.get("simulate_result") in {"fail", "failed"}:
            return {"state": "failed", "error_message": payload.get("error_message") or "Simulated failure"}
        if payload.get("force_fail") is True:
            return {"state": "failed", "error_message": "Forced failure"}
        if (command.command_type or "").lower() in {"fail", "error", "reject"}:
            return {"state": "failed", "error_message": "Command type rejected"}
        bucket = sum(ord(ch) for ch in (command.code or "")) % 5
        if bucket == 0:
            return {"state": "failed", "error_message": "Deterministic demo failure"}
        return {
            "state": "done",
            "response_text": json.dumps(
                {"command_code": command.code, "status": "done", "bucket": bucket},
                ensure_ascii=False,
            ),
            "diagnostic_state": json.dumps({"bucket": bucket, "processed": True}, ensure_ascii=False),
        }

    def _format_command_request(self, command):
        return json.dumps(
            {
                "code": command.code,
                "command_type": command.command_type,
                "entry_code": command.entry_id.code if command.entry_id else None,
                "device_code": command.device_id.code if command.device_id else None,
                "signal_code": command.signal_id.code if command.signal_id else None,
            },
            ensure_ascii=False,
        )

    def _safe_json(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _serialize_adapter(self, record):
        capability = self.build_capability_payload(adapter=record, payload={"adapter_code": record.code})
        coordinator = self._coordinator_state_payload(adapter=record, payload={"adapter_code": record.code})
        issue_summary = self._runtime_issue_summary(record)
        return {
            "id": record.id,
            "name": record.name,
            "code": record.code,
            "state": record.state,
            "adapter_type": record.adapter_type,
            "entry": record.entry_id.code if record.entry_id else None,
            "workstation": record.workstation_id.code if record.workstation_id else None,
            "device_code": record.device_code,
            "runtime_unique_id": record.runtime_unique_id,
            "health_state": record.health_state,
            "health_score": record.health_score,
            "health_detail": record.health_detail,
            "diagnostic_summary": self._parse_json(record.diagnostic_summary),
            "diagnostic_state": self._parse_json(record.diagnostic_state),
            "coordinator_mode": record.coordinator_mode,
            "update_interval_seconds": record.update_interval_seconds,
            "retry_after_seconds": record.retry_after_seconds,
            "last_update_success": record.last_update_success,
            "last_exception_class": record.last_exception_class,
            "last_exception_message": record.last_exception_message,
            "last_update_started_at": record.last_update_started_at,
            "last_update_finished_at": record.last_update_finished_at,
            "last_update_success_at": record.last_update_success_at,
            "last_update_failure_at": record.last_update_failure_at,
            "first_refresh_required": record.first_refresh_required,
            "always_update": record.always_update,
            "listener_count": record.listener_count,
            "timeout_seconds": record.timeout_seconds,
            "heartbeat_timeout_seconds": record.heartbeat_timeout_seconds,
            "supports_push": record.supports_push,
            "supports_poll": record.supports_poll,
            "supports_read": record.supports_read,
            "supports_write": record.supports_write,
            "supports_subscribe": record.supports_subscribe,
            "supports_discovery": record.supports_discovery,
            "supports_ack": record.supports_ack,
            "supports_diagnostics": record.supports_diagnostics,
            "supports_repair": record.supports_repair,
            "supports_reload": record.supports_reload,
            "supports_load": record.supports_load,
            "supports_unload": record.supports_unload,
            "supports_dispatch": record.supports_dispatch,
            "reconnect_policy": record.reconnect_policy,
            "reconnect_delay_seconds": record.reconnect_delay_seconds,
            "max_reconnect_attempts": record.max_reconnect_attempts,
            "reconnect_attempts": record.reconnect_attempts,
            "last_reconnect_at": record.last_reconnect_at,
            "last_success_at": record.last_success_at,
            "last_failure_at": record.last_failure_at,
            "last_error": record.last_error,
            "last_heartbeat_at": record.last_heartbeat_at,
            "last_poll_at": record.last_poll_at,
            "heartbeat_count": record.heartbeat_count,
            "event_count": record.event_count,
            "command_count": record.command_count,
            "lifecycle_state": record.lifecycle_state,
            "lifecycle_detail": record.lifecycle_detail,
            "capability_summary": record.capability_summary,
            "capability": capability,
            "coordinator": coordinator,
            "issue_summary": issue_summary,
        }

    def _serialize_heartbeat(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "code": record.code,
            "status": record.status,
            "state": record.state,
            "adapter": record.adapter_id.code if record.adapter_id else None,
            "entry": record.entry_id.code if record.entry_id else None,
            "device": record.device_id.code if record.device_id else None,
            "message": record.message,
            "received_at": record.received_at,
        }

    def _serialize_event(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "code": record.code,
            "event_kind": record.event_kind,
            "change_kind": record.change_kind,
            "discovery_state": record.discovery_state,
            "severity": record.severity,
            "state": record.state,
            "adapter": record.adapter_id.code if record.adapter_id else None,
            "entry": record.entry_id.code if record.entry_id else None,
            "device": record.device_id.code if record.device_id else None,
            "command": record.command_id.code if record.command_id else None,
            "source_signal": record.source_signal,
            "source_payload_id": record.source_payload_id,
            "probe_session_id": record.probe_session_id,
            "state_version": record.state_version,
            "registry_action": record.registry_action,
            "ui_refresh_hint": record.ui_refresh_hint,
            "message": record.message,
            "result": record.result,
        }

    def _serialize_probe_session(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "code": record.code,
            "session_key": record.session_key,
            "adapter": record.adapter_id.code if record.adapter_id else None,
            "protocol": record.protocol,
            "capability": record.capability,
            "probe_kind": record.probe_kind,
            "target_ref": record.target_ref,
            "source_signal": record.source_signal,
            "source_payload_id": record.source_payload_id,
            "change_kind": record.change_kind,
            "discovery_state": record.discovery_state,
            "state": record.state,
            "result_state": record.result_state,
            "severity": record.severity,
            "detail": record.detail,
            "state_version": record.state_version,
            "normalized_json": record.normalized_json,
            "ui_refresh_hint": record.ui_refresh_hint,
            "request_json": record.request_json,
            "response_json": record.response_json,
            "payload_json": record.payload_json,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "latency_ms": record.latency_ms,
            "runtime_event_id": record.runtime_event_id.id if record.runtime_event_id else None,
            "summary": record.summary,
            "message": record.message,
            "last_error": record.last_error,
            "issue_id": record.issue_id.id if record.issue_id else None,
            "issue_key": record.issue_key,
            "request_summary": record.request_summary,
            "response_summary": record.response_summary,
            "result_summary": record.result_summary,
            "session_summary": record.session_summary,
        }

    def _serialize_command(self, record):
        return {
            "id": record.id,
            "code": record.code,
            "state": record.state,
            "attempt_count": record.attempt_count,
            "processed_at": record.processed_at,
            "diagnostic_state": record.diagnostic_state,
        }
