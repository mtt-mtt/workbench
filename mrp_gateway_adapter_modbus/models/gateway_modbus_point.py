from odoo import api, fields, models, _

from ..services.modbus_service import GatewayModbusService


class GatewayModbusPoint(models.Model):
    _name = "gateway.modbus.point"
    _description = "Gateway Modbus Point"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("degraded", "Degraded"),
            ("offline", "Offline"),
            ("disabled", "Disabled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    adapter_id = fields.Many2one("gateway.modbus.adapter", ondelete="cascade", required=True)
    signal_id = fields.Many2one("gateway.signal", ondelete="set null")
    point_kind = fields.Selection(
        [
            ("input", "Input"),
            ("holding", "Holding Register"),
            ("coil", "Coil"),
            ("discrete", "Discrete Input"),
            ("status", "Status"),
            ("command", "Command"),
            ("alarm", "Alarm"),
        ],
        default="holding",
        required=True,
    )
    register_group = fields.Char()
    function_code = fields.Integer(default=3, required=True)
    register_address = fields.Integer(required=True)
    register_count = fields.Integer(default=1, required=True)
    data_type = fields.Selection(
        [
            ("bool", "Boolean"),
            ("int16", "Int16"),
            ("uint16", "UInt16"),
            ("int32", "Int32"),
            ("uint32", "UInt32"),
            ("float32", "Float32"),
            ("float64", "Float64"),
            ("string", "String"),
            ("raw", "Raw"),
        ],
        default="uint16",
        required=True,
    )
    bit_index = fields.Integer()
    scale_factor = fields.Float(default=1.0)
    offset = fields.Float(default=0.0)
    unit = fields.Char()
    endian = fields.Selection([("big", "Big Endian"), ("little", "Little Endian")], default="big", required=True)
    byte_order = fields.Selection([("big", "Big Endian"), ("little", "Little Endian")], default="big", required=True)
    read_only = fields.Boolean(default=True)
    writable = fields.Boolean(default=False)
    current_value_text = fields.Char()
    current_value_number = fields.Float()
    last_snapshot_at = fields.Datetime()
    note = fields.Text()

    _gateway_modbus_point_code_uniq = models.Constraint(
        "unique(code)",
        "Modbus point code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.modbus.point") or _("New")
        return super().create(vals_list)

    def _notify_action(self, title, message, level="success"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": level,
                "sticky": False,
            },
        }

    def action_preview_read_plan(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).preview_read_plan(self.adapter_id, {"point_ids": [self.id]})
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to preview point read plan"])), "warning")
        data = result["data"]
        return self._notify_action(
            _("Point Read Plan"),
            _("Point %s mapped into %s read groups") % (self.code, data.get("group_count", 0)),
        )

    def action_preview_write_plan(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).preview_write_plan(self.adapter_id, {"point_ids": [self.id]})
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to preview point write plan"])), "warning")
        data = result["data"]
        return self._notify_action(
            _("Point Write Plan"),
            _("Point %s mapped into %s write operations") % (self.code, data.get("operation_count", 0)),
        )

    def action_submit_test_snapshot(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).submit_test_snapshot(self.adapter_id, {"point_ids": [self.id]})
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to submit test snapshot"])), "warning")
        data = result.get("data", {})
        snapshot = data.get("snapshot", {})
        return self._notify_action(
            _("Test Snapshot Submitted"),
            _("Point %s snapshot replayed as %s") % (self.code, snapshot.get("code", "-")),
        )

    def action_submit_test_write_ack(self):
        self.ensure_one()
        result = GatewayModbusService(self.env).submit_test_write_ack(self.adapter_id, {"point_ids": [self.id], "limit": 1})
        if not result.get("ok"):
            return self._notify_action(_("Modbus"), ", ".join(result.get("errors", ["Unable to submit test write ack"])), "warning")
        return self._notify_action(
            _("Test Write Ack Submitted"),
            _("Point %s write acknowledgement replayed") % self.code,
        )
