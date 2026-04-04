from odoo import _, fields, models
from odoo.exceptions import UserError


class ShopfloorWorkstation(models.Model):
    _name = "shopfloor.workstation"
    _description = "Shopfloor Workstation"
    _order = "sequence, name, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    app_id = fields.Many2one("shopfloor.app", required=True, ondelete="cascade")
    profile_id = fields.Many2one("shopfloor.profile", ondelete="set null")
    terminal_uid = fields.Char()
    default_printer_ref = fields.Char()
    gateway_ref = fields.Char()
    location_ref = fields.Char()
    note = fields.Text()

    current_session_id = fields.Many2one(
        "shopfloor.session",
        string="Current Session",
        readonly=True,
        ondelete="set null",
    )
    session_ids = fields.One2many("shopfloor.session", "workstation_id", string="Sessions")

    _code_uniq = models.Constraint(
        "unique (code)",
        "The workstation code must be unique.",
    )

    def _demo_code_prefix(self):
        self.ensure_one()
        value = (self.code or self.name or "shopfloor").upper()
        sanitized = "".join(character for character in value if character.isalnum())
        return sanitized[:12] or "SHOPFLOOR"

    def _get_demo_calendar(self):
        calendar = self.env.company.resource_calendar_id
        if not calendar:
            calendar = self.env.ref("resource.resource_calendar_std", raise_if_not_found=False)
        if not calendar:
            calendar = self.env["resource.calendar"].search([], limit=1)
        if not calendar:
            raise UserError(_("No resource calendar is available for the demo workcenter."))
        return calendar

    def _get_demo_picking_type(self):
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "mrp_operation"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )
        if not picking_type:
            picking_type = self.env["stock.picking.type"].search(
                [("code", "=", "mrp_operation")],
                limit=1,
            )
        if not picking_type:
            raise UserError(_("No manufacturing operation type was found for the demo manufacturing order."))
        return picking_type

    def _ensure_demo_workcenter(self):
        self.ensure_one()
        code = f"SFWC-{self._demo_code_prefix()}"
        workcenter = self.env["mrp.workcenter"].search([("code", "=", code)], limit=1)
        if workcenter:
            return workcenter
        return self.env["mrp.workcenter"].create(
            {
                "name": f"Shopfloor Demo {self.code}",
                "code": code,
                "sequence": 90,
                "resource_calendar_id": self._get_demo_calendar().id,
                "costs_hour": 12.0,
                "time_start": 5.0,
                "time_stop": 5.0,
            }
        )

    def _ensure_demo_product(self):
        self.ensure_one()
        default_code = f"SFP-{self._demo_code_prefix()}"
        product = self.env["product.product"].search([("default_code", "=", default_code)], limit=1)
        if product:
            return product
        unit = self.env.ref("uom.product_uom_unit", raise_if_not_found=False) or self.env["uom.uom"].search([], limit=1)
        template = self.env["product.template"].create(
            {
                "name": f"Shopfloor Demo Product {self.code}",
                "default_code": default_code,
                "type": "consu",
                "uom_id": unit.id,
                "sale_ok": False,
                "purchase_ok": False,
            }
        )
        return template.product_variant_id

    def _ensure_demo_bom(self, product, workcenter):
        self.ensure_one()
        prefix = self._demo_code_prefix()
        bom_code = f"SFBOM-{prefix}"
        bom = self.env["mrp.bom"].search([("code", "=", bom_code)], limit=1)
        if not bom:
            bom = self.env["mrp.bom"].create(
                {
                    "code": bom_code,
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "product_id": product.id,
                    "product_qty": 1.0,
                    "product_uom_id": product.uom_id.id,
                    "type": "normal",
                    "ready_to_produce": "asap",
                    "consumption": "flexible",
                    "picking_type_id": self._get_demo_picking_type().id,
                }
            )
        operation_name = f"Demo Operation {self.code}"
        operation = self.env["mrp.routing.workcenter"].search(
            [("bom_id", "=", bom.id), ("name", "=", operation_name)],
            limit=1,
        )
        if not operation:
            self.env["mrp.routing.workcenter"].create(
                {
                    "name": operation_name,
                    "bom_id": bom.id,
                    "workcenter_id": workcenter.id,
                    "sequence": 100,
                    "time_mode": "manual",
                    "time_cycle_manual": 15.0,
                    "cost_mode": "estimated",
                }
            )
        return bom

    def action_generate_demo_workorder(self):
        action = None
        for workstation in self:
            workcenter = workstation._ensure_demo_workcenter()
            product = workstation._ensure_demo_product()
            bom = workstation._ensure_demo_bom(product, workcenter)
            origin = f"Shopfloor Demo {workstation.code}"
            open_workorders = self.env["mrp.workorder"].search(
                [
                    ("workcenter_id", "=", workcenter.id),
                    ("production_id.origin", "=", origin),
                    ("state", "in", ["ready", "progress", "blocked"]),
                ],
                order="id desc",
            )
            if open_workorders:
                workorders = open_workorders
            else:
                production = self.env["mrp.production"].create(
                    {
                        "product_id": product.id,
                        "product_qty": 5.0,
                        "product_uom_id": product.uom_id.id,
                        "bom_id": bom.id,
                        "picking_type_id": bom.picking_type_id.id or workstation._get_demo_picking_type().id,
                        "origin": origin,
                    }
                )
                production.action_confirm()
                if not production.workorder_ids:
                    raise UserError(_("The demo manufacturing order was created but no workorder was generated."))
                workorders = production.workorder_ids
            if workstation.current_session_id:
                workstation.current_session_id._touch()
            action = {
                "type": "ir.actions.act_window",
                "name": _("Demo Workorders"),
                "res_model": "mrp.workorder",
                "view_mode": "list,form",
                "domain": [("id", "in", workorders.ids)],
                "context": {
                    "search_default_group_by_workcenter_id": workcenter.id,
                },
            }
        return action
