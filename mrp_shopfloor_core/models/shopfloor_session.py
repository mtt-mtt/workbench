from odoo import fields, models


class ShopfloorSession(models.Model):
    _name = "shopfloor.session"
    _description = "Shopfloor Session"
    _order = "start_date desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
    )

    app_id = fields.Many2one("shopfloor.app", required=True, ondelete="cascade")
    profile_id = fields.Many2one("shopfloor.profile", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    user_id = fields.Many2one("res.users", ondelete="set null")
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    last_action_at = fields.Datetime()
    note = fields.Text()

    _code_uniq = models.Constraint(
        "unique (code)",
        "The session code must be unique.",
    )

    def _touch(self):
        self.write({"last_action_at": fields.Datetime.now()})

    def action_start(self):
        now = fields.Datetime.now()
        for session in self:
            values = {
                "state": "active",
                "active": True,
                "start_date": session.start_date or now,
                "last_action_at": now,
            }
            session.write(values)
            if session.workstation_id and session.workstation_id.current_session_id != session:
                session.workstation_id.write({"current_session_id": session.id})
        return True

    def action_close(self):
        now = fields.Datetime.now()
        for session in self:
            session.write(
                {
                    "state": "closed",
                    "end_date": now,
                    "last_action_at": now,
                }
            )
            if session.workstation_id and session.workstation_id.current_session_id == session:
                session.workstation_id.write({"current_session_id": False})
        return True

    def action_cancel(self):
        now = fields.Datetime.now()
        for session in self:
            session.write(
                {
                    "state": "cancelled",
                    "end_date": now,
                    "last_action_at": now,
                }
            )
            if session.workstation_id and session.workstation_id.current_session_id == session:
                session.workstation_id.write({"current_session_id": False})
        return True
