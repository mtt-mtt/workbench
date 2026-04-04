from odoo import api, fields, models, _


class ShopfloorExecution(models.Model):
    _name = "shopfloor.execution"
    _description = "Shopfloor Execution"
    _order = "id desc"

    name = fields.Char(default="/", required=True, copy=False, index=True)
    reference = fields.Char(index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("running", "Running"),
            ("paused", "Paused"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    action_type = fields.Selection(
        [
            ("boot", "Boot"),
            ("start", "Start"),
            ("pause", "Pause"),
            ("resume", "Resume"),
            ("finish", "Finish"),
            ("fail", "Fail"),
            ("custom", "Custom"),
        ],
        default="custom",
        required=True,
        index=True,
    )
    app_code = fields.Char(index=True)
    workstation_code = fields.Char(index=True)
    session_ref = fields.Char(index=True)
    gateway_entry_code = fields.Char(index=True)
    production_id = fields.Many2one("mrp.production", ondelete="set null", index=True)
    workorder_id = fields.Many2one("mrp.workorder", ondelete="set null", index=True)
    command_key = fields.Char(index=True)
    gateway_command_code = fields.Char(index=True)
    exception_code = fields.Char(index=True)
    idempotency_key = fields.Char(index=True)
    payload_data = fields.Text()
    response_data = fields.Text()
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") in (None, "/", "New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "shopfloor.execution"
                ) or _("New")
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_running(self):
        self.write({"state": "running"})

    def action_mark_paused(self):
        self.write({"state": "paused"})

    def action_mark_done(self):
        self.write({"state": "done"})

    def action_mark_failed(self):
        self.write({"state": "failed"})

    def action_mark_cancelled(self):
        self.write({"state": "cancelled"})
