from odoo import api, fields, models, _


class GatewayModbusSnapshot(models.Model):
    _name = "gateway.modbus.snapshot"
    _description = "Gateway Modbus Snapshot"
    _order = "received_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.modbus.adapter", ondelete="cascade", required=True)
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null")
    point_id = fields.Many2one("gateway.modbus.point", ondelete="set null")
    command_id = fields.Many2one("gateway.command", ondelete="set null")
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    device_id = fields.Many2one("gateway.device", ondelete="set null")
    snapshot_kind = fields.Selection(
        [
            ("register_snapshot", "Register Snapshot"),
            ("poll", "Poll"),
            ("write_ack", "Write Ack"),
            ("manual", "Manual"),
            ("replay", "Replay"),
            ("error", "Error"),
        ],
        default="register_snapshot",
        required=True,
        index=True,
    )
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
    latency_ms = fields.Integer()
    payload_json = fields.Text()
    normalized_json = fields.Text()
    point_values_json = fields.Text()
    message = fields.Char()
    received_at = fields.Datetime(default=fields.Datetime.now, required=True)
    processed_at = fields.Datetime()
    note = fields.Text()

    _gateway_modbus_snapshot_code_uniq = models.Constraint(
        "unique(code)",
        "Modbus snapshot code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.modbus.snapshot") or _("New")
        return super().create(vals_list)
