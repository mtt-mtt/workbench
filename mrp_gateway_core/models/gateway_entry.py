from odoo import fields, models


class GatewayEntry(models.Model):
    _name = "gateway.entry"
    _description = "Gateway Entry"
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
    entry_type = fields.Char(string="Entry Type")
    workstation_ref = fields.Char(string="Workstation Ref")
    app_ref = fields.Char(string="App Ref")
    connection_target = fields.Char(string="Connection Target")
    config_json = fields.Text(string="Config JSON")
    config_text = fields.Text(string="Config Text")
    diagnostic_state = fields.Text(string="Diagnostic State")
    last_seen_at = fields.Datetime(string="Last Seen At")
    device_ids = fields.One2many("gateway.device", "entry_id", string="Devices")
    signal_ids = fields.One2many("gateway.signal", "entry_id", string="Signals")
    command_ids = fields.One2many("gateway.command", "entry_id", string="Commands")

    _gateway_entry_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Gateway entry code must be unique.",
    )
