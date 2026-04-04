from odoo import fields

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService

from .s7_client import GatewayS7ClientHelper


class GatewayS7BridgeService:
    def __init__(self, env):
        self.env = env
        self.client_helper = GatewayS7ClientHelper()

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
        import json

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

    def _create_diagnostic(self, adapter, kind, state, message, detail=None, payload=None, result=None, tag=None):
        Diagnostic = self._model("gateway.s7.diagnostic")
        if Diagnostic is None:
            return None
        return Diagnostic.create(
            {
                "name": f"{adapter.code}-{kind}",
                "adapter_id": adapter.id,
                "tag_id": tag.id if tag else False,
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
        Adapter = self._model("gateway.s7.adapter")
        if Adapter is None:
            return {"ok": False, "errors": ["gateway.s7.adapter model is not installed."]}
        payload = dict(payload or {})
        code = payload.get("code")
        adapter = Adapter.search([("code", "=", code)], limit=1) if code else Adapter.browse()
        if not adapter:
            adapter = Adapter.create(
                {
                    "name": payload.get("name") or code or "S7 Adapter",
                    "code": code or self.env["ir.sequence"].next_by_code("gateway.s7.adapter") or "S7",
                    "host": payload.get("host") or "127.0.0.1",
                    "port": payload.get("port") or 102,
                    "rack": payload.get("rack") or 0,
                    "slot": payload.get("slot") or 1,
                    "cpu": payload.get("cpu"),
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
            detail=adapter.connection_target,
            payload=payload,
            result={"state": adapter.state, "code": adapter.code, "runtime_result": runtime_result, "capability": capability},
        )
        adapter.write(
            {
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
        return {"ok": True, "adapter_id": adapter.id, "diagnostic_id": diag.id if diag else None, "runtime_result": runtime_result}

    def preview_read_plan(self, adapter):
        tags = adapter.tag_ids.sorted(lambda record: (record.sequence, record.id))
        summary = {
            "tag_count": len(tags),
            "read_tags": len(tags.filtered(lambda record: record.access_mode in {"read", "read_write"})),
        }
        diag = self._create_diagnostic(adapter, "read", "info", "S7 read plan preview generated", detail=f"{summary['tag_count']} tag(s)", payload=adapter._runtime_payload(), result=summary)
        return {"ok": True, "diagnostic_id": diag.id if diag else None, "summary": summary}

    def preview_write_plan(self, adapter):
        tags = adapter.tag_ids.sorted(lambda record: (record.sequence, record.id))
        summary = {
            "tag_count": len(tags),
            "write_tags": len(tags.filtered(lambda record: record.access_mode in {"write", "read_write"})),
        }
        diag = self._create_diagnostic(adapter, "write", "info", "S7 write plan preview generated", detail=f"{summary['write_tags']} writable tag(s)", payload=adapter._runtime_payload(), result=summary)
        return {"ok": True, "diagnostic_id": diag.id if diag else None, "summary": summary}

    def submit_test_snapshot(self, adapter):
        tags = adapter.tag_ids.sorted(lambda record: (record.sequence, record.id))
        sample = [{"tag_code": tag.code, "db_number": tag.db_number, "address": tag.address, "value": tag.last_value or "sample", "state": tag.state} for tag in tags[:5]]
        diag = self._create_diagnostic(adapter, "snapshot", "success", "S7 test snapshot collected", detail=f"{len(sample)} tag sample(s)", payload=adapter._runtime_payload(), result={"samples": sample})
        adapter.write({"last_snapshot_at": fields.Datetime.now(), "point_count": len(tags), "snapshot_count": adapter.snapshot_count + 1})
        return {"ok": True, "diagnostic_id": diag.id if diag else None, "snapshot": sample}

    def submit_test_write_ack(self, adapter):
        tags = adapter.tag_ids.filtered(lambda record: record.access_mode in {"write", "read_write"})
        acks = []
        for tag in tags[:5]:
            ack = self._model("gateway.s7.write.ack")
            if ack is None:
                break
            record = ack.create(
                {
                    "name": f"{adapter.code}-{tag.code}",
                    "adapter_id": adapter.id,
                    "tag_id": tag.id,
                    "state": "acknowledged",
                    "ack_code": f"ACK-{tag.code}",
                    "command_code": tag.code,
                    "requested_value": tag.last_value or "sample",
                    "acked_value": tag.last_value or "sample",
                    "sent_at": fields.Datetime.now(),
                    "acked_at": fields.Datetime.now(),
                }
            )
            acks.append(record.id)
            self._create_diagnostic(adapter, "write", "success", "S7 write acknowledgement recorded", detail=tag.code, payload=adapter._runtime_payload(), result={"ack_id": record.id}, tag=tag)
        adapter.write({"last_ack_at": fields.Datetime.now(), "ack_count": adapter.ack_count + len(acks)})
        return {"ok": True, "ack_ids": acks}

    def refresh_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().refresh_runtime({**adapter._runtime_payload(), "reason": reason or "s7_refresh"})
        self._store_runtime_feedback(adapter, runtime_result, touch_field="runtime_last_refresh_at")
        return runtime_result

    def repair_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().repair_runtime({**adapter._runtime_payload(), "reason": reason or "s7_repair"})
        self._store_runtime_feedback(adapter, runtime_result, touch_field="runtime_last_repair_at")
        return runtime_result

    def reload_runtime(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().reload_runtime({**adapter._runtime_payload(), "reason": reason or "s7_reload"})
        self._store_runtime_feedback(adapter, runtime_result, touch_field="runtime_last_reload_at")
        return runtime_result

    def runtime_diagnostics(self, adapter, reason=None):
        self.register_adapter_definition(adapter._runtime_payload())
        runtime_result = self._runtime_service().runtime_diagnostics({**adapter._runtime_payload(), "reason": reason or "s7_diagnostics"})
        self._store_runtime_feedback(adapter, runtime_result)
        return runtime_result
