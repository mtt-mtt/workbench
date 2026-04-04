from odoo import fields, models


class GatewayOpcuaDiagnostic(models.Model):
    _name = "gateway.opcua.diagnostic"
    _description = "OPC UA Diagnostic"
    _order = "observed_at desc, id desc"

    name = fields.Char(required=True)
    adapter_id = fields.Many2one("gateway.opcua.adapter", required=True, ondelete="cascade")
    node_id = fields.Many2one("gateway.opcua.node", ondelete="set null")
    kind = fields.Selection(
        [
            ("connect", "Connect"),
            ("browse", "Browse"),
            ("read", "Read"),
            ("write", "Write"),
            ("snapshot", "Snapshot"),
            ("heartbeat", "Heartbeat"),
        ],
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
