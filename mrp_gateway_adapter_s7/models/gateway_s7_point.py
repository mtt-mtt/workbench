from odoo import api, fields, models, _

from ..services.s7_service import GatewayS7Service


class GatewayS7Point(models.Model):
    _name = "gateway.s7.point"
    _description = "Gateway S7 Point"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        [("draft", "Draft"), ("ready", "Ready"), ("degraded", "Degraded"), ("offline", "Offline"), ("disabled", "Disabled")],
        default="draft",
        required=True,
        index=True,
    )
    adapter_id = fields.Many2one("gateway.s7.adapter", ondelete="cascade", required=True)
    tag_id = fields.Many2one("gateway.s7.tag", ondelete="set null")
    signal_id = fields.Many2one("gateway.signal", ondelete="set null")
    db_number = fields.Integer(default=1, required=True)
    byte_offset = fields.Integer(default=0, required=True)
    bit_index = fields.Integer()
    data_type = fields.Selection(
        [("bool", "Boolean"), ("int16", "Int16"), ("uint16", "UInt16"), ("int32", "Int32"), ("uint32", "UInt32"), ("real", "Real"), ("string", "String"), ("raw", "Raw")],
        default="bool",
        required=True,
    )
    writable = fields.Boolean(default=False)
    read_only = fields.Boolean(default=True)
    current_value_text = fields.Char()
    current_value_number = fields.Float()
    last_snapshot_at = fields.Datetime()
    note = fields.Text()

    _gateway_s7_point_code_uniq = models.Constraint("unique(code)", "S7 point code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.s7.point") or _("New")
        return super().create(vals_list)

    def _notify_action(self, title, message, level="success"):
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {"title": title, "message": message, "type": level, "sticky": False}}

    def action_preview_read_plan(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).preview_read_plan(self.adapter_id)
        if not result.get("ok"):
            return self._notify_action(_("S7"), ", ".join(result.get("errors", ["Unable to preview point read plan"])), "warning")
        data = result["data"]
        return self._notify_action(_("Point Read Plan"), _("Point %s grouped into %s batch(es)") % (self.code, data.get("group_count", 0)))

    def action_preview_write_plan(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).preview_write_plan(self.adapter_id)
        if not result.get("ok"):
            return self._notify_action(_("S7"), ", ".join(result.get("errors", ["Unable to preview point write plan"])), "warning")
        data = result["data"]
        return self._notify_action(_("Point Write Plan"), _("Point %s marked in %s write operation(s)") % (self.code, data.get("operation_count", 0)))

    def action_submit_test_snapshot(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).submit_test_snapshot(self.adapter_id, {"point_ids": [self.id]})
        if not result.get("ok"):
            return self._notify_action(_("S7"), ", ".join(result.get("errors", ["Unable to submit test snapshot"])), "warning")
        snapshot = result.get("data", {}).get("snapshot", {})
        return self._notify_action(_("Test Snapshot Submitted"), _("Point %s snapshot replayed as %s") % (self.code, snapshot.get("code", "-")))

    def action_submit_test_write_ack(self):
        self.ensure_one()
        result = GatewayS7Service(self.env).submit_test_write_ack(self.adapter_id, {"point_ids": [self.id], "limit": 1})
        if not result.get("ok"):
            return self._notify_action(_("S7"), ", ".join(result.get("errors", ["Unable to submit test write ack"])), "warning")
        ack = result.get("data", {}).get("ack", {})
        return self._notify_action(_("Test Write Ack Submitted"), _("Point %s ack replayed as %s") % (self.code, ack.get("code", "-")))
