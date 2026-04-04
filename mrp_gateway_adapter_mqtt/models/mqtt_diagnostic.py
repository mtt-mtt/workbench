import json

from odoo import api, fields, models, _


class GatewayMqttDiagnostic(models.Model):
    _name = "gateway.mqtt.diagnostic"
    _description = "MQTT Diagnostic"
    _order = "occurred_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    adapter_id = fields.Many2one("gateway.mqtt.adapter", required=True, ondelete="cascade", index=True)
    topic_id = fields.Many2one("gateway.mqtt.topic", ondelete="set null", index=True)
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null", readonly=True)
    direction = fields.Selection(
        [
            ("preview", "Preview"),
            ("test", "Test"),
            ("inbound", "Inbound"),
            ("outbound", "Outbound"),
        ],
        default="preview",
        required=True,
        index=True,
    )
    event_kind = fields.Selection(
        [
            ("registration", "Registration"),
            ("subscription", "Subscription"),
            ("publish", "Publish"),
            ("receive", "Receive"),
            ("heartbeat", "Heartbeat"),
            ("event", "Event"),
            ("diagnostic", "Diagnostic"),
            ("test", "Test"),
        ],
        default="diagnostic",
        required=True,
        index=True,
    )
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("simulated", "Simulated"),
            ("ok", "OK"),
            ("warn", "Warn"),
            ("error", "Error"),
            ("sent", "Sent"),
            ("received", "Received"),
        ],
        default="simulated",
        required=True,
        index=True,
    )
    topic_path = fields.Char(index=True)
    broker_url = fields.Char()
    client_id = fields.Char()
    message = fields.Text()
    payload_json = fields.Text()
    result_json = fields.Text()
    occurred_at = fields.Datetime(default=lambda self: fields.Datetime.now(), required=True)
    processed_at = fields.Datetime()
    note = fields.Text()

    _gateway_mqtt_diagnostic_code_uniq = models.Constraint(
        "unique(code)",
        "MQTT diagnostic code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.mqtt.diagnostic") or _("New")
        return super().create(vals_list)

    def write_json_payload(self, payload=None, result=None):
        self.ensure_one()
        values = {}
        if payload is not None:
            values["payload_json"] = json.dumps(payload, ensure_ascii=False, default=str)
        if result is not None:
            values["result_json"] = json.dumps(result, ensure_ascii=False, default=str)
        if values:
            self.write(values)
