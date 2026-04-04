from odoo import fields, models


class ShopfloorApp(models.Model):
    _name = "shopfloor.app"
    _description = "Shopfloor App"
    _order = "sequence, name, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()

    profile_ids = fields.One2many("shopfloor.profile", "app_id", string="Profiles")
    menu_ids = fields.One2many("shopfloor.menu", "app_id", string="Menus")
    scenario_ids = fields.One2many("shopfloor.scenario", "app_id", string="Scenarios")
    workstation_ids = fields.One2many("shopfloor.workstation", "app_id", string="Workstations")
    session_ids = fields.One2many("shopfloor.session", "app_id", string="Sessions")

    _code_uniq = models.Constraint(
        "unique (code)",
        "The app code must be unique.",
    )
