import json

from odoo import api, fields, models, _

from ..services.s7_bridge_service import GatewayS7BridgeService
from ..services.s7_service import GatewayS7Service


class GatewayS7Adapter(models.Model):
    _name = "gateway.s7.adapter"
    _description = "Siemens S7 Adapter"
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
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null", readonly=True)
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    host = fields.Char(required=True)
    port = fields.Integer(default=102)
    rack = fields.Integer(default=0)
    slot = fields.Integer(default=1)
    cpu = fields.Char()
    connection_target = fields.Char()
    poll_interval_seconds = fields.Integer(default=5)
    timeout_seconds = fields.Integer(default=3)
    retry_limit = fields.Integer(default=3)
    config_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    runtime_capability_json = fields.Text(readonly=True)
    runtime_capability_summary = fields.Char(readonly=True)
    runtime_diagnostic_summary = fields.Text(readonly=True)
    runtime_last_refresh_at = fields.Datetime(readonly=True)
    runtime_last_repair_at = fields.Datetime(readonly=True)
    runtime_last_reload_at = fields.Datetime(readonly=True)
    runtime_lifecycle_state = fields.Selection(related="runtime_adapter_id.lifecycle_state", readonly=True)
    runtime_health_state = fields.Selection(related="runtime_adapter_id.health_state", readonly=True)
    runtime_issue_count = fields.Integer(related="runtime_adapter_id.issue_count", readonly=True)
    runtime_open_issue_count = fields.Integer(related="runtime_adapter_id.open_issue_count", readonly=True)
    last_snapshot_at = fields.Datetime()
    last_ack_at = fields.Datetime()
    point_count = fields.Integer(default=0)
    snapshot_count = fields.Integer(default=0)
    ack_count = fields.Integer(default=0)
    note = fields.Text()
    tag_ids = fields.One2many("gateway.s7.tag", "adapter_id", string="Tags")
    snapshot_ids = fields.One2many("gateway.s7.snapshot", "adapter_id", string="Snapshots")
    ack_ids = fields.One2many("gateway.s7.write.ack", "adapter_id", string="Write Acks")
    diagnostic_ids = fields.One2many("gateway.s7.diagnostic", "adapter_id", string="Diagnostics", readonly=True)

    _gateway_s7_adapter_code_uniq = models.Constraint(
        "unique(code)",
        "S7 adapter code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.s7.adapter") or _("New")
            vals.setdefault("state", "draft")
        records = super().create(vals_list)
        for record in records:
            if not record.connection_target:
                record.connection_target = record._build_connection_target()
        return records

    def write(self, vals):
        result = super().write(vals)
        if {"host", "port", "rack", "slot"} & set(vals):
            for record in self:
                if not record.connection_target or vals.get("host") or vals.get("port") or vals.get("rack") or vals.get("slot"):
                    record.connection_target = record._build_connection_target()
        return result

    def _build_connection_target(self):
        self.ensure_one()
        return f"s7://{self.host}:{self.port}?rack={self.rack}&slot={self.slot}&cpu={self.cpu or 'S7'}"

    def _runtime_payload(self):
        self.ensure_one()
        return {
            "code": self.code,
            "name": self.name,
            "adapter_type": "s7",
            "entry_code": self.entry_id.code if self.entry_id else None,
            "workstation_code": self.workstation_id.code if self.workstation_id else None,
            "app_code": self.app_id.code if self.app_id else None,
            "device_code": self.code,
            "connection_target": self.connection_target or self._build_connection_target(),
            "host": self.host,
            "port": self.port,
            "rack": self.rack,
            "slot": self.slot,
            "cpu": self.cpu,
            "config_json": self.config_json,
            "config_text": self.config_text,
        }

    def _runtime_notification(self, title, message, level="success"):
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

    def _write_runtime_feedback(self, result, touch_field=None):
        self.ensure_one()
        if not result or not result.get("ok"):
            return self._runtime_notification(_("S7"), ", ".join(result.get("errors", ["Runtime action failed"])), "warning")
        data = result.get("data") or {}
        capability = data.get("capability") or {}
        coordinator = data.get("coordinator") or {}
        values = {
            "diagnostic_state": json.dumps(result, ensure_ascii=False, default=str),
            "runtime_diagnostic_summary": json.dumps(
                {
                    "capability": capability,
                    "coordinator": coordinator,
                    "signal": data.get("signal"),
                },
                ensure_ascii=False,
                default=str,
            ),
        }
        runtime_adapter = data.get("adapter") or {}
        if runtime_adapter:
            values["runtime_adapter_id"] = runtime_adapter.get("id") if isinstance(runtime_adapter, dict) else False
        if capability:
            values["runtime_capability_json"] = capability.get("capability_json") or json.dumps(capability, ensure_ascii=False, default=str)
            values["runtime_capability_summary"] = self._runtime_capability_summary(capability)
        if touch_field:
            values[touch_field] = fields.Datetime.now()
        self.write(values)
        return self._runtime_notification(_("S7"), _("Runtime action completed"), "success")

    def action_sync_runtime_definition(self):
        service = GatewayS7Service(self.env)
        results = [service.register_adapter_definition(record._runtime_payload()) for record in self]
        return results[0] if len(results) == 1 else results

    def action_open_runtime_adapter(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("S7"), _("No linked runtime adapter found"), "warning")
        return {
            "type": "ir.actions.act_window",
            "name": _("S7 Runtime"),
            "res_model": "gateway.runtime.adapter",
            "view_mode": "form",
            "res_id": runtime.id,
            "context": {"active_id": runtime.id, "active_model": "gateway.runtime.adapter"},
        }

    def action_open_runtime_diagnostics(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("S7"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("S7 Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("S7 Runtime Diagnostics"),
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
            return self._runtime_notification(_("S7"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("S7 Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("S7 Runtime Diagnostics"),
            "res_model": "gateway.runtime.event",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", runtime.id),
                ("event_kind", "in", ["diagnostic", "alarm", "command"]),
            ],
            "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
        }

    def action_refresh_runtime(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).refresh_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_refresh_at")

    def action_repair_runtime(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).repair_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_repair_at")

    def action_load_runtime(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).load_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_refresh_at")

    def action_reload_runtime(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).reload_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_reload_at")

    def action_refresh_diagnostics(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).runtime_diagnostics(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_refresh_at")

    def action_preview_read_plan(self):
        self.ensure_one()
        GatewayS7BridgeService(self.env).preview_read_plan(self)
        return self._action_open_diagnostics(_("S7 Read Preview"))

    def action_preview_write_plan(self):
        self.ensure_one()
        GatewayS7BridgeService(self.env).preview_write_plan(self)
        return self._action_open_diagnostics(_("S7 Write Preview"))

    def action_submit_test_snapshot(self):
        self.ensure_one()
        GatewayS7BridgeService(self.env).submit_test_snapshot(self)
        return self._action_open_diagnostics(_("S7 Test Snapshot"))

    def action_submit_test_write_ack(self):
        self.ensure_one()
        GatewayS7BridgeService(self.env).submit_test_write_ack(self)
        return self._action_open_diagnostics(_("S7 Test Write Ack"))

    def _action_open_diagnostics(self, title):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "gateway.s7.diagnostic",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id)],
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }
