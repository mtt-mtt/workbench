from odoo import fields, models


class ShopfloorScenario(models.Model):
    _name = "shopfloor.scenario"
    _description = "Shopfloor Scenario"
    _order = "sequence, name, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    app_id = fields.Many2one("shopfloor.app", required=True, ondelete="cascade")
    profile_id = fields.Many2one("shopfloor.profile", ondelete="set null")
    menu_id = fields.Many2one("shopfloor.menu", ondelete="set null")
    technical_name = fields.Char()
    description = fields.Text()

    _code_uniq = models.Constraint(
        "unique (code)",
        "The scenario code must be unique.",
    )
