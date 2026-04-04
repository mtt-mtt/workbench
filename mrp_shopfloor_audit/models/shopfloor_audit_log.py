from odoo import api, fields, models


class ShopfloorAuditLog(models.Model):
    _name = "shopfloor.audit.log"
    _description = "Shopfloor Audit Log"
    _order = "event_at desc, id desc"

    name = fields.Char(required=True, copy=False, index=True)
    event_type = fields.Selection(
        [
            ("business", "Business"),
            ("device", "Device"),
            ("system", "System"),
            ("security", "Security"),
            ("exception", "Exception"),
        ],
        required=True,
        default="business",
        index=True,
    )
    event_code = fields.Char(required=True, index=True)
    severity = fields.Selection(
        [
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ],
        required=True,
        default="info",
        index=True,
    )
    workstation_code = fields.Char(index=True)
    session_ref = fields.Char(index=True)
    execution_ref = fields.Char(index=True)
    execution_id = fields.Integer(index=True)
    gateway_command_ref = fields.Char(index=True)
    actor = fields.Char(index=True)
    actor_user_id = fields.Many2one("res.users", string="Actor User", ondelete="set null")
    payload = fields.Text()
    result = fields.Text()
    message = fields.Char()
    note = fields.Text()
    event_at = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    processed_at = fields.Datetime()
    active = fields.Boolean(default=True)

    _name_uniq = models.Constraint(
        "unique (name)",
        "Audit log name must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") in (None, "/", "New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "shopfloor.audit.log"
                ) or "New"
        return super().create(vals_list)

    @api.model
    def _log_values(self, **kwargs):
        return {
            "name": kwargs.get("name") or "/",
            "event_type": kwargs.get("event_type", "business"),
            "event_code": kwargs.get("event_code", "unknown"),
            "severity": kwargs.get("severity", "info"),
            "workstation_code": kwargs.get("workstation_code"),
            "session_ref": kwargs.get("session_ref"),
            "execution_ref": kwargs.get("execution_ref"),
            "execution_id": kwargs.get("execution_id"),
            "gateway_command_ref": kwargs.get("gateway_command_ref"),
            "actor": kwargs.get("actor") or self.env.user.name,
            "actor_user_id": kwargs.get("actor_user_id") or self.env.user.id,
            "payload": kwargs.get("payload"),
            "result": kwargs.get("result"),
            "message": kwargs.get("message"),
            "note": kwargs.get("note"),
            "event_at": kwargs.get("event_at") or fields.Datetime.now(),
            "processed_at": kwargs.get("processed_at"),
            "active": kwargs.get("active", True),
        }

    @api.model
    def log_business_action(self, event_code, **kwargs):
        values = self._log_values(
            event_type="business",
            event_code=event_code,
            **kwargs,
        )
        return self.create(values)

    @api.model
    def log_device_command(self, event_code, **kwargs):
        values = self._log_values(
            event_type="device",
            event_code=event_code,
            severity=kwargs.pop("severity", "info"),
            **kwargs,
        )
        return self.create(values)

    @api.model
    def log_exception(self, event_code, **kwargs):
        values = self._log_values(
            event_type="exception",
            event_code=event_code,
            severity=kwargs.pop("severity", "warning"),
            **kwargs,
        )
        return self.create(values)
