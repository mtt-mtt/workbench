from odoo import fields, models


class GatewayS7WriteAck(models.Model):
    _name = "gateway.s7.write.ack"
    _description = "S7 Write Ack"
    _order = "sent_at desc, id desc"

    name = fields.Char(required=True)
    adapter_id = fields.Many2one("gateway.s7.adapter", required=True, ondelete="cascade")
    tag_id = fields.Many2one("gateway.s7.tag", ondelete="set null")
    state = fields.Selection(
        [("queued", "Queued"), ("sent", "Sent"), ("acknowledged", "Acknowledged"), ("done", "Done"), ("failed", "Failed")],
        default="queued",
        required=True,
        index=True,
    )
    ack_code = fields.Char()
    command_code = fields.Char()
    requested_value = fields.Char()
    acked_value = fields.Char()
    sent_at = fields.Datetime(default=fields.Datetime.now, required=True)
    acked_at = fields.Datetime()
    note = fields.Text()
