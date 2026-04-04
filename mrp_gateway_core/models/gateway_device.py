import hashlib
import json

from odoo import api, fields, models, _


class GatewayDevice(models.Model):
    _name = "gateway.device"
    _description = "Gateway Device"
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
    entry_id = fields.Many2one("gateway.entry", string="Gateway Entry", ondelete="cascade", required=True)
    parent_device_id = fields.Many2one("gateway.device", string="Parent Device", ondelete="set null", index=True)
    via_device_id = fields.Many2one("gateway.device", string="Via Device", related="parent_device_id", readonly=True)
    device_type = fields.Char(string="Device Type")
    workstation_ref = fields.Char(string="Workstation Ref")
    app_ref = fields.Char(string="App Ref")
    external_ref = fields.Char(string="External Ref")
    device_uid = fields.Char(string="Device UID", index=True)
    disabled_by = fields.Char(string="Disabled By")
    protocol = fields.Char(string="Protocol")
    address = fields.Char(string="Address")
    identifiers_json = fields.Text(string="Identifiers JSON")
    connections_json = fields.Text(string="Connections JSON")
    lifecycle_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("discovered", "Discovered"),
            ("bound", "Bound"),
            ("ready", "Ready"),
            ("degraded", "Degraded"),
            ("offline", "Offline"),
            ("removed", "Removed"),
            ("disabled", "Disabled"),
        ],
        string="Lifecycle State",
        default="draft",
        required=True,
        index=True,
    )
    config_binding = fields.Char(string="Config Binding")
    change_kind = fields.Selection(
        [
            ("identity", "Identity"),
            ("topology", "Topology"),
            ("state", "State"),
            ("probe", "Probe"),
        ],
        string="Last Change Kind",
        default="state",
        required=True,
        index=True,
    )
    changed_fields_json = fields.Text(string="Changed Fields JSON")
    source_signal = fields.Char(string="Source Signal", index=True)
    source_payload_id = fields.Char(string="Source Payload ID", index=True)
    state_version = fields.Integer(string="State Version", default=0)
    probe_session_id = fields.Char(string="Probe Session ID", index=True)
    discovery_state = fields.Selection(
        [
            ("discovered", "Discovered"),
            ("bound", "Bound"),
            ("enriched", "Enriched"),
            ("ready", "Ready"),
            ("removed", "Removed"),
        ],
        string="Discovery State",
        default="discovered",
        required=True,
        index=True,
    )
    capability_state = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("pending", "Pending"),
            ("partial", "Partial"),
            ("ready", "Ready"),
            ("error", "Error"),
        ],
        string="Capability State",
        default="unknown",
        required=True,
        index=True,
    )
    point_sync_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("synced", "Synced"),
            ("stale", "Stale"),
            ("error", "Error"),
        ],
        string="Point Sync State",
        default="pending",
        required=True,
        index=True,
    )
    subscription_state = fields.Selection(
        [
            ("idle", "Idle"),
            ("requested", "Requested"),
            ("subscribed", "Subscribed"),
            ("paused", "Paused"),
            ("error", "Error"),
        ],
        string="Subscription State",
        default="idle",
        required=True,
        index=True,
    )
    probe_ready = fields.Boolean(string="Probe Ready", default=False)
    last_transition_at = fields.Datetime(string="Last Transition At")
    config_json = fields.Text(string="Config JSON")
    config_text = fields.Text(string="Config Text")
    diagnostic_state = fields.Text(string="Diagnostic State")
    last_seen_at = fields.Datetime(string="Last Seen At")
    identifier_count = fields.Integer(compute="_compute_device_profile", readonly=True)
    connection_count = fields.Integer(compute="_compute_device_profile", readonly=True)
    registry_summary = fields.Char(compute="_compute_device_profile", readonly=True)
    registry_fingerprint = fields.Char(compute="_compute_device_profile", readonly=True)
    registry_match_count = fields.Integer(compute="_compute_device_profile", readonly=True)
    registry_match_basis = fields.Char(compute="_compute_device_profile", readonly=True)
    registry_match_summary = fields.Char(compute="_compute_device_profile", readonly=True)
    binding_state = fields.Selection(
        [
            ("unbound", "Unbound"),
            ("bound", "Bound"),
            ("parent", "Parent"),
            ("orphan", "Orphan"),
            ("disabled", "Disabled"),
        ],
        compute="_compute_device_profile",
        readonly=True,
        index=True,
    )
    device_summary = fields.Char(compute="_compute_device_profile", readonly=True)
    topology_summary = fields.Char(compute="_compute_device_profile", readonly=True)
    signal_count = fields.Integer(compute="_compute_device_profile", readonly=True)
    command_count = fields.Integer(compute="_compute_device_profile", readonly=True)
    child_device_ids = fields.One2many("gateway.device", "parent_device_id", string="Child Devices", readonly=True)
    signal_ids = fields.One2many("gateway.signal", "device_id", string="Signals")
    command_ids = fields.One2many("gateway.command", "device_id", string="Commands")

    _gateway_device_code_uniq = models.Constraint(
        "UNIQUE(code)",
        "Gateway device code must be unique.",
    )

    def _load_json(self, value):
        if value in (None, False, ""):
            return {}
        if isinstance(value, (dict, list, tuple)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {"raw": value}
        return value

    def _count_json_items(self, value):
        value = self._load_json(value)
        if isinstance(value, dict):
            return len(value)
        if isinstance(value, (list, tuple, set)):
            return len(value)
        return 0

    def _registry_fingerprint_value(self, record):
        payload = {
            "code": record.code,
            "entry": record.entry_id.code if record.entry_id else None,
            "parent": record.parent_device_id.code if record.parent_device_id else None,
            "device_uid": record.device_uid,
            "identifiers": self._load_json(record.identifiers_json),
            "connections": self._load_json(record.connections_json),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        return hashlib.sha1(raw).hexdigest()[:16]

    def _registry_match_domain(self, record):
        if not record.entry_id:
            return []
        domains = []
        if record.device_uid:
            domains.append([("device_uid", "=", record.device_uid)])
        if record.external_ref:
            domains.append([("external_ref", "=", record.external_ref)])
        if record.protocol and record.address:
            domains.append([("protocol", "=", record.protocol), ("address", "=", record.address)])
        if record.parent_device_id:
            domains.append([("parent_device_id", "=", record.parent_device_id.id)])
        return domains

    def _registry_match_records(self, record, limit=10):
        if not record.entry_id:
            return self.browse()
        candidates = self.browse()
        for domain in self._registry_match_domain(record):
            candidates |= self.search([("id", "!=", record.id), ("entry_id", "=", record.entry_id.id)] + domain, limit=limit)
        return candidates[:limit]

    def _registry_match_hints(self, record):
        hints = []
        if record.device_uid:
            hints.append(_("Device UID"))
        if record.external_ref:
            hints.append(_("External Ref"))
        if record.protocol and record.address:
            hints.append(_("Protocol + Address"))
        if record.parent_device_id:
            hints.append(_("Parent Device"))
        return hints

    @api.depends(
        "active",
        "state",
        "protocol",
        "device_type",
        "address",
        "external_ref",
        "lifecycle_state",
        "change_kind",
        "discovery_state",
        "capability_state",
        "point_sync_state",
        "subscription_state",
        "probe_ready",
        "state_version",
        "parent_device_id",
        "child_device_ids",
        "child_device_ids.active",
        "child_device_ids.state",
        "child_device_ids.last_seen_at",
        "signal_ids",
        "command_ids",
        "identifiers_json",
        "connections_json",
        "last_seen_at",
        "device_uid",
        "external_ref",
        "protocol",
        "address",
        "parent_device_id",
    )
    def _compute_device_profile(self):
        for record in self:
            signal_count = len(record.signal_ids)
            command_count = len(record.command_ids)
            child_count = len(record.child_device_ids)
            if not record.active or record.state == "disabled":
                binding_state = "disabled"
            elif record.parent_device_id:
                binding_state = "bound"
            elif child_count:
                binding_state = "parent"
            elif record.identifiers_json or record.connections_json or record.external_ref:
                binding_state = "bound"
            else:
                binding_state = "unbound"
            if not record.active and record.state != "disabled":
                binding_state = "orphan" if child_count or signal_count or command_count else "unbound"
            record.binding_state = binding_state
            record.identifier_count = record._count_json_items(record.identifiers_json)
            record.connection_count = record._count_json_items(record.connections_json)
            record.signal_count = signal_count
            record.command_count = command_count
            record.device_summary = " · ".join(
                part
                for part in (
                    record.protocol or _("Generic"),
                    record.device_type or _("Device"),
                    record.address or record.external_ref or _("Local"),
                )
                if part
            )
            record.topology_summary = _("%(children)s child device(s), %(signals)s signal(s), %(commands)s command(s), v%(version)s") % {
                "children": child_count,
                "signals": signal_count,
                "commands": command_count,
                "version": record.state_version or 0,
            }
            record.registry_summary = _("%(identifiers)s identifier(s), %(connections)s connection(s), via %(via)s") % {
                "identifiers": record.identifier_count,
                "connections": record.connection_count,
                "via": record.parent_device_id.code if record.parent_device_id else _("direct"),
            }
            record.registry_fingerprint = record._registry_fingerprint_value(record)
            matches = record._registry_match_records(record, limit=10)
            record.registry_match_count = len(matches)
            hints = record._registry_match_hints(record)
            record.registry_match_basis = _("No duplicate detection hints")
            if hints:
                record.registry_match_basis = _("%(count)s duplicate hint(s): %(names)s") % {
                    "count": len(hints),
                    "names": ", ".join(hints),
                }
            record.registry_match_summary = _("No potential duplicate candidates")
            if matches:
                record.registry_match_summary = _("%(count)s potential duplicate candidate(s): %(names)s") % {
                    "count": len(matches),
                    "names": ", ".join(matches.mapped("code")[:3]),
                }

    def action_mark_ready(self):
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        self.write({"state": "disabled"})

    def action_clear_parent_binding(self):
        self.ensure_one()
        self.write(
            {
                "parent_device_id": False,
                "change_kind": "topology",
                "discovery_state": "discovered",
                "last_transition_at": fields.Datetime.now(),
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Gateway Device"),
                "message": _("Parent binding cleared."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_open_registry_matches(self):
        self.ensure_one()
        if not self._registry_match_domain(self):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Gateway Device"),
                    "message": _("No duplicate detection hints are available for this device."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        matches = self._registry_match_records(self, limit=10)
        if not matches:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Gateway Device"),
                    "message": _("No potential duplicate candidates are available for this device."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Potential Duplicate Candidates"),
            "res_model": "gateway.device",
            "view_mode": "list,form",
            "domain": [("id", "in", matches.ids)],
            "context": {"search_default_entry_id": self.entry_id.id},
        }

    def action_open_signals(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Gateway Signals"),
            "res_model": "gateway.signal",
            "view_mode": "list,form",
            "domain": [("device_id", "=", self.id)],
            "context": {"default_device_id": self.id, "search_default_device_id": self.id},
        }

    def action_open_commands(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Gateway Commands"),
            "res_model": "gateway.command",
            "view_mode": "list,form",
            "domain": [("device_id", "=", self.id)],
            "context": {"default_device_id": self.id, "search_default_device_id": self.id},
        }

    def action_open_children(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Child Devices"),
            "res_model": "gateway.device",
            "view_mode": "list,form",
            "domain": [("parent_device_id", "=", self.id)],
            "context": {"default_parent_device_id": self.id, "search_default_parent_device_id": self.id},
        }

    def action_open_parent(self):
        self.ensure_one()
        if not self.parent_device_id:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Gateway Device"),
                    "message": _("This device has no parent device."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Parent Device"),
            "res_model": "gateway.device",
            "view_mode": "form",
            "res_id": self.parent_device_id.id,
        }
