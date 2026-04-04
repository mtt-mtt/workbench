import secrets
import uuid

from odoo import api, fields, models, _

from ..services.bridge_service import GatewayHttpBridgeService


class GatewayHttpBridge(models.Model):
    _name = "gateway.http.bridge"
    _description = "Gateway HTTP Bridge"
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
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", string="Runtime Adapter", ondelete="set null")
    runtime_adapter_code = fields.Char(index=True)
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    bridge_key = fields.Char(index=True)
    secret_token = fields.Char(index=True)
    endpoint_base_url = fields.Char()
    auth_mode = fields.Selection(
        [
            ("token", "Token"),
            ("header", "Header"),
            ("none", "None"),
        ],
        default="token",
        required=True,
    )
    config_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    last_request_at = fields.Datetime()
    push_count = fields.Integer(default=0)
    heartbeat_count = fields.Integer(default=0)
    event_count = fields.Integer(default=0)
    note = fields.Text()
    endpoint_ids = fields.One2many("gateway.http.endpoint", "bridge_id", string="Endpoints")

    _gateway_http_bridge_code_uniq = models.Constraint(
        "unique(code)",
        "HTTP bridge code must be unique.",
    )
    _gateway_http_bridge_key_uniq = models.Constraint(
        "unique(bridge_key)",
        "HTTP bridge key must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.http.bridge") or _("New")
            if not vals.get("runtime_adapter_code"):
                vals["runtime_adapter_code"] = f"HTTP-{vals['code']}"
            if not vals.get("bridge_key"):
                vals["bridge_key"] = uuid.uuid4().hex
            if not vals.get("secret_token"):
                vals["secret_token"] = secrets.token_urlsafe(24)
        records = super().create(vals_list)
        records.action_sync_runtime_adapter()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(key in vals for key in {"name", "code", "active", "entry_id", "app_id", "workstation_id", "endpoint_base_url", "config_json", "config_text", "runtime_adapter_code"}):
            self.action_sync_runtime_adapter()
        return result

    def action_sync_runtime_adapter(self):
        service = GatewayHttpBridgeService(self.env)
        return service.sync_bridges(self)

    def action_regenerate_secret(self):
        for bridge in self:
            bridge.write({"secret_token": secrets.token_urlsafe(24)})
        return True

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled"})
