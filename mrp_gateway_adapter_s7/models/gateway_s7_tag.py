from odoo import api, fields, models, _


class GatewayS7Tag(models.Model):
    _name = "gateway.s7.tag"
    _description = "S7 Tag"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    adapter_id = fields.Many2one("gateway.s7.adapter", required=True, ondelete="cascade")
    db_number = fields.Integer(default=1)
    address = fields.Integer(default=0)
    bit_offset = fields.Integer(default=0)
    byte_length = fields.Integer(default=1)
    data_type = fields.Selection(
        [("bool", "Bool"), ("int", "Int"), ("dint", "DInt"), ("real", "Real"), ("string", "String"), ("json", "JSON")],
        default="bool",
        required=True,
    )
    access_mode = fields.Selection([("read", "Read"), ("write", "Write"), ("read_write", "Read / Write")], default="read", required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("ready", "Ready"), ("degraded", "Degraded"), ("offline", "Offline"), ("disabled", "Disabled")],
        default="draft",
        required=True,
        index=True,
    )
    last_value = fields.Char()
    last_status = fields.Char()
    note = fields.Text()

    _gateway_s7_tag_code_uniq = models.Constraint("unique(code)", "S7 tag code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.s7.tag") or _("New")
            vals.setdefault("state", "draft")
        return super().create(vals_list)

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled"})
