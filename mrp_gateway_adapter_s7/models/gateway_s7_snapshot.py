from odoo import fields, models


class GatewayS7Snapshot(models.Model):
    _name = "gateway.s7.snapshot"
    _description = "S7 Snapshot"
    _order = "collected_at desc, id desc"

    name = fields.Char(required=True)
    adapter_id = fields.Many2one("gateway.s7.adapter", required=True, ondelete="cascade")
    code = fields.Char(required=True, index=True)
    state = fields.Selection(
        [("draft", "Draft"), ("success", "Success"), ("warning", "Warning"), ("danger", "Danger")],
        default="draft",
        required=True,
    )
    collected_at = fields.Datetime(default=fields.Datetime.now, required=True)
    payload_json = fields.Text()
    result_json = fields.Text()
    note = fields.Text()
