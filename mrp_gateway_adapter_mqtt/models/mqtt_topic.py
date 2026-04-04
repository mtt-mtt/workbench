from odoo import api, fields, models, _

from ..services.mqtt_bridge_service import GatewayMqttBridgeService


class GatewayMqttTopic(models.Model):
    _name = "gateway.mqtt.topic"
    _description = "MQTT Topic"
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
    adapter_id = fields.Many2one("gateway.mqtt.adapter", required=True, ondelete="cascade")
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null", readonly=True)
    topic_name = fields.Char(required=True, index=True)
    topic_kind = fields.Selection(
        [
            ("event", "Event"),
            ("heartbeat", "Heartbeat"),
            ("status", "Status"),
            ("command", "Command"),
            ("diagnostic", "Diagnostic"),
        ],
        default="event",
        required=True,
        index=True,
    )
    event_kind = fields.Selection(
        [
            ("custom", "Custom"),
            ("status", "Status"),
            ("heartbeat", "Heartbeat"),
            ("diagnostic", "Diagnostic"),
            ("alarm", "Alarm"),
        ],
        default="custom",
        required=True,
    )
    default_status = fields.Selection(
        [
            ("ok", "OK"),
            ("warn", "Warn"),
            ("error", "Error"),
            ("offline", "Offline"),
        ],
        default="ok",
        required=True,
    )
    payload_format = fields.Selection(
        [("json", "JSON"), ("text", "Text"), ("raw", "Raw")],
        default="json",
        required=True,
    )
    qos = fields.Integer(default=0)
    retain = fields.Boolean(default=False)
    message_hint = fields.Char()
    last_payload_text = fields.Text()
    last_normalized_json = fields.Text()
    last_seen_at = fields.Datetime()
    note = fields.Text()
    diagnostic_ids = fields.One2many("gateway.mqtt.diagnostic", "topic_id", string="Diagnostics", readonly=True)

    _gateway_mqtt_topic_code_uniq = models.Constraint(
        "unique(code)",
        "MQTT topic code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.mqtt.topic") or _("New")
        return super().create(vals_list)

    def action_push_test_event(self):
        self.ensure_one()
        service = GatewayMqttBridgeService(self.env)
        service.push_test_event(self.adapter_id, topic_code=self.code)
        return self.adapter_id._action_open_diagnostics(_("MQTT Test Event"), [("topic_id", "=", self.id)])
