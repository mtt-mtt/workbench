from odoo import api, fields, models, _

from ..services.ads_service import GatewayAdsService


class GatewayAdsNotification(models.Model):
    _name = "gateway.ads.notification"
    _description = "ADS Notification"
    _order = "received_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.ads.adapter", required=True, ondelete="cascade", index=True)
    symbol_id = fields.Many2one("gateway.ads.symbol", required=True, ondelete="cascade", index=True)
    subscription_id = fields.Many2one("gateway.ads.subscription", ondelete="set null", index=True)
    event_kind = fields.Selection(
        [
            ("subscribe", "Subscribe"),
            ("unsubscribe", "Unsubscribe"),
            ("change", "Change"),
            ("update", "Update"),
            ("read", "Read"),
            ("write", "Write"),
            ("snapshot", "Snapshot"),
            ("heartbeat", "Heartbeat"),
            ("dispatch", "Dispatch"),
            ("error", "Error"),
            ("diagnostic", "Diagnostic"),
        ],
        default="update",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("queued", "Queued"),
            ("dispatched", "Dispatched"),
            ("acknowledged", "Acknowledged"),
            ("failed", "Failed"),
            ("dropped", "Dropped"),
        ],
        default="queued",
        required=True,
        index=True,
    )
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="low",
        required=True,
        index=True,
    )
    source = fields.Selection(
        [("runtime", "Runtime"), ("service", "Service"), ("client", "Client"), ("manual", "Manual"), ("subscription", "Subscription")],
        default="manual",
        required=True,
        index=True,
    )
    payload_json = fields.Text()
    value_text = fields.Char()
    value_json = fields.Text()
    result_json = fields.Text()
    received_at = fields.Datetime(default=fields.Datetime.now, required=True)
    dispatched_at = fields.Datetime()
    acknowledged_at = fields.Datetime()
    note = fields.Text()

    _gateway_ads_notification_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "ADS notification code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.ads.notification") or _("New")
            vals.setdefault("state", "queued")
            vals.setdefault("event_kind", "update")
            vals.setdefault("severity", "low")
            vals.setdefault("source", "manual")
            vals.setdefault("received_at", fields.Datetime.now())
            if not vals.get("name"):
                symbol_id = vals.get("symbol_id")
                symbol = self.env["gateway.ads.symbol"].browse(symbol_id).exists() if symbol_id else self.env["gateway.ads.symbol"]
                symbol_code = symbol.code if symbol else vals.get("code")
                vals["name"] = f"{symbol_code}:{vals.get('event_kind', 'update')}"
        return super().create(vals_list)

    def _set_state(self, state, *, note=None):
        values = {"state": state}
        now = fields.Datetime.now()
        if state == "dispatched":
            values["dispatched_at"] = now
        if state == "acknowledged":
            values["acknowledged_at"] = now
            values["dispatched_at"] = values.get("dispatched_at") or now
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
                    "message": ", ".join(result.get("errors", ["Notification action failed"])) if result else "Notification action failed",
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

    def action_mark_dispatched(self):
        self._set_state("dispatched")

    def action_mark_acknowledged(self):
        self.ensure_one()
        result = GatewayAdsService(self.env).acknowledge_notification(self)
        return self._feedback(_("ADS Notification"), result, _("Notification acknowledged"))

    def action_mark_failed(self):
        self._set_state("failed")

    def action_mark_dropped(self):
        self._set_state("dropped")

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

    def action_open_subscription(self):
        self.ensure_one()
        if not self.subscription_id:
            return self.action_open_symbol()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Subscription"),
            "res_model": "gateway.ads.subscription",
            "view_mode": "form",
            "res_id": self.subscription_id.id,
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
