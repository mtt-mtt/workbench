from odoo import fields, models


class ShopfloorException(models.Model):
    _name = "shopfloor.exception"
    _description = "Shopfloor Exception"
    _order = "id desc"

    name = fields.Char(required=True, copy=False, index=True)
    execution_id = fields.Many2one(
        "shopfloor.execution", ondelete="cascade", index=True
    )
    exception_type = fields.Selection(
        [
            ("quality", "Quality"),
            ("device", "Device"),
            ("process", "Process"),
            ("material", "Material"),
            ("custom", "Custom"),
        ],
        default="custom",
        required=True,
        index=True,
    )
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="medium",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("open", "Open"),
            ("ack", "Acknowledged"),
            ("blocked", "Blocked"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        required=True,
        index=True,
    )
    app_code = fields.Char(index=True)
    workstation_code = fields.Char(index=True)
    session_ref = fields.Char(index=True)
    gateway_entry_code = fields.Char(index=True)
    gateway_command_code = fields.Char(index=True)
    message = fields.Char(required=True)
    payload_data = fields.Text()
    details = fields.Text()
    resolution_note = fields.Text()
    raised_at = fields.Datetime(default=fields.Datetime.now, required=True)
    resolved_at = fields.Datetime()

    def _write_state(self, state, **extra_values):
        values = {"state": state}
        values.update(extra_values)
        if state in {"resolved", "closed", "cancelled"}:
            values["resolved_at"] = fields.Datetime.now()
        elif "resolved_at" in self._fields:
            values["resolved_at"] = False
        self.write(values)

    def action_ack(self):
        self._write_state("ack")

    def action_claim(self):
        self._write_state("open")

    def action_open(self):
        self._write_state("open")

    def action_escalate(self, severity=None):
        values = {}
        if severity:
            values["severity"] = severity
        self._write_state("blocked", **values)

    def action_resolve(self):
        self._write_state("resolved")

    def action_close(self):
        self._write_state("closed")

    def action_cancel(self):
        self._write_state("cancelled")

    def action_follow_up(self):
        self._write_state("new")
