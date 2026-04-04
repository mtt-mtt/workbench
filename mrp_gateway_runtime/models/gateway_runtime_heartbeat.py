from odoo import api, fields, models, _


class GatewayRuntimeHeartbeat(models.Model):
    _name = "gateway.runtime.heartbeat"
    _description = "Gateway Runtime Heartbeat"
    _order = "received_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null")
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    device_id = fields.Many2one("gateway.device", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    status = fields.Selection(
        [
            ("ok", "OK"),
            ("warn", "Warn"),
            ("error", "Error"),
            ("offline", "Offline"),
        ],
        default="ok",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("processed", "Processed"),
            ("ignored", "Ignored"),
            ("failed", "Failed"),
        ],
        default="new",
        required=True,
        index=True,
    )
    payload_json = fields.Text()
    normalized_json = fields.Text()
    message = fields.Char()
    latency_ms = fields.Integer()
    received_at = fields.Datetime(default=fields.Datetime.now, required=True)
    processed_at = fields.Datetime()
    note = fields.Text()

    _gateway_runtime_heartbeat_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Heartbeat code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.runtime.heartbeat") or _("New")
        return super().create(vals_list)
