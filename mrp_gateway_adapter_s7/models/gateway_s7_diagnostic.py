from odoo import fields, models


class GatewayS7Diagnostic(models.Model):
    _name = "gateway.s7.diagnostic"
    _description = "S7 Diagnostic"
    _order = "observed_at desc, id desc"

    name = fields.Char(required=True)
    adapter_id = fields.Many2one("gateway.s7.adapter", required=True, ondelete="cascade")
    tag_id = fields.Many2one("gateway.s7.tag", ondelete="set null")
    kind = fields.Selection(
        [("connect", "Connect"), ("read", "Read"), ("write", "Write"), ("snapshot", "Snapshot"), ("heartbeat", "Heartbeat")],
        default="connect",
        required=True,
    )
    state = fields.Selection([("info", "Info"), ("success", "Success"), ("warning", "Warning"), ("danger", "Danger")], default="info", required=True)
    message = fields.Char(required=True)
    detail = fields.Text()
    payload_json = fields.Text()
    result_json = fields.Text()
    observed_at = fields.Datetime(default=fields.Datetime.now, required=True)
    note = fields.Text()
