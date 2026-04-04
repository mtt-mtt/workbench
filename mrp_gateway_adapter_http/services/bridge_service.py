import json

from odoo import _, fields

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService


class GatewayHttpBridgeService:
    def __init__(self, env):
        self.env = env
        self.runtime = GatewayRuntimeService(env)

    def _registry_has_model(self, model_name):
        return model_name in self.env.registry.models

    def _model(self, model_name):
        if not self._registry_has_model(model_name):
            return None
        return self.env[model_name].sudo()

    def _json(self, value):
        return json.dumps(value, ensure_ascii=False, default=str)

    def _resolve_bridge(self, payload):
        Bridge = self._model("gateway.http.bridge")
        if not Bridge:
            return None
        bridge_secret = payload.get("bridge_secret") or payload.get("secret_token")
        if not bridge_secret:
            return None
        bridge_candidates = [
            payload.get("bridge_code"),
            payload.get("bridge_key"),
            payload.get("bridge"),
            payload.get("code"),
        ]
        for candidate in bridge_candidates:
            if not candidate:
                continue
            bridge = Bridge.search(
                ["|", ("code", "=", str(candidate)), ("bridge_key", "=", str(candidate))],
                limit=1,
            )
            if bridge and bridge.secret_token == bridge_secret:
                return bridge
        endpoint_code = payload.get("endpoint_code")
        if endpoint_code:
            endpoint = self._model("gateway.http.endpoint")
            if endpoint:
                endpoint = endpoint.search([("code", "=", str(endpoint_code))], limit=1)
                if endpoint and endpoint.bridge_id and endpoint.bridge_id.secret_token == bridge_secret:
                    return endpoint.bridge_id
        return None

    def _bridge_runtime_adapter_payload(self, bridge):
        return {
            "code": bridge.runtime_adapter_code or f"HTTP-{bridge.code}",
            "name": bridge.name,
            "adapter_type": "http",
            "entry_code": bridge.entry_id.code if bridge.entry_id else None,
            "workstation_code": bridge.workstation_id.code if bridge.workstation_id else None,
            "device_code": bridge.code,
            "connection_target": bridge.endpoint_base_url,
            "config_json": bridge.config_json,
            "config_text": bridge.config_text,
        }

    def sync_bridges(self, bridges):
        if not bridges:
            return []
        runtime_records = []
        for bridge in bridges:
            runtime_data = self.runtime.register_adapter_definition(self._bridge_runtime_adapter_payload(bridge))
            runtime_adapter = self._model("gateway.runtime.adapter")
            runtime_record = None
            if runtime_adapter:
                runtime_record = runtime_adapter.search([("code", "=", bridge.runtime_adapter_code or f"HTTP-{bridge.code}")], limit=1)
            bridge.write(
                {
                    "runtime_adapter_id": runtime_record.id if runtime_record else False,
                    "diagnostic_state": self._json(runtime_data),
                    "state": "ready",
                }
            )
            runtime_records.append(runtime_data)
        return runtime_records

    def _ingest(self, bridge, payload, route_kind):
        payload = dict(payload or {})
        payload.setdefault("bridge_code", bridge.code)
        payload.setdefault("bridge_key", bridge.bridge_key)
        payload.setdefault("adapter_code", bridge.runtime_adapter_code or f"HTTP-{bridge.code}")
        payload.setdefault("adapter_code", bridge.runtime_adapter_code or f"HTTP-{bridge.code}")
        payload.setdefault("app_code", bridge.app_id.code if bridge.app_id else None)
        payload.setdefault("workstation_code", bridge.workstation_id.code if bridge.workstation_id else None)
        payload.setdefault("entry_code", bridge.entry_id.code if bridge.entry_id else None)
        payload.setdefault("session_ref", payload.get("session_ref") or payload.get("session_id"))
        payload.setdefault("message", payload.get("message") or payload.get("note") or f"HTTP {route_kind} received")
        payload.setdefault("payload_json", self._json(payload))
        if route_kind == "heartbeat":
            payload.setdefault("status", payload.get("status") or "ok")
            bridge_state = {
                "ok": "ready",
                "warn": "degraded",
                "error": "degraded",
                "offline": "offline",
            }.get(payload.get("status"), "ready")
            result = self.runtime.ingest_heartbeat(payload)
            bridge.write(
                {
                    "heartbeat_count": bridge.heartbeat_count + 1,
                    "state": bridge_state,
                    "last_request_at": fields.Datetime.now(),
                    "diagnostic_state": self._json(result),
                }
            )
            return result
        payload.setdefault("event_kind", payload.get("event_kind") or "custom")
        result = self.runtime.ingest_event(payload)
        bridge_state = "degraded" if payload.get("severity") in {"warning", "error", "critical"} else bridge.state
        bridge.write(
            {
                "event_count": bridge.event_count + 1,
                "push_count": bridge.push_count + 1,
                "state": bridge_state,
                "last_request_at": fields.Datetime.now(),
                "diagnostic_state": self._json(result),
            }
        )
        return result

    def heartbeat_payload(self, payload):
        bridge = self._resolve_bridge(payload)
        if not bridge:
            return {"ok": False, "status": 403, "errors": [{"message": "Bridge not found or token invalid"}]}
        self.sync_bridges([bridge])
        return self._ingest(bridge, payload, "heartbeat")

    def push_payload(self, payload):
        bridge = self._resolve_bridge(payload)
        if not bridge:
            return {"ok": False, "status": 403, "errors": [{"message": "Bridge not found or token invalid"}]}
        self.sync_bridges([bridge])
        route_kind = payload.get("route_kind") or payload.get("kind") or "push"
        if route_kind == "heartbeat" or payload.get("status") in {"ok", "warn", "error", "offline"}:
            return self._ingest(bridge, payload, "heartbeat")
        return self._ingest(bridge, payload, "event")
