from odoo import api, fields, models, _


class GatewayModbusWriteAck(models.Model):
    _name = "gateway.modbus.write.ack"
    _description = "Gateway Modbus Write Ack"
    _order = "ack_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.modbus.adapter", ondelete="cascade", required=True)
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null")
    point_id = fields.Many2one("gateway.modbus.point", ondelete="set null")
    command_id = fields.Many2one("gateway.command", ondelete="set null")
    ack_kind = fields.Selection(
        [
            ("write", "Write"),
            ("readback", "Readback"),
            ("command", "Command"),
            ("manual", "Manual"),
            ("error", "Error"),
        ],
        default="write",
        required=True,
        index=True,
    )
    result_state = fields.Selection(
        [
            ("done", "Done"),
            ("failed", "Failed"),
            ("acknowledged", "Acknowledged"),
            ("pending", "Pending"),
        ],
        default="acknowledged",
        required=True,
        index=True,
    )
    register_address = fields.Integer()
    register_count = fields.Integer(default=1)
    write_value_text = fields.Char()
    payload_json = fields.Text()
    normalized_json = fields.Text()
    response_text = fields.Text()
    error_message = fields.Text()
    latency_ms = fields.Integer()
    ack_at = fields.Datetime(default=fields.Datetime.now, required=True)
    processed_at = fields.Datetime()
    note = fields.Text()

    _gateway_modbus_write_ack_code_uniq = models.Constraint(
        "unique(code)",
        "Modbus write ack code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.modbus.write.ack") or _("New")
        return super().create(vals_list)
