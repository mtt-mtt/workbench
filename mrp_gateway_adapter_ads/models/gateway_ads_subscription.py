from odoo import api, fields, models, _

from ..services.ads_client import GatewayAdsClientHelper
from ..services.ads_service import GatewayAdsService


class GatewayAdsSubscription(models.Model):
    _name = "gateway.ads.subscription"
    _description = "ADS Subscription"
    _order = "last_notified_at desc, priority, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.ads.adapter", required=True, ondelete="cascade", index=True)
    symbol_id = fields.Many2one("gateway.ads.symbol", required=True, ondelete="cascade", index=True)
    subscription_key = fields.Char(required=True, index=True)
    dispatcher_signal = fields.Char(index=True)
    subscription_mode = fields.Selection(
        [("change", "Change"), ("push", "Push"), ("poll", "Poll"), ("hybrid", "Hybrid")],
        default="change",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("requested", "Requested"),
            ("subscribed", "Subscribed"),
            ("paused", "Paused"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    priority = fields.Integer(default=10)
    notify_on_change = fields.Boolean(default=True)
    listener_count = fields.Integer(default=0)
    last_subscribed_at = fields.Datetime()
    last_unsubscribed_at = fields.Datetime()
    last_notified_at = fields.Datetime()
    last_error_at = fields.Datetime()
    last_error = fields.Text()
    payload_json = fields.Text()
    note = fields.Text()
    notification_ids = fields.One2many("gateway.ads.notification", "subscription_id", string="Notifications", readonly=True)

    _gateway_ads_subscription_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "ADS subscription code must be unique.",
    )
    _gateway_ads_subscription_key_uniq = models.Constraint(
        "UNIQUE(subscription_key)",
        "ADS subscription key must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        helper = GatewayAdsClientHelper()
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.ads.subscription") or _("New")
            adapter = self.env["gateway.ads.adapter"].browse(vals.get("adapter_id")).exists() if vals.get("adapter_id") else self.env["gateway.ads.adapter"]
            symbol = self.env["gateway.ads.symbol"].browse(vals.get("symbol_id")).exists() if vals.get("symbol_id") else self.env["gateway.ads.symbol"]
            adapter_code = adapter.code if adapter else vals.get("adapter_code")
            symbol_code = symbol.code if symbol else vals.get("symbol_code")
            subscription_mode = vals.get("subscription_mode") or "change"
            vals.setdefault("subscription_mode", subscription_mode)
            vals.setdefault("state", "draft")
            vals.setdefault("active", True)
            vals.setdefault("priority", 10)
            vals.setdefault("notify_on_change", True)
            vals.setdefault("listener_count", 0)
            if not vals.get("subscription_key"):
                vals["subscription_key"] = helper.build_subscription_key(
                    adapter_code=adapter_code,
                    symbol_code=symbol_code or vals.get("code"),
                    subscription_mode=subscription_mode,
                )
            if not vals.get("dispatcher_signal"):
                vals["dispatcher_signal"] = helper.build_dispatch_signal(
                    adapter_code=adapter_code,
                    symbol_code=symbol_code or vals.get("code"),
                    event_kind="subscription",
                )
        return super().create(vals_list)

    def _set_state(self, state, *, note=None):
        values = {"state": state}
        now = fields.Datetime.now()
        if state == "subscribed":
            values["last_subscribed_at"] = now
        if state in {"paused", "cancelled"}:
            values["last_unsubscribed_at"] = now
        if state == "error":
            values["last_error_at"] = now
            if note is not None:
                values["last_error"] = note
        if note is not None:
            values["note"] = note
        self.write(values)
        return True

    def _feedback(self, title, result, success_message):
        if not result or not result.get("ok"):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": title,
                    "message": ", ".join(result.get("errors", ["Subscription action failed"])) if result else "Subscription action failed",
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

    def action_mark_requested(self):
        self._set_state("requested")

    def action_mark_subscribed(self):
        self._set_state("subscribed")

    def action_mark_paused(self):
        self._set_state("paused")

    def action_mark_error(self):
        self._set_state("error")

    def action_mark_cancelled(self):
        self._set_state("cancelled")

    def action_open_symbol(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Symbol"),
            "res_model": "gateway.ads.symbol",
            "view_mode": "form",
            "res_id": self.symbol_id.id,
            "target": "current",
        }

    def action_open_adapter(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Adapter"),
            "res_model": "gateway.ads.adapter",
            "view_mode": "form",
            "res_id": self.adapter_id.id,
            "target": "current",
        }

    def action_open_notifications(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Notifications"),
            "res_model": "gateway.ads.notification",
            "view_mode": "list,form",
            "domain": [("subscription_id", "=", self.id)],
            "context": {"default_subscription_id": self.id, "search_default_subscription_id": self.id},
        }

    def action_publish_notification(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).push_symbol_notification(self.symbol_id, extra={"source": "subscription", "event_kind": "dispatch"})
        return self._feedback(_("ADS Subscription"), result, _("Subscription notification published"))
