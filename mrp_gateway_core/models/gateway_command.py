from odoo import fields, models


class GatewayCommand(models.Model):
    _name = "gateway.command"
    _description = "Gateway Command"
    _order = "create_date desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("sent", "Sent"),
            ("acknowledged", "Acknowledged"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    entry_id = fields.Many2one("gateway.entry", string="Gateway Entry", ondelete="cascade", required=True)
    device_id = fields.Many2one("gateway.device", string="Gateway Device", ondelete="set null")
    signal_id = fields.Many2one("gateway.signal", string="Gateway Signal", ondelete="set null")
    workstation_ref = fields.Char(string="Workstation Ref")
    app_ref = fields.Char(string="App Ref")
    command_type = fields.Char(string="Command Type")
    idempotency_key = fields.Char(string="Idempotency Key", index=True)
    payload_json = fields.Text(string="Payload JSON")
    request_text = fields.Text(string="Request Text")
    response_text = fields.Text(string="Response Text")
    error_message = fields.Text(string="Error Message")
    attempt_count = fields.Integer(string="Attempt Count", default=0)
    last_attempt_at = fields.Datetime(string="Last Attempt At")
    processed_at = fields.Datetime(string="Processed At")
    diagnostic_state = fields.Text(string="Diagnostic State")

    _gateway_command_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Gateway command code must be unique.",
    )
