import json

from odoo import api, fields, models, _


class GatewayRuntimeIssue(models.Model):
    _name = "gateway.runtime.issue"
    _description = "Gateway Runtime Issue"
    _order = "last_seen_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(string="Issue Code", required=True, index=True)
    issue_key = fields.Char(string="Issue Key", index=True)
    active = fields.Boolean(default=True)
    adapter_id = fields.Many2one("gateway.runtime.adapter", required=True, ondelete="cascade", index=True)
    adapter_code = fields.Char(string="Adapter Code", related="adapter_id.code", readonly=True, store=True)
    adapter_type = fields.Selection(related="adapter_id.adapter_type", readonly=True, store=True)
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="medium",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
            ("ignored", "Ignored"),
        ],
        default="new",
        required=True,
        index=True,
    )
    issue_kind = fields.Selection(
        [
            ("diagnostic", "Diagnostic"),
            ("repair", "Repair"),
            ("connectivity", "Connectivity"),
            ("configuration", "Configuration"),
            ("discovery", "Discovery"),
            ("health", "Health"),
            ("cleanup", "Cleanup"),
            ("custom", "Custom"),
        ],
        default="diagnostic",
        required=True,
        index=True,
    )
    is_fixable = fields.Boolean(default=False, index=True)
    recommended_action_key = fields.Selection(
        [
            ("review_runtime", "Review Runtime"),
            ("review_runtime_events", "Review Runtime Events"),
            ("refresh_runtime", "Refresh Runtime"),
            ("repair_runtime", "Repair Runtime"),
            ("reload_runtime", "Reload Runtime"),
            ("request_edge_replay", "Request Edge Replay"),
            ("review_edge_dead_letter", "Review Edge Dead Letter"),
            ("load_runtime", "Load Runtime"),
            ("unload_runtime", "Unload Runtime"),
            ("configure_adapter", "Configure Adapter"),
        ],
        default="review_runtime",
        required=True,
        index=True,
    )
    message = fields.Char(required=True)
    detail = fields.Text()
    recommended_action = fields.Text()
    last_seen_at = fields.Datetime(default=fields.Datetime.now, required=True)
    resolved_at = fields.Datetime()
    payload_json = fields.Text()
    repair_summary = fields.Char(compute="_compute_issue_summaries", readonly=True)
    payload_summary = fields.Char(compute="_compute_issue_summaries", readonly=True)
    note = fields.Text()

    _gateway_runtime_issue_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Issue code must be unique.",
    )
    _gateway_runtime_issue_key_uniq = models.Constraint(
        "UNIQUE(issue_key)",
        "Issue registry key must be unique.",
    )

    @api.model
    def _fixable_action_keys(self):
        return {
            "refresh_runtime",
            "repair_runtime",
            "reload_runtime",
            "request_edge_replay",
            "review_edge_dead_letter",
            "load_runtime",
            "unload_runtime",
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.runtime.issue") or _("New")
            adapter = self.env["gateway.runtime.adapter"].browse(vals.get("adapter_id")).exists() if vals.get("adapter_id") else self.env["gateway.runtime.adapter"]
            vals.setdefault("state", "new")
            vals.setdefault("severity", "medium")
            vals.setdefault("issue_kind", "diagnostic")
            vals.setdefault("recommended_action_key", "review_runtime")
            if not vals.get("issue_key") and adapter:
                issue_kind = vals.get("issue_kind") or "diagnostic"
                vals["issue_key"] = f"runtime:{adapter.code}:{issue_kind}"
            vals.setdefault("is_fixable", vals.get("recommended_action_key") in self._fixable_action_keys())
            vals.setdefault("last_seen_at", fields.Datetime.now())
        return super().create(vals_list)

    def _set_state(self, state, *, note=None):
        values = {"state": state}
        if state in {"resolved", "closed"}:
            values["resolved_at"] = fields.Datetime.now()
        else:
            values["resolved_at"] = False
        if note is not None:
            values["note"] = note
        self.write(values)
        return True

    @api.depends(
        "adapter_id",
        "adapter_code",
        "adapter_type",
        "severity",
        "state",
        "is_fixable",
        "recommended_action_key",
        "recommended_action",
        "message",
        "payload_json",
    )
    def _compute_issue_summaries(self):
        def _compact(value, limit=160):
            if value in (None, False, ""):
                return ""
            if not isinstance(value, str):
                try:
                    value = json.dumps(value, ensure_ascii=False, default=str)
                except Exception:
                    value = str(value)
            value = " ".join(value.split())
            if len(value) <= limit:
                return value
            return value[: max(0, limit - 1)].rstrip() + "..."

        severity_labels = dict(self._fields["severity"].selection)
        state_labels = dict(self._fields["state"].selection)
        action_labels = dict(self._fields["recommended_action_key"].selection)

        for record in self:
            action_key = record.recommended_action_key or "review_runtime"
            record.repair_summary = _("%(severity)s / %(state)s / %(action)s") % {
                "severity": severity_labels.get(record.severity, record.severity or _("Medium")),
                "state": state_labels.get(record.state, record.state or _("New")),
                "action": action_labels.get(action_key, action_key),
            }
            payload = record._payload_summary()
            adapter_payload = payload.get("adapter") if isinstance(payload, dict) else {}
            protocol_payload = payload.get("protocol_runtime") if isinstance(payload, dict) else {}
            if isinstance(adapter_payload, dict) and adapter_payload:
                protocol_text = ""
                if isinstance(protocol_payload, dict) and protocol_payload:
                    protocol_text = protocol_payload.get("summary") or protocol_payload.get("state") or ""
                record.payload_summary = _compact(
                    _("%(code)s %(adapter_type)s %(health)s %(runtime)s%(protocol)s") % {
                        "code": adapter_payload.get("code") or record.adapter_code or _("adapter"),
                        "adapter_type": adapter_payload.get("adapter_type") or record.adapter_type or _("runtime"),
                        "health": adapter_payload.get("health_state") or _("unknown"),
                        "runtime": adapter_payload.get("state") or _("state"),
                        "protocol": _(" protocol %(value)s") % {"value": protocol_text} if protocol_text else "",
                    }
                )
            elif isinstance(payload, dict) and payload:
                record.payload_summary = _compact(", ".join(sorted(payload.keys())))
            else:
                record.payload_summary = _compact(record.message or _("No payload summary"))

    def action_mark_open(self):
        self._set_state("open")

    def action_mark_in_progress(self):
        self._set_state("in_progress")

    def action_mark_resolved(self):
        self._set_state("resolved")

    def action_mark_closed(self):
        self._set_state("closed")

    def action_mark_ignored(self):
        self._set_state("ignored")

    def action_reopen(self):
        self._set_state("open")

    def action_run_recommended_action(self):
        self.ensure_one()
        action_key = self.recommended_action_key or "review_runtime"
        if self.state in {"new", "open"}:
            self._set_state("in_progress")
        if action_key == "configure_adapter":
            return self.action_open_adapter()
        if action_key == "review_runtime_events":
            return self.action_open_events()
        if action_key == "review_runtime":
            return self.action_open_diagnostics()
        if action_key == "refresh_runtime":
            return self.action_refresh_adapter_diagnostics()
        if action_key == "repair_runtime":
            return self.action_repair_adapter()
        if action_key == "reload_runtime":
            return self.action_reload_adapter()
        if action_key == "request_edge_replay":
            return self.action_request_edge_replay()
        if action_key == "review_edge_dead_letter":
            return self.action_review_edge_dead_letter()
        if action_key == "load_runtime" and self.adapter_id:
            self.adapter_id.action_load_adapter()
            return self.action_open_diagnostics()
        if action_key == "unload_runtime" and self.adapter_id:
            self.adapter_id.action_unload_adapter()
            return self.action_open_diagnostics()
        return self.action_open_diagnostics()

    def action_open_diagnostics(self):
        self.ensure_one()
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_console").read()[0]
        if self.adapter_id:
            action["domain"] = [("id", "=", self.adapter_id.id)]
            action["name"] = _("Adapter Console")
        return action

    def action_open_events(self):
        self.ensure_one()
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_event").read()[0]
        action["name"] = _("Runtime Events")
        context = action.get("context")
        if not isinstance(context, dict):
            context = {}
        if self.adapter_id:
            action["domain"] = [("adapter_id", "=", self.adapter_id.id)]
            action["context"] = {**context, "search_default_adapter_id": self.adapter_id.id, "default_adapter_id": self.adapter_id.id}
        return action

    def action_open_edge_actions(self):
        self.ensure_one()
        if self.adapter_id:
            return self.adapter_id.action_open_edge_actions()
        return self.action_open_events()

    def action_open_protocol_runtime_issues(self):
        self.ensure_one()
        if self.adapter_id:
            return self.adapter_id.action_open_protocol_runtime_issues()
        return self.action_open_diagnostics()

    def action_open_protocol_runtime_console(self):
        self.ensure_one()
        if self.adapter_id:
            return self.adapter_id.action_open_protocol_runtime_console()
        return self.action_open_diagnostics()

    def action_open_protocol_runtime_probe(self):
        self.ensure_one()
        if self.adapter_id:
            return self.adapter_id.action_open_protocol_runtime_probe()
        return self.action_open_diagnostics()

    def action_refresh_adapter_diagnostics(self):
        self.ensure_one()
        if self.adapter_id:
            self.adapter_id.action_refresh_diagnostics()
        return self.action_open_diagnostics()

    def action_repair_adapter(self):
        self.ensure_one()
        if self.adapter_id:
            self.adapter_id.action_repair_adapter()
        return self.action_open_diagnostics()

    def action_request_edge_replay(self):
        self.ensure_one()
        if self.adapter_id:
            return self.adapter_id.action_request_edge_replay()
        return self.action_open_diagnostics()

    def action_review_edge_dead_letter(self):
        self.ensure_one()
        if self.adapter_id:
            return self.adapter_id.action_review_edge_dead_letter()
        return self.action_open_diagnostics()

    def action_reload_adapter(self):
        self.ensure_one()
        if self.adapter_id:
            self.adapter_id.action_reload_adapter()
        return self.action_open_diagnostics()

    def action_open_adapter(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Runtime Adapter"),
            "res_model": "gateway.runtime.adapter",
            "view_mode": "form",
            "res_id": self.adapter_id.id,
            "target": "current",
        }

    def _payload_summary(self):
        self.ensure_one()
        if not self.payload_json:
            return {}
        try:
            parsed = json.loads(self.payload_json)
            return parsed if isinstance(parsed, dict) else {"payload": parsed}
        except Exception:
            return {"payload": self.payload_json}
