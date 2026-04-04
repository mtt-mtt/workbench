from odoo import api, fields, models, _


class GatewayRuntimeEvent(models.Model):
    _name = "gateway.runtime.event"
    _description = "Gateway Runtime Event"
    _order = "occurred_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null")
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    device_id = fields.Many2one("gateway.device", ondelete="set null")
    command_id = fields.Many2one("gateway.command", ondelete="set null")
    event_kind = fields.Selection(
        [
            ("heartbeat", "Heartbeat"),
            ("status", "Status"),
            ("signal", "Signal"),
            ("command", "Command"),
            ("diagnostic", "Diagnostic"),
            ("alarm", "Alarm"),
            ("custom", "Custom"),
        ],
        default="custom",
        required=True,
        index=True,
    )
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="medium",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("processing", "Processing"),
            ("processed", "Processed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        required=True,
        index=True,
    )
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    session_ref = fields.Char(index=True)
    change_kind = fields.Selection(
        [
            ("identity", "Identity"),
            ("topology", "Topology"),
            ("state", "State"),
            ("probe", "Probe"),
        ],
        default="state",
        required=True,
        index=True,
    )
    discovery_state = fields.Selection(
        [
            ("discovered", "Discovered"),
            ("bound", "Bound"),
            ("enriched", "Enriched"),
            ("ready", "Ready"),
            ("removed", "Removed"),
        ],
        default="bound",
        required=True,
        index=True,
    )
    source_signal = fields.Char(index=True)
    source_payload_id = fields.Char(index=True)
    probe_session_id = fields.Char(index=True)
    state_version = fields.Char(index=True)
    registry_action = fields.Char()
    ui_refresh_hint = fields.Char()
    payload_json = fields.Text()
    normalized_json = fields.Text()
    message = fields.Char()
    result = fields.Char()
    occurred_at = fields.Datetime(default=fields.Datetime.now, required=True)
    processed_at = fields.Datetime()
    note = fields.Text()

    _gateway_runtime_event_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Event code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.runtime.event") or _("New")
        return super().create(vals_list)
