import json
from urllib.parse import urlparse

from odoo.fields import Datetime

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService

from .mqtt_client import GatewayMqttClientHelper


class GatewayMqttBridgeService:
    def __init__(self, env):
        self.env = env
        self.runtime = GatewayRuntimeService(env)
        self.client_helper = GatewayMqttClientHelper()

    def _registry_has_model(self, model_name):
        return model_name in self.env.registry.models

    def _now(self):
        return Datetime.now()

    def _safe_json(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {"payload": parsed}
            except Exception:
                return {"payload": value}
        return {"payload": value}

    def _adapter_payload_from_record(self, record):
        return {
            "adapter_id": record.id,
            "code": record.code,
            "name": record.name,
            "adapter_type": "mqtt",
            "entry_code": record.entry_id.code if record.entry_id else None,
            "workstation_code": record.workstation_id.code if record.workstation_id else None,
            "device_code": record.device_code,
            "broker_url": record.broker_url,
            "client_id": record.client_id,
            "username": record.username,
            "password": record.password,
            "base_topic": record.base_topic,
            "qos": record.qos,
            "retain_default": record.retain_default,
            "connection_target": record.broker_url or record.connection_target,
            "config_json": record.config_json,
            "config_text": record.config_text,
        }

    def _topic_payload_from_record(self, record):
        return {
            "topic_id": record.id,
            "adapter_code": record.adapter_id.code if record.adapter_id else None,
            "code": record.code,
            "name": record.name,
            "topic_name": record.topic_name,
            "topic_kind": record.topic_kind,
            "event_kind": record.event_kind,
        }

    def _resolve_adapter_record(self, payload):
        if not self._registry_has_model("gateway.mqtt.adapter"):
            return None
        MQTT = self.env["gateway.mqtt.adapter"].sudo()
        adapter_code = payload.get("adapter_code") or payload.get("code") or payload.get("gateway_entry_code")
        if adapter_code:
            adapter = MQTT.search([("code", "=", str(adapter_code))], limit=1)
            if adapter:
                return adapter
        topic_name = payload.get("topic") or payload.get("topic_name")
        if topic_name:
            adapter = MQTT.search([("topic_ids.topic_name", "=", str(topic_name))], limit=1)
            if adapter:
                return adapter
        return None

    def _resolve_adapter_from_target(self, target):
        if hasattr(target, "_name") and getattr(target, "_name", None) == "gateway.mqtt.adapter":
            return target, self._adapter_payload_from_record(target)
        if hasattr(target, "_name") and getattr(target, "_name", None) == "gateway.mqtt.topic":
            return target.adapter_id, self._topic_payload_from_record(target)
        payload = self._safe_json(target)
        return self._resolve_adapter_record(payload), payload

    def _resolve_topic_record(self, adapter, payload):
        if not adapter or not self._registry_has_model("gateway.mqtt.topic"):
            return None
        Topic = self.env["gateway.mqtt.topic"].sudo()
        candidates = [payload.get("topic"), payload.get("topic_name"), payload.get("topic_code"), payload.get("code")]
        for candidate in candidates:
            if not candidate:
                continue
            topic = Topic.search([("adapter_id", "=", adapter.id), ("topic_name", "=", str(candidate))], limit=1)
            if topic:
                return topic
            topic = Topic.search([("adapter_id", "=", adapter.id), ("code", "=", str(candidate))], limit=1)
            if topic:
                return topic
        return None

    def _resolve_topic_from_target(self, adapter, payload=None, topic_name=None, topic_code=None):
        if not adapter or not self._registry_has_model("gateway.mqtt.topic"):
            return None
        payload = payload or {}
        Topic = self.env["gateway.mqtt.topic"].sudo()
        candidates = [topic_code, topic_name, payload.get("topic_code"), payload.get("topic"), payload.get("topic_name"), payload.get("code")]
        for candidate in candidates:
            if not candidate:
                continue
            topic = Topic.search([("adapter_id", "=", adapter.id), ("code", "=", str(candidate))], limit=1)
            if topic:
                return topic
            topic = Topic.search([("adapter_id", "=", adapter.id), ("topic_name", "=", str(candidate))], limit=1)
            if topic:
                return topic
        return None

    def _compose_topic_path(self, adapter, topic_name):
        topic_name = (topic_name or "").strip("/")
        base_topic = (adapter.base_topic or "").strip("/") if adapter else ""
        if not topic_name:
            return base_topic
        if not base_topic:
            return topic_name
        if topic_name.startswith(base_topic):
            return topic_name
        return "/".join(part for part in [base_topic, topic_name] if part)

    def _parse_broker_url(self, broker_url):
        broker_url = (broker_url or "").strip()
        if not broker_url:
            return {"scheme": "mqtt", "host": None, "port": 1883}
        if "://" not in broker_url:
            if ":" in broker_url:
                host, port = broker_url.rsplit(":", 1)
                try:
                    port = int(port)
                except Exception:
                    port = 1883
                return {"scheme": "mqtt", "host": host or None, "port": port}
            return {"scheme": "mqtt", "host": broker_url, "port": 1883}
        parsed = urlparse(broker_url)
        scheme = parsed.scheme or "mqtt"
        host = parsed.hostname or parsed.path or None
        port = parsed.port or (8883 if scheme in {"mqtts", "ssl", "tls", "wss"} else 1883)
        return {
            "scheme": scheme,
            "host": host,
            "port": port,
            "path": parsed.path or "",
            "username": parsed.username,
            "password_set": bool(parsed.password),
        }

    def _log_diagnostic(self, adapter, topic=None, direction="preview", event_kind="diagnostic", status="simulated", message="", payload=None, result=None, topic_path=None):
        if not adapter or not self._registry_has_model("gateway.mqtt.diagnostic"):
            return None
        Diagnostic = self.env["gateway.mqtt.diagnostic"].sudo()
        runtime_adapter = self._find_runtime_adapter(adapter)
        values = {
            "name": message or f"{adapter.code} {event_kind}",
            "code": self.env["ir.sequence"].next_by_code("gateway.mqtt.diagnostic") or "New",
            "adapter_id": adapter.id,
            "topic_id": topic.id if topic else False,
            "runtime_adapter_id": runtime_adapter.id if runtime_adapter else False,
            "direction": direction,
            "event_kind": event_kind,
            "status": status,
            "topic_path": topic_path or (topic.topic_name if topic else None),
            "broker_url": adapter.broker_url,
            "client_id": adapter.client_id,
            "message": message,
            "payload_json": json.dumps(self._safe_json(payload), ensure_ascii=False, default=str),
            "result_json": json.dumps(result if result is not None else {}, ensure_ascii=False, default=str),
            "occurred_at": self._now(),
            "processed_at": self._now(),
        }
        return Diagnostic.create(values)

    def _normalize_topic_payload(self, payload, topic=None, adapter=None):
        data = self._safe_json(payload)
        topic_name = data.get("topic") or data.get("topic_name") or (topic.topic_name if topic else None)
        topic_kind = data.get("topic_kind") or (topic.topic_kind if topic else "event")
        status = data.get("status") or (topic.default_status if topic else "ok")
        message = data.get("message") or data.get("text") or data.get("payload") or ""
        normalized = {
            "name": data.get("name") or topic_name or "MQTT Topic",
            "code": data.get("code") or (topic.code if topic else None) or topic_name,
            "adapter_code": adapter.code if adapter else data.get("adapter_code"),
            "entry_code": adapter.entry_id.code if adapter and adapter.entry_id else data.get("entry_code"),
            "device_code": adapter.device_code if adapter else data.get("device_code"),
            "workstation_code": adapter.workstation_id.code if adapter and adapter.workstation_id else data.get("workstation_code"),
            "app_code": adapter.app_id.code if adapter and adapter.app_id else data.get("app_code"),
            "session_ref": data.get("session_ref"),
            "topic": topic_name,
            "topic_kind": topic_kind,
            "event_kind": data.get("event_kind") or (topic.event_kind if topic else "custom"),
            "status": status,
            "severity": data.get("severity") or ("low" if status == "ok" else "medium" if status == "warn" else "high"),
            "message": message,
            "payload_json": json.dumps(data, ensure_ascii=False, default=str),
        }
        normalized["normalized_json"] = json.dumps(normalized, ensure_ascii=False, default=str)
        return normalized

    def _find_runtime_adapter(self, record):
        if not self._registry_has_model("gateway.runtime.adapter"):
            return None
        return self.env["gateway.runtime.adapter"].sudo().search([("code", "=", record.code)], limit=1)

    def _adapter_payload_for_runtime(self, record):
        return {
            "adapter_id": record.id,
            "code": record.code,
            "name": record.name,
            "adapter_type": "mqtt",
            "entry_code": record.entry_id.code if record.entry_id else None,
            "workstation_code": record.workstation_id.code if record.workstation_id else None,
            "device_code": record.device_code,
            "connection_target": record.broker_url or record.connection_target,
            "broker_url": record.broker_url,
            "client_id": record.client_id,
            "username": record.username,
            "base_topic": record.base_topic,
            "qos": record.qos,
            "retain_default": record.retain_default,
            "config_json": record.config_json,
            "config_text": record.config_text,
        }

    def build_runtime_payload(self, target):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        runtime_payload = self._adapter_payload_for_runtime(adapter)
        capability = self.runtime.build_capability_payload(payload=runtime_payload)
        diagnostics = self.runtime.runtime_diagnostics({"adapter_code": adapter.code})
        coordinator = capability.get("coordinator", {})
        runtime_payload.update(
            {
                "transport": "mqtt",
                "coordinator_mode": "hybrid",
                "update_interval_seconds": 30,
                "retry_after_seconds": coordinator.get("retry_after", 0),
                "capability_json": capability.get("capability_json"),
                "coordinator_json": json.dumps(coordinator, ensure_ascii=False, default=str),
                "diagnostic_summary_json": json.dumps(diagnostics.get("data", {}), ensure_ascii=False, default=str),
                "runtime_context_json": json.dumps(
                    {
                        "payload": payload,
                        "capability": capability,
                        "coordinator": coordinator,
                        "diagnostics": diagnostics.get("data"),
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            }
        )
        return {
            "ok": True,
            "data": runtime_payload,
            "capability": capability,
            "coordinator": coordinator,
            "diagnostics": diagnostics.get("data"),
        }

    def build_runtime_summary(self, target):
        adapter, _payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        runtime_payload = self.build_runtime_payload(adapter)
        diagnostics = self.runtime.runtime_diagnostics({"adapter_code": adapter.code})
        capability = self.runtime.build_capability_payload(payload=runtime_payload.get("data") if runtime_payload.get("ok") else self._adapter_payload_for_runtime(adapter))
        return {
            "ok": True,
            "data": {
                "adapter": self._adapter_payload_for_runtime(adapter),
                "runtime_payload": runtime_payload.get("data") if runtime_payload.get("ok") else {},
                "capability": capability,
                "coordinator": capability.get("coordinator", {}),
                "diagnostics": diagnostics.get("data"),
                "diagnostic_summary_json": json.dumps(diagnostics.get("data", {}), ensure_ascii=False, default=str),
            },
            "message": {"type": "success", "text": "MQTT runtime summary ready"},
        }

    def _apply_runtime_result(self, adapter, result):
        if not adapter:
            return result
        values = {
            "diagnostic_state": json.dumps(result, ensure_ascii=False, default=str),
            "last_sync_at": self._now(),
        }
        data = result.get("data") if isinstance(result, dict) else {}
        if isinstance(data, dict):
            runtime_adapter = self._find_runtime_adapter(adapter)
            if runtime_adapter:
                values["runtime_adapter_id"] = runtime_adapter.id
            adapter_data = data.get("adapter") or {}
            if adapter_data.get("state"):
                values["state"] = adapter_data["state"]
        adapter.write(values)
        return result

    def refresh_runtime_adapter(self, target, reason=None):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        result = self.runtime.refresh_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": payload.get("entry_code"),
                "workstation_code": payload.get("workstation_code"),
                "device_code": payload.get("device_code") or adapter.device_code,
                "reason": reason or payload.get("reason") or "manual_refresh",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def repair_runtime_adapter(self, target, reason=None):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        result = self.runtime.repair_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": payload.get("entry_code"),
                "workstation_code": payload.get("workstation_code"),
                "device_code": payload.get("device_code") or adapter.device_code,
                "reason": reason or payload.get("reason") or "manual_repair",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def load_runtime_adapter(self, target, reason=None):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        result = self.runtime.load_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": payload.get("entry_code"),
                "workstation_code": payload.get("workstation_code"),
                "device_code": payload.get("device_code") or adapter.device_code,
                "reason": reason or payload.get("reason") or "manual_load",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def reload_runtime_adapter(self, target, reason=None):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        result = self.runtime.reload_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": payload.get("entry_code"),
                "workstation_code": payload.get("workstation_code"),
                "device_code": payload.get("device_code") or adapter.device_code,
                "reason": reason or payload.get("reason") or "manual_reload",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def _register_runtime_adapter(self, record):
        runtime_payload = self.build_runtime_payload(record)
        values = runtime_payload.get("data") if runtime_payload.get("ok") else self._adapter_payload_for_runtime(record)
        result = self.runtime.register_adapter_definition(values)
        runtime_adapter = self._find_runtime_adapter(record)
        if runtime_adapter:
            record.write(
                {
                    "runtime_adapter_id": runtime_adapter.id,
                    "state": runtime_adapter.state if runtime_adapter.state else record.state,
                    "last_sync_at": self._now(),
                    "diagnostic_state": json.dumps(result, ensure_ascii=False, default=str),
                }
            )
        self._log_diagnostic(
            record,
            direction="outbound",
            event_kind="registration",
            status="ok" if result.get("ok") else "error",
            message=f"Runtime adapter registration for {record.code}",
            payload=values,
            result=result,
            topic_path=record.base_topic,
        )
        return result

    def register_adapter_from_records(self, records):
        results = []
        for record in records:
            runtime_payload = self.build_runtime_payload(record)
            results.append(self.register_adapter_from_payload(runtime_payload.get("data") if runtime_payload.get("ok") else self._adapter_payload_for_runtime(record)))
        return {"ok": True, "data": results}

    def register_adapter_from_payload(self, payload):
        data = self._safe_json(payload)
        if "adapter_id" in data and self._registry_has_model("gateway.mqtt.adapter"):
            record = self.env["gateway.mqtt.adapter"].sudo().browse(int(data["adapter_id"])).exists()
            if record:
                return self._register_runtime_adapter(record)
        if self._registry_has_model("gateway.mqtt.adapter") and data.get("code"):
            record = self.env["gateway.mqtt.adapter"].sudo().search([("code", "=", str(data["code"]))], limit=1)
            if record:
                return self._register_runtime_adapter(record)
        return {"ok": False, "errors": ["MQTT adapter not found"]}

    def build_broker_connection_settings(self, target):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        broker_url = payload.get("broker_url") or adapter.broker_url or payload.get("connection_target") or adapter.connection_target
        parsed = self._parse_broker_url(broker_url)
        settings = {
            "adapter_id": adapter.id,
            "adapter_code": adapter.code,
            "name": adapter.name,
            "broker_url": broker_url,
            "scheme": parsed.get("scheme"),
            "host": parsed.get("host"),
            "port": parsed.get("port") or 1883,
            "path": parsed.get("path"),
            "client_id": payload.get("client_id") or adapter.client_id or f"{adapter.code}-client",
            "username": payload.get("username") or adapter.username,
            "password_set": bool(payload.get("password") or adapter.password),
            "base_topic": payload.get("base_topic") or adapter.base_topic,
            "qos": payload.get("qos") if payload.get("qos") is not None else adapter.qos,
            "retain_default": payload.get("retain_default") if payload.get("retain_default") is not None else adapter.retain_default,
            "connection_target": payload.get("connection_target") or adapter.connection_target or broker_url,
            "client_backend": self.client_helper.describe(),
        }
        return {"ok": True, "data": settings, "message": {"type": "success", "text": "Broker settings built"}}

    def build_subscription_plan(self, target):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        topics = adapter.topic_ids.sorted(lambda record: (record.sequence, record.id))
        subscriptions = []
        for topic in topics:
            topic_path = self._compose_topic_path(adapter, topic.topic_name)
            handler = "ingest_event"
            if topic.topic_kind in {"heartbeat", "status"}:
                handler = "ingest_heartbeat"
            elif topic.topic_kind == "command":
                handler = "publish_command"
            subscriptions.append(
                {
                    "topic_id": topic.id,
                    "topic_code": topic.code,
                    "topic_name": topic.topic_name,
                    "topic_path": topic_path,
                    "topic_kind": topic.topic_kind,
                    "event_kind": topic.event_kind,
                    "direction": "outbound" if topic.topic_kind == "command" else "inbound",
                    "handler": handler,
                    "qos": topic.qos,
                    "retain": topic.retain,
                }
            )
        if not subscriptions:
            subscriptions.append(
                {
                    "topic_id": None,
                    "topic_code": None,
                    "topic_name": "#",
                    "topic_path": self._compose_topic_path(adapter, "#"),
                    "topic_kind": "event",
                    "event_kind": "custom",
                    "direction": "inbound",
                    "handler": "ingest_event",
                    "qos": adapter.qos,
                    "retain": adapter.retain_default,
                }
            )
        plan = {
            "adapter_id": adapter.id,
            "adapter_code": adapter.code,
            "base_topic": adapter.base_topic,
            "subscription_count": len(subscriptions),
            "subscriptions": subscriptions,
        }
        return {"ok": True, "data": plan, "message": {"type": "success", "text": "Subscription plan built"}}

    def preview_runtime_registration(self, target):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        settings = self.build_broker_connection_settings(adapter)
        plan = self.build_subscription_plan(adapter)
        preview = {
            "adapter": self._adapter_payload_for_runtime(adapter),
            "connection": settings.get("data") if settings.get("ok") else {},
            "subscriptions": plan.get("data", {}).get("subscriptions", []),
            "client_backend": self.client_helper.describe(),
        }
        diagnostic = self._log_diagnostic(
            adapter,
            direction="preview",
            event_kind="registration",
            status="simulated",
            message=f"Runtime registration preview for {adapter.code}",
            payload={"settings": settings.get("data"), "plan": plan.get("data"), "source": payload},
            result=preview,
            topic_path=adapter.base_topic,
        )
        preview["diagnostic_id"] = diagnostic.id if diagnostic else None
        return {"ok": True, "data": preview, "message": {"type": "success", "text": "Runtime registration preview built"}}

    def preview_subscription_plan(self, target):
        adapter, payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        plan = self.build_subscription_plan(adapter)
        diagnostic = self._log_diagnostic(
            adapter,
            direction="preview",
            event_kind="subscription",
            status="simulated",
            message=f"Subscription preview for {adapter.code}",
            payload={"plan": plan.get("data"), "source": payload},
            result=plan.get("data"),
            topic_path=adapter.base_topic,
        )
        result = dict(plan)
        if result.get("data"):
            result["data"] = dict(result["data"])
            result["data"]["diagnostic_id"] = diagnostic.id if diagnostic else None
        return result

    def sync_topics(self, records):
        results = []
        for record in records:
            runtime = self._register_runtime_adapter(record)
            results.append(runtime)
            if self._registry_has_model("gateway.mqtt.topic"):
                topics = self.env["gateway.mqtt.topic"].sudo().search([("adapter_id", "=", record.id)])
                runtime_adapter = self._find_runtime_adapter(record)
                if runtime_adapter:
                    topics.write({"runtime_adapter_id": runtime_adapter.id})
        return {"ok": True, "data": results}

    def ingest_topic_event(self, payload):
        data = self._safe_json(payload)
        adapter = self._resolve_adapter_record(data)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        topic = self._resolve_topic_record(adapter, data)
        normalized = self._normalize_topic_payload(data, topic=topic, adapter=adapter)
        runtime_adapter = self._find_runtime_adapter(adapter)
        if topic:
            topic.write(
                {
                    "runtime_adapter_id": runtime_adapter.id if runtime_adapter else False,
                    "last_payload_text": normalized["payload_json"],
                    "last_normalized_json": normalized["normalized_json"],
                    "last_seen_at": self._now(),
                    "state": "ready" if normalized["status"] == "ok" else "degraded",
                }
            )
        if (topic.topic_kind if topic else data.get("topic_kind")) in {"heartbeat", "status"}:
            return self.ingest_topic_heartbeat(data)
        response = self.runtime.ingest_event(
            {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "device_code": adapter.device_code,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else data.get("workstation_code"),
                "app_code": adapter.app_id.code if adapter.app_id else data.get("app_code"),
                "event_kind": normalized["event_kind"],
                "severity": normalized["severity"],
                "message": normalized["message"],
                "result": data.get("result"),
                "command_code": data.get("command_code"),
                "command_id": data.get("command_id"),
            }
        )
        self._store_topic_telemetry(adapter, topic, normalized, response)
        self._log_diagnostic(
            adapter,
            topic=topic,
            direction="inbound",
            event_kind=normalized["event_kind"] or "event",
            status="received" if response.get("ok") else "error",
            message=normalized["message"] or "MQTT event received",
            payload=data,
            result=response,
            topic_path=self._compose_topic_path(adapter, normalized.get("topic")),
        )
        return response

    def ingest_topic_heartbeat(self, payload):
        data = self._safe_json(payload)
        adapter = self._resolve_adapter_record(data)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        topic = self._resolve_topic_record(adapter, data)
        normalized = self._normalize_topic_payload(data, topic=topic, adapter=adapter)
        response = self.runtime.ingest_heartbeat(
            {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                "device_code": adapter.device_code,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else data.get("workstation_code"),
                "app_code": adapter.app_id.code if adapter.app_id else data.get("app_code"),
                "status": normalized["status"],
                "severity": normalized["severity"],
                "message": normalized["message"],
                "latency_ms": data.get("latency_ms"),
            }
        )
        self._store_topic_telemetry(adapter, topic, normalized, response)
        self._log_diagnostic(
            adapter,
            topic=topic,
            direction="inbound",
            event_kind="heartbeat",
            status="received" if response.get("ok") else "error",
            message=normalized["message"] or "MQTT heartbeat received",
            payload=data,
            result=response,
            topic_path=self._compose_topic_path(adapter, normalized.get("topic")),
        )
        return response

    def simulate_publish_receive(self, target, topic_name=None, topic_code=None, payload=None, direction="receive"):
        adapter, source_payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        message_payload = payload if payload is not None else source_payload
        topic = self._resolve_topic_from_target(adapter, payload=source_payload, topic_name=topic_name, topic_code=topic_code)
        normalized = self._normalize_topic_payload(message_payload, topic=topic, adapter=adapter)
        topic_path = self._compose_topic_path(adapter, topic.topic_name if topic else normalized.get("topic"))
        connection = self.build_broker_connection_settings(adapter)
        subscriptions = self.build_subscription_plan(adapter)
        is_outbound = str(direction).lower() in {"out", "outbound", "publish", "tx"}
        if is_outbound:
            simulated = {
                "direction": "outbound",
                "topic_path": topic_path,
                "payload_json": normalized["payload_json"],
                "qos": topic.qos if topic else adapter.qos,
                "retain": topic.retain if topic else adapter.retain_default,
                "client_id": connection.get("data", {}).get("client_id") if connection.get("ok") else None,
            }
            diagnostic = self._log_diagnostic(
                adapter,
                topic=topic,
                direction="outbound",
                event_kind="publish",
                status="simulated",
                message=f"Simulated MQTT publish for {adapter.code}",
                payload=message_payload,
                result=simulated,
                topic_path=topic_path,
            )
            simulated["diagnostic_id"] = diagnostic.id if diagnostic else None
            return {"ok": True, "data": simulated, "connection": connection.get("data"), "subscriptions": subscriptions.get("data"), "message": {"type": "success", "text": "Publish simulated"}}
        if topic and topic.topic_kind in {"heartbeat", "status"}:
            response = self.ingest_topic_heartbeat(message_payload)
        else:
            response = self.ingest_topic_event(message_payload)
        simulated = {
            "direction": "inbound",
            "topic_path": topic_path,
            "payload_json": normalized["payload_json"],
            "runtime_response": response,
        }
        return {"ok": True, "data": simulated, "connection": connection.get("data"), "subscriptions": subscriptions.get("data"), "message": {"type": "success", "text": "Receive simulated"}}

    def push_test_event(self, target, topic_code=None, payload=None):
        adapter, source_payload = self._resolve_adapter_from_target(target)
        if not adapter:
            return {"ok": False, "errors": ["MQTT adapter not found"]}
        topic = self._resolve_topic_from_target(adapter, payload=source_payload, topic_code=topic_code)
        if not topic and self._registry_has_model("gateway.mqtt.topic"):
            ordered = adapter.topic_ids.sorted(lambda record: (record.sequence, record.id))
            preferred = ordered.filtered(lambda record: record.topic_kind in {"event", "heartbeat", "status"})
            topic = (preferred[:1] or ordered[:1])
            topic = topic[:1] if topic else None
        test_payload = payload if payload is not None else {
            "name": f"MQTT test event for {adapter.code}",
            "adapter_code": adapter.code,
            "entry_code": adapter.entry_id.code if adapter.entry_id else None,
            "device_code": adapter.device_code,
            "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
            "app_code": adapter.app_id.code if adapter.app_id else None,
            "topic": topic.topic_name if topic else None,
            "topic_name": topic.topic_name if topic else None,
            "topic_kind": topic.topic_kind if topic else "event",
            "event_kind": topic.event_kind if topic else "diagnostic",
            "status": topic.default_status if topic else "ok",
            "severity": "low",
            "message": f"MQTT test event pushed from adapter {adapter.code}",
            "result": {"mode": "test", "adapter_code": adapter.code, "topic_code": topic.code if topic else None},
        }
        if topic and topic.topic_kind in {"heartbeat", "status"}:
            response = self.runtime.ingest_heartbeat(test_payload)
        else:
            response = self.runtime.ingest_event(test_payload)
        diagnostic = self._log_diagnostic(
            adapter,
            topic=topic,
            direction="test",
            event_kind="test",
            status="received" if response.get("ok") else "error",
            message=f"MQTT test event pushed for {adapter.code}",
            payload=test_payload,
            result=response,
            topic_path=self._compose_topic_path(adapter, topic.topic_name if topic else None),
        )
        return {
            "ok": True,
            "data": {
                "adapter_code": adapter.code,
                "topic_code": topic.code if topic else None,
                "runtime_response": response,
                "diagnostic_id": diagnostic.id if diagnostic else None,
            },
            "message": {"type": "success", "text": "Test event pushed into runtime"},
        }

    def _store_topic_telemetry(self, adapter, topic, normalized, response):
        if topic:
            topic.write(
                {
                    "last_payload_text": normalized["payload_json"],
                    "last_normalized_json": normalized["normalized_json"],
                    "last_seen_at": self._now(),
                    "state": "ready" if normalized["status"] == "ok" else "degraded",
                }
            )
        if adapter:
            adapter.write(
                {
                    "diagnostic_state": json.dumps(response, ensure_ascii=False, default=str),
                    "last_sync_at": self._now(),
                    "state": "ready",
                }
            )
