import json

from odoo import api, fields, models, _

from ..services.runtime_service import GatewayRuntimeService


class GatewayRuntimeAdapter(models.Model):
    _name = "gateway.runtime.adapter"
    _description = "Gateway Runtime Adapter"
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
    adapter_type = fields.Selection(
        [
            ("mock", "Mock"),
            ("mqtt", "MQTT"),
            ("modbus", "Modbus"),
            ("opcua", "OPC UA"),
            ("ads", "ADS"),
            ("s7", "S7"),
            ("http", "HTTP"),
            ("print", "Print"),
            ("scale", "Scale"),
            ("generic", "Generic"),
        ],
        default="mock",
        required=True,
        index=True,
    )
    entry_id = fields.Many2one("gateway.entry", ondelete="set null")
    app_id = fields.Many2one("shopfloor.app", ondelete="set null")
    workstation_id = fields.Many2one("shopfloor.workstation", ondelete="set null")
    device_code = fields.Char(index=True)
    runtime_unique_id = fields.Char(index=True)
    connection_target = fields.Char()
    config_json = fields.Text()
    config_text = fields.Text()
    diagnostic_state = fields.Text()
    diagnostic_summary = fields.Text()
    capability_json = fields.Text(compute="_compute_runtime_profile", readonly=True)
    capability_summary = fields.Char(compute="_compute_runtime_profile", readonly=True)
    lifecycle_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("configuring", "Configuring"),
            ("ready", "Ready"),
            ("degraded", "Degraded"),
            ("offline", "Offline"),
            ("disabled", "Disabled"),
        ],
        compute="_compute_runtime_profile",
        readonly=True,
        index=True,
    )
    lifecycle_detail = fields.Char(compute="_compute_runtime_profile", readonly=True)
    health_state = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("healthy", "Healthy"),
            ("warning", "Warning"),
            ("degraded", "Degraded"),
            ("offline", "Offline"),
        ],
        default="unknown",
        required=True,
        index=True,
    )
    health_score = fields.Integer(default=0)
    health_detail = fields.Char()
    last_error = fields.Text()
    coordinator_mode = fields.Selection(
        [
            ("poll", "Poll"),
            ("push", "Push"),
            ("hybrid", "Hybrid"),
        ],
        default="poll",
        required=True,
        index=True,
    )
    update_interval_seconds = fields.Integer(default=30)
    retry_after_seconds = fields.Integer(default=0)
    last_update_success = fields.Boolean(default=False)
    last_exception_class = fields.Char()
    last_exception_message = fields.Text()
    last_update_started_at = fields.Datetime()
    last_update_finished_at = fields.Datetime()
    last_update_success_at = fields.Datetime()
    last_update_failure_at = fields.Datetime()
    first_refresh_required = fields.Boolean(default=True)
    always_update = fields.Boolean(default=True)
    listener_count = fields.Integer(default=0)
    dispatch_state = fields.Selection(
        [
            ("idle", "Idle"),
            ("active", "Active"),
            ("paused", "Paused"),
            ("error", "Error"),
        ],
        default="idle",
        required=True,
        index=True,
    )
    listener_state = fields.Selection(
        [
            ("idle", "Idle"),
            ("attached", "Attached"),
            ("suspended", "Suspended"),
            ("error", "Error"),
        ],
        default="idle",
        required=True,
        index=True,
    )
    listener_contract_json = fields.Text()
    dispatch_contract_json = fields.Text()
    lifecycle_checkpoint = fields.Char()
    last_dispatch_at = fields.Datetime()
    last_listener_sync_at = fields.Datetime()
    last_listener_cleanup_at = fields.Datetime()
    listener_summary = fields.Char(compute="_compute_listener_lifecycle", readonly=True)
    dispatch_summary = fields.Char(compute="_compute_listener_lifecycle", readonly=True)
    timeout_seconds = fields.Integer(default=30)
    heartbeat_timeout_seconds = fields.Integer(default=60)
    supports_push = fields.Boolean(default=False)
    supports_poll = fields.Boolean(default=True)
    supports_read = fields.Boolean(default=True)
    supports_write = fields.Boolean(default=True)
    supports_subscribe = fields.Boolean(default=False)
    supports_discovery = fields.Boolean(default=False)
    supports_ack = fields.Boolean(default=False)
    supports_diagnostics = fields.Boolean(default=True)
    supports_repair = fields.Boolean(default=True)
    supports_reload = fields.Boolean(default=True)
    supports_load = fields.Boolean(default=True)
    supports_unload = fields.Boolean(default=True)
    supports_dispatch = fields.Boolean(default=True)
    reconnect_policy = fields.Selection(
        [
            ("manual", "Manual"),
            ("auto", "Auto"),
            ("off", "Off"),
        ],
        default="auto",
        required=True,
        index=True,
    )
    reconnect_delay_seconds = fields.Integer(default=5)
    max_reconnect_attempts = fields.Integer(default=3)
    reconnect_attempts = fields.Integer(default=0)
    last_reconnect_at = fields.Datetime()
    last_reload_at = fields.Datetime()
    last_repair_at = fields.Datetime()
    last_success_at = fields.Datetime()
    last_failure_at = fields.Datetime()
    last_heartbeat_at = fields.Datetime()
    last_poll_at = fields.Datetime()
    heartbeat_count = fields.Integer(default=0)
    event_count = fields.Integer(default=0)
    command_count = fields.Integer(default=0)
    note = fields.Text()
    heartbeat_ids = fields.One2many("gateway.runtime.heartbeat", "adapter_id", string="Heartbeats")
    event_ids = fields.One2many("gateway.runtime.event", "adapter_id", string="Events")
    issue_ids = fields.One2many("gateway.runtime.issue", "adapter_id", string="Issues")
    probe_session_ids = fields.One2many("gateway.runtime.probe.session", "adapter_id", string="Probe Sessions")
    issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    open_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    repair_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    driver_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    open_driver_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    driver_issue_summary = fields.Char(compute="_compute_issue_stats", readonly=True)
    edge_cache_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    open_edge_cache_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    edge_cache_issue_summary = fields.Char(compute="_compute_issue_stats", readonly=True)
    protocol_runtime_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    open_protocol_runtime_issue_count = fields.Integer(compute="_compute_issue_stats", readonly=True)
    protocol_runtime_issue_summary = fields.Char(compute="_compute_issue_stats", readonly=True)
    mqtt_adapter_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    modbus_adapter_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    opcua_adapter_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    ads_adapter_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    s7_adapter_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    probe_session_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    open_probe_session_count = fields.Integer(compute="_compute_protocol_probe_stats", readonly=True)
    last_probe_session_at = fields.Datetime(compute="_compute_protocol_probe_stats", readonly=True)
    probe_focus_state = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("ready", "Ready"),
            ("attention", "Attention"),
            ("offline", "Offline"),
            ("disabled", "Disabled"),
        ],
        compute="_compute_protocol_probe_stats",
        readonly=True,
        index=True,
    )
    probe_summary = fields.Char(compute="_compute_protocol_probe_stats", readonly=True)
    probe_focus_summary = fields.Char(compute="_compute_protocol_probe_stats", readonly=True)
    probe_attention_summary = fields.Char(compute="_compute_protocol_probe_stats", readonly=True)
    probe_session_summary = fields.Char(compute="_compute_protocol_probe_stats", readonly=True)
    probe_detail = fields.Text(compute="_compute_protocol_probe_stats", readonly=True)
    driver_diagnostic_state = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("ready", "Ready"),
            ("attention", "Attention"),
            ("error", "Error"),
        ],
        compute="_compute_driver_diagnostics",
        readonly=True,
        index=True,
    )
    driver_diagnostic_summary = fields.Char(compute="_compute_driver_diagnostics", readonly=True)
    driver_diagnostic_detail = fields.Text(compute="_compute_driver_diagnostics", readonly=True)
    console_summary = fields.Char(compute="_compute_console_summary", readonly=True)
    console_attention_summary = fields.Char(compute="_compute_console_summary", readonly=True)
    recent_activity_summary = fields.Char(compute="_compute_recent_activity_summary", readonly=True)
    recent_activity_timeline = fields.Text(compute="_compute_recent_activity_summary", readonly=True)
    attention_route_summary = fields.Char(compute="_compute_attention_route_summary", readonly=True)
    print_driver_summary = fields.Char(compute="_compute_print_driver_diagnostics", readonly=True)
    print_driver_state_summary = fields.Char(compute="_compute_print_driver_diagnostics", readonly=True)
    print_driver_polling_summary = fields.Char(compute="_compute_print_driver_diagnostics", readonly=True)
    edge_replay_pending_count = fields.Integer(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_replay_due_count = fields.Integer(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_replay_scheduled_count = fields.Integer(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_replay_coalesced_count = fields.Integer(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_replay_summary = fields.Char(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_last_replay_outcome = fields.Char(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_last_replay_summary = fields.Char(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_dead_letter_count = fields.Integer(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_dead_letter_summary = fields.Char(compute="_compute_edge_cache_diagnostics", readonly=True)
    edge_protocol_runtime_state = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("ready", "Ready"),
            ("attention", "Attention"),
            ("error", "Error"),
        ],
        compute="_compute_edge_protocol_runtime_diagnostics",
        readonly=True,
        index=True,
    )
    edge_protocol_runtime_summary = fields.Char(compute="_compute_edge_protocol_runtime_diagnostics", readonly=True)
    edge_protocol_runtime_count = fields.Integer(compute="_compute_edge_protocol_runtime_diagnostics", readonly=True)
    edge_protocol_runtime_entry_count = fields.Integer(compute="_compute_edge_protocol_runtime_diagnostics", readonly=True)
    edge_protocol_runtime_state_counts_summary = fields.Char(compute="_compute_edge_protocol_runtime_diagnostics", readonly=True)
    edge_protocol_runtime_kind_counts_summary = fields.Char(compute="_compute_edge_protocol_runtime_diagnostics", readonly=True)
    edge_protocol_runtime_detail = fields.Text(compute="_compute_edge_protocol_runtime_diagnostics", readonly=True)
    edge_action_count = fields.Integer(compute="_compute_edge_action_stats", readonly=True)
    pending_edge_action_count = fields.Integer(compute="_compute_edge_action_stats", readonly=True)
    processing_edge_action_count = fields.Integer(compute="_compute_edge_action_stats", readonly=True)
    processed_edge_action_count = fields.Integer(compute="_compute_edge_action_stats", readonly=True)
    edge_action_summary = fields.Char(compute="_compute_edge_action_stats", readonly=True)

    _gateway_runtime_adapter_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Adapter code must be unique.",
    )

    @api.model
    def _default_capability_values(self, adapter_type):
        adapter_type = adapter_type or "generic"
        defaults = {
            "supports_push": False,
            "supports_poll": True,
            "supports_read": True,
            "supports_write": True,
            "supports_subscribe": False,
            "supports_discovery": False,
            "supports_ack": True,
            "supports_diagnostics": True,
            "supports_repair": True,
            "supports_reload": True,
            "supports_load": True,
            "supports_unload": True,
            "supports_dispatch": True,
        }
        type_defaults = {
            "mock": {"supports_push": True, "supports_subscribe": True, "supports_discovery": True},
            "mqtt": {"supports_push": True, "supports_subscribe": True, "supports_discovery": True},
            "modbus": {"supports_push": False, "supports_subscribe": False, "supports_discovery": False},
            "opcua": {"supports_push": True, "supports_subscribe": True, "supports_discovery": True},
            "ads": {"supports_push": True, "supports_subscribe": True},
            "s7": {"supports_push": False, "supports_subscribe": False, "supports_discovery": False},
            "http": {"supports_push": True, "supports_poll": False, "supports_read": False, "supports_subscribe": False},
            "print": {"supports_push": True, "supports_poll": False, "supports_read": False, "supports_subscribe": False},
            "scale": {"supports_push": False, "supports_write": False},
        }
        defaults.update(type_defaults.get(adapter_type, {}))
        return defaults

    @api.model
    def _default_coordinator_mode(self, adapter_type, values=None):
        values = values or {}
        supports_push = values.get("supports_push")
        supports_poll = values.get("supports_poll")
        if supports_push is None or supports_poll is None:
            defaults = self._default_capability_values(adapter_type)
            supports_push = defaults["supports_push"] if supports_push is None else supports_push
            supports_poll = defaults["supports_poll"] if supports_poll is None else supports_poll
        if supports_push and supports_poll:
            return "hybrid"
        if supports_push:
            return "push"
        return "poll"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") in (None, "/", "New"):
                vals["code"] = self.env["ir.sequence"].next_by_code("gateway.runtime.adapter") or _("New")
            adapter_type = vals.get("adapter_type") or "generic"
            for key, value in self._default_capability_values(adapter_type).items():
                vals.setdefault(key, value)
            vals.setdefault("coordinator_mode", self._default_coordinator_mode(adapter_type, vals))
            vals.setdefault("update_interval_seconds", vals.get("timeout_seconds") or 30)
        return super().create(vals_list)

    @api.depends(
        "active",
        "state",
        "adapter_type",
        "health_state",
        "health_score",
        "connection_target",
        "config_json",
        "timeout_seconds",
        "heartbeat_timeout_seconds",
        "coordinator_mode",
        "update_interval_seconds",
        "retry_after_seconds",
        "last_update_success",
        "last_exception_class",
        "last_exception_message",
        "last_update_started_at",
        "last_update_finished_at",
        "last_update_success_at",
        "last_update_failure_at",
        "first_refresh_required",
        "always_update",
        "listener_count",
        "dispatch_state",
        "listener_state",
        "listener_contract_json",
        "dispatch_contract_json",
        "lifecycle_checkpoint",
        "last_dispatch_at",
        "last_listener_sync_at",
        "last_listener_cleanup_at",
        "supports_push",
        "supports_poll",
        "supports_read",
        "supports_write",
        "supports_subscribe",
        "supports_discovery",
        "supports_ack",
        "supports_diagnostics",
        "supports_repair",
        "supports_reload",
        "supports_load",
        "supports_unload",
        "supports_dispatch",
        "reconnect_policy",
        "reconnect_attempts",
        "max_reconnect_attempts",
        "last_success_at",
        "last_failure_at",
        "last_error",
        "last_reload_at",
        "last_repair_at",
    )
    def _compute_runtime_profile(self):
        for record in self:
            capabilities = record._build_capability_payload()
            lifecycle_state, lifecycle_detail = record._build_lifecycle_payload(capabilities)
            record.capability_json = json.dumps(capabilities, ensure_ascii=False, default=str)
            record.capability_summary = record._build_capability_summary(capabilities)
            record.lifecycle_state = lifecycle_state
            record.lifecycle_detail = lifecycle_detail

    @api.depends(
        "dispatch_state",
        "listener_state",
        "listener_count",
        "coordinator_mode",
        "supports_dispatch",
        "supports_subscribe",
        "last_dispatch_at",
        "last_listener_sync_at",
        "last_listener_cleanup_at",
        "lifecycle_checkpoint",
        "last_error",
    )
    def _compute_listener_lifecycle(self):
        for record in self:
            dispatch_bits = [
                record.dispatch_state or _("idle"),
                _("mode %(mode)s") % {"mode": record.coordinator_mode or "poll"},
                _("dispatch %(enabled)s") % {"enabled": _("enabled") if record.supports_dispatch else _("disabled")},
            ]
            if record.last_dispatch_at:
                dispatch_bits.append(_("last dispatch %(when)s") % {"when": record.last_dispatch_at})
            if record.last_error and record.dispatch_state == "error":
                dispatch_bits.append(_("error recorded"))
            record.dispatch_summary = ", ".join(dispatch_bits)

            listener_bits = [
                record.listener_state or _("idle"),
                _("%(count)s listener(s)") % {"count": record.listener_count or 0},
                _("subscribe %(enabled)s") % {"enabled": _("enabled") if record.supports_subscribe else _("not required")},
            ]
            if record.last_listener_sync_at:
                listener_bits.append(_("synced %(when)s") % {"when": record.last_listener_sync_at})
            if record.last_listener_cleanup_at:
                listener_bits.append(_("cleanup %(when)s") % {"when": record.last_listener_cleanup_at})
            if record.lifecycle_checkpoint:
                listener_bits.append(_("checkpoint %(checkpoint)s") % {"checkpoint": record.lifecycle_checkpoint})
            record.listener_summary = ", ".join(listener_bits)

    @api.depends("issue_ids", "issue_ids.state", "issue_ids.issue_key", "issue_ids.is_fixable")
    def _compute_issue_stats(self):
        for record in self:
            issues = record.issue_ids
            open_issues = issues.filtered(lambda issue: issue.state in {"new", "open", "in_progress"})
            driver_issues = issues.filtered(lambda issue: (issue.issue_key or "").endswith(":driver_diagnostic"))
            open_driver_issues = driver_issues.filtered(lambda issue: issue.state in {"new", "open", "in_progress"})
            edge_cache_issues = issues.filtered(
                lambda issue: (issue.issue_key or "").endswith(":edge_dead_letter") or (issue.issue_key or "").endswith(":edge_replay")
            )
            open_edge_cache_issues = edge_cache_issues.filtered(lambda issue: issue.state in {"new", "open", "in_progress"})
            protocol_runtime_issues = issues.filtered(lambda issue: (issue.issue_key or "").endswith(":protocol_runtime"))
            open_protocol_runtime_issues = protocol_runtime_issues.filtered(lambda issue: issue.state in {"new", "open", "in_progress"})
            record.issue_count = len(issues)
            record.open_issue_count = len(open_issues)
            record.repair_issue_count = len(open_issues.filtered("is_fixable"))
            record.driver_issue_count = len(driver_issues)
            record.open_driver_issue_count = len(open_driver_issues)
            record.driver_issue_summary = _("%(total)s driver issue(s), %(open)s open") % {
                "total": record.driver_issue_count or 0,
                "open": record.open_driver_issue_count or 0,
            }
            record.edge_cache_issue_count = len(edge_cache_issues)
            record.open_edge_cache_issue_count = len(open_edge_cache_issues)
            record.edge_cache_issue_summary = _("%(total)s edge cache issue(s), %(open)s open") % {
                "total": record.edge_cache_issue_count or 0,
                "open": record.open_edge_cache_issue_count or 0,
            }
            record.protocol_runtime_issue_count = len(protocol_runtime_issues)
            record.open_protocol_runtime_issue_count = len(open_protocol_runtime_issues)
            record.protocol_runtime_issue_summary = _("%(total)s protocol runtime issue(s), %(open)s open") % {
                "total": record.protocol_runtime_issue_count or 0,
                "open": record.open_protocol_runtime_issue_count or 0,
            }

    @api.depends(
        "state",
        "active",
        "health_state",
        "health_score",
        "last_heartbeat_at",
        "last_success_at",
        "last_failure_at",
        "issue_ids",
        "issue_ids.state",
        "issue_ids.is_fixable",
        "probe_session_ids",
        "probe_session_ids.state",
        "probe_session_ids.result_state",
        "probe_session_ids.started_at",
        "probe_session_ids.finished_at",
        "mqtt_adapter_count",
        "modbus_adapter_count",
        "opcua_adapter_count",
        "ads_adapter_count",
        "s7_adapter_count",
    )
    def _compute_protocol_probe_stats(self):
        def _compact(value, limit=180):
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

        def _protocol_summary(record, model_name, label, recent_fields):
            if model_name not in record.env.registry.models:
                return 0, _("%s: module not installed") % label, _("%s: module not installed") % label
            linked = record.env[model_name].sudo().search([("runtime_adapter_id", "=", record.id)], order="sequence, id")
            if not linked:
                return 0, _("%s: no linked adapters") % label, _("%s: no linked adapters") % label
            primary = linked[0]
            status = (
                getattr(primary, "runtime_health_state", False)
                or getattr(primary, "runtime_lifecycle_state", False)
                or getattr(primary, "state", False)
                or "unknown"
            )
            issue_count = getattr(primary, "runtime_issue_count", 0) or 0
            open_issue_count = getattr(primary, "runtime_open_issue_count", 0) or 0
            repair_issue_count = getattr(primary, "runtime_repair_issue_count", 0) or 0
            recent_bits = []
            for field_name in recent_fields:
                value = getattr(primary, field_name, None)
                if value:
                    recent_bits.append(_compact(value))
            summary = _("%(label)s %(count)s linked, %(status)s, issues %(issues)s/%(open)s/%(repair)s") % {
                "label": label,
                "count": len(linked),
                "status": status,
                "issues": issue_count,
                "open": open_issue_count,
                "repair": repair_issue_count,
            }
            detail = summary
            if recent_bits:
                detail = f"{summary} | {'; '.join(recent_bits)}"
            return len(linked), summary, detail

        for record in self:
            mqtt_count, mqtt_summary, mqtt_detail = _protocol_summary(
                record,
                "gateway.mqtt.adapter",
                _("MQTT"),
                ("runtime_diagnostic_summary", "diagnostic_state", "last_sync_at"),
            )
            modbus_count, modbus_summary, modbus_detail = _protocol_summary(
                record,
                "gateway.modbus.adapter",
                _("Modbus"),
                ("runtime_diagnostic_summary", "diagnostic_state", "last_snapshot_at", "last_ack_at"),
            )
            opcua_count, opcua_summary, opcua_detail = _protocol_summary(
                record,
                "gateway.opcua.adapter",
                _("OPC UA"),
                ("runtime_diagnostic_summary", "diagnostic_state", "last_sync_at"),
            )
            ads_count, ads_summary, ads_detail = _protocol_summary(
                record,
                "gateway.ads.adapter",
                _("ADS"),
                (
                    "runtime_diagnostic_summary",
                    "diagnostic_state",
                    "subscription_summary",
                    "notification_summary",
                    "last_sync_at",
                    "runtime_last_refresh_at",
                    "runtime_last_reload_at",
                ),
            )
            s7_count, s7_summary, s7_detail = _protocol_summary(
                record,
                "gateway.s7.adapter",
                _("S7"),
                ("runtime_diagnostic_summary", "diagnostic_state", "last_snapshot_at", "last_ack_at"),
            )
            sessions = record.probe_session_ids
            open_sessions = sessions.filtered(lambda item: item.state in {"draft", "running"})
            session_summary = _("%(sessions)s session(s), %(open)s open") % {
                "sessions": len(sessions),
                "open": len(open_sessions),
            }
            last_probe_session_at = max([item.started_at for item in sessions if item.started_at], default=False)
            summaries = [summary for summary in (mqtt_summary, modbus_summary, opcua_summary, ads_summary, s7_summary) if summary]
            details = [detail for detail in (mqtt_detail, modbus_detail, opcua_detail, ads_detail, s7_detail) if detail]
            record.mqtt_adapter_count = mqtt_count
            record.modbus_adapter_count = modbus_count
            record.opcua_adapter_count = opcua_count
            record.ads_adapter_count = ads_count
            record.s7_adapter_count = s7_count
            record.probe_session_count = len(sessions)
            record.open_probe_session_count = len(open_sessions)
            record.last_probe_session_at = last_probe_session_at
            if not record.active or record.state == "disabled":
                focus_state = "disabled"
                focus_summary = _("Adapter is disabled")
            elif record.health_state == "offline" or record.state == "offline":
                focus_state = "offline"
                focus_summary = _("Adapter is offline")
            elif record.open_issue_count or record.health_state in {"warning", "degraded"} or record.state == "degraded":
                focus_state = "attention"
                focus_summary = _("%(issues)s open issue(s), %(health)s") % {
                    "issues": record.open_issue_count,
                    "health": record.health_state or _("attention"),
                }
            elif mqtt_count or modbus_count or opcua_count or ads_count or s7_count or sessions:
                focus_state = "ready"
                focus_summary = _("%(protocols)s probe target(s), %(sessions)s probe session(s)") % {
                    "protocols": mqtt_count + modbus_count + opcua_count + ads_count + s7_count,
                    "sessions": len(sessions),
                }
            else:
                focus_state = "unknown"
                focus_summary = _("No linked protocol adapters")
            record.probe_focus_state = focus_state
            record.probe_summary = "; ".join(summaries) if summaries else _("No linked protocol adapters")
            record.probe_focus_summary = focus_summary
            record.probe_attention_summary = _("%(open)s open issue(s), %(repair)s fixable, %(health)s, %(sessions)s open probe session(s)") % {
                "open": record.open_issue_count,
                "repair": record.repair_issue_count,
                "health": record.health_state or _("unknown"),
                "sessions": len(open_sessions),
            }
            probe_details = details + [session_summary]
            if last_probe_session_at:
                probe_details.append(_("Last probe session at %(when)s") % {"when": last_probe_session_at})
            record.probe_session_summary = session_summary
            record.probe_detail = "\n".join(probe_details)

    @api.depends(
        "last_heartbeat_at",
        "last_success_at",
        "last_failure_at",
        "last_reload_at",
        "last_repair_at",
        "last_reconnect_at",
        "last_probe_session_at",
        "last_update_success_at",
        "last_update_failure_at",
        "last_error",
    )
    def _compute_recent_activity_summary(self):
        labels = (
            ("last_heartbeat_at", _("Heartbeat")),
            ("last_success_at", _("Success")),
            ("last_failure_at", _("Failure")),
            ("last_reload_at", _("Reload")),
            ("last_repair_at", _("Repair")),
            ("last_reconnect_at", _("Reconnect")),
            ("last_probe_session_at", _("Probe")),
            ("last_update_success_at", _("Update OK")),
            ("last_update_failure_at", _("Update Fail")),
        )
        for record in self:
            events = []
            for field_name, label in labels:
                value = getattr(record, field_name, False)
                if value:
                    events.append((value, label))
            events.sort(key=lambda item: item[0], reverse=True)
            if not events:
                record.recent_activity_summary = _("No recent runtime activity")
                record.recent_activity_timeline = _("No heartbeat, update, reload, repair, reconnect, or probe activity recorded yet.")
                continue
            latest_value, latest_label = events[0]
            record.recent_activity_summary = _("%(label)s at %(when)s") % {"label": latest_label, "when": latest_value}
            timeline_lines = [_("%(label)s: %(when)s") % {"label": label, "when": value} for value, label in events[:6]]
            if record.last_error:
                timeline_lines.append(_("Last error: %(error)s") % {"error": record.last_error})
            record.recent_activity_timeline = "\n".join(timeline_lines)

    @api.depends("diagnostic_state", "diagnostic_summary")
    def _compute_driver_diagnostics(self):
        for record in self:
            payload = {}
            for source in (record.diagnostic_state, record.diagnostic_summary):
                if not source:
                    continue
                if isinstance(source, dict):
                    payload = dict(source)
                    break
                try:
                    parsed = json.loads(source)
                    if isinstance(parsed, dict):
                        payload = parsed
                        break
                except Exception:
                    continue
            execution = payload.get("print_execution") if isinstance(payload.get("print_execution"), dict) else {}
            diagnostics = payload.get("driver_diagnostics") if isinstance(payload.get("driver_diagnostics"), dict) else {}
            capabilities = payload.get("driver_capabilities") if isinstance(payload.get("driver_capabilities"), dict) else {}
            if isinstance(execution, dict):
                diagnostics = diagnostics or (execution.get("driver_diagnostics") if isinstance(execution.get("driver_diagnostics"), dict) else {})
                capabilities = capabilities or (execution.get("driver_capabilities") if isinstance(execution.get("driver_capabilities"), dict) else {})
            origin = diagnostics.get("origin") or execution.get("driver_origin")
            label = diagnostics.get("label") or execution.get("driver_label")
            driver_type = diagnostics.get("type") or execution.get("driver_type")
            path = diagnostics.get("path") or execution.get("driver_path")
            ready = diagnostics.get("ready") if "ready" in diagnostics else execution.get("driver_ready")
            polling_supported = diagnostics.get("status_polling_supported")
            if polling_supported is None:
                polling_supported = capabilities.get("status_polling_supported")
            refresh_supported = diagnostics.get("supports_refresh_status")
            if refresh_supported is None:
                refresh_supported = capabilities.get("supports_refresh_status")
            endpoint_supported = diagnostics.get("supports_status_endpoint")
            if endpoint_supported is None:
                endpoint_supported = capabilities.get("supports_status_endpoint")
            if ready is False:
                state = "error"
            elif any(value not in (None, "", False) for value in [origin, label, driver_type, path]):
                state = "attention" if polling_supported is False else "ready"
            else:
                state = "unknown"
            summary_parts = [
                origin and _("driver %(value)s") % {"value": origin},
                label and _("label %(value)s") % {"value": label},
                driver_type and _("type %(value)s") % {"value": driver_type},
                ready is True and _("driver ready"),
                ready is False and _("driver not ready"),
                polling_supported is True and _("polling supported"),
                polling_supported is False and _("polling limited"),
            ]
            detail_parts = [
                origin and _("Origin: %(value)s") % {"value": origin},
                label and _("Label: %(value)s") % {"value": label},
                driver_type and _("Type: %(value)s") % {"value": driver_type},
                path and _("Path: %(value)s") % {"value": path},
                ready is True and _("Ready: yes"),
                ready is False and _("Ready: no"),
                polling_supported is True and _("Polling supported: yes"),
                polling_supported is False and _("Polling supported: no"),
                refresh_supported is True and _("Refresh-status supported: yes"),
                refresh_supported is False and _("Refresh-status supported: no"),
                endpoint_supported is True and _("Status endpoint available: yes"),
                endpoint_supported is False and _("Status endpoint available: no"),
            ]
            record.driver_diagnostic_state = state
            record.driver_diagnostic_summary = ", ".join([part for part in summary_parts if part]) or _("No driver diagnostics")
            record.driver_diagnostic_detail = "\n".join([part for part in detail_parts if part]) or _("No print driver diagnostics recorded yet.")

    @api.depends(
        "state",
        "active",
        "health_state",
        "health_score",
        "lifecycle_state",
        "open_issue_count",
        "repair_issue_count",
        "probe_focus_state",
        "probe_session_count",
        "open_probe_session_count",
        "last_heartbeat_at",
        "last_success_at",
        "last_failure_at",
        "last_error",
        "probe_focus_summary",
        "probe_session_summary",
        "driver_diagnostic_state",
        "driver_diagnostic_summary",
        "driver_issue_summary",
        "open_driver_issue_count",
        "edge_cache_issue_summary",
        "open_edge_cache_issue_count",
        "protocol_runtime_issue_count",
        "open_protocol_runtime_issue_count",
        "protocol_runtime_issue_summary",
        "edge_replay_pending_count",
        "edge_replay_coalesced_count",
        "edge_replay_summary",
        "edge_last_replay_outcome",
        "edge_last_replay_summary",
        "edge_dead_letter_count",
        "edge_dead_letter_summary",
        "edge_protocol_runtime_state",
        "edge_protocol_runtime_summary",
        "edge_protocol_runtime_count",
        "edge_protocol_runtime_entry_count",
        "edge_protocol_runtime_state_counts_summary",
        "edge_protocol_runtime_kind_counts_summary",
        "edge_protocol_runtime_detail",
        "edge_action_count",
        "pending_edge_action_count",
        "processing_edge_action_count",
        "edge_action_summary",
    )
    def _compute_console_summary(self):
        for record in self:
            issue_text = _("%(open)s open issue(s), %(fixable)s fixable") % {
                "open": record.open_issue_count or 0,
                "fixable": record.repair_issue_count or 0,
            }
            edge_cache_bits = []
            if record.edge_replay_pending_count:
                edge_cache_bits.append(record.edge_replay_summary or _("replay pending"))
            if record.edge_last_replay_summary:
                edge_cache_bits.append(record.edge_last_replay_summary)
            if record.edge_dead_letter_count:
                edge_cache_bits.append(record.edge_dead_letter_summary or _("dead letters present"))
            if record.edge_action_count:
                edge_cache_bits.append(record.edge_action_summary or _("edge actions recorded"))
            if record.protocol_runtime_issue_count:
                edge_cache_bits.append(
                    record.protocol_runtime_issue_summary or _("protocol runtime issue(s) recorded")
                )
            if record.edge_protocol_runtime_count:
                edge_cache_bits.append(record.edge_protocol_runtime_summary or _("protocol runtime present"))
            if not record.active or record.state == "disabled":
                state_text = _("disabled")
            elif record.health_state in {"offline", "degraded", "warning"}:
                state_text = record.health_state
            else:
                state_text = record.lifecycle_state or record.health_state or record.state or _("unknown")
            probe_text = record.probe_session_summary or _("0 session(s), 0 open")
            driver_text = record.driver_diagnostic_summary or _("No driver diagnostics")
            record.console_summary = _("%(state)s, %(issues)s, %(probes)s, %(driver)s") % {
                "state": state_text,
                "issues": issue_text,
                "probes": probe_text,
                "driver": driver_text,
            }
            if edge_cache_bits:
                record.console_summary = f"{record.console_summary}, {'; '.join(edge_cache_bits)}"
            attention_bits = []
            if record.open_edge_cache_issue_count:
                attention_bits.append(record.edge_cache_issue_summary or _("%s open edge cache issue(s)") % (record.open_edge_cache_issue_count or 0))
            if record.pending_edge_action_count:
                attention_bits.append(record.edge_action_summary or _("%s pending edge action(s)") % (record.pending_edge_action_count or 0))
            if record.open_protocol_runtime_issue_count:
                attention_bits.append(
                    record.protocol_runtime_issue_summary or _("%s open protocol runtime issue(s)") % (record.open_protocol_runtime_issue_count or 0)
                )
            if record.edge_dead_letter_count:
                attention_bits.append(record.edge_dead_letter_summary or _("%s dead letter(s)") % (record.edge_dead_letter_count or 0))
            if record.edge_replay_pending_count:
                attention_bits.append(record.edge_replay_summary or _("%s replay pending") % (record.edge_replay_pending_count or 0))
            if record.edge_last_replay_summary:
                attention_bits.append(record.edge_last_replay_summary)
            if record.open_driver_issue_count:
                attention_bits.append(record.driver_issue_summary or _("%s open driver issue(s)") % (record.open_driver_issue_count or 0))
            if record.open_issue_count:
                attention_bits.append(issue_text)
            if record.probe_focus_state == "attention":
                attention_bits.append(record.probe_focus_summary or _("probe attention"))
            if record.open_probe_session_count:
                attention_bits.append(_("%s open probe session(s)") % (record.open_probe_session_count or 0))
            if record.driver_diagnostic_state in {"attention", "error"}:
                attention_bits.append(record.driver_diagnostic_summary or _("driver diagnostics require review"))
            if record.edge_protocol_runtime_state in {"attention", "error"}:
                attention_bits.append(record.edge_protocol_runtime_summary or _("protocol runtime requires review"))
            if record.last_error:
                attention_bits.append(record.last_error)
            if not attention_bits:
                attention_bits.append(_("No active attention items"))
            record.console_attention_summary = " | ".join(attention_bits)

    @api.depends(
        "open_issue_count",
        "repair_issue_count",
        "open_driver_issue_count",
        "open_probe_session_count",
        "probe_focus_state",
        "health_state",
        "state",
        "driver_diagnostic_state",
        "driver_diagnostic_summary",
        "open_edge_cache_issue_count",
        "edge_cache_issue_summary",
        "protocol_runtime_issue_count",
        "open_protocol_runtime_issue_count",
        "protocol_runtime_issue_summary",
        "edge_replay_pending_count",
        "edge_replay_coalesced_count",
        "edge_last_replay_outcome",
        "edge_last_replay_summary",
        "edge_dead_letter_count",
        "edge_dead_letter_summary",
        "edge_protocol_runtime_state",
        "edge_protocol_runtime_summary",
        "edge_protocol_runtime_count",
        "edge_protocol_runtime_entry_count",
        "edge_protocol_runtime_state_counts_summary",
        "edge_protocol_runtime_kind_counts_summary",
        "edge_protocol_runtime_detail",
        "pending_edge_action_count",
        "processing_edge_action_count",
        "edge_action_summary",
    )
    def _compute_attention_route_summary(self):
        for record in self:
            if record.open_edge_cache_issue_count:
                record.attention_route_summary = record.edge_cache_issue_summary or _("Review edge cache backlog")
            elif record.pending_edge_action_count:
                record.attention_route_summary = record.edge_action_summary or _("Review pending edge actions")
            elif record.open_protocol_runtime_issue_count:
                record.attention_route_summary = record.protocol_runtime_issue_summary or _("Review protocol runtime diagnostics")
            elif record.open_driver_issue_count and record.open_issue_count == record.open_driver_issue_count:
                record.attention_route_summary = record.driver_diagnostic_summary or _("%s open driver issue(s)") % (record.open_driver_issue_count or 0)
            elif record.edge_replay_pending_count:
                record.attention_route_summary = record.edge_last_replay_summary or record.edge_replay_summary or _("Review edge replay queue")
            elif record.open_issue_count:
                if record.repair_issue_count:
                    record.attention_route_summary = _("%(issues)s issue(s), %(repairs)s fixable") % {
                        "issues": record.open_issue_count,
                        "repairs": record.repair_issue_count,
                    }
                else:
                    record.attention_route_summary = _("%s open issue(s)") % (record.open_issue_count or 0)
            elif record.open_probe_session_count:
                record.attention_route_summary = _("%s open probe session(s)") % (record.open_probe_session_count or 0)
            elif record.driver_diagnostic_state in {"attention", "error"}:
                record.attention_route_summary = record.driver_diagnostic_summary or _("Review print driver diagnostics")
            elif record.edge_protocol_runtime_state in {"attention", "error"}:
                record.attention_route_summary = record.edge_protocol_runtime_summary or _("Review protocol runtime diagnostics")
            elif record.health_state in {"warning", "degraded", "offline"} or record.state in {"degraded", "offline"}:
                record.attention_route_summary = _("Review diagnostics")
            else:
                record.attention_route_summary = _("Open runtime overview")

    @staticmethod
    def _safe_parse_json(value):
        if not value:
            return {}
        if isinstance(value, dict):
            return dict(value)
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _extract_print_driver_snapshot(self):
        self.ensure_one()
        sources = [
            self._safe_parse_json(self.diagnostic_summary),
            self._safe_parse_json(self.diagnostic_state),
        ]
        for source in sources:
            execution = source.get("print_execution") if isinstance(source.get("print_execution"), dict) else {}
            diagnostics = execution.get("driver_diagnostics") if isinstance(execution.get("driver_diagnostics"), dict) else {}
            top_diagnostics = source.get("driver_diagnostics") if isinstance(source.get("driver_diagnostics"), dict) else {}
            capabilities = execution.get("driver_capabilities") if isinstance(execution.get("driver_capabilities"), dict) else {}
            top_capabilities = source.get("driver_capabilities") if isinstance(source.get("driver_capabilities"), dict) else {}
            if execution or diagnostics or top_diagnostics or capabilities or top_capabilities:
                merged_diagnostics = dict(top_diagnostics)
                merged_diagnostics.update(diagnostics)
                merged_capabilities = dict(top_capabilities)
                merged_capabilities.update(capabilities)
                return {
                    "origin": execution.get("driver_origin") or merged_diagnostics.get("origin"),
                    "ready": execution.get("driver_ready")
                    if "driver_ready" in execution
                    else merged_diagnostics.get("ready"),
                    "label": execution.get("driver_label") or merged_diagnostics.get("label"),
                    "type": execution.get("driver_type") or merged_diagnostics.get("type"),
                    "path": execution.get("driver_path") or merged_diagnostics.get("path"),
                    "execution_state": execution.get("execution_state") or execution.get("state"),
                    "status": execution.get("status") or execution.get("result"),
                    "printer_status": execution.get("printer_status"),
                    "capabilities": merged_capabilities,
                }
        return {}

    @api.depends("diagnostic_summary", "diagnostic_state")
    def _compute_print_driver_diagnostics(self):
        for record in self:
            snapshot = record._extract_print_driver_snapshot()
            if not snapshot:
                record.print_driver_summary = _("No print driver diagnostics")
                record.print_driver_state_summary = _("No print execution diagnostics recorded yet")
                record.print_driver_polling_summary = _("No polling diagnostics recorded yet")
                continue
            origin = snapshot.get("origin") or _("unknown")
            label = snapshot.get("label") or snapshot.get("type") or _("unnamed driver")
            ready = snapshot.get("ready")
            ready_text = _("driver ready") if ready is True else _("driver not ready") if ready is False else _("driver state unknown")
            state_bits = [ready_text]
            if snapshot.get("execution_state"):
                state_bits.append(_("execution %(state)s") % {"state": snapshot.get("execution_state")})
            if snapshot.get("printer_status"):
                state_bits.append(_("printer %(state)s") % {"state": snapshot.get("printer_status")})
            if snapshot.get("status"):
                state_bits.append(_("result %(state)s") % {"state": snapshot.get("status")})
            caps = snapshot.get("capabilities") or {}
            polling_bits = []
            if caps.get("status_polling_supported") is True:
                polling_bits.append(_("polling supported"))
            elif caps.get("status_polling_supported") is False:
                polling_bits.append(_("polling limited"))
            if caps.get("supports_refresh_status") is True:
                polling_bits.append(_("refresh-status supported"))
            elif caps.get("supports_refresh_status") is False:
                polling_bits.append(_("refresh-status unavailable"))
            if caps.get("supports_status_endpoint") is True:
                polling_bits.append(_("status endpoint ready"))
            elif caps.get("has_status_endpoint_method") is True:
                polling_bits.append(_("status endpoint empty"))
            record.print_driver_summary = _("%(origin)s / %(label)s") % {"origin": origin, "label": label}
            record.print_driver_state_summary = ", ".join(state_bits)
            record.print_driver_polling_summary = ", ".join(polling_bits) if polling_bits else _("No polling diagnostics recorded yet")

    @api.depends("diagnostic_summary", "diagnostic_state")
    def _compute_edge_cache_diagnostics(self):
        for record in self:
            payload = {}
            for source in (record.diagnostic_state, record.diagnostic_summary):
                parsed = record._safe_parse_json(source)
                if parsed:
                    payload = parsed
                    break
            replay = payload.get("replay_summary") if isinstance(payload.get("replay_summary"), dict) else {}
            dead_letter = payload.get("dead_letter_summary") if isinstance(payload.get("dead_letter_summary"), dict) else {}
            edge_diagnostics = payload.get("edge_diagnostics") if isinstance(payload.get("edge_diagnostics"), dict) else {}
            if not replay:
                replay = edge_diagnostics.get("replay") if isinstance(edge_diagnostics.get("replay"), dict) else {}
            if not dead_letter:
                dead_letter = edge_diagnostics.get("dead_letter") if isinstance(edge_diagnostics.get("dead_letter"), dict) else {}
            cache_summary = payload.get("cache_summary") if isinstance(payload.get("cache_summary"), dict) else {}
            if not replay:
                replay = cache_summary.get("outbound_replay") if isinstance(cache_summary.get("outbound_replay"), dict) else {}
            if not dead_letter:
                dead_letter = cache_summary.get("outbound_dead_letter") if isinstance(cache_summary.get("outbound_dead_letter"), dict) else {}
            last_replay_cycle = payload.get("last_outbound_replay_cycle") if isinstance(payload.get("last_outbound_replay_cycle"), dict) else {}
            if not last_replay_cycle:
                last_replay_cycle = edge_diagnostics.get("last_replay_cycle") if isinstance(edge_diagnostics.get("last_replay_cycle"), dict) else {}
            if not last_replay_cycle:
                last_replay_cycle = cache_summary.get("last_outbound_replay_cycle") if isinstance(cache_summary.get("last_outbound_replay_cycle"), dict) else {}
            cycle_digest = last_replay_cycle.get("cycle_digest") if isinstance(last_replay_cycle.get("cycle_digest"), dict) else {}
            record.edge_replay_pending_count = int(replay.get("pending_count") or 0)
            record.edge_replay_due_count = int(replay.get("due_count") or 0)
            record.edge_replay_scheduled_count = int(replay.get("scheduled_count") or 0)
            record.edge_replay_coalesced_count = int(replay.get("coalesced_count") or replay.get("duplicate_count") or 0)
            record.edge_replay_summary = replay.get("summary") or _("pending_count=%s, kinds=none") % (record.edge_replay_pending_count or 0)
            record.edge_last_replay_outcome = str(cycle_digest.get("outcome") or last_replay_cycle.get("outcome") or "").strip()
            if record.edge_last_replay_outcome:
                outcome_label = record.edge_last_replay_outcome.replace("_", " ")
                record.edge_last_replay_summary = _(
                    "%(outcome)s, replayed %(replayed)s, deferred %(deferred)s, coalesced %(coalesced)s"
                ) % {
                    "outcome": outcome_label,
                    "replayed": int(last_replay_cycle.get("replayed_count") or 0),
                    "deferred": int(last_replay_cycle.get("remaining_count") or 0),
                    "coalesced": int(
                        last_replay_cycle.get("replayed_coalesced_count")
                        or last_replay_cycle.get("replayed_duplicate_count")
                        or last_replay_cycle.get("deferred_coalesced_count")
                        or last_replay_cycle.get("deferred_duplicate_count")
                        or record.edge_replay_coalesced_count
                        or 0
                    ),
                }
            else:
                record.edge_last_replay_summary = False
            record.edge_dead_letter_count = int(dead_letter.get("dead_letter_count") or 0)
            record.edge_dead_letter_summary = dead_letter.get("summary") or _("dead_letter_count=%s, kinds=none") % (record.edge_dead_letter_count or 0)

    @api.depends("diagnostic_summary", "diagnostic_state")
    def _compute_edge_protocol_runtime_diagnostics(self):
        def _format_counts(counts):
            if not isinstance(counts, dict) or not counts:
                return ""
            parts = []
            for key in sorted(counts):
                value = counts.get(key)
                if value in (None, "", False):
                    continue
                parts.append(f"{key}={value}")
            return ", ".join(parts)

        for record in self:
            runtime = {}
            for source in (record.diagnostic_state, record.diagnostic_summary):
                payload = record._safe_parse_json(source)
                if not payload:
                    continue
                runtime = payload.get("edge_protocol_runtime") or payload.get("protocol_runtime") or {}
                if not runtime and isinstance(payload.get("edge_diagnostics"), dict):
                    edge_diagnostics = payload.get("edge_diagnostics") or {}
                    runtime = edge_diagnostics.get("protocol_runtime") or {}
                if runtime:
                    break

            runtime = runtime if isinstance(runtime, dict) else {}
            state_counts = record._safe_parse_json(runtime.get("state_counts") or runtime.get("protocol_runtime_state_counts"))
            kind_counts = record._safe_parse_json(runtime.get("kind_counts") or runtime.get("protocol_runtime_kind_counts"))
            count = int(runtime.get("count") or runtime.get("protocol_runtime_count") or 0)
            entry_count = int(runtime.get("entry_count") or runtime.get("protocol_runtime_entry_count") or 0)
            state = str(runtime.get("state") or "unknown").strip().lower() or "unknown"
            summary = runtime.get("summary") or _("No protocol runtime data")
            state_summary = _format_counts(state_counts)
            kind_summary = _format_counts(kind_counts)
            detail_parts = [summary]
            if count or entry_count:
                detail_parts.append(_("%(count)s runtime item(s), %(entries)s entry(ies)") % {"count": count, "entries": entry_count})
            if state_summary:
                detail_parts.append(_("State counts: %(value)s") % {"value": state_summary})
            if kind_summary:
                detail_parts.append(_("Kind counts: %(value)s") % {"value": kind_summary})
            record.edge_protocol_runtime_state = state if state in {"unknown", "ready", "attention", "error"} else "unknown"
            record.edge_protocol_runtime_summary = summary
            record.edge_protocol_runtime_count = count
            record.edge_protocol_runtime_entry_count = entry_count
            record.edge_protocol_runtime_state_counts_summary = state_summary or _("No state counts")
            record.edge_protocol_runtime_kind_counts_summary = kind_summary or _("No kind counts")
            record.edge_protocol_runtime_detail = "\n".join(detail_parts)

    @api.depends("event_ids", "event_ids.event_kind", "event_ids.source_signal", "event_ids.state")
    def _compute_edge_action_stats(self):
        for record in self:
            events = record.event_ids.filtered(
                lambda event: event.event_kind == "signal" and "edge_cache_action" in str(event.source_signal or "").lower()
            )
            pending = events.filtered(lambda event: event.state in {"new", "processing"})
            processing = events.filtered(lambda event: event.state == "processing")
            processed = events.filtered(lambda event: event.state == "processed")
            record.edge_action_count = len(events)
            record.pending_edge_action_count = len(pending)
            record.processing_edge_action_count = len(processing)
            record.processed_edge_action_count = len(processed)
            record.edge_action_summary = _("%(total)s action(s), %(pending)s pending, %(processing)s processing, %(processed)s processed") % {
                "total": record.edge_action_count or 0,
                "pending": record.pending_edge_action_count or 0,
                "processing": record.processing_edge_action_count or 0,
                "processed": record.processed_edge_action_count or 0,
            }

    def _parse_config_json(self):
        self.ensure_one()
        if not self.config_json:
            return {}
        try:
            parsed = json.loads(self.config_json)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _build_capability_payload(self):
        self.ensure_one()
        config = self._parse_config_json()
        adapter_type = self.adapter_type or "generic"
        payload = {
            "adapter_type": adapter_type,
            "supports_push": self.supports_push,
            "supports_poll": self.supports_poll,
            "supports_read": self.supports_read,
            "supports_write": self.supports_write,
            "supports_subscribe": self.supports_subscribe,
            "supports_discovery": self.supports_discovery,
            "supports_ack": self.supports_ack,
            "supports_diagnostics": self.supports_diagnostics,
            "supports_repair": self.supports_repair,
            "supports_reload": self.supports_reload,
            "supports_load": self.supports_load,
            "supports_unload": self.supports_unload,
            "supports_dispatch": self.supports_dispatch,
        }
        payload.update(
            {
                "runtime_unique_id": self.runtime_unique_id,
                "coordinator_mode": self.coordinator_mode,
                "update_interval_seconds": self.update_interval_seconds,
                "retry_after_seconds": self.retry_after_seconds,
                "last_update_success": self.last_update_success,
                "last_exception_class": self.last_exception_class,
                "last_exception_message": self.last_exception_message,
                "last_update_started_at": self.last_update_started_at.isoformat() if self.last_update_started_at else None,
                "last_update_finished_at": self.last_update_finished_at.isoformat() if self.last_update_finished_at else None,
                "last_update_success_at": self.last_update_success_at.isoformat() if self.last_update_success_at else None,
                "last_update_failure_at": self.last_update_failure_at.isoformat() if self.last_update_failure_at else None,
                "first_refresh_required": self.first_refresh_required,
                "always_update": self.always_update,
                "listener_count": self.listener_count,
                "dispatch_state": self.dispatch_state,
                "listener_state": self.listener_state,
                "lifecycle_checkpoint": self.lifecycle_checkpoint,
                "last_dispatch_at": self.last_dispatch_at.isoformat() if self.last_dispatch_at else None,
                "last_listener_sync_at": self.last_listener_sync_at.isoformat() if self.last_listener_sync_at else None,
                "last_listener_cleanup_at": self.last_listener_cleanup_at.isoformat() if self.last_listener_cleanup_at else None,
                "timeout_seconds": self.timeout_seconds,
                "heartbeat_timeout_seconds": self.heartbeat_timeout_seconds,
                "reconnect_policy": self.reconnect_policy,
                "reconnect_attempts": self.reconnect_attempts,
                "max_reconnect_attempts": self.max_reconnect_attempts,
                "health_state": self.health_state,
                "health_score": self.health_score,
                "last_error": self.last_error,
                "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
                "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            }
        )
        if config:
            payload["config_flags"] = config
        return payload

    def _build_capability_summary(self, capabilities):
        flags = []
        for key, label in (
            ("supports_poll", "poll"),
            ("supports_push", "push"),
            ("supports_read", "read"),
            ("supports_write", "write"),
            ("supports_subscribe", "subscribe"),
            ("supports_discovery", "discovery"),
            ("supports_ack", "ack"),
            ("supports_diagnostics", "diagnostics"),
            ("supports_repair", "repair"),
            ("supports_reload", "reload"),
            ("supports_load", "load"),
            ("supports_unload", "unload"),
        ):
            if capabilities.get(key):
                flags.append(label)
        if not flags:
            return "No capabilities declared"
        return ", ".join(flags)

    def _build_lifecycle_payload(self, capabilities):
        self.ensure_one()
        if not self.active or self.state == "disabled":
            return "disabled", "Adapter is disabled"
        if self.dispatch_state == "error" or self.listener_state == "error":
            return "degraded", self.last_error or "Runtime coordination reported an error"
        if self.dispatch_state == "paused" or self.listener_state == "suspended":
            return "degraded", "Runtime coordination is paused"
        if self.health_state == "offline" or self.state == "offline":
            return "offline", self.last_error or "Adapter is offline"
        if self.health_state in {"warning", "degraded"} or self.state == "degraded":
            return "degraded", self.last_error or "Adapter needs attention"
        if not self.connection_target and not self.config_json:
            return "draft", "Adapter is not configured yet"
        if capabilities.get("supports_poll") or capabilities.get("supports_push"):
            return "ready", "Adapter is ready for runtime coordination"
        return "configuring", "Adapter is being configured"

    def _runtime_mark_action(self, action_name, values):
        self.ensure_one()
        values = dict(values or {})
        values.setdefault("health_state", self.health_state)
        values.setdefault("diagnostic_summary", self.diagnostic_summary)
        self.write(values)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Gateway Runtime"),
                "message": action_name,
                "type": "success",
                "sticky": False,
            },
        }

    def _runtime_service_notification(self, result, *, success_title=None, failure_title=None, next_action=None):
        self.ensure_one()
        result = result or {}
        message_payload = result.get("message") if isinstance(result, dict) else {}
        if not isinstance(message_payload, dict):
            message_payload = {}
        ok = bool(result.get("ok"))
        errors = result.get("errors") if isinstance(result, dict) else []
        if not isinstance(errors, list):
            errors = [str(errors)] if errors else []
        message_text = (
            message_payload.get("text")
            or ", ".join(str(item) for item in errors if item)
            or _("Runtime request processed")
        )
        notification_type = message_payload.get("type") or ("success" if ok else "warning")
        params = {
            "title": success_title if ok else failure_title or success_title or _("Gateway Runtime"),
            "message": message_text,
            "type": notification_type,
            "sticky": not ok,
        }
        if ok and next_action:
            params["next"] = next_action
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": params,
        }

    def action_mark_ready(self):
        return self._runtime_mark_action(
            _("Adapter marked ready"),
            {
                "state": "ready",
                "health_state": "healthy",
                "dispatch_state": "active",
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "last_error": False,
                "last_exception_class": False,
                "last_exception_message": False,
                "lifecycle_checkpoint": "ready",
            },
        )

    def action_mark_disabled(self):
        return self._runtime_mark_action(
            _("Adapter disabled"),
            {
                "state": "disabled",
                "health_state": "offline",
                "dispatch_state": "paused",
                "listener_state": "suspended" if self.supports_subscribe else "idle",
                "listener_count": 0,
                "listener_contract_json": False,
                "last_listener_cleanup_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "disabled",
            },
        )

    def action_refresh_diagnostics(self):
        service = GatewayRuntimeService(self.env)
        self.write({"last_reload_at": fields.Datetime.now()})
        return service.refresh_adapter_diagnostics(adapter_code=self.code if len(self) == 1 else None)

    def _issue_defaults(self):
        self.ensure_one()
        if self.health_state in {"offline", "degraded"}:
            severity = "high"
            issue_kind = "repair"
            recommended_action = _("Reload the adapter, then inspect connectivity and recent runtime events.")
            recommended_action_key = "reload_runtime"
            is_fixable = True
            state = "open"
        elif self.health_state in {"warning"}:
            severity = "medium"
            issue_kind = "diagnostic"
            recommended_action = _("Refresh diagnostics and review the latest heartbeat or event trail.")
            recommended_action_key = "refresh_runtime"
            is_fixable = True
            state = "new"
        else:
            severity = "low"
            issue_kind = "diagnostic"
            recommended_action = _("Review the runtime summary and clear the issue when verified.")
            recommended_action_key = "review_runtime"
            is_fixable = False
            state = "new"
        return {
            "name": f"{self.code} issue",
            "adapter_id": self.id,
            "severity": severity,
            "state": state,
            "issue_kind": issue_kind,
            "issue_key": f"runtime:{self.code}:{issue_kind}",
            "is_fixable": is_fixable,
            "recommended_action_key": recommended_action_key,
            "message": self.health_detail or self.last_error or _("Runtime issue detected"),
            "detail": self.diagnostic_summary or self.diagnostic_state or self.capability_summary or "",
            "recommended_action": recommended_action,
            "payload_json": json.dumps(
                {
                    "adapter": {
                        "code": self.code,
                        "name": self.name,
                        "state": self.state,
                        "adapter_type": self.adapter_type,
                        "health_state": self.health_state,
                        "health_score": self.health_score,
                    },
                    "capability": self._build_capability_payload(),
                },
                ensure_ascii=False,
                default=str,
            ),
            "last_seen_at": fields.Datetime.now(),
        }

    def action_open_issues(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Runtime Issues"),
            "res_model": "gateway.runtime.issue",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id)],
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }

    def action_open_driver_issues(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Driver Issues"),
            "res_model": "gateway.runtime.issue",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id), ("issue_key", "=", f"runtime:{self.code}:driver_diagnostic")],
            "context": {
                "default_adapter_id": self.id,
                "search_default_adapter_id": self.id,
                "search_default_open": 1,
            },
        }

    def action_open_edge_cache_issues(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Edge Cache Issues"),
            "res_model": "gateway.runtime.issue",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", self.id),
                "|",
                ("issue_key", "=", f"runtime:{self.code}:edge_dead_letter"),
                ("issue_key", "=", f"runtime:{self.code}:edge_replay"),
            ],
            "context": {
                "default_adapter_id": self.id,
                "search_default_adapter_id": self.id,
                "search_default_open": 1,
            },
        }

    def action_open_edge_actions(self):
        self.ensure_one()
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_edge_action").read()[0]
        action["domain"] = [
            ("adapter_id", "=", self.id),
            ("event_kind", "=", "signal"),
            ("source_signal", "ilike", "edge_cache_action"),
        ]
        context = action.get("context")
        if not isinstance(context, dict):
            context = {}
        action["context"] = {
            **context,
            "search_default_edge_actions": 1,
            "search_default_adapter_id": self.id,
            "default_adapter_id": self.id,
        }
        return action

    def action_open_protocol_runtime_issues(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Protocol Runtime Issues"),
            "res_model": "gateway.runtime.issue",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id), ("issue_key", "ilike", ":protocol_runtime")],
            "context": {
                "default_adapter_id": self.id,
                "search_default_adapter_id": self.id,
                "search_default_open": 1,
                "search_default_protocol_runtime_issues": 1,
            },
        }

    def action_open_protocol_runtime_console(self):
        self.ensure_one()
        return self.action_open_console()

    def action_open_protocol_runtime_probe(self):
        self.ensure_one()
        return self.action_open_protocol_probe()

    def action_request_edge_replay(self):
        self.ensure_one()
        service = GatewayRuntimeService(self.env)
        result = service.request_edge_cache_action(
            {
                "adapter_code": self.code,
                "entry_code": self.entry_id.code if self.entry_id else False,
                "workstation_code": self.workstation_id.code if self.workstation_id else False,
                "action": "replay",
            }
        )
        return self._runtime_service_notification(
            result,
            success_title=_("Edge Replay Requested"),
            failure_title=_("Edge Replay Request Failed"),
            next_action=self.action_open_edge_cache_issues(),
        )

    def action_review_edge_dead_letter(self):
        self.ensure_one()
        service = GatewayRuntimeService(self.env)
        result = service.request_edge_cache_action(
            {
                "adapter_code": self.code,
                "entry_code": self.entry_id.code if self.entry_id else False,
                "workstation_code": self.workstation_id.code if self.workstation_id else False,
                "action": "review_dead_letter",
            }
        )
        return self._runtime_service_notification(
            result,
            success_title=_("Edge Dead-Letter Review Requested"),
            failure_title=_("Edge Dead-Letter Review Request Failed"),
            next_action=self.action_open_edge_cache_issues(),
        )

    def action_open_repairs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Runtime Repairs"),
            "res_model": "gateway.runtime.issue",
            "view_mode": "list,form",
            "domain": [
                ("adapter_id", "=", self.id),
                ("is_fixable", "=", True),
                ("state", "in", ["new", "open", "in_progress"]),
            ],
            "context": {
                "default_adapter_id": self.id,
                "search_default_adapter_id": self.id,
                "search_default_fixable": 1,
                "search_default_open": 1,
            },
        }

    def action_open_console(self):
        self.ensure_one()
        action = self.env.ref("mrp_gateway_runtime.action_gateway_runtime_console").read()[0]
        action["domain"] = [("id", "=", self.id)]
        action["name"] = _("Runtime Console")
        return action

    def action_open_protocol_probe(self):
        self.ensure_one()
        action = self.env.ref("mrp_gateway_runtime.action_gateway_protocol_probe").read()[0]
        action["domain"] = [("id", "=", self.id)]
        action["name"] = _("Protocol Probe")
        return action

    def action_open_attention_route(self):
        self.ensure_one()
        if self.open_edge_cache_issue_count:
            return self.action_open_edge_cache_issues()
        if self.pending_edge_action_count:
            return self.action_open_edge_actions()
        if self.open_protocol_runtime_issue_count:
            return self.action_open_protocol_runtime_issues()
        if self.open_driver_issue_count:
            return self.action_open_driver_issues()
        if self.open_issue_count:
            if self.repair_issue_count:
                return self.action_open_repairs()
            return self.action_open_issues()
        if self.open_probe_session_count or self.probe_focus_state == "attention":
            return self.action_open_probe_sessions()
        if self.health_state in {"warning", "degraded", "offline"} or self.state in {"degraded", "offline"}:
            return self.action_open_console()
        return self.action_open_console()

    def _protocol_probe_open_action(self, model_name, title):
        self.ensure_one()
        if model_name not in self.env.registry.models:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": title,
                    "message": _("Linked protocol module is not installed"),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": model_name,
            "view_mode": "list,form",
            "domain": [("runtime_adapter_id", "=", self.id)],
            "context": {"default_runtime_adapter_id": self.id, "search_default_runtime_adapter_id": self.id},
        }

    def action_open_mqtt_probe(self):
        return self._protocol_probe_open_action("gateway.mqtt.adapter", _("MQTT Probe"))

    def action_open_modbus_probe(self):
        return self._protocol_probe_open_action("gateway.modbus.adapter", _("Modbus Probe"))

    def action_open_ads_probe(self):
        return self._protocol_probe_open_action("gateway.ads.adapter", _("ADS Probe"))

    def action_open_opcua_probe(self):
        return self._protocol_probe_open_action("gateway.opcua.adapter", _("OPC UA Probe"))

    def action_open_s7_probe(self):
        return self._protocol_probe_open_action("gateway.s7.adapter", _("S7 Probe"))

    def action_open_probe_sessions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Probe Sessions"),
            "res_model": "gateway.runtime.probe.session",
            "view_mode": "list,form",
            "domain": [("adapter_id", "=", self.id)],
            "context": {"default_adapter_id": self.id, "search_default_adapter_id": self.id},
        }

    def action_start_probe_session(self):
        self.ensure_one()
        result = GatewayRuntimeService(self.env).create_probe_session({"adapter_code": self.code, "probe_kind": "summary"})
        if not result.get("ok"):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Probe Session"),
                    "message": ", ".join(result.get("errors", ["Probe session could not be created"])),
                    "type": "warning",
                    "sticky": False,
                },
            }
        session_data = result.get("data") or {}
        session_id = session_data.get("id")
        if session_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Probe Session"),
                "res_model": "gateway.runtime.probe.session",
                "view_mode": "form",
                "res_id": session_id,
                "target": "current",
            }
        return self.action_open_probe_sessions()

    def action_create_issue(self):
        self.ensure_one()
        values = self._issue_defaults()
        issue = self.env["gateway.runtime.issue"].sudo().search([("issue_key", "=", values["issue_key"])], limit=1)
        if issue:
            issue.write(values)
        else:
            issue = self.env["gateway.runtime.issue"].sudo().create(values)
        return {
            "type": "ir.actions.act_window",
            "name": _("Runtime Issue"),
            "res_model": "gateway.runtime.issue",
            "view_mode": "form",
            "res_id": issue.id,
            "target": "current",
        }

    def action_load_adapter(self):
        self.ensure_one()
        service = GatewayRuntimeService(self.env)
        self.write(
            {
                "dispatch_state": "active",
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "loaded",
            }
        )
        return service.load_runtime({"adapter_code": self.code})

    def action_unload_adapter(self):
        self.ensure_one()
        service = GatewayRuntimeService(self.env)
        self.write(
            {
                "dispatch_state": "paused",
                "listener_state": "suspended" if self.supports_subscribe else "idle",
                "listener_contract_json": False,
                "last_listener_cleanup_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "unloaded",
            }
        )
        return service.unload_runtime({"adapter_code": self.code})

    def action_trigger_reconnect(self):
        service = GatewayRuntimeService(self.env)
        self.write(
            {
                "last_repair_at": fields.Datetime.now(),
                "reconnect_attempts": 0 if self.reconnect_policy == "manual" else self.reconnect_attempts + 1,
                "dispatch_state": "active",
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "health_state": "warning",
                "lifecycle_checkpoint": "reconnect_requested",
            }
        )
        return service.request_adapter_reconnect(adapter_code=self.code if len(self) == 1 else None)

    def action_mark_offline(self):
        return self._runtime_mark_action(
            _("Adapter marked offline"),
            {
                "state": "offline",
                "health_state": "offline",
                "dispatch_state": "error",
                "listener_state": "error" if self.supports_subscribe else "idle",
                "last_listener_cleanup_at": fields.Datetime.now(),
                "last_failure_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "offline",
            },
        )

    def action_reload_adapter(self):
        self.write(
            {
                "last_reload_at": fields.Datetime.now(),
                "dispatch_state": "active",
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "reloaded",
            }
        )
        return self.action_refresh_diagnostics()

    def action_repair_adapter(self):
        self.write(
            {
                "last_repair_at": fields.Datetime.now(),
                "dispatch_state": "active",
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "health_state": "warning",
                "lifecycle_checkpoint": "repair_requested",
            }
        )
        return self.action_trigger_reconnect()

    def action_pause_dispatch(self):
        return self._runtime_mark_action(
            _("Runtime dispatch paused"),
            {
                "dispatch_state": "paused",
                "listener_state": "suspended" if self.supports_subscribe else self.listener_state,
                "health_state": "warning",
                "last_listener_cleanup_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "dispatch_paused",
            },
        )

    def action_resume_dispatch(self):
        return self._runtime_mark_action(
            _("Runtime dispatch resumed"),
            {
                "dispatch_state": "active",
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "dispatch_resumed",
            },
        )

    def action_sync_listeners(self):
        contract = {
            "adapter_code": self.code if len(self) == 1 else False,
            "listener_count": self.listener_count,
            "supports_subscribe": self.supports_subscribe,
            "supports_dispatch": self.supports_dispatch,
            "coordinator_mode": self.coordinator_mode,
        }
        return self._runtime_mark_action(
            _("Runtime listeners synchronized"),
            {
                "listener_state": "attached" if self.supports_subscribe else "idle",
                "last_dispatch_at": fields.Datetime.now(),
                "last_listener_sync_at": fields.Datetime.now(),
                "listener_contract_json": json.dumps(contract, ensure_ascii=False, default=str),
                "dispatch_contract_json": json.dumps(contract, ensure_ascii=False, default=str),
                "lifecycle_checkpoint": "listeners_synced",
            },
        )

    def action_cleanup_listeners(self):
        return self._runtime_mark_action(
            _("Runtime listeners cleaned up"),
            {
                "listener_state": "idle",
                "listener_count": 0,
                "listener_contract_json": False,
                "last_listener_cleanup_at": fields.Datetime.now(),
                "lifecycle_checkpoint": "listeners_cleaned",
            },
        )

    def action_simulate_poll(self):
        service = GatewayRuntimeService(self.env)
        return service.simulate_coordinator_poll(adapter_code=self.code if len(self) == 1 else None)

    def cron_process_queued_commands(self):
        service = GatewayRuntimeService(self.env)
        return service.process_queued_commands()

    def cron_refresh_diagnostics(self):
        service = GatewayRuntimeService(self.env)
        return service.refresh_adapter_diagnostics()

    def cron_repair_stale_adapters(self):
        service = GatewayRuntimeService(self.env)
        return service.repair_stale_adapters()

    def action_register_adapter(self):
        service = GatewayRuntimeService(self.env)
        return service.register_adapter_definition(
            {
                "code": self.code,
                "name": self.name,
                "adapter_type": self.adapter_type,
                "entry_code": self.entry_id.code if self.entry_id else None,
                "workstation_code": self.workstation_id.code if self.workstation_id else None,
                "device_code": self.device_code,
                "connection_target": self.connection_target,
                "config_json": self.config_json,
                "config_text": self.config_text,
            }
        )
