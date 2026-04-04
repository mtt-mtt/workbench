from odoo import api, fields, models, _


class GatewayRuntimeProbeSession(models.Model):
    _name = "gateway.runtime.probe.session"
    _description = "Gateway Runtime Probe Session"
    _order = "started_at desc, id desc"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    session_key = fields.Char(index=True)
    adapter_id = fields.Many2one("gateway.runtime.adapter", ondelete="set null", index=True)
    entry_id = fields.Many2one("gateway.entry", ondelete="set null", index=True)
    device_id = fields.Many2one("gateway.device", ondelete="set null", index=True)
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    protocol = fields.Char(index=True)
    trigger_kind = fields.Selection(
        [
            ("manual", "Manual"),
            ("probe", "Probe"),
            ("callback", "Callback"),
            ("heartbeat", "Heartbeat"),
            ("event", "Event"),
            ("runtime", "Runtime"),
            ("diagnostic", "Diagnostic"),
            ("repair", "Repair"),
        ],
        default="manual",
        required=True,
        index=True,
    )
    capability = fields.Char()
    probe_kind = fields.Selection(
        [
            ("summary", "Summary"),
            ("connectivity", "Connectivity"),
            ("subscription", "Subscription"),
            ("read", "Read"),
            ("write", "Write"),
            ("subscribe", "Subscribe"),
            ("heartbeat", "Heartbeat"),
            ("event", "Event"),
            ("diagnostic", "Diagnostic"),
            ("reload", "Reload"),
            ("repair", "Repair"),
            ("custom", "Custom"),
        ],
        default="summary",
        required=True,
        index=True,
    )
    change_kind = fields.Selection(
        [
            ("identity", "Identity"),
            ("topology", "Topology"),
            ("state", "State"),
            ("probe", "Probe"),
        ],
        default="probe",
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
        default="discovered",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("running", "Running"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        index=True,
    )
    result_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("success", "Success"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="low",
        required=True,
        index=True,
    )
    target_ref = fields.Char(index=True)
    source_signal = fields.Char(index=True)
    source_payload_id = fields.Char(index=True)
    state_version = fields.Char(index=True)
    ui_refresh_hint = fields.Char()
    latency_ms = fields.Integer(default=0)
    request_json = fields.Text()
    response_json = fields.Text()
    payload_json = fields.Text()
    normalized_json = fields.Text()
    summary = fields.Char()
    message = fields.Char()
    last_error = fields.Text()
    issue_id = fields.Many2one("gateway.runtime.issue", ondelete="set null")
    issue_key = fields.Char(index=True)
    request_summary = fields.Char(compute="_compute_session_summary", readonly=True)
    response_summary = fields.Char(compute="_compute_session_summary", readonly=True)
    result_summary = fields.Char(compute="_compute_session_summary", readonly=True)
    session_summary = fields.Char(compute="_compute_session_summary", readonly=True)
    started_at = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    finished_at = fields.Datetime()
    runtime_event_id = fields.Many2one("gateway.runtime.event", ondelete="set null")
    note = fields.Text()

    _gateway_runtime_probe_session_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Probe session code must be unique.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.runtime.probe.session") or _("New")
            vals.setdefault("session_key", vals.get("code"))
            vals.setdefault("name", vals.get("target_ref") or vals.get("session_key") or vals.get("code") or _("Probe Session"))
            vals.setdefault("summary", vals.get("message") or vals.get("name"))
        return super().create(vals_list)

    @api.depends("state", "result_state", "probe_kind", "summary", "last_error", "latency_ms", "started_at", "finished_at")
    def _compute_session_summary(self):
        for record in self:
            state = record.state or _("draft")
            result = record.result_state or _("pending")
            record.session_summary = _("%(kind)s / %(state)s / %(result)s") % {
                "kind": record.probe_kind or _("probe"),
                "state": state,
                "result": result,
            }
            record.result_summary = record.summary or record.message or record.last_error or _("No result recorded")
            request_label = record.summary or record.message or _("%s probe request") % (record.probe_kind or _("Runtime"))
            record.request_summary = _("%(label)s | started %(started)s") % {
                "label": request_label,
                "started": record.started_at or _("unknown"),
            }
            response_label = record.last_error or (record.response_json and _("Response captured")) or _("Awaiting response")
            record.response_summary = _("%(label)s | finished %(finished)s, %(latency)s ms") % {
                "label": response_label,
                "finished": record.finished_at or _("pending"),
                "latency": record.latency_ms or 0,
            }

    def _set_state(self, state, result_state=None, *, summary=None, message=None, last_error=None, response=None):
        values = {"state": state}
        if result_state:
            values["result_state"] = result_state
        if summary is not None:
            values["summary"] = summary
        if message is not None:
            values["message"] = message
        if last_error is not None:
            values["last_error"] = last_error
        if state in {"done", "failed", "cancelled"}:
            values["finished_at"] = fields.Datetime.now()
        if response is not None:
            values["response_json"] = json.dumps(response, ensure_ascii=False, default=str)
        if values.get("finished_at") and self.started_at:
            delta = values["finished_at"] - self.started_at
            values["latency_ms"] = int(max(0, delta.total_seconds() * 1000))
        self.write(values)
        return True

    def action_mark_running(self):
        self.ensure_one()
        self._set_state("running", "pending", summary=_("Probe session started"), message=_("Probe session started"))
        return self.action_open_adapter()

    def action_mark_done(self):
        self.ensure_one()
        self._set_state("done", "success", summary=_("Probe session completed"), message=_("Probe session completed"))
        return self.action_open_adapter()

    def action_mark_failed(self):
        self.ensure_one()
        self._set_state("failed", "error", summary=_("Probe session failed"), message=_("Probe session failed"))
        return self.action_open_adapter()

    def action_mark_cancelled(self):
        self.ensure_one()
        self._set_state("cancelled", "cancelled", summary=_("Probe session cancelled"), message=_("Probe session cancelled"))
        return self.action_open_adapter()

    def action_open_adapter(self):
        self.ensure_one()
        if not self.adapter_id:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Probe Session"),
                    "message": _("This probe session is not linked to a runtime adapter."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Runtime Adapter"),
            "res_model": "gateway.runtime.adapter",
            "view_mode": "form",
            "res_id": self.adapter_id.id,
            "target": "current",
        }

    def action_open_sessions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Probe Sessions"),
            "res_model": "gateway.runtime.probe.session",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.adapter_id.id)] if self.adapter_id else [],
            "context": {"default_adapter_id": self.adapter_id.id if self.adapter_id else False},
        }

    def action_refresh_probe(self):
        self.ensure_one()
        result = GatewayRuntimeService(self.env).create_probe_session(
            {"adapter_code": self.adapter_id.code if self.adapter_id else None, "probe_kind": self.probe_kind}
        )
        if result.get("ok") and result.get("data"):
            session_id = result["data"].get("id") if isinstance(result["data"], dict) else None
            if session_id:
                return {
                    "type": "ir.actions.act_window",
                    "name": _("Probe Session"),
                    "res_model": "gateway.runtime.probe.session",
                    "view_mode": "form",
                    "res_id": session_id,
                    "target": "current",
                }
        return self.action_open_sessions()
