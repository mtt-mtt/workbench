import json

from odoo.fields import Datetime

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService

from .modbus_client import OptionalPymodbusClient


class GatewayModbusService:
    def __init__(self, env):
        self.env = env

    def _registry_has_model(self, model_name):
        return model_name in self.env.registry.models

    def _now(self):
        return Datetime.now()

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

    def _coerce_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _coerce_float(self, value, default=0.0):
        try:
            return float(value)
        except Exception:
            return default

    def _adapter_payload_for_runtime(self, record):
        return {
            "adapter_id": record.id,
            "code": record.code,
            "name": record.name,
            "adapter_type": "modbus",
            "entry_code": record.entry_id.code if record.entry_id else None,
            "workstation_code": record.workstation_id.code if record.workstation_id else None,
            "app_code": record.app_id.code if record.app_id else None,
            "device_code": record.code,
            "transport": record.transport,
            "host": record.host,
            "port": record.port,
            "serial_port": record.serial_port,
            "baudrate": record.baudrate,
            "parity": record.parity,
            "stop_bits": record.stop_bits,
            "unit_id": record.unit_id,
            "poll_interval_seconds": record.poll_interval_seconds,
            "timeout_seconds": record.timeout_seconds,
            "retry_limit": record.retry_limit,
            "connection_target": record.connection_target or self._build_connection_target(
                {
                    "transport": record.transport,
                    "host": record.host,
                    "port": record.port,
                    "serial_port": record.serial_port,
                    "baudrate": record.baudrate,
                    "parity": record.parity,
                    "stop_bits": record.stop_bits,
                    "unit_id": record.unit_id,
                }
            ),
            "config_json": record.config_json,
            "config_text": record.config_text,
        }

    def _resolve_modbus_adapter(self, payload):
        if not self._registry_has_model("gateway.modbus.adapter"):
            return None
        adapter_id = payload.get("adapter_id") or payload.get("modbus_adapter_id")
        adapter_code = payload.get("adapter_code") or payload.get("code")
        Adapter = self.env["gateway.modbus.adapter"].sudo()
        if adapter_id:
            return Adapter.browse(int(adapter_id)).exists()
        if adapter_code:
            return Adapter.search([("code", "=", adapter_code)], limit=1)
        return None

    def _resolve_point(self, adapter, payload):
        if not adapter or not self._registry_has_model("gateway.modbus.point"):
            return None
        point_id = payload.get("point_id")
        point_code = payload.get("point_code") or payload.get("code")
        address = payload.get("register_address")
        function_code = payload.get("function_code")
        Point = self.env["gateway.modbus.point"].sudo()
        if point_id:
            return Point.browse(int(point_id)).exists()
        if point_code:
            point = Point.search([("adapter_id", "=", adapter.id), ("code", "=", point_code)], limit=1)
            if point:
                return point
        if address is not None:
            domain = [("adapter_id", "=", adapter.id), ("register_address", "=", self._coerce_int(address))]
            if function_code is not None:
                domain.append(("function_code", "=", self._coerce_int(function_code, 3)))
            return Point.search(domain, limit=1)
        return None

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

    def _resolve_entry(self, payload):
        if not self._registry_has_model("gateway.entry"):
            return None
        entry_id = payload.get("entry_id")
        entry_code = payload.get("entry_code")
        Entry = self.env["gateway.entry"].sudo()
        if entry_id:
            return Entry.browse(int(entry_id)).exists()
        if entry_code:
            return Entry.search([("code", "=", entry_code)], limit=1)
        return None

    def _resolve_workstation(self, payload):
        if not self._registry_has_model("shopfloor.workstation"):
            return None
        workstation_id = payload.get("workstation_id")
        workstation_code = payload.get("workstation_code")
        Workstation = self.env["shopfloor.workstation"].sudo()
        if workstation_id:
            return Workstation.browse(int(workstation_id)).exists()
        if workstation_code:
            return Workstation.search([("code", "=", workstation_code)], limit=1)
        return None

    def _resolve_app(self, payload):
        if not self._registry_has_model("shopfloor.app"):
            return None
        app_id = payload.get("app_id")
        app_code = payload.get("app_code")
        App = self.env["shopfloor.app"].sudo()
        if app_id:
            return App.browse(int(app_id)).exists()
        if app_code:
            return App.search([("code", "=", app_code)], limit=1)
        return None

    def _build_connection_target(self, data):
        transport = data.get("transport") or "tcp"
        unit_id = self._coerce_int(data.get("unit_id"), 1)
        if transport == "rtu":
            serial_port = data.get("serial_port") or "/dev/ttyUSB0"
            baudrate = self._coerce_int(data.get("baudrate"), 9600)
            parity = data.get("parity") or "N"
            stop_bits = data.get("stop_bits") or "1"
            return f"modbus+rtu://{serial_port}?baudrate={baudrate}&parity={parity}&stop_bits={stop_bits}&unit={unit_id}"
        if transport == "ascii":
            serial_port = data.get("serial_port") or "/dev/ttyUSB0"
            baudrate = self._coerce_int(data.get("baudrate"), 9600)
            parity = data.get("parity") or "N"
            stop_bits = data.get("stop_bits") or "1"
            return f"modbus+ascii://{serial_port}?baudrate={baudrate}&parity={parity}&stop_bits={stop_bits}&unit={unit_id}"
        host = data.get("host") or "127.0.0.1"
        port = self._coerce_int(data.get("port"), 502)
        scheme = "modbus+tls" if transport == "tcp_tls" else "modbus"
        return f"{scheme}://{host}:{port}/unit/{unit_id}"

    def _status_from_payload(self, data):
        status = data.get("status") or data.get("state")
        if status in {"ok", "warn", "error", "offline"}:
            return status
        result = data.get("result")
        if result in {"failed", "error"}:
            return "error"
        return "ok"

    def _severity_from_status(self, status):
        return {"ok": "low", "warn": "medium", "error": "high", "offline": "high"}.get(status, "medium")

    def _resolve_adapter_record(self, adapter):
        if not adapter:
            return None
        if getattr(adapter, "_name", None) == "gateway.modbus.adapter":
            return adapter.exists()
        if isinstance(adapter, dict):
            return self._resolve_modbus_adapter(adapter)
        return None

    def _selected_points(self, adapter, options=None, writable_only=False):
        adapter = self._resolve_adapter_record(adapter)
        if not adapter or not self._registry_has_model("gateway.modbus.point"):
            return self.env["gateway.modbus.point"].sudo().browse()
        options = self._as_dict(options)
        points = adapter.point_ids.filtered(lambda point: point.active)
        point_ids = options.get("point_ids") or options.get("point_id_list") or []
        if point_ids:
            wanted_ids = {self._coerce_int(point_id) for point_id in point_ids if point_id}
            points = points.filtered(lambda point: point.id in wanted_ids)
        point_codes = options.get("point_codes") or []
        if point_codes:
            wanted_codes = set(point_codes)
            points = points.filtered(lambda point: point.code in wanted_codes)
        function_codes = options.get("function_codes") or []
        if function_codes:
            wanted_functions = {self._coerce_int(function_code) for function_code in function_codes if function_code is not None}
            points = points.filtered(lambda point: point.function_code in wanted_functions)
        if writable_only:
            points = points.filtered(lambda point: point.writable or not point.read_only)
        if options.get("writable_only"):
            points = points.filtered(lambda point: point.writable or not point.read_only)
        return points

    def _serialize_point(self, point):
        return {
            "id": point.id,
            "name": point.name,
            "code": point.code,
            "state": point.state,
            "point_kind": point.point_kind,
            "register_group": point.register_group,
            "function_code": point.function_code,
            "register_address": point.register_address,
            "register_count": point.register_count,
            "data_type": point.data_type,
            "bit_index": point.bit_index,
            "scale_factor": point.scale_factor,
            "offset": point.offset,
            "unit": point.unit,
            "endian": point.endian,
            "byte_order": point.byte_order,
            "read_only": point.read_only,
            "writable": point.writable,
            "current_value_text": point.current_value_text,
            "current_value_number": point.current_value_number,
            "last_snapshot_at": point.last_snapshot_at,
        }

    def _point_read_method(self, point):
        return {
            1: "read_coils",
            2: "read_discrete_inputs",
            3: "read_holding_registers",
            4: "read_input_registers",
        }.get(self._coerce_int(point.function_code, 3), "read_holding_registers")

    def _point_write_method(self, point):
        return {
            5: "write_coil",
            6: "write_register",
            15: "write_coils",
            16: "write_registers",
        }.get(self._coerce_int(point.function_code, 16), "write_registers")

    def _coerce_optional_float(self, value):
        if value in (None, ""):
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _coerce_optional_bool(self, value):
        if isinstance(value, bool):
            return value
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}
        return None

    def _sample_point_value(self, point):
        base = point.register_address + max(point.register_count or 1, 1)
        if point.data_type == "bool":
            return bool(base % 2)
        if point.data_type in {"int16", "uint16", "int32", "uint32"}:
            return base
        if point.data_type in {"float32", "float64"}:
            scale = point.scale_factor or 1.0
            return round(base / scale, 3)
        if point.data_type == "string":
            return f"{point.code}:{point.register_address}"
        if point.register_count and point.register_count > 1:
            return [point.register_address + offset for offset in range(point.register_count)]
        return base

    def _coerce_point_value(self, point, raw_value):
        if raw_value is None:
            raw_value = self._sample_point_value(point)
        if point.data_type == "bool":
            value_bool = self._coerce_optional_bool(raw_value)
            if value_bool is None and isinstance(raw_value, (list, tuple)) and raw_value:
                value_bool = self._coerce_optional_bool(raw_value[0])
            return {
                "value": value_bool if value_bool is not None else bool(raw_value),
                "value_text": str(value_bool if value_bool is not None else raw_value),
                "value_number": 1.0 if value_bool else 0.0,
                "raw_value": raw_value,
            }
        if point.data_type in {"int16", "uint16", "int32", "uint32"}:
            value_number = self._coerce_optional_float(raw_value)
            if value_number is None and isinstance(raw_value, (list, tuple)) and raw_value:
                value_number = self._coerce_optional_float(raw_value[0])
            value_number = value_number if value_number is not None else 0.0
            value_int = self._coerce_int(value_number, 0)
            return {
                "value": value_int,
                "value_text": str(value_int),
                "value_number": float(value_number),
                "raw_value": raw_value,
            }
        if point.data_type in {"float32", "float64"}:
            value_number = self._coerce_optional_float(raw_value)
            if value_number is None and isinstance(raw_value, (list, tuple)) and raw_value:
                value_number = self._coerce_optional_float(raw_value[0])
            value_number = value_number if value_number is not None else 0.0
            value_number = round(value_number, 6)
            return {
                "value": value_number,
                "value_text": str(value_number),
                "value_number": value_number,
                "raw_value": raw_value,
            }
        if point.data_type == "string":
            value_text = "" if raw_value is None else str(raw_value)
            return {
                "value": value_text,
                "value_text": value_text,
                "value_number": None,
                "raw_value": raw_value,
            }
        if isinstance(raw_value, (list, tuple)):
            value_text = json.dumps(list(raw_value), ensure_ascii=False, default=str)
        else:
            value_text = "" if raw_value is None else str(raw_value)
        return {
            "value": raw_value,
            "value_text": value_text,
            "value_number": self._coerce_optional_float(raw_value),
            "raw_value": raw_value,
        }

    def _build_read_groups(self, points):
        groups = []
        current = None
        for point in points.sorted(key=lambda record: (record.function_code, record.register_group or "", record.register_address, record.sequence, record.id)):
            start = self._coerce_int(point.register_address, 0)
            count = max(self._coerce_int(point.register_count, 1), 1)
            end = start + count - 1
            point_payload = self._serialize_point(point)
            point_payload.update(
                {
                    "read_method": self._point_read_method(point),
                    "write_method": self._point_write_method(point),
                }
            )
            if (
                current
                and current["function_code"] == point.function_code
                and current["register_group"] == point.register_group
                and start <= current["range_end"] + 1
            ):
                current["range_end"] = max(current["range_end"], end)
                current["register_count"] = current["range_end"] - current["range_start"] + 1
                current["points"].append(point_payload)
                current["point_ids"].append(point.id)
                current["point_codes"].append(point.code)
                continue
            current = {
                "function_code": point.function_code,
                "register_group": point.register_group,
                "range_start": start,
                "range_end": end,
                "register_count": count,
                "read_method": self._point_read_method(point),
                "points": [point_payload],
                "point_ids": [point.id],
                "point_codes": [point.code],
            }
            groups.append(current)
        return groups

    def _build_write_operations(self, points, values=None):
        values = self._as_dict(values)
        operations = []
        for point in points.sorted(key=lambda record: (record.function_code, record.register_address, record.sequence, record.id)):
            candidate = None
            for key in (
                str(point.id),
                point.code,
                f"{point.function_code}:{point.register_address}",
                f"{point.register_group or ''}:{point.register_address}",
            ):
                if key in values:
                    candidate = values[key]
                    break
            if isinstance(candidate, dict):
                raw_value = candidate.get("value", candidate.get("raw_value"))
                note = candidate.get("note")
                ack_kind = candidate.get("ack_kind")
            else:
                raw_value = candidate
                note = None
                ack_kind = None
            coerced = self._coerce_point_value(point, raw_value)
            operations.append(
                {
                    "point_id": point.id,
                    "point_code": point.code,
                    "function_code": point.function_code,
                    "register_group": point.register_group,
                    "register_address": point.register_address,
                    "register_count": point.register_count,
                    "data_type": point.data_type,
                    "write_method": self._point_write_method(point),
                    "writable": point.writable or not point.read_only,
                    "value": coerced["value"],
                    "value_text": coerced["value_text"],
                    "value_number": coerced["value_number"],
                    "raw_value": coerced["raw_value"],
                    "note": note,
                    "ack_kind": ack_kind,
                }
            )
        return operations

    def _build_runtime_event_payload(self, adapter, point_payload, status, payload, event_kind="modbus_point_snapshot"):
        severity = self._severity_from_status(status)
        message = point_payload.get("message") or payload.get("message") or f"{point_payload.get('point_code') or adapter.code} snapshot normalized"
        return {
            "adapter_code": adapter.code,
            "entry_code": adapter.entry_id.code if adapter.entry_id else payload.get("entry_code"),
            "workstation_code": adapter.workstation_id.code if adapter.workstation_id else payload.get("workstation_code"),
            "app_code": adapter.app_id.code if adapter.app_id else payload.get("app_code"),
            "device_code": payload.get("device_code") or adapter.code,
            "event_kind": event_kind,
            "name": point_payload.get("name") or f"{point_payload.get('point_code') or adapter.code} event",
            "status": status,
            "severity": severity,
            "message": message,
            "result": point_payload.get("result") or status,
            "payload": {
                **payload,
                "point": point_payload,
            },
            "point_code": point_payload.get("point_code"),
            "register_address": point_payload.get("register_address"),
            "register_count": point_payload.get("register_count"),
            "function_code": point_payload.get("function_code"),
        }

    def _normalize_point_items(self, adapter, payload):
        raw_items = payload.get("point_values") or payload.get("register_values") or payload.get("points") or []
        if isinstance(raw_items, dict):
            raw_items = [{"point_code": key, "value": value} for key, value in raw_items.items()]
        elif not isinstance(raw_items, list):
            raw_items = [raw_items]
        normalized = []
        changed_points = []
        for item in raw_items:
            if not isinstance(item, dict):
                item = {"value": item}
            point = self._resolve_point(adapter, item)
            raw_value = item.get("value", item.get("raw_value"))
            text_value = item.get("text_value")
            if text_value is None and raw_value is not None:
                text_value = str(raw_value)
            number_value = item.get("number_value")
            if number_value is None:
                number_value = self._coerce_float(raw_value, 0.0)
            normalized_item = {
                "point_code": item.get("point_code") or item.get("code") or (point.code if point else None),
                "register_address": item.get("register_address", point.register_address if point else None),
                "function_code": item.get("function_code", point.function_code if point else None),
                "value_text": text_value,
                "value_number": number_value,
                "unit": item.get("unit", point.unit if point else None),
                "status": item.get("status") or "ok",
            }
            normalized.append(normalized_item)
            if point:
                point.write(
                    {
                        "current_value_text": text_value,
                        "current_value_number": number_value,
                        "last_snapshot_at": self._now(),
                        "state": "ready" if normalized_item["status"] == "ok" else "degraded",
                    }
                )
                changed_points.append(point)
        return normalized, changed_points

    def build_read_plan(self, adapter, options=None):
        adapter = self._resolve_adapter_record(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        options = self._as_dict(options)
        points = self._selected_points(adapter, options)
        groups = self._build_read_groups(points)
        client_hint = OptionalPymodbusClient(
            {
                "transport": adapter.transport,
                "host": adapter.host,
                "port": adapter.port,
                "serial_port": adapter.serial_port,
                "baudrate": adapter.baudrate,
                "parity": adapter.parity,
                "stop_bits": adapter.stop_bits,
                "timeout_seconds": adapter.timeout_seconds,
                "unit_id": adapter.unit_id,
            }
        ).capability_summary()
        plan = {
            "adapter": self._serialize_adapter(adapter),
            "connection_target": adapter.connection_target or adapter._build_connection_target(),
            "client_hint": client_hint,
            "point_count": len(points),
            "group_count": len(groups),
            "estimated_register_count": sum(group["register_count"] for group in groups),
            "groups": groups,
        }
        return {"ok": True, "data": plan}

    def build_write_plan(self, adapter, options=None):
        adapter = self._resolve_adapter_record(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        options = self._as_dict(options)
        points = self._selected_points(adapter, options, writable_only=True)
        values = options.get("values") or options.get("point_values") or options.get("writes") or {}
        operations = self._build_write_operations(points, values)
        client_hint = OptionalPymodbusClient(
            {
                "transport": adapter.transport,
                "host": adapter.host,
                "port": adapter.port,
                "serial_port": adapter.serial_port,
                "baudrate": adapter.baudrate,
                "parity": adapter.parity,
                "stop_bits": adapter.stop_bits,
                "timeout_seconds": adapter.timeout_seconds,
                "unit_id": adapter.unit_id,
            }
        ).capability_summary()
        plan = {
            "adapter": self._serialize_adapter(adapter),
            "connection_target": adapter.connection_target or adapter._build_connection_target(),
            "client_hint": client_hint,
            "point_count": len(points),
            "operation_count": len(operations),
            "operations": operations,
        }
        return {"ok": True, "data": plan}

    def normalize_register_snapshot(self, adapter, payload):
        adapter = self._resolve_adapter_record(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        data = self._as_dict(payload)
        status = self._status_from_payload(data)
        raw_items = data.get("point_values") or data.get("register_values") or data.get("points") or []
        if isinstance(raw_items, dict):
            raw_items = [{"point_code": key, "value": value} for key, value in raw_items.items()]
        elif not isinstance(raw_items, list):
            raw_items = [raw_items]
        normalized_points = []
        runtime_events = []
        changed_points = []
        for item in raw_items:
            if not isinstance(item, dict):
                item = {"value": item}
            point = self._resolve_point(adapter, item)
            raw_value = item.get("value", item.get("raw_value", item.get("register_value", item.get("registers"))))
            point_payload = self._serialize_point(point) if point else {}
            point_payload.update(
                {
                    "point_id": point.id if point else item.get("point_id"),
                    "point_code": item.get("point_code") or item.get("code") or (point.code if point else None),
                    "register_address": item.get("register_address", point.register_address if point else None),
                    "register_count": item.get("register_count", point.register_count if point else 1),
                    "function_code": item.get("function_code", point.function_code if point else 3),
                    "data_type": item.get("data_type", point.data_type if point else "raw"),
                    "unit": item.get("unit", point.unit if point else None),
                    "signal_code": point.signal_id.code if point and point.signal_id else item.get("signal_code"),
                    "status": item.get("status") or status,
                    "message": item.get("message"),
                }
            )
            coerced = self._coerce_point_value(point or type("PointPayload", (), {
                "data_type": point_payload["data_type"],
                "register_address": point_payload["register_address"] or 0,
                "register_count": point_payload["register_count"] or 1,
                "scale_factor": 1.0,
                "code": point_payload["point_code"] or adapter.code,
            })(), raw_value)
            normalized_item = {
                **point_payload,
                "value": coerced["value"],
                "value_text": item.get("text_value") or coerced["value_text"],
                "value_number": item.get("number_value") if item.get("number_value") is not None else coerced["value_number"],
                "raw_value": coerced["raw_value"],
                "registers": item.get("registers"),
                "payload": item,
            }
            normalized_points.append(normalized_item)
            runtime_events.append(
                self._build_runtime_event_payload(
                    adapter,
                    normalized_item,
                    normalized_item["status"],
                    data,
                )
            )
            if point:
                changed_points.append(point)
        heartbeat_payload = {
            "adapter_code": adapter.code,
            "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
            "workstation_code": adapter.workstation_id.code if adapter.workstation_id else data.get("workstation_code"),
            "app_code": adapter.app_id.code if adapter.app_id else data.get("app_code"),
            "device_code": data.get("device_code") or adapter.code,
            "status": status,
            "message": data.get("message") or f"Modbus snapshot received for {adapter.code}",
            "latency_ms": self._coerce_int(data.get("latency_ms"), 0),
            "payload": data,
        }
        return {
            "ok": True,
            "data": {
                "status": status,
                "adapter": self._serialize_adapter(adapter),
                "point_values": normalized_points,
                "runtime_events": runtime_events,
                "heartbeat_payload": heartbeat_payload,
                "changed_points": changed_points,
            },
        }

    def preview_read_plan(self, adapter, options=None):
        adapter = self._resolve_adapter_record(adapter)
        plan = self.build_read_plan(adapter, options)
        if not plan.get("ok"):
            return plan
        preview = {
            "preview_kind": "read_plan",
            "plan": plan["data"],
            "client_hint": plan["data"].get("client_hint"),
        }
        adapter.write({"diagnostic_state": json.dumps(preview, ensure_ascii=False, default=str)})
        return {
            "ok": True,
            "data": plan["data"],
            "message": {
                "type": "success",
                "text": f"Read plan preview updated for {adapter.code}",
            },
        }

    def preview_write_plan(self, adapter, options=None):
        adapter = self._resolve_adapter_record(adapter)
        plan = self.build_write_plan(adapter, options)
        if not plan.get("ok"):
            return plan
        preview = {
            "preview_kind": "write_plan",
            "plan": plan["data"],
            "client_hint": plan["data"].get("client_hint"),
        }
        adapter.write({"diagnostic_state": json.dumps(preview, ensure_ascii=False, default=str)})
        return {
            "ok": True,
            "data": plan["data"],
            "message": {
                "type": "success",
                "text": f"Write plan preview updated for {adapter.code}",
            },
        }

    def submit_test_snapshot(self, adapter, options=None):
        adapter = self._resolve_adapter_record(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        options = self._as_dict(options)
        points = self._selected_points(adapter, options)
        point_values = []
        for point in points:
            payload = self._coerce_point_value(point, options.get("values", {}).get(point.code) if isinstance(options.get("values"), dict) else None)
            point_values.append(
                {
                    "point_id": point.id,
                    "point_code": point.code,
                    "register_address": point.register_address,
                    "register_count": point.register_count,
                    "function_code": point.function_code,
                    "data_type": point.data_type,
                    "unit": point.unit,
                    "value": payload["value"],
                    "text_value": payload["value_text"],
                    "number_value": payload["value_number"],
                    "registers": payload["raw_value"] if isinstance(payload["raw_value"], list) else [payload["raw_value"]],
                    "status": options.get("status") or "ok",
                    "message": options.get("message"),
                }
            )
        snapshot_payload = {
            "adapter_code": adapter.code,
            "entry_code": options.get("entry_code"),
            "workstation_code": options.get("workstation_code"),
            "app_code": options.get("app_code"),
            "device_code": options.get("device_code") or adapter.code,
            "snapshot_kind": options.get("snapshot_kind") or "manual",
            "status": options.get("status") or "ok",
            "message": options.get("message") or f"Test snapshot for {adapter.code}",
            "point_values": point_values,
            "latency_ms": self._coerce_int(options.get("latency_ms"), 0),
            "result": options.get("result") or "ok",
        }
        return self.ingest_register_snapshot(snapshot_payload)

    def submit_test_write_ack(self, adapter, options=None):
        adapter = self._resolve_adapter_record(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        options = self._as_dict(options)
        points = self._selected_points(adapter, options, writable_only=True)
        if not points:
            return {"ok": False, "errors": ["No writable Modbus points available"]}
        limit = self._coerce_int(options.get("limit"), 1)
        if limit > 0:
            points = points[:limit]
        values = options.get("values") or {}
        results = []
        for point in points:
            operation = self._build_write_operations(self.env["gateway.modbus.point"].sudo().browse(point.id), values)[0]
            ack_payload = {
                "adapter_code": adapter.code,
                "entry_code": options.get("entry_code"),
                "workstation_code": options.get("workstation_code"),
                "app_code": options.get("app_code"),
                "device_code": options.get("device_code") or adapter.code,
                "point_id": point.id,
                "point_code": point.code,
                "register_address": operation["register_address"],
                "register_count": operation["register_count"],
                "ack_kind": options.get("ack_kind") or "manual",
                "result_state": options.get("result_state") or "acknowledged",
                "write_value_text": operation["value_text"],
                "value": operation["value"],
                "response_text": options.get("response_text")
                or json.dumps(
                    {
                        "point_code": point.code,
                        "result_state": options.get("result_state") or "acknowledged",
                        "transport": adapter.transport,
                    },
                    ensure_ascii=False,
                ),
                "error_message": options.get("error_message"),
                "latency_ms": self._coerce_int(options.get("latency_ms"), 0),
                "message": options.get("message") or f"Test write ack for {point.code}",
                "note": options.get("note"),
            }
            results.append(self.ingest_write_ack(ack_payload))
        if len(results) == 1:
            return results[0]
        return {
            "ok": True,
            "data": results,
            "message": {
                "type": "success",
                "text": f"Write acknowledgements submitted for {len(results)} points",
            },
        }

    def _serialize_adapter(self, record):
        return {
            "id": record.id,
            "name": record.name,
            "code": record.code,
            "state": record.state,
            "transport": record.transport,
            "connection_target": record.connection_target,
            "entry": record.entry_id.code if record.entry_id else None,
            "runtime_adapter": record.runtime_adapter_id.code if record.runtime_adapter_id else None,
            "snapshot_count": record.snapshot_count,
            "ack_count": record.ack_count,
            "last_snapshot_at": record.last_snapshot_at,
            "last_ack_at": record.last_ack_at,
        }

    def _serialize_snapshot(self, record):
        return {
            "id": record.id,
            "code": record.code,
            "status": record.status,
            "state": record.state,
            "adapter": record.adapter_id.code if record.adapter_id else None,
            "point": record.point_id.code if record.point_id else None,
            "command": record.command_id.code if record.command_id else None,
            "message": record.message,
            "received_at": record.received_at,
        }

    def _serialize_write_ack(self, record):
        return {
            "id": record.id,
            "code": record.code,
            "ack_kind": record.ack_kind,
            "result_state": record.result_state,
            "adapter": record.adapter_id.code if record.adapter_id else None,
            "point": record.point_id.code if record.point_id else None,
            "command": record.command_id.code if record.command_id else None,
            "message": record.response_text or record.error_message,
            "ack_at": record.ack_at,
        }

    def build_runtime_payload(self, target):
        adapter = self._resolve_adapter_record(target)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        runtime_payload = self._adapter_payload_for_runtime(adapter)
        capability = self.runtime.build_capability_payload(payload=runtime_payload)
        diagnostics = self.runtime.runtime_diagnostics({"adapter_code": adapter.code})
        coordinator = capability.get("coordinator", {})
        runtime_payload.update(
            {
                "coordinator_mode": "poll",
                "update_interval_seconds": adapter.poll_interval_seconds or 5,
                "retry_after_seconds": coordinator.get("retry_after", 0),
                "capability_json": capability.get("capability_json"),
                "coordinator_json": json.dumps(coordinator, ensure_ascii=False, default=str),
                "diagnostic_summary_json": json.dumps(diagnostics.get("data", {}), ensure_ascii=False, default=str),
                "runtime_context_json": json.dumps(
                    {
                        "capability": capability,
                        "coordinator": coordinator,
                        "diagnostics": diagnostics.get("data"),
                    },
                    ensure_ascii=False,
                    default=str,
                ),
                "client_backend_json": json.dumps(
                    OptionalPymodbusClient(runtime_payload).capability_summary(),
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
        adapter = self._resolve_adapter_record(target)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        runtime_payload = self.build_runtime_payload(adapter)
        diagnostics = self.runtime.runtime_diagnostics({"adapter_code": adapter.code})
        capability = self.runtime.build_capability_payload(payload=runtime_payload.get("data") if runtime_payload.get("ok") else self._adapter_payload_for_runtime(adapter))
        return {
            "ok": True,
            "data": {
                "adapter": self._serialize_adapter(adapter),
                "runtime_payload": runtime_payload.get("data") if runtime_payload.get("ok") else {},
                "capability": capability,
                "coordinator": capability.get("coordinator", {}),
                "diagnostics": diagnostics.get("data"),
                "diagnostic_summary_json": json.dumps(diagnostics.get("data", {}), ensure_ascii=False, default=str),
            },
            "message": {"type": "success", "text": "Modbus runtime summary ready"},
        }

    def _apply_runtime_result(self, adapter, result):
        if not adapter:
            return result
        values = {"diagnostic_state": json.dumps(result, ensure_ascii=False, default=str)}
        data = result.get("data") if isinstance(result, dict) else {}
        if isinstance(data, dict):
            runtime_adapter = self.env["gateway.runtime.adapter"].sudo().search([("code", "=", adapter.code)], limit=1)
            if runtime_adapter:
                values["runtime_adapter_id"] = runtime_adapter.id
            adapter_data = data.get("adapter") or {}
            if adapter_data.get("state"):
                values["state"] = adapter_data["state"]
        adapter.write(values)
        return result

    def refresh_runtime_adapter(self, target, reason=None):
        adapter = self._resolve_adapter_record(target)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        result = self.runtime.refresh_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else None,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
                "device_code": adapter.code,
                "reason": reason or "manual_refresh",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def repair_runtime_adapter(self, target, reason=None):
        adapter = self._resolve_adapter_record(target)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        result = self.runtime.repair_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else None,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
                "device_code": adapter.code,
                "reason": reason or "manual_repair",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def load_runtime_adapter(self, target, reason=None):
        adapter = self._resolve_adapter_record(target)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        result = self.runtime.load_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else None,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
                "device_code": adapter.code,
                "reason": reason or "manual_load",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def reload_runtime_adapter(self, target, reason=None):
        adapter = self._resolve_adapter_record(target)
        if not adapter:
            return {"ok": False, "errors": ["Modbus adapter not found"]}
        result = self.runtime.reload_runtime(
            {
                "adapter_code": adapter.code,
                "entry_code": adapter.entry_id.code if adapter.entry_id else None,
                "workstation_code": adapter.workstation_id.code if adapter.workstation_id else None,
                "device_code": adapter.code,
                "reason": reason or "manual_reload",
            }
        )
        return self._apply_runtime_result(adapter, result)

    def register_adapter_definition(self, payload):
        data = self._as_dict(payload)
        adapter = self._resolve_modbus_adapter(data)
        entry = self._resolve_entry(data)
        workstation = self._resolve_workstation(data)
        app = self._resolve_app(data)
        values = {
            "name": data.get("name") or data.get("adapter_name") or (adapter.name if adapter else "Modbus Adapter"),
            "adapter_type": "modbus",
            "entry_id": entry.id if entry else (adapter.entry_id.id if adapter and adapter.entry_id else False),
            "app_id": app.id if app else (adapter.app_id.id if adapter and adapter.app_id else False),
            "workstation_id": workstation.id if workstation else (adapter.workstation_id.id if adapter and adapter.workstation_id else False),
            "transport": data.get("transport") or (adapter.transport if adapter else "tcp"),
            "host": data.get("host") if "host" in data else (adapter.host if adapter else False),
            "port": self._coerce_int(data.get("port"), adapter.port if adapter else 502),
            "serial_port": data.get("serial_port") if "serial_port" in data else (adapter.serial_port if adapter else False),
            "baudrate": self._coerce_int(data.get("baudrate"), adapter.baudrate if adapter else 9600),
            "parity": data.get("parity") or (adapter.parity if adapter else "N"),
            "stop_bits": data.get("stop_bits") or (adapter.stop_bits if adapter else "1"),
            "unit_id": self._coerce_int(data.get("unit_id"), adapter.unit_id if adapter else 1),
            "poll_interval_seconds": self._coerce_int(data.get("poll_interval_seconds"), adapter.poll_interval_seconds if adapter else 5),
            "timeout_seconds": self._coerce_int(data.get("timeout_seconds"), adapter.timeout_seconds if adapter else 3),
            "retry_limit": self._coerce_int(data.get("retry_limit"), adapter.retry_limit if adapter else 3),
            "connection_target": data.get("connection_target") or (adapter.connection_target if adapter else None) or self._build_connection_target(
                {
                    "transport": data.get("transport") or (adapter.transport if adapter else "tcp"),
                    "host": data.get("host") if "host" in data else (adapter.host if adapter else None),
                    "port": data.get("port") if "port" in data else (adapter.port if adapter else 502),
                    "serial_port": data.get("serial_port") if "serial_port" in data else (adapter.serial_port if adapter else None),
                    "baudrate": data.get("baudrate") if "baudrate" in data else (adapter.baudrate if adapter else 9600),
                    "parity": data.get("parity") or (adapter.parity if adapter else "N"),
                    "stop_bits": data.get("stop_bits") or (adapter.stop_bits if adapter else "1"),
                    "unit_id": data.get("unit_id") if "unit_id" in data else (adapter.unit_id if adapter else 1),
                }
            ),
            "config_json": data.get("config_json") if data.get("config_json") is not None else (adapter.config_json if adapter else False),
            "config_text": data.get("config_text") if data.get("config_text") is not None else (adapter.config_text if adapter else False),
            "diagnostic_state": json.dumps(
                {
                    "registered": True,
                    "transport": data.get("transport") or (adapter.transport if adapter else "tcp"),
                },
                ensure_ascii=False,
                default=str,
            ),
            "state": data.get("state") or (adapter.state if adapter else "ready"),
        }
        if adapter:
            adapter.write(values)
        else:
            values["code"] = data.get("code") or data.get("adapter_code") or "New"
            adapter = self.env["gateway.modbus.adapter"].sudo().create(values)
        runtime_payload = self.build_runtime_payload(adapter)
        runtime_result = GatewayRuntimeService(self.env).register_adapter_definition(
            runtime_payload.get("data") if runtime_payload.get("ok") else adapter._runtime_payload()
        )
        runtime_adapter = self.env["gateway.runtime.adapter"].sudo().search([("code", "=", adapter.code)], limit=1)
        adapter.write(
            {
                "runtime_adapter_id": runtime_adapter.id if runtime_adapter else False,
                "state": runtime_adapter.state if runtime_adapter else adapter.state,
                "diagnostic_state": json.dumps(
                    {
                        "registered": True,
                        "runtime_result": runtime_result,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            }
        )
        return {
            "ok": True,
            "data": self._serialize_adapter(adapter),
            "runtime_result": runtime_result,
            "message": {"type": "success", "text": "Modbus adapter registered"},
        }

    def ingest_register_snapshot(self, payload):
        data = self._as_dict(payload)
        adapter = self._resolve_modbus_adapter(data)
        if not adapter:
            registration = self.register_adapter_definition(data)
            if not registration.get("ok"):
                return registration
            adapter = self._resolve_modbus_adapter(data)
        normalized = self.normalize_register_snapshot(adapter, data)
        if not normalized.get("ok"):
            return normalized
        normalized_data = normalized["data"]
        status = normalized_data["status"]
        point_values = normalized_data["point_values"]
        changed_points = normalized_data["changed_points"]
        point = self._resolve_point(adapter, data)
        if not point and point_values:
            first_point_id = point_values[0].get("point_id")
            if first_point_id:
                point = self.env["gateway.modbus.point"].sudo().browse(first_point_id).exists()
        command = self._resolve_command(data)
        runtime_service = GatewayRuntimeService(self.env)
        runtime_heartbeat = runtime_service.ingest_heartbeat(normalized_data["heartbeat_payload"])
        runtime_event_results = []
        for event_payload in normalized_data["runtime_events"]:
            runtime_event_results.append(runtime_service.ingest_event(event_payload))
        snapshot = self.env["gateway.modbus.snapshot"].sudo().create(
            {
                "name": data.get("name") or f"Snapshot {adapter.code}",
                "adapter_id": adapter.id,
                "runtime_adapter_id": adapter.runtime_adapter_id.id if adapter.runtime_adapter_id else False,
                "point_id": point.id if point else False,
                "command_id": command.id if command else False,
                "entry_id": adapter.entry_id.id if adapter.entry_id else (self._resolve_entry(data).id if self._resolve_entry(data) else False),
                "device_id": command.device_id.id if command and command.device_id else False,
                "snapshot_kind": data.get("snapshot_kind") or "register_snapshot",
                "status": status,
                "state": "processed",
                "latency_ms": self._coerce_int(data.get("latency_ms"), 0),
                "payload_json": json.dumps(data, ensure_ascii=False, default=str),
                "normalized_json": json.dumps(
                    {
                        "status": status,
                        "points": point_values,
                        "runtime_heartbeat": runtime_heartbeat,
                        "runtime_events": runtime_event_results,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
                "point_values_json": json.dumps(point_values, ensure_ascii=False, default=str),
                "message": data.get("message") or f"Snapshot received for {adapter.code}",
                "processed_at": self._now(),
            }
        )
        point_status_map = {item.get("point_id"): item for item in point_values if item.get("point_id")}
        for changed_point in changed_points:
            point_item = point_status_map.get(changed_point.id)
            if not point_item:
                continue
            changed_point.write(
                {
                    "current_value_text": point_item.get("value_text"),
                    "current_value_number": point_item.get("value_number") if point_item.get("value_number") is not None else changed_point.current_value_number,
                    "last_snapshot_at": self._now(),
                    "state": "ready" if point_item.get("status") == "ok" else "degraded",
                }
            )
        adapter.write(
            {
                "snapshot_count": adapter.snapshot_count + 1,
                "last_snapshot_at": snapshot.received_at,
                "state": "ready" if status == "ok" else "degraded" if status == "warn" else "offline" if status == "offline" else "degraded",
                "diagnostic_state": json.dumps(
                    {
                        "snapshot": self._serialize_snapshot(snapshot),
                        "points": point_values,
                        "runtime_events": runtime_event_results,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            }
        )
        return {
            "ok": True,
            "data": {
                "snapshot": self._serialize_snapshot(snapshot),
                "adapter": self._serialize_adapter(adapter),
                "changed_points": [point_record.code for point_record in changed_points],
                "runtime_heartbeat": runtime_heartbeat,
                "runtime_events": runtime_event_results,
            },
            "message": {"type": "success", "text": "Register snapshot ingested"},
        }

    def ingest_write_ack(self, payload):
        data = self._as_dict(payload)
        adapter = self._resolve_modbus_adapter(data)
        if not adapter:
            registration = self.register_adapter_definition(data)
            if not registration.get("ok"):
                return registration
            adapter = self._resolve_modbus_adapter(data)
        point = self._resolve_point(adapter, data)
        command = self._resolve_command(data)
        result_state = data.get("result_state") or data.get("state") or data.get("ack_state") or "acknowledged"
        if result_state not in {"done", "failed", "acknowledged", "pending"}:
            result_state = "acknowledged"
        ack = self.env["gateway.modbus.write.ack"].sudo().create(
            {
                "name": data.get("name") or f"Ack {adapter.code}",
                "adapter_id": adapter.id,
                "runtime_adapter_id": adapter.runtime_adapter_id.id if adapter.runtime_adapter_id else False,
                "point_id": point.id if point else False,
                "command_id": command.id if command else False,
                "ack_kind": data.get("ack_kind") or ("command" if command else "write"),
                "result_state": result_state,
                "register_address": self._coerce_int(data.get("register_address"), point.register_address if point else 0),
                "register_count": self._coerce_int(data.get("register_count"), point.register_count if point else 1),
                "write_value_text": data.get("write_value_text") or data.get("value_text") or str(data.get("value") or ""),
                "payload_json": json.dumps(data, ensure_ascii=False, default=str),
                "normalized_json": json.dumps(
                    {
                        "result_state": result_state,
                        "point_code": point.code if point else None,
                        "command_code": command.code if command else None,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
                "response_text": data.get("response_text"),
                "error_message": data.get("error_message"),
                "latency_ms": self._coerce_int(data.get("latency_ms"), 0),
                "processed_at": self._now(),
                "note": data.get("note"),
            }
        )
        if point and (data.get("write_value_text") is not None or data.get("value") is not None):
            point.write(
                {
                    "current_value_text": data.get("write_value_text") or str(data.get("value")),
                    "current_value_number": self._coerce_float(data.get("value"), point.current_value_number),
                    "last_snapshot_at": self._now(),
                    "state": "ready" if result_state != "failed" else "degraded",
                }
            )
        if command:
            runtime_result = GatewayRuntimeService(self.env).queue_command_execution_result(
                command,
                {
                    "state": "done" if result_state in {"done", "acknowledged"} else "failed",
                    "response_text": data.get("response_text") or json.dumps(data, ensure_ascii=False, default=str),
                    "error_message": data.get("error_message"),
                    "diagnostic_state": json.dumps(
                        {
                            "ack_code": ack.code,
                            "point_code": point.code if point else None,
                        },
                        ensure_ascii=False,
                        default=str,
                    ),
                },
            )
        else:
            runtime_result = GatewayRuntimeService(self.env).ingest_event(
                {
                    "adapter_code": adapter.code,
                    "entry_code": adapter.entry_id.code if adapter.entry_id else data.get("entry_code"),
                    "workstation_code": adapter.workstation_id.code if adapter.workstation_id else data.get("workstation_code"),
                    "app_code": adapter.app_id.code if adapter.app_id else data.get("app_code"),
                    "device_code": data.get("device_code") or adapter.code,
                    "event_kind": data.get("event_kind") or "command",
                    "status": "error" if result_state == "failed" else "ok",
                    "severity": "high" if result_state == "failed" else "low",
                    "message": data.get("response_text") or data.get("error_message") or f"Write ack for {adapter.code}",
                    "result": result_state,
                    "payload": data,
                }
            )
        adapter.write(
            {
                "ack_count": adapter.ack_count + 1,
                "last_ack_at": ack.ack_at,
                "state": "ready" if result_state in {"done", "acknowledged"} else "degraded",
                "diagnostic_state": json.dumps(
                    {
                        "ack": self._serialize_write_ack(ack),
                        "runtime_result": runtime_result,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            }
        )
        return {
            "ok": True,
            "data": {
                "ack": self._serialize_write_ack(ack),
                "adapter": self._serialize_adapter(adapter),
                "runtime_result": runtime_result,
            },
            "message": {"type": "success", "text": "Write acknowledgement ingested"},
        }
