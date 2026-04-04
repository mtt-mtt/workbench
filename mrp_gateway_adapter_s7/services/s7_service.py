import json

from odoo import _, fields

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService

from .s7_client import GatewayS7ClientHelper


class GatewayS7Service:
    def __init__(self, env):
        self.env = env
        self._client_helper = GatewayS7ClientHelper()

    def _runtime_service(self):
        return GatewayRuntimeService(self.env)

    def _json_dumps(self, value):
        return json.dumps(value, ensure_ascii=False, default=str)

    def _model(self, model_name):
        try:
            return self.env[model_name].sudo()
        except KeyError:
            return None

    def _resolve_relation(self, model_name, code):
        if not code:
            return None
        model = self._model(model_name)
        if model is None:
            return None
        record = model.search([("code", "=", code)], limit=1)
        return record.id if record else None

    def _resolve_adapter(self, adapter):
        Adapter = self._model("gateway.s7.adapter")
        if Adapter is None:
            return None
        if hasattr(adapter, "_name") and getattr(adapter, "_name", None) == "gateway.s7.adapter":
            return adapter.exists()
        if isinstance(adapter, int):
            return Adapter.browse(adapter).exists()
        if isinstance(adapter, dict):
            if adapter.get("adapter_id"):
                return Adapter.browse(int(adapter["adapter_id"])).exists()
            if adapter.get("code"):
                return Adapter.search([("code", "=", adapter["code"])], limit=1)
        return None

    def _points_for_adapter(self, adapter):
        Point = self._model("gateway.s7.point")
        adapter = self._resolve_adapter(adapter)
        if Point is None or not adapter:
            return self.env["gateway.s7.point"].sudo().browse()
        return Point.search([("adapter_id", "=", adapter.id)])

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
        runtime_adapter = data.get("adapter") or {}
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
            values["runtime_adapter_id"] = runtime_adapter.get("id") if isinstance(runtime_adapter, dict) else False
        if capability:
            values["runtime_capability_json"] = capability.get("capability_json") or self._json_dumps(capability)
            values["runtime_capability_summary"] = self._runtime_capability_summary(capability)
        if touch_field:
            values[touch_field] = fields.Datetime.now()
        adapter.write(values)
        return result

    def register_adapter_definition(self, adapter_payload):
        Adapter = self._model("gateway.s7.adapter")
        if Adapter is None:
            return {"ok": False, "errors": ["gateway.s7.adapter model is not installed"]}
        code = adapter_payload.get("code")
        record = Adapter.search([("code", "=", code)], limit=1) if code else Adapter.browse()
        values = {
            "name": adapter_payload.get("name") or code or _("S7 Adapter"),
            "code": code or self.env["ir.sequence"].next_by_code("gateway.s7.adapter") or _("New"),
            "entry_id": self._resolve_relation("gateway.entry", adapter_payload.get("entry_code")),
            "app_id": self._resolve_relation("shopfloor.app", adapter_payload.get("app_code")),
            "workstation_id": self._resolve_relation("shopfloor.workstation", adapter_payload.get("workstation_code")),
            "host": adapter_payload.get("host"),
            "port": adapter_payload.get("port"),
            "rack": adapter_payload.get("rack"),
            "slot": adapter_payload.get("slot"),
            "cpu": adapter_payload.get("cpu"),
            "connection_target": adapter_payload.get("connection_target"),
            "config_json": adapter_payload.get("config_json"),
            "config_text": adapter_payload.get("config_text"),
        }
        values = {key: value for key, value in values.items() if value is not None}
        if record:
            record.write(values)
        else:
            record = Adapter.create(values)
        runtime_result = self._runtime_service().register_adapter_definition(record._runtime_payload())
        capability = self._runtime_service().build_capability_payload(payload=record._runtime_payload())
        runtime_adapter = self._model("gateway.runtime.adapter").search([("code", "=", record.code)], limit=1) if self._model("gateway.runtime.adapter") else None
        if runtime_adapter:
            record.write({"runtime_adapter_id": runtime_adapter.id})
        record.write(
            {
                "runtime_capability_json": capability.get("capability_json") or self._json_dumps(capability),
                "runtime_capability_summary": self._runtime_capability_summary(capability),
                "runtime_diagnostic_summary": self._json_dumps(
                    {
                        "registration": {"id": record.id, "code": record.code},
                        "runtime_result": runtime_result,
                        "capability": capability,
                    }
                ),
                "diagnostic_state": self._json_dumps(
                    {
                        "registration": {"id": record.id, "code": record.code},
                        "runtime_result": runtime_result,
                    }
                ),
            }
        )
        return {"ok": True, "data": {"id": record.id, "code": record.code}, "runtime_result": runtime_result, "capability": capability}

    def preview_read_plan(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        points = self._points_for_adapter(adapter)
        extra = dict(extra or {})
        if extra.get("point_ids"):
            points = points.filtered(lambda point: point.id in set(extra["point_ids"]))
        return {
            "ok": True,
            "data": {
                "point_count": len(points),
                "group_count": len(set(points.mapped("db_number"))),
            },
        }

    def preview_write_plan(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        points = self._points_for_adapter(adapter).filtered(lambda point: point.writable)
        extra = dict(extra or {})
        if extra.get("point_ids"):
            points = points.filtered(lambda point: point.id in set(extra["point_ids"]))
        return {
            "ok": True,
            "data": {
                "point_count": len(points),
                "operation_count": len(points),
            },
        }

    def submit_test_snapshot(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        Snapshot = self._model("gateway.s7.snapshot")
        if Snapshot is None:
            return {"ok": False, "errors": ["gateway.s7.snapshot model is not installed"]}
        extra = dict(extra or {})
        point_ids = extra.get("point_ids") or self._points_for_adapter(adapter).ids[:1]
        point_model = self._model("gateway.s7.point")
        point = point_model.browse(point_ids[0]).exists() if point_model and point_ids else None
        tag = point.tag_id if point and point.tag_id else adapter.tag_ids[:1]
        tag = tag[:1] if tag else None
        snapshot = Snapshot.create(
            {
                "name": f"{adapter.code}-snapshot",
                "code": self.env["ir.sequence"].next_by_code("gateway.s7.snapshot") or _("New"),
                "adapter_id": adapter.id,
                "state": "success",
                "payload_json": self._json_dumps({"point_code": point.code if point else None, "tag_code": tag.code if tag else None}),
                "result_json": self._json_dumps({"status": "success", "point_code": point.code if point else None, "tag_code": tag.code if tag else None}),
                "note": "Manual S7 snapshot created",
            }
        )
        if point:
            point.write({"last_snapshot_at": fields.Datetime.now(), "state": "ready"})
        return {"ok": True, "data": {"snapshot": {"id": snapshot.id, "code": snapshot.code}}}

    def submit_test_write_ack(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        Ack = self._model("gateway.s7.write.ack")
        if Ack is None:
            return {"ok": False, "errors": ["gateway.s7.write.ack model is not installed"]}
        extra = dict(extra or {})
        writable_points = self._points_for_adapter(adapter).filtered(lambda point: point.writable)
        point_ids = extra.get("point_ids") or writable_points.ids[:1]
        point_model = self._model("gateway.s7.point")
        point = point_model.browse(point_ids[0]).exists() if point_model and point_ids else None
        tag = point.tag_id if point and point.tag_id else adapter.tag_ids.filtered(lambda rec: rec.access_mode in {"write", "read_write"})[:1]
        tag = tag[:1] if tag else None
        ack = Ack.create(
            {
                "name": f"{adapter.code}-ack",
                "adapter_id": adapter.id,
                "tag_id": tag.id if tag else False,
                "state": "acknowledged",
                "ack_code": self.env["ir.sequence"].next_by_code("gateway.s7.write.ack") or _("New"),
                "command_code": point.code if point else tag.code if tag else None,
                "requested_value": point.current_value_text if point else tag.last_value if tag else None,
                "acked_value": point.current_value_text if point else tag.last_value if tag else None,
                "acked_at": fields.Datetime.now(),
                "note": "S7 write ack recorded",
            }
        )
        if point:
            point.write({"state": "ready"})
        return {"ok": True, "data": {"ack": {"id": ack.id, "code": ack.ack_code}}}

    def refresh_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().refresh_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._store_runtime_feedback(adapter, result, touch_field="last_snapshot_at")
        return result

    def repair_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().repair_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._store_runtime_feedback(adapter, result)
        return result

    def load_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().load_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._store_runtime_feedback(adapter, result, touch_field="last_snapshot_at")
        return result

    def reload_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().reload_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._store_runtime_feedback(adapter, result, touch_field="last_snapshot_at")
        return result

    def runtime_diagnostics(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().runtime_diagnostics({**adapter._runtime_payload(), **dict(extra or {})})
        self._store_runtime_feedback(adapter, result)
        return result
