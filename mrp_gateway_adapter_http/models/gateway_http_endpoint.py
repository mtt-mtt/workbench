from odoo import api, fields, models, _

from ..services.bridge_service import GatewayHttpBridgeService


class GatewayHttpEndpoint(models.Model):
    _name = "gateway.http.endpoint"
    _description = "Gateway HTTP Endpoint"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("disabled", "Disabled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    bridge_id = fields.Many2one("gateway.http.bridge", required=True, ondelete="cascade")
    route_kind = fields.Selection(
        [
            ("push", "Push"),
            ("heartbeat", "Heartbeat"),
            ("webhook", "Webhook"),
        ],
        default="push",
        required=True,
        index=True,
    )
    path = fields.Char(required=True, index=True)
    http_method = fields.Selection(
        [("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH")],
        default="POST",
        required=True,
    )
    auth_mode = fields.Selection(
        [
            ("token", "Token"),
            ("header", "Header"),
            ("none", "None"),
        ],
        default="token",
        required=True,
    )
    header_name = fields.Char(default="X-HTTP-Bridge-Key")
    mapping_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    last_seen_at = fields.Datetime()
    request_count = fields.Integer(default=0)
    success_count = fields.Integer(default=0)
    failure_count = fields.Integer(default=0)
    note = fields.Text()

    _gateway_http_endpoint_code_uniq = models.Constraint(
        "unique(code)",
        "HTTP endpoint code must be unique.",
    )
    _gateway_http_endpoint_path_uniq = models.Constraint(
        "unique(path)",
        "HTTP endpoint path must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.http.endpoint") or _("New")
        return super().create(vals_list)

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled"})

    def action_sync_runtime_adapter(self):
        service = GatewayHttpBridgeService(self.env)
        return service.sync_bridges(self.bridge_id)
