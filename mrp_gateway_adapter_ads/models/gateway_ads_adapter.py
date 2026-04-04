import json

from odoo import api, fields, models, _

from ..services.ads_service import GatewayAdsService


class GatewayAdsAdapter(models.Model):
    _name = "gateway.ads.adapter"
    _description = "ADS Adapter"
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
    adapter_type = fields.Selection([("ads", "ADS")], default="ads", required=True, index=True)
    runtime_adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null", readonly=True)
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    device_code = fields.Char(index=True)
    host = fields.Char()
    port = fields.Integer(default=48898)
    ams_net_id = fields.Char(string="AMS Net ID")
    ads_port = fields.Integer(default=851)
    connection_target = fields.Char()
    poll_interval_seconds = fields.Integer(default=5)
    timeout_seconds = fields.Integer(default=3)
    retry_limit = fields.Integer(default=3)
    config_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    runtime_capability_json = fields.Text(readonly=True)
    runtime_capability_summary = fields.Char(readonly=True)
    runtime_diagnostic_summary = fields.Text(readonly=True)
    runtime_last_refresh_at = fields.Datetime(readonly=True)
    runtime_last_repair_at = fields.Datetime(readonly=True)
    runtime_last_reload_at = fields.Datetime(readonly=True)
    runtime_lifecycle_state = fields.Selection(related="runtime_adapter_id.lifecycle_state", readonly=True)
    runtime_health_state = fields.Selection(related="runtime_adapter_id.health_state", readonly=True)
    runtime_issue_count = fields.Integer(related="runtime_adapter_id.issue_count", readonly=True)
    runtime_open_issue_count = fields.Integer(related="runtime_adapter_id.open_issue_count", readonly=True)
    runtime_repair_issue_count = fields.Integer(related="runtime_adapter_id.repair_issue_count", readonly=True)
    last_sync_at = fields.Datetime()
    last_connect_at = fields.Datetime()
    symbol_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    diagnostic_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    subscribed_symbol_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    subscription_error_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    subscription_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    active_subscription_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    notification_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    open_notification_count = fields.Integer(compute="_compute_symbol_stats", readonly=True)
    has_notifications = fields.Boolean(compute="_compute_notification_flags", readonly=True, store=True, index=True)
    has_open_notifications = fields.Boolean(compute="_compute_notification_flags", readonly=True, store=True, index=True)
    subscription_summary = fields.Char(compute="_compute_symbol_stats", readonly=True)
    notification_summary = fields.Char(compute="_compute_symbol_stats", readonly=True)
    note = fields.Text()
    symbol_ids = fields.One2many("gateway.ads.symbol", "adapter_id", string="Symbols")
    subscription_ids = fields.One2many("gateway.ads.subscription", "adapter_id", string="Subscriptions")
    notification_ids = fields.One2many("gateway.ads.notification", "adapter_id", string="Notifications")
    diagnostic_ids = fields.One2many("gateway.ads.diagnostic", "adapter_id", string="Diagnostics", readonly=True)

    _gateway_ads_adapter_code_uniq = models.Constraint("unique(code)", "ADS adapter code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.ads.adapter") or _("New")
            vals.setdefault("adapter_type", "ads")
        records = super().create(vals_list)
        for record in records:
            if not record.connection_target:
                record.connection_target = record._build_connection_target()
        return records

    def write(self, vals):
        result = super().write(vals)
        if {"host", "port", "ams_net_id", "ads_port"} & set(vals):
            for record in self:
                if not record.connection_target or vals.get("host") or vals.get("port") or vals.get("ams_net_id") or vals.get("ads_port"):
                    record.connection_target = record._build_connection_target()
        return result

    @api.depends(
        "symbol_ids",
        "symbol_ids.subscription_state",
        "subscription_ids",
        "subscription_ids.state",
        "notification_ids",
        "notification_ids.state",
        "diagnostic_ids",
    )
    def _compute_symbol_stats(self):
        for record in self:
            record.symbol_count = len(record.symbol_ids)
            record.diagnostic_count = len(record.diagnostic_ids)
            record.subscribed_symbol_count = len(record.symbol_ids.filtered(lambda symbol: symbol.subscription_state == "subscribed"))
            record.subscription_error_count = len(record.symbol_ids.filtered(lambda symbol: symbol.subscription_state == "error"))
            record.subscription_count = len(record.subscription_ids)
            record.active_subscription_count = len(record.subscription_ids.filtered(lambda item: item.active and item.state in {"requested", "subscribed"}))
            record.notification_count = len(record.notification_ids)
            record.open_notification_count = len(record.notification_ids.filtered(lambda item: item.state in {"queued", "dispatched"}))
            record.subscription_summary = _(
                "%(subscriptions)s subscription(s), %(active)s active"
            ) % {
                "subscriptions": record.subscription_count,
                "active": record.active_subscription_count,
            }
            record.notification_summary = _(
                "%(notifications)s notification(s), %(open)s open"
            ) % {
                "notifications": record.notification_count,
                "open": record.open_notification_count,
            }

    @api.depends("notification_ids", "notification_ids.state")
    def _compute_notification_flags(self):
        for record in self:
            record.has_notifications = bool(record.notification_ids)
            record.has_open_notifications = bool(record.notification_ids.filtered(lambda item: item.state in {"queued", "dispatched"}))

    def _build_connection_target(self):
        self.ensure_one()
        host = self.host or "127.0.0.1"
        port = self.port or 48898
        ads_port = self.ads_port or 851
        if self.ams_net_id:
            return f"ads://{self.ams_net_id}@{host}:{port}/port/{ads_port}"
        return f"ads://{host}:{port}/port/{ads_port}"

    def _runtime_payload(self):
        self.ensure_one()
        return {
            "code": self.code,
            "name": self.name,
            "adapter_type": "ads",
            "entry_code": self.entry_id.code if self.entry_id else None,
            "workstation_code": self.workstation_id.code if self.workstation_id else None,
            "app_code": self.app_id.code if self.app_id else None,
            "device_code": self.device_code or self.code,
            "host": self.host,
            "port": self.port,
            "ams_net_id": self.ams_net_id,
            "ads_port": self.ads_port,
            "connection_target": self.connection_target or self._build_connection_target(),
            "poll_interval_seconds": self.poll_interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "retry_limit": self.retry_limit,
            "config_json": self.config_json,
            "config_text": self.config_text,
        }

    def _runtime_notification(self, title, message, level="success"):
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {"title": title, "message": message, "type": level, "sticky": False}}

    def _runtime_capability_summary(self, capability):
        supports = capability.get("supports") or {}
        labels = []
        for key, label in (
            ("poll", "poll"),
            ("push", "push"),
            ("read", "read"),
            ("write", "write"),
            ("subscribe", "subscribe"),
            ("diagnostic", "diagnostics"),
            ("repair", "repair"),
            ("reload", "reload"),
            ("load", "load"),
            ("unload", "unload"),
            ("dispatch", "dispatch"),
        ):
            if supports.get(key):
                labels.append(label)
        base = capability.get("adapter_type") or capability.get("transport") or "runtime"
        return f"{base}: {', '.join(labels)}" if labels else base

    def _write_runtime_feedback(self, result, touch_field=None):
        self.ensure_one()
        if not result or not result.get("ok"):
            return self._runtime_notification(_("ADS"), ", ".join(result.get("errors", ["Runtime action failed"])), "warning")
        data = result.get("data") or {}
        capability = data.get("capability") or {}
        coordinator = data.get("coordinator") or {}
        values = {
            "diagnostic_state": json.dumps(result, ensure_ascii=False, default=str),
            "runtime_diagnostic_summary": json.dumps({"capability": capability, "coordinator": coordinator, "signal": data.get("signal")}, ensure_ascii=False, default=str),
        }
        runtime_adapter = data.get("adapter") or {}
        if runtime_adapter:
            values["runtime_adapter_id"] = runtime_adapter.get("id") if isinstance(runtime_adapter, dict) else False
        if capability:
            values["runtime_capability_json"] = capability.get("capability_json") or json.dumps(capability, ensure_ascii=False, default=str)
            values["runtime_capability_summary"] = self._runtime_capability_summary(capability)
        if touch_field:
            values[touch_field] = fields.Datetime.now()
        self.write(values)
        return self._runtime_notification(_("ADS"), _("Runtime action completed"), "success")

    def action_sync_runtime_definition(self):
        results = [GatewayAdsService(self.env).register_adapter_definition(record._runtime_payload()) for record in self]
        return results[0] if len(results) == 1 else results

    def action_open_runtime_adapter(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("ADS"), _("No linked runtime adapter found"), "warning")
        return {"type": "ir.actions.act_window", "name": _("ADS Runtime"), "res_model": "gateway.runtime.adapter", "view_mode": "form", "res_id": runtime.id, "context": {"active_id": runtime.id, "active_model": "gateway.runtime.adapter"}}

    def action_open_runtime_console(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("ADS"), _("No linked runtime adapter found"), "warning")
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_console").read()[0]
        action["domain"] = [("id", "=", runtime.id)]
        action["context"] = {"search_default_needs_attention": 1}
        action["name"] = _("ADS Runtime Console")
        return action

    def action_open_protocol_probe(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("ADS"), _("No linked runtime adapter found"), "warning")
        return runtime.action_open_protocol_probe()

    def action_open_runtime_issues(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("ADS"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {"type": "ir.actions.act_window", "name": _("ADS Runtime Issues"), "res_model": "gateway.runtime.issue", "view_mode": "list,form", "domain": [("adapter_id", "=", runtime.id)], "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id}}
        return {"type": "ir.actions.act_window", "name": _("ADS Runtime Diagnostics"), "res_model": "gateway.runtime.event", "view_mode": "list,form", "domain": [("adapter_id", "=", runtime.id), ("event_kind", "in", ["diagnostic", "alarm", "command"])], "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id}}

    def action_open_runtime_diagnostics(self):
        return self.action_open_runtime_issues()

    def action_open_repairs(self):
        self.ensure_one()
        runtime = self.runtime_adapter_id
        if not runtime:
            return self._runtime_notification(_("ADS"), _("No linked runtime adapter found"), "warning")
        if "gateway.runtime.issue" in self.env.registry.models:
            return {"type": "ir.actions.act_window", "name": _("ADS Runtime Repairs"), "res_model": "gateway.runtime.issue", "view_mode": "list,form", "domain": [("adapter_id", "=", runtime.id), ("is_fixable", "=", True)], "context": {"default_adapter_id": runtime.id, "search_default_adapter_id": runtime.id, "search_default_fixable": 1, "search_default_open": 1}}
        return self.action_open_runtime_issues()

    def action_open_subscriptions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Subscriptions"),
            "res_model": "gateway.ads.subscription",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id)],
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }

    def action_open_notifications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Notifications"),
            "res_model": "gateway.ads.notification",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id)],
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }

    def action_preview_connectivity(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).preview_connectivity(self)
        return self._runtime_notification(_("ADS Connectivity Preview"), _("Connectivity preview generated"), "success" if result.get("ok") else "warning")

    def action_preview_symbol_map(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).preview_symbol_map(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS"), ", ".join(result.get("errors", ["Unable to preview symbol map"])), "warning")
        summary = result.get("summary", {})
        return self._runtime_notification(_("ADS Symbol Map"), _("Symbols: %s, Readable: %s, Writable: %s") % (summary.get("symbol_count", 0), summary.get("readable_count", 0), summary.get("writable_count", 0)), "success")

    def action_preview_subscription_plan(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).preview_subscription_plan(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS"), ", ".join(result.get("errors", ["Unable to preview subscription plan"])), "warning")
        summary = result.get("summary", {})
        return self._runtime_notification(_("ADS Subscription Plan"), _("Symbols: %s, Subscribable: %s") % (summary.get("symbol_count", 0), summary.get("subscribable_count", 0)), "success")

    def action_subscribe_symbols(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).subscribe_adapter_symbols(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS Subscriptions"), ", ".join(result.get("errors", ["Unable to subscribe symbols"])), "warning")
        return self._runtime_notification(_("ADS Subscriptions"), _("Subscriptions requested for %s symbol(s)") % len(result.get("results", [])), "success")

    def action_unsubscribe_symbols(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).unsubscribe_adapter_symbols(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS Subscriptions"), ", ".join(result.get("errors", ["Unable to unsubscribe symbols"])), "warning")
        return self._runtime_notification(_("ADS Subscriptions"), _("Subscriptions cancelled for %s symbol(s)") % len(result.get("results", [])), "success")

    def action_push_test_notification(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).push_test_notification(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS Notifications"), ", ".join(result.get("errors", ["Unable to send notification"])), "warning")
        return self._runtime_notification(_("ADS Notifications"), _("Test callback consumed"), "success")

    def action_submit_test_read(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).submit_test_read(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS"), ", ".join(result.get("errors", ["Unable to submit test read"])), "warning")
        symbol = result.get("symbol") or {}
        return self._runtime_notification(_("ADS Test Read"), _("Read recorded for %s") % (symbol.get("code") or "-"), "success")

    def action_submit_test_write(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).submit_test_write(self)
        if not result.get("ok"):
            return self._runtime_notification(_("ADS"), ", ".join(result.get("errors", ["Unable to submit test write"])), "warning")
        symbol = result.get("symbol") or {}
        return self._runtime_notification(_("ADS Test Write"), _("Write recorded for %s") % (symbol.get("code") or "-"), "success")

    def action_refresh_runtime(self):
        self.ensure_one()
        return self._write_runtime_feedback(GatewayAdsService(self.env).refresh_runtime(self), touch_field="last_sync_at")

    def action_repair_runtime(self):
        self.ensure_one()
        return self._write_runtime_feedback(GatewayAdsService(self.env).repair_runtime(self), touch_field="runtime_last_repair_at")

    def action_load_runtime(self):
        self.ensure_one()
        return self._write_runtime_feedback(GatewayAdsService(self.env).load_runtime(self), touch_field="last_sync_at")

    def action_reload_runtime(self):
        self.ensure_one()
        return self._write_runtime_feedback(GatewayAdsService(self.env).reload_runtime(self), touch_field="runtime_last_reload_at")

    def action_refresh_diagnostics(self):
        self.ensure_one()
        return self._write_runtime_feedback(GatewayAdsService(self.env).runtime_diagnostics(self), touch_field="last_sync_at")
