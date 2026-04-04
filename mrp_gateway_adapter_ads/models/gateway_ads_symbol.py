from odoo import api, fields, models, _

from ..services.ads_client import GatewayAdsClientHelper
from ..services.ads_service import GatewayAdsService


class GatewayAdsSymbol(models.Model):
    _name = "gateway.ads.symbol"
    _description = "ADS Symbol"
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
    adapter_id = fields.Many2one("gateway.ads.adapter", required=True, ondelete="cascade", index=True)
    symbol_path = fields.Char(required=True)
    index_group = fields.Char()
    index_offset = fields.Integer(default=0)
    data_type = fields.Char()
    access_mode = fields.Selection([("read", "Read"), ("write", "Write"), ("read_write", "Read / Write")], default="read")
    writable = fields.Boolean(default=False)
    array_length = fields.Integer(default=1)
    subscription_mode = fields.Selection(
        [("change", "Change"), ("push", "Push"), ("poll", "Poll"), ("hybrid", "Hybrid")],
        default="change",
        required=True,
        index=True,
    )
    subscription_enabled = fields.Boolean(default=False)
    subscription_state = fields.Selection(
        [
            ("idle", "Idle"),
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("subscribed", "Subscribed"),
            ("paused", "Paused"),
            ("stale", "Stale"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
            ("disabled", "Disabled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    subscription_signal = fields.Char()
    subscription_handle = fields.Char()
    last_subscription_at = fields.Datetime()
    last_unsubscription_at = fields.Datetime()
    last_event_at = fields.Datetime()
    last_dispatch_at = fields.Datetime()
    update_count = fields.Integer(default=0)
    last_error = fields.Text()
    subscription_key = fields.Char(index=True)
    dispatcher_signal = fields.Char(index=True)
    notify_on_change = fields.Boolean(default=True)
    subscription_count = fields.Integer(compute="_compute_stream_stats", readonly=True)
    active_subscription_count = fields.Integer(compute="_compute_stream_stats", readonly=True)
    notification_count = fields.Integer(compute="_compute_stream_stats", readonly=True)
    open_notification_count = fields.Integer(compute="_compute_stream_stats", readonly=True)
    has_notifications = fields.Boolean(compute="_compute_stream_flags", readonly=True, store=True, index=True)
    has_open_notifications = fields.Boolean(compute="_compute_stream_flags", readonly=True, store=True, index=True)
    subscription_summary = fields.Char(compute="_compute_stream_stats", readonly=True)
    notification_summary = fields.Char(compute="_compute_stream_stats", readonly=True)
    stream_state = fields.Selection(
        [
            ("idle", "Idle"),
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("subscribed", "Subscribed"),
            ("paused", "Paused"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
        ],
        compute="_compute_stream_stats",
        readonly=True,
        index=True,
    )
    subscription_ids = fields.One2many("gateway.ads.subscription", "symbol_id", string="Subscriptions", readonly=True)
    notification_ids = fields.One2many("gateway.ads.notification", "symbol_id", string="Notifications", readonly=True)
    last_value_text = fields.Char()
    last_value_json = fields.Text()
    last_read_at = fields.Datetime()
    last_write_at = fields.Datetime()
    note = fields.Text()
    diagnostic_ids = fields.One2many("gateway.ads.diagnostic", "symbol_id", string="Diagnostics", readonly=True)

    _gateway_ads_symbol_code_uniq = models.Constraint("unique(adapter_id, code)", "ADS symbol code must be unique per adapter.")

    @api.model_create_multi
    def create(self, vals_list):
        helper = GatewayAdsClientHelper()
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.ads.symbol") or _("New")
            adapter = self.env["gateway.ads.adapter"].browse(vals.get("adapter_id")).exists() if vals.get("adapter_id") else self.env["gateway.ads.adapter"]
            vals.setdefault("writable", vals.get("access_mode") in {"write", "read_write"})
            vals.setdefault("state", "draft")
            vals.setdefault("subscription_state", "draft")
            vals.setdefault("notify_on_change", True)
            adapter_code = adapter.code if adapter else vals.get("adapter_code")
            if not vals.get("subscription_key"):
                vals["subscription_key"] = helper.build_subscription_key(
                    adapter_code=adapter_code,
                    symbol_code=vals.get("code"),
                    subscription_mode=vals.get("subscription_mode") or "change",
                )
            if not vals.get("dispatcher_signal"):
                vals["dispatcher_signal"] = helper.build_dispatch_signal(
                    adapter_code=adapter_code,
                    symbol_code=vals.get("code"),
                    event_kind="change",
                )
        return super().create(vals_list)

    def _stream_notification(self, title, result, success_message):
        if not result or not result.get("ok"):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": title,
                    "message": ", ".join(result.get("errors", ["Stream action failed"])) if result else "Stream action failed",
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": success_message,
                "type": "success",
                "sticky": False,
            },
        }

    @api.depends(
        "subscription_ids",
        "subscription_ids.state",
        "subscription_ids.active",
        "subscription_ids.last_subscribed_at",
        "subscription_ids.last_unsubscribed_at",
        "notification_ids",
        "notification_ids.state",
        "notification_ids.received_at",
        "notification_ids.dispatched_at",
    )
    def _compute_stream_stats(self):
        def latest_datetime(values):
            values = [value for value in values if value]
            return max(values) if values else False

        for record in self:
            subscriptions = record.subscription_ids
            notifications = record.notification_ids
            active_subscriptions = subscriptions.filtered(lambda item: item.active and item.state in {"requested", "subscribed"})
            open_notifications = notifications.filtered(lambda item: item.state in {"queued", "dispatched"})
            states = {item.state for item in subscriptions}
            if not subscriptions:
                stream_state = "idle"
            elif "error" in states:
                stream_state = "error"
            elif "requested" in states:
                stream_state = "requested"
            elif "subscribed" in states:
                stream_state = "subscribed"
            elif "paused" in states:
                stream_state = "paused"
            elif "cancelled" in states:
                stream_state = "cancelled"
            else:
                stream_state = "draft"
            record.stream_state = stream_state
            record.subscription_count = len(subscriptions)
            record.active_subscription_count = len(active_subscriptions)
            record.notification_count = len(notifications)
            record.open_notification_count = len(open_notifications)
            record.subscription_summary = _("%(subscriptions)s subscription(s), %(active)s active") % {
                "subscriptions": record.subscription_count,
                "active": record.active_subscription_count,
            }
            record.notification_summary = _("%(notifications)s notification(s), %(open)s open") % {
                "notifications": record.notification_count,
                "open": record.open_notification_count,
            }

    @api.depends(
        "notification_ids",
        "notification_ids.state",
        "notification_ids.received_at",
        "notification_ids.dispatched_at",
    )
    def _compute_stream_flags(self):
        for record in self:
            notifications = record.notification_ids
            record.has_notifications = bool(notifications)
            record.has_open_notifications = bool(notifications.filtered(lambda item: item.state in {"queued", "dispatched"}))

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled", "subscription_state": "disabled"})

    def action_subscribe(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).subscribe_symbol(self)
        return self._stream_notification(_("ADS Subscription"), result, _("Subscription requested"))

    def action_unsubscribe(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).unsubscribe_symbol(self)
        return self._stream_notification(_("ADS Subscription"), result, _("Subscription cancelled"))

    def action_push_test_update(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).push_symbol_notification(self)
        return self._stream_notification(_("ADS Notification"), result, _("Test notification sent"))

    def action_consume_test_callback(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).consume_device_notification(
            {
                "adapter_code": self.adapter_id.code,
                "symbol_code": self.code,
                "subscription_key": self.subscription_key,
                "event_kind": "change",
                "source": "manual",
                "value_text": self.last_value_text or self.code,
                "value_json": {"value": self.last_value_text or self.code},
                "acknowledged": True,
                "note": _("Simulated ADS device_notification callback"),
            },
            symbol=self,
        )
        return self._stream_notification(_("ADS Callback"), result, _("Callback consumed"))

    def action_open_subscriptions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Subscriptions"),
            "res_model": "gateway.ads.subscription",
            "view_mode": "list,form",
            "domain": [("symbol_id", "=", self.id)],
            "context": {"default_symbol_id": self.id, "search_default_symbol_id": self.id},
        }

    def action_open_notifications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Notifications"),
            "res_model": "gateway.ads.notification",
            "view_mode": "list,form",
            "domain": [("symbol_id", "=", self.id)],
            "context": {"default_symbol_id": self.id, "search_default_symbol_id": self.id},
        }

    def action_preview_subscription_plan(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).preview_subscription_plan(self.adapter_id)
        if not result.get("ok"):
            return self._stream_notification(_("ADS Subscription Plan"), result, _("Subscription plan preview generated"))
        summary = result.get("summary", {})
        return self._stream_notification(
            _("ADS Subscription Plan"),
            result,
            _("Symbols: %s, Subscribable: %s") % (summary.get("symbol_count", 0), summary.get("subscribable_count", 0)),
        )

    def action_refresh_subscription(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).refresh_symbol_subscription(self)
        return self._stream_notification(_("ADS Subscription"), result, _("Subscription refreshed"))
