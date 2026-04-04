from odoo import api, fields, models, _

from ..services.mqtt_bridge_service import GatewayMqttBridgeService


class GatewayMqttAdapter(models.Model):
    _name = "gateway.mqtt.adapter"
    _description = "MQTT Adapter"
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
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null", readonly=True)
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    device_code = fields.Char(index=True)
    broker_url = fields.Char(string="Broker URL")
    client_id = fields.Char(string="Client ID")
    username = fields.Char()
    password = fields.Char()
    base_topic = fields.Char(string="Base Topic")
    qos = fields.Integer(default=0)
    retain_default = fields.Boolean(default=False)
    connection_target = fields.Char()
    config_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    last_sync_at = fields.Datetime()
    note = fields.Text()
    topic_ids = fields.One2many("gateway.mqtt.topic", "adapter_id", string="Topics")
    diagnostic_ids = fields.One2many("gateway.mqtt.diagnostic", "adapter_id", string="Diagnostics", readonly=True)
    runtime_lifecycle_state = fields.Selection(related="runtime_adapter_id.lifecycle_state", readonly=True)
    runtime_health_state = fields.Selection(related="runtime_adapter_id.health_state", readonly=True)
    runtime_capability_summary = fields.Char(related="runtime_adapter_id.capability_summary", readonly=True)
    runtime_diagnostic_summary = fields.Text(related="runtime_adapter_id.diagnostic_summary", readonly=True)
    runtime_issue_count = fields.Integer(related="runtime_adapter_id.issue_count", readonly=True)
    runtime_open_issue_count = fields.Integer(related="runtime_adapter_id.open_issue_count", readonly=True)
    runtime_repair_issue_count = fields.Integer(related="runtime_adapter_id.repair_issue_count", readonly=True)

    _gateway_mqtt_adapter_code_uniq = models.Constraint(
        "unique(code)",
        "MQTT adapter code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.mqtt.adapter") or _("New")
        records = super().create(vals_list)
        return records

    def action_sync_runtime_adapter(self):
        service = GatewayMqttBridgeService(self.env)
        return service.register_adapter_from_records(self)

    def action_open_runtime_adapter(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        return {
            "type": "ir.actions.act_window",
            "name": _("MQTT Runtime"),
            "res_model": "gateway.runtime.adapter",
            "view_mode": "form",
            "res_id": runtime.id,
            "context": {"active_id": runtime.id, "active_model": "gateway.runtime.adapter"},
        }

    def action_open_runtime_console(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_console").read()[0]
        action["domain"] = [("id", "=", runtime.id)]
        action["context"] = {"search_default_needs_attention": 1}
        action["name"] = _("MQTT Runtime Console")
        return action

    def action_open_protocol_probe(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        return runtime.action_open_protocol_probe()

    def action_open_runtime_diagnostics(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("MQTT Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("MQTT Runtime Diagnostics"),
            "res_model": "gateway.runtime.event",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", runtime.id),
                ("event_kind", "in", ["diagnostic", "alarm", "command"]),
            ],
            "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
        }

    def action_open_runtime_issues(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("MQTT Runtime Issues"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("MQTT Runtime Diagnostics"),
            "res_model": "gateway.runtime.event",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", runtime.id),
                ("event_kind", "in", ["diagnostic", "alarm", "command"]),
            ],
            "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id},
        }

    def action_open_repairs(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("MQTT Runtime Repairs"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id), ("is_fixable", "=", True)],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id, "search_default_fixable": 1, "search_default_open": 1},
            }
        return self.action_open_runtime_issues()

    def action_open_repairs(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._action_notification(_("MQTT Runtime"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {
                "type": "ir.actions.act_window",
                "name": _("MQTT Runtime Repairs"),
                "res_model": "gateway.runtime.issue",
                "view_mode": "list,form",
                "domain": [("adapter_id", "=", runtime.id), ("is_fixable", "=", True), ("state", "in", ["new", "open", "in_progress"])],
                "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id, "search_default_fixable": 1, "search_default_open": 1},
            }
        return self.action_open_runtime_issues()

    def _runtime_payload(self):
        self.ensure_one()
        service = GatewayMqttBridgeService(self.env)
        result = service.build_runtime_payload(self)
        if result.get("ok"):
            return result["data"]
        return {
            "adapter_id": self.id,
            "code": self.code,
            "name": self.name,
            "adapter_type": "mqtt",
            "entry_code": self.entry_id.code if self.entry_id else None,
            "workstation_code": self.workstation_id.code if self.workstation_id else None,
            "device_code": self.device_code,
            "broker_url": self.broker_url,
            "client_id": self.client_id,
            "username": self.username,
            "password": self.password,
            "base_topic": self.base_topic,
            "qos": self.qos,
            "retain_default": self.retain_default,
            "connection_target": self.broker_url or self.connection_target,
            "config_json": self.config_json,
            "config_text": self.config_text,
        }

    def action_refresh_topics(self):
        service = GatewayMqttBridgeService(self.env)
        return service.sync_topics(self)

    def action_preview_runtime_registration(self):
        self.ensure_one()
        service = GatewayMqttBridgeService(self.env)
        service.preview_runtime_registration(self)
        return self._action_open_diagnostics(_("MQTT Runtime Preview"))

    def action_preview_subscription_plan(self):
        self.ensure_one()
        service = GatewayMqttBridgeService(self.env)
        service.preview_subscription_plan(self)
        return self._action_open_diagnostics(_("MQTT Subscription Preview"))

    def action_push_test_event(self):
        self.ensure_one()
        service = GatewayMqttBridgeService(self.env)
        topic = self._get_default_test_topic()
        service.push_test_event(self, topic_code=topic.code if topic else None)
        return self._action_open_diagnostics(_("MQTT Test Event"))

    def action_refresh_runtime(self):
        self.ensure_one()
        result = GatewayMqttBridgeService(self.env).refresh_runtime_adapter(self)
        return self._runtime_feedback(_("MQTT Runtime Refresh"), result)

    def action_repair_runtime(self):
        self.ensure_one()
        result = GatewayMqttBridgeService(self.env).repair_runtime_adapter(self)
        return self._runtime_feedback(_("MQTT Runtime Repair"), result)

    def action_load_runtime(self):
        self.ensure_one()
        result = GatewayMqttBridgeService(self.env).load_runtime_adapter(self)
        return self._runtime_feedback(_("MQTT Runtime Load"), result)

    def action_reload_runtime(self):
        self.ensure_one()
        result = GatewayMqttBridgeService(self.env).reload_runtime_adapter(self)
        return self._runtime_feedback(_("MQTT Runtime Reload"), result)

    def _get_default_test_topic(self):
        self.ensure_one()
        ordered = self.topic_ids.sorted(lambda record: (record.sequence, record.id))
        preferred = ordered.filtered(lambda record: record.topic_kind in {"event", "heartbeat", "status"})
        if preferred:
            return preferred[0]
        return ordered[0] if ordered else self.env["gateway.mqtt.topic"]

    def _runtime_feedback(self, title, result):
        if not result.get("ok"):
            return self._action_notification(title, ", ".join(result.get("errors", ["Runtime action failed"])), "warning")
        message = result.get("message", {}).get("text") or title
        return self._action_notification(title, message, "success")

    def _action_notification(self, title, message, level="success"):
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

    def _action_open_diagnostics(self, title, extra_domain=None):
        self.ensure_one()
        domain = [("adapter_id", "=", self.id)]
        if extra_domain:
            domain.extend(extra_domain)
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "gateway.mqtt.diagnostic",
            "view_mode": "list,form",
            "domain": domain,
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }
