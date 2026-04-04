from odoo import fields, models


class ShopfloorProfile(models.Model):
    _name = "shopfloor.profile"
    _description = "Shopfloor Profile"
    _order = "sequence, name, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    app_id = fields.Many2one("shopfloor.app", required=True, ondelete="cascade")
    description = fields.Text()

    menu_ids = fields.One2many("shopfloor.menu", "profile_id", string="Menus")
    scenario_ids = fields.One2many("shopfloor.scenario", "profile_id", string="Scenarios")
    workstation_ids = fields.One2many("shopfloor.workstation", "profile_id", string="Workstations")

    _code_uniq = models.Constraint(
        "unique (code)",
        "The profile code must be unique.",
    )
