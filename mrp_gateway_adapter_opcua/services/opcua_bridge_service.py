import json

from odoo import fields

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService

from .opcua_client import GatewayOpcuaClientHelper


class GatewayOpcuaBridgeService:
    def __init__(self, env):
        self.env = env
        self.client_helper = GatewayOpcuaClientHelper()

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

    def _json_dumps(self, value):
        return json.dumps(value, ensure_ascii=False, default=str)

    def _runtime_service(self):
        return GatewayRuntimeService(self.env)

    def _runtime_capability_summary(self, capability):
        supports = capability.get("supports") or {}
        labels = []
        for key, label in (
            ("poll", "poll"),
            ("push", "push"),
            ("read", "read"),
            ("write", "write"),
            ("subscribe", "subscribe"),
            ("diagnostic", "diagnostics"),
            ("repair", "repair"),
            ("reload", "reload"),
            ("load", "load"),
            ("unload", "unload"),
            ("dispatch", "dispatch"),
        ):
            if supports.get(key):
                labels.append(label)
        base = capability.get("adapter_type") or capability.get("transport") or "runtime"
        return f"{base}: {', '.join(labels)}" if labels else base

    def _store_runtime_feedback(self, adapter, result, touch_field=None):
        if not adapter or not result:
            return result
        data = result.get("data") or {}
        capability = data.get("capability") or {}
        coordinator = data.get("coordinator") or {}
        runtime_adapter = self._model("gateway.runtime.adapter").search([("code", "=", adapter.code)], limit=1) if self._registry_has_model("gateway.runtime.adapter") else None
        values = {
            "diagnostic_state": self._json_dumps(result),
            "runtime_diagnostic_summary": self._json_dumps(
                {
                    "capability": capability,
                    "coordinator": coordinator,
                    "signal": data.get("signal"),
                }
            ),
        }
        if runtime_adapter:
            values["runtime_adapter_id"] = runtime_adapter.id
        if capability:
            values["runtime_capability_json"] = capability.get("capability_json") or self._json_dumps(capability)
            values["runtime_capability_summary"] = self._runtime_capability_summary(capability)
        if touch_field:
            values[touch_field] = fields.Datetime.now()
        adapter.write(values)
        return result

    def _create_diagnostic(self, adapter, kind, state, message, detail=None, payload=None, result=None, node=None):
        Diagnostic = self._model("gateway.opcua.diagnostic")
        if Diagnostic is None:
            return None
        return Diagnostic.create(
            {
                "name": f"{adapter.code}-{kind}",
                "adapter_id": adapter.id,
                "node_id": node.id if node else False,
                "kind": kind,
                "state": state,
                "message": message,
                "detail": detail or "",
                "payload_json": self._json_dumps(payload or {}),
                "result_json": self._json_dumps(result or {}),
                "observed_at": fields.Datetime.now(),
            }
        )

    def register_adapter_definition(self, payload):
        Adapter = self._model("gateway.opcua.adapter")
        if Adapter is None:
            return {"ok": False, "errors": ["gateway.opcua.adapter model is not installed."]}
        payload = dict(payload or {})
        code = payload.get("code")
        adapter = Adapter.search([("code", "=", code)], limit=1) if code else Adapter.browse()
        if not adapter:
            adapter = Adapter.create(
                {
                    "name": payload.get("name") or code or "OPC UA Adapter",
                    "code": code or self.env["ir.sequence"].next_by_code("gateway.opcua.adapter") or "OPCUA",
                    "endpoint_url": payload.get("endpoint_url") or "opc.tcp://127.0.0.1:4840",
                    "security_policy": payload.get("security_policy") or "none",
                    "security_mode": payload.get("security_mode") or "none",
                    "auth_mode": payload.get("auth_mode") or "anonymous",
                    "namespace_uri": payload.get("namespace_uri"),
                    "config_json": self._json_dumps(payload),
                }
            )
        runtime_result = self._runtime_service().register_adapter_definition(adapter._runtime_payload())
        capability = self._runtime_service().build_capability_payload(payload=adapter._runtime_payload())
        runtime_adapter = self._model("gateway.runtime.adapter").search([("code", "=", adapter.code)], limit=1) if self._registry_has_model("gateway.runtime.adapter") else None
        if runtime_adapter:
            adapter.write({"runtime_adapter_id": runtime_adapter.id})
        diag = self._create_diagnostic(
            adapter,
            "connect",
            "info",
            "Adapter definition synchronized",
            detail=adapter.endpoint_url,
            payload=payload,
            result={"state": adapter.state, "code": adapter.code, "runtime_result": runtime_result, "capability": capability},
        )
        adapter.write(
            {
                "last_sync_at": fields.Datetime.now(),
                "runtime_capability_json": capability.get("capability_json") or self._json_dumps(capability),
                "runtime_capability_summary": self._runtime_capability_summary(capability),
                "runtime_diagnostic_summary": self._json_dumps(
                    {
                        "registration": {"state": adapter.state, "code": adapter.code},
                        "runtime_result": runtime_result,
                        "capability": capability,
                    }
                ),
                "diagnostic_state": self._json_dumps(
                    {
                        "registration": {"state": adapter.state, "code": adapter.code},
                        "runtime_result": runtime_result,
                    }
                ),
            }
        )
        return {"ok": True, "adapter_id": adapter.id, "runtime_result": runtime_result, "diagnostic_id": diag.id if diag else None}

    def preview_connectivity(self, adapter):
        helper_state = self.client_helper.describe()
        capability = self._runtime_service().build_capability_payload(payload=adapter._runtime_payload())
        diag = self._create_diagnostic(
            adapter,
            "connect",
            "warning" if not helper_state["available"] else "success",
            "OPC UA connectivity preview generated",
            detail=adapter.endpoint_url,
            payload=adapter._runtime_payload(),
            result={"client": helper_state, "capability": capability},
        )
        adapter.write(
            {
                "runtime_capability_json": capability.get("capability_json") or self._json_dumps(capability),
                "runtime_capability_summary": self._runtime_capability_summary(capability),
                "runtime_diagnostic_summary": self._json_dumps({"client": helper_state, "capability": capability}),
            }
        )
        return {"ok": True, "diagnostic_id": diag.id if diag else None, "details": helper_state, "capability": capability}

    def preview_node_map(self, adapter):
        nodes = adapter.node_ids.sorted(lambda record: (record.sequence, record.id))
        summary = {
            "node_count": len(nodes),
            "read_nodes": len(nodes.filtered(lambda record: record.access_mode in {"read", "read_write"})),
            "write_nodes": len(nodes.filtered(lambda record: record.access_mode in {"write", "read_write"})),
        }
        diag = self._create_diagnostic(adapter, "browse", "info", "OPC UA node map preview generated", detail=f"{summary['node_count']} node(s)", payload=adapter._runtime_payload(), result=summary)
        adapter.write({"runtime_diagnostic_summary": self._json_dumps({"node_map": summary})})
        return {"ok": True, "diagnostic_id": diag.id if diag else None, "summary": summary}

    def push_test_snapshot(self, adapter):
        nodes = adapter.node_ids.sorted(lambda record: (record.sequence, record.id))
        sample = [{"node_code": node.code, "node_id": node.node_id, "value": node.last_value or "sample", "state": node.state} for node in nodes[:5]]
        diag = self._create_diagnostic(adapter, "snapshot", "success", "OPC UA test snapshot collected", detail=f"{len(sample)} node sample(s)", payload=adapter._runtime_payload(), result={"samples": sample})
        adapter.write({"last_sync_at": fields.Datetime.now(), "node_count": len(nodes)})
        return {"ok": True, "diagnostic_id": diag.id if diag else None, "snapshot": sample}

    def refresh_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().refresh_runtime({**adapter._runtime_payload(), "reason": reason or "opcua_refresh"})
        self._store_runtime_feedback(adapter, runtime_result, touch_field="last_sync_at")
        return runtime_result

    def repair_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().repair_runtime({**adapter._runtime_payload(), "reason": reason or "opcua_repair"})
        self._store_runtime_feedback(adapter, runtime_result)
        adapter.write({"last_connect_at": fields.Datetime.now()})
        return runtime_result

    def load_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().load_runtime({**adapter._runtime_payload(), "reason": reason or "opcua_load"})
        self._store_runtime_feedback(adapter, runtime_result, touch_field="last_sync_at")
        return runtime_result

    def reload_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().reload_runtime({**adapter._runtime_payload(), "reason": reason or "opcua_reload"})
        self._store_runtime_feedback(adapter, runtime_result, touch_field="last_sync_at")
        return runtime_result

    def runtime_diagnostics(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().runtime_diagnostics({**adapter._runtime_payload(), "reason": reason or "opcua_diagnostics"})
        self._store_runtime_feedback(adapter, runtime_result)
        return runtime_result
