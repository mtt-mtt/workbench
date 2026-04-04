from odoo import fields, models


class GatewaySignal(models.Model):
    _name = "gateway.signal"
    _description = "Gateway Signal"
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
    entry_id = fields.Many2one("gateway.entry", string="Gateway Entry", ondelete="cascade", required=True)
    device_id = fields.Many2one("gateway.device", string="Gateway Device", ondelete="cascade")
    signal_kind = fields.Selection(
        [
            ("input", "Input"),
            ("output", "Output"),
            ("status", "Status"),
            ("counter", "Counter"),
            ("alarm", "Alarm"),
            ("command", "Command"),
        ],
        default="status",
        required=True,
    )
    technical_key = fields.Char(string="Technical Key")
    unit = fields.Char(string="Unit")
    value_text = fields.Char(string="Value Text")
    value_number = fields.Float(string="Value Number")
    config_json = fields.Text(string="Config JSON")
    config_text = fields.Text(string="Config Text")
    last_seen_at = fields.Datetime(string="Last Seen At")

    _gateway_signal_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Gateway signal code must be unique.",
    )
