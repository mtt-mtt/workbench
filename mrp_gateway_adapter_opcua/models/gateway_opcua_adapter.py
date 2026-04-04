import json

from odoo import api, fields, models, _

from ..services.opcua_bridge_service import GatewayOpcuaBridgeService


class GatewayOpcuaAdapter(models.Model):
    _name = "gateway.opcua.adapter"
    _description = "OPC UA Adapter"
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
    endpoint_url = fields.Char(required=True)
    security_policy = fields.Selection(
        [("none", "None"), ("basic128rsa15", "Basic128Rsa15"), ("basic256", "Basic256"), ("basic256sha256", "Basic256Sha256")],
        default="none",
        required=True,
    )
    security_mode = fields.Selection(
        [("none", "None"), ("sign", "Sign"), ("sign_and_encrypt", "Sign and Encrypt")],
        default="none",
        required=True,
    )
    auth_mode = fields.Selection([("anonymous", "Anonymous"), ("username", "Username")], default="anonymous", required=True)
    username = fields.Char()
    password = fields.Char()
    namespace_uri = fields.Char()
    connection_target = fields.Char()
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
    last_sync_at = fields.Datetime()
    last_connect_at = fields.Datetime()
    node_count = fields.Integer(default=0)
    diagnostic_count = fields.Integer(default=0)
    note = fields.Text()
    node_ids = fields.One2many("gateway.opcua.node", "adapter_id", string="Nodes")
    diagnostic_ids = fields.One2many("gateway.opcua.diagnostic", "adapter_id", string="Diagnostics", readonly=True)

    _gateway_opcua_adapter_code_uniq = models.Constraint(
        "unique(code)",
        "OPC UA adapter code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.opcua.adapter") or _("New")
            vals.setdefault("state", "draft")
        return super().create(vals_list)

    def _runtime_payload(self):
        self.ensure_one()
        return {
            "code": self.code,
            "name": self.name,
            "adapter_type": "opcua",
            "entry_code": self.entry_id.code if self.entry_id else None,
            "workstation_code": self.workstation_id.code if self.workstation_id else None,
            "app_code": self.app_id.code if self.app_id else None,
            "device_code": self.code,
            "endpoint_url": self.endpoint_url,
            "security_policy": self.security_policy,
            "security_mode": self.security_mode,
            "auth_mode": self.auth_mode,
            "namespace_uri": self.namespace_uri,
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
            return self._runtime_notification(_("OPC UA"), ", ".join(result.get("errors", ["Runtime action failed"])), "warning")
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
        if capability:
            values["runtime_capability_json"] = capability.get("capability_json") or json.dumps(capability, ensure_ascii=False, default=str)
            values["runtime_capability_summary"] = self._runtime_capability_summary(capability)
        if touch_field:
            values[touch_field] = fields.Datetime.now()
        self.write(values)
        return self._runtime_notification(_("OPC UA"), _("Runtime action completed"), "success")

    def action_sync_runtime_definition(self):
        service = GatewayOpcuaBridgeService(self.env)
        results = [service.register_adapter_definition(record._runtime_payload()) for record in self]
        return results[0] if len(results) == 1 else results

    def action_open_runtime_adapter(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("OPC UA"), _("No linked runtime adapter found"), "warning")
        return {
            "type": "ir.actions.act_window",
            "name": _("OPC UA Runtime"),
            "res_model": "gateway.runtime.adapter",
            "view_mode": "form",
            "res_id": runtime.id,
            "context": {"active_id": runtime.id, "active_model": "gateway.runtime.adapter"},
        }

    def action_open_runtime_diagnostics(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("OPC UA"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("OPC UA Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("OPC UA Runtime Diagnostics"),
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
            return self._runtime_notification(_("OPC UA"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("OPC UA Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("OPC UA Runtime Diagnostics"),
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
        result = GatewayOpcuaBridgeService(self.env).refresh_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_refresh_at")

    def action_repair_runtime(self):
        self.ensure_one()
        result = GatewayOpcuaBridgeService(self.env).repair_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_repair_at")

    def action_load_runtime(self):
        self.ensure_one()
        result = GatewayOpcuaBridgeService(self.env).load_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_refresh_at")

    def action_reload_runtime(self):
        self.ensure_one()
        result = GatewayOpcuaBridgeService(self.env).reload_runtime(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_reload_at")

    def action_refresh_diagnostics(self):
        self.ensure_one()
        result = GatewayOpcuaBridgeService(self.env).runtime_diagnostics(self)
        return self._write_runtime_feedback(result, touch_field="runtime_last_refresh_at")

    def action_preview_connectivity(self):
        self.ensure_one()
        service = GatewayOpcuaBridgeService(self.env)
        service.preview_connectivity(self)
        return self._action_open_diagnostics(_("OPC UA Connectivity Preview"))

    def action_preview_node_map(self):
        self.ensure_one()
        service = GatewayOpcuaBridgeService(self.env)
        service.preview_node_map(self)
        return self._action_open_diagnostics(_("OPC UA Node Map Preview"))

    def action_push_test_snapshot(self):
        self.ensure_one()
        service = GatewayOpcuaBridgeService(self.env)
        service.push_test_snapshot(self)
        return self._action_open_diagnostics(_("OPC UA Test Snapshot"))

    def _action_open_diagnostics(self, title):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "gateway.opcua.diagnostic",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id)],
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }
