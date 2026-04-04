from odoo import api, fields, models, _


class GatewayOpcuaNode(models.Model):
    _name = "gateway.opcua.node"
    _description = "OPC UA Node"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    adapter_id = fields.Many2one("gateway.opcua.adapter", required=True, ondelete="cascade")
    node_id = fields.Char(required=True)
    namespace_index = fields.Integer(default=0)
    browse_path = fields.Char()
    node_class = fields.Selection(
        [("variable", "Variable"), ("object", "Object"), ("method", "Method"), ("folder", "Folder"), ("reference", "Reference")],
        default="variable",
        required=True,
    )
    data_type = fields.Selection(
        [("string", "String"), ("boolean", "Boolean"), ("integer", "Integer"), ("float", "Float"), ("json", "JSON")],
        default="string",
        required=True,
    )
    access_mode = fields.Selection([("read", "Read"), ("write", "Write"), ("read_write", "Read / Write")], default="read", required=True)
    sampling_interval = fields.Integer(default=1000)
    value_rank = fields.Integer(default=-1)
    scale_factor = fields.Float(default=1.0)
    unit = fields.Char()
    state = fields.Selection(
        [("draft", "Draft"), ("ready", "Ready"), ("degraded", "Degraded"), ("offline", "Offline"), ("disabled", "Disabled")],
        default="draft",
        required=True,
        index=True,
    )
    last_value = fields.Char()
    last_status = fields.Char()
    last_seen_at = fields.Datetime()
    diagnostic_state = fields.Text()
    note = fields.Text()

    _gateway_opcua_node_code_uniq = models.Constraint(
        "unique(code)",
        "OPC UA node code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.opcua.node") or _("New")
            vals.setdefault("state", "draft")
        return super().create(vals_list)

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled"})
