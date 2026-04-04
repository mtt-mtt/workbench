from odoo import api, fields, models, _

from ..services.modbus_service import GatewayModbusService


class GatewayModbusAdapter(models.Model):
    _name = "gateway.modbus.adapter"
    _description = "Gateway Modbus Adapter"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("degraded", "Degraded"),
            ("offline", "Offline"),
            ("disabled", "Disabled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    adapter_type = fields.Selection([("modbus", "Modbus")], default="modbus", required=True)
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null")
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    transport = fields.Selection(
        [
            ("tcp", "TCP"),
            ("rtu", "RTU"),
            ("ascii", "ASCII"),
            ("tcp_tls", "TCP/TLS"),
            ("mock", "Mock"),
        ],
        default="tcp",
        required=True,
    )
    host = fields.Char()
    port = fields.Integer(default=502)
    serial_port = fields.Char()
    baudrate = fields.Integer(default=9600)
    parity = fields.Selection([("N", "None"), ("E", "Even"), ("O", "Odd")], default="N")
    stop_bits = fields.Selection([("1", "1"), ("2", "2")], default="1")
    unit_id = fields.Integer(default=1)
    poll_interval_seconds = fields.Integer(default=5)
    timeout_seconds = fields.Integer(default=3)
    retry_limit = fields.Integer(default=3)
    connection_target = fields.Char()
    config_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    last_snapshot_at = fields.Datetime()
    last_ack_at = fields.Datetime()
    snapshot_count = fields.Integer(default=0)
    ack_count = fields.Integer(default=0)
    note = fields.Text()
    point_ids = fields.One2many("gateway.modbus.point", "adapter_id", string="Points")
    snapshot_ids = fields.One2many("gateway.modbus.snapshot", "adapter_id", string="Snapshots")
    ack_ids = fields.One2many("gateway.modbus.write.ack", "adapter_id", string="Write Acks")
    runtime_lifecycle_state = fields.Selection(related="runtime_adapter_id.lifecycle_state", readonly=True)
    runtime_health_state = fields.Selection(related="runtime_adapter_id.health_state", readonly=True)
    runtime_capability_summary = fields.Char(related="runtime_adapter_id.capability_summary", readonly=True)
    runtime_diagnostic_summary = fields.Text(related="runtime_adapter_id.diagnostic_summary", readonly=True)
    runtime_issue_count = fields.Integer(related="runtime_adapter_id.issue_count", readonly=True)
    runtime_open_issue_count = fields.Integer(related="runtime_adapter_id.open_issue_count", readonly=True)
    runtime_repair_issue_count = fields.Integer(related="runtime_adapter_id.repair_issue_count", readonly=True)

    _gateway_modbus_adapter_code_uniq = models.Constraint(
        "unique(code)",
        "Modbus adapter code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.modbus.adapter") or _("New")
            vals.setdefault("adapter_type", "modbus")
        records = super().create(vals_list)
        for record in records:
            if not record.connection_target:
                record.connection_target = record._build_connection_target()
        return records

    def write(self, vals):
        result = super().write(vals)
        if {"transport", "host", "port", "serial_port", "baudrate", "unit_id"} & set(vals):
            for record in self:
                if not record.connection_target or vals.get("transport") or vals.get("host") or vals.get("port") or vals.get("serial_port"):
                    record.connection_target = record._build_connection_target()
        return result

    def _build_connection_target(self):
        self.ensure_one()
        if self.transport == "rtu":
            base = self.serial_port or "/dev/ttyUSB0"
            return f"modbus+rtu://{base}?baudrate={self.baudrate}&parity={self.parity}&stop_bits={self.stop_bits}&unit={self.unit_id}"
        if self.transport == "ascii":
            base = self.serial_port or "/dev/ttyUSB0"
            return f"modbus+ascii://{base}?baudrate={self.baudrate}&parity={self.parity}&stop_bits={self.stop_bits}&unit={self.unit_id}"
        scheme = "modbus+tls" if self.transport == "tcp_tls" else "modbus"
        host = self.host or "127.0.0.1"
        return f"{scheme}://{host}:{self.port}/unit/{self.unit_id}"

    def _runtime_payload(self):
        self.ensure_one()
        service = GatewayModbusService(self.env)
        result = service.build_runtime_payload(self)
        if result.get("ok"):
            return result["data"]
        return {
            "code": self.code,
            "name": self.name,
            "adapter_type": "modbus",
            "entry_code": self.entry_id.code if self.entry_id else None,
            "workstation_code": self.workstation_id.code if self.workstation_id else None,
            "app_code": self.app_id.code if self.app_id else None,
            "device_code": self.code,
            "transport": self.transport,
            "host": self.host,
            "port": self.port,
            "serial_port": self.serial_port,
            "baudrate": self.baudrate,
            "parity": self.parity,
            "stop_bits": self.stop_bits,
            "unit_id": self.unit_id,
            "poll_interval_seconds": self.poll_interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "retry_limit": self.retry_limit,
            "connection_target": self.connection_target or self._build_connection_target(),
            "config_json": self.config_json,
            "config_text": self.config_text,
        }

    def action_sync_runtime_definition(self):
        service = GatewayModbusService(self.env)
        results = [service.register_adapter_definition(record._runtime_payload()) for record in self]
        return results[0] if len(results) == 1 else results

    def action_open_runtime_adapter(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        return {
            "type": "ir.actions.act_window",
            "name": _("Modbus Runtime"),
            "res_model": "gateway.runtime.adapter",
            "view_mode": "form",
            "res_id": runtime.id,
            "context": {"active_id": runtime.id, "active_model": "gateway.runtime.adapter"},
        }

    def action_open_runtime_console(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_console").read()[0]
        action["domain"] = [("id", "=", runtime.id)]
        action["context"] = {"search_default_needs_attention": 1}
        action["name"] = _("Modbus Runtime Console")
        return action

    def action_open_protocol_probe(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        return runtime.action_open_protocol_probe()

    def action_open_runtime_diagnostics(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("Modbus Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Modbus Runtime Diagnostics"),
            "res_model": "gateway.runtime.event",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", runtime.id),
                ("event_kind", "in", ["diagnostic", "alarm", "command"]),
            ],
            "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
        }

    def action_open_runtime_issues(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("Modbus Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Modbus Runtime Diagnostics"),
            "res_model": "gateway.runtime.event",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", runtime.id),
                ("event_kind", "in", ["diagnostic", "alarm", "command"]),
            ],
            "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
        }

    def action_open_repairs(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("Modbus Runtime Repairs"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id), ("is_fixable", "=", True)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id, "search_default_fixable": 1, "search_default_open": 1},
            }
        return self.action_open_runtime_issues()

    def action_open_repairs(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._notify_action(_("Modbus Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("Modbus Runtime Repairs"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id), ("is_fixable", "=", True), ("state", "in", ["new", "open", "in_progress"])],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id, "search_default_fixable": 1, "search_default_open": 1},
            }
        return self.action_open_runtime_issues()

    def _notify_action(self, title, message, level="success"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": level,
                "sticky": False,
            },
        }

    def action_preview_read_plan(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).preview_read_plan(self)
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to preview read plan"])), "warning")
        data = result["data"]
        return self._notify_action(
            _("Read Plan Preview"),
            _("Groups: %s, Points: %s, Registers: %s")
            % (data.get("group_count", 0), data.get("point_count", 0), data.get("estimated_register_count", 0)),
        )

    def action_preview_write_plan(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).preview_write_plan(self)
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to preview write plan"])), "warning")
        data = result["data"]
        return self._notify_action(
            _("Write Plan Preview"),
            _("Operations: %s, Writable points: %s") % (data.get("operation_count", 0), data.get("point_count", 0)),
        )

    def action_submit_test_snapshot(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).submit_test_snapshot(self)
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to submit test snapshot"])), "warning")
        data = result.get("data", {})
        snapshot = data.get("snapshot", {})
        runtime_events = data.get("runtime_events", [])
        return self._notify_action(
            _("Test Snapshot Submitted"),
            _("Snapshot %s sent with %s runtime events") % (snapshot.get("code", "-"), len(runtime_events)),
        )

    def action_submit_test_write_ack(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).submit_test_write_ack(self)
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to submit test write ack"])), "warning")
        data = result.get("data", {})
        if isinstance(data, list):
            count = len(data)
        else:
            count = 1
        return self._notify_action(
            _("Test Write Ack Submitted"),
            _("Write acknowledgements sent: %s") % count,
        )

    def action_refresh_runtime(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).refresh_runtime_adapter(self)
        return self._runtime_feedback(_("Modbus Runtime Refresh"), result)

    def action_repair_runtime(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).repair_runtime_adapter(self)
        return self._runtime_feedback(_("Modbus Runtime Repair"), result)

    def action_load_runtime(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).load_runtime_adapter(self)
        return self._runtime_feedback(_("Modbus Runtime Load"), result)

    def action_reload_runtime(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).reload_runtime_adapter(self)
        return self._runtime_feedback(_("Modbus Runtime Reload"), result)

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled"})

    def _runtime_feedback(self, title, result):
        if not result.get("ok"):
            return self._notify_action(title, ", ".join(result.get("errors", ["Runtime action failed"])), "warning")
        message = result.get("message", {}).get("text") or title
        return self._notify_action(title, message, "success")
