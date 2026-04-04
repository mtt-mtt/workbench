import json

from odoo import api, fields, models, _


class GatewayAdsDiagnostic(models.Model):
    _name = "gateway.ads.diagnostic"
    _description = "ADS Diagnostic"
    _order = "observed_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.ads.adapter", required=True, ondelete="cascade", index=True)
    symbol_id = fields.Many2one("gateway.ads.symbol", ondelete="set null", index=True)
    subscription_id = fields.Many2one("gateway.ads.subscription", ondelete="set null", index=True)
    notification_id = fields.Many2one("gateway.ads.notification", ondelete="set null", index=True)
    kind = fields.Selection(
        [("connect", "Connect"), ("browse", "Browse"), ("read", "Read"), ("write", "Write"), ("snapshot", "Snapshot"), ("diagnostic", "Diagnostic"), ("repair", "Repair"), ("reload", "Reload"), ("load", "Load"), ("unload", "Unload")],
        default="diagnostic",
        required=True,
        index=True,
    )
    state = fields.Selection([("info", "Info"), ("success", "Success"), ("warning", "Warning"), ("error", "Error")], default="info", required=True, index=True)
    message = fields.Char(required=True)
    detail = fields.Text()
    payload_json = fields.Text()
    result_json = fields.Text()
    observed_at = fields.Datetime(default=fields.Datetime.now, required=True)
    note = fields.Text()

    _gateway_ads_diagnostic_code_uniq = models.Constraint("UNIQUE(code)", "ADS diagnostic code must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.ads.diagnostic") or _("New")
            vals.setdefault("kind", "diagnostic")
            vals.setdefault("state", "info")
            vals.setdefault("observed_at", fields.Datetime.now())
        return super().create(vals_list)

    def _payload_summary(self):
        self.ensure_one()
        if not self.payload_json:
            return {}
        try:
            parsed = json.loads(self.payload_json)
            return parsed if isinstance(parsed, dict) else {"payload": parsed}
        except Exception:
            return {"payload": self.payload_json}

    def action_open_adapter(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "name": _("ADS Adapter"), "res_model": "gateway.ads.adapter", "view_mode": "form", "res_id": self.adapter_id.id, "target": "current"}

    def action_open_symbol(self):
        self.ensure_one()
        if not self.symbol_id:
            return self.action_open_adapter()
        return {"type": "ir.actions.act_window", "name": _("ADS Symbol"), "res_model": "gateway.ads.symbol", "view_mode": "form", "res_id": self.symbol_id.id, "target": "current"}

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

    def action_open_notification(self):
        self.ensure_one()
        if not self.notification_id:
            return self.action_open_subscription()
        return {
            "type": "ir.actions.act_window",
            "name": _("ADS Notification"),
            "res_model": "gateway.ads.notification",
            "view_mode": "form",
            "res_id": self.notification_id.id,
            "target": "current",
        }
