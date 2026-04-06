import hashlib
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


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
    merge_target_id = fields.Many2one("gateway.device", string="Merge Target", ondelete="set null", index=True)
    merged_into_id = fields.Many2one("gateway.device", string="Merged Into", ondelete="set null", readonly=True, index=True)
    merge_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preview", "Preview"),
            ("merged", "Merged"),
            ("conflict", "Conflict"),
        ],
        string="Merge State",
        default="draft",
        required=True,
        index=True,
    )
    merge_note = fields.Text(string="Merge Note")
    merge_preview_json = fields.Text(string="Merge Preview", readonly=True)
    merge_snapshot_json = fields.Text(string="Merge Snapshot", readonly=True)
    merged_at = fields.Datetime(string="Merged At", readonly=True)
    merged_by = fields.Many2one("res.users", string="Merged By", readonly=True, ondelete="set null")
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
    merge_summary = fields.Char(compute="_compute_device_profile", readonly=True)
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
        base_domain = [
            ("id", "!=", record.id),
            ("entry_id", "=", record.entry_id.id),
            ("active", "=", True),
            ("state", "!=", "disabled"),
            ("merge_state", "!=", "merged"),
            ("merged_into_id", "=", False),
        ]
        for domain in self._registry_match_domain(record):
            candidates |= self.search(base_domain + domain, limit=limit)
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

    def _merge_managed_fields(self):
        return (
            "device_uid",
            "external_ref",
            "protocol",
            "address",
            "device_type",
            "workstation_ref",
            "app_ref",
        )

    def _merge_snapshot_values(self, record):
        record.ensure_one()
        return {
            "id": record.id,
            "code": record.code,
            "name": record.name,
            "active": record.active,
            "state": record.state,
            "lifecycle_state": record.lifecycle_state,
            "discovery_state": record.discovery_state,
            "capability_state": record.capability_state,
            "point_sync_state": record.point_sync_state,
            "subscription_state": record.subscription_state,
            "probe_ready": record.probe_ready,
            "change_kind": record.change_kind,
            "state_version": record.state_version,
            "config_binding": record.config_binding,
            "last_transition_at": record.last_transition_at,
            "identifiers_json": record.identifiers_json,
            "connections_json": record.connections_json,
            "device_type": record.device_type,
            "workstation_ref": record.workstation_ref,
            "app_ref": record.app_ref,
            "external_ref": record.external_ref,
            "device_uid": record.device_uid,
            "protocol": record.protocol,
            "address": record.address,
            "parent_device_id": record.parent_device_id.id if record.parent_device_id else False,
            "merge_target_id": record.merge_target_id.id if record.merge_target_id else False,
            "merged_into_id": record.merged_into_id.id if record.merged_into_id else False,
            "merge_state": record.merge_state,
            "merge_note": record.merge_note,
            "merge_preview_json": record.merge_preview_json,
            "merged_at": record.merged_at,
            "merged_by": record.merged_by.id if record.merged_by else False,
            "disabled_by": record.disabled_by,
            "source_signal": record.source_signal,
            "source_payload_id": record.source_payload_id,
            "probe_session_id": record.probe_session_id,
            "config_json": record.config_json,
            "config_text": record.config_text,
            "diagnostic_state": record.diagnostic_state,
            "child_device_ids": record.child_device_ids.ids,
            "signal_ids": record.signal_ids.ids,
            "command_ids": record.command_ids.ids,
        }

    def _merge_conflict_payload(self, source, target):
        field_conflicts = {}
        field_fill = {}
        for field_name in self._merge_managed_fields():
            source_value = getattr(source, field_name)
            target_value = getattr(target, field_name)
            if source_value and target_value and source_value != target_value:
                field_conflicts[field_name] = {
                    "source": source_value,
                    "target": target_value,
                }
            elif source_value and not target_value:
                field_fill[field_name] = source_value

        parent_conflict = bool(source.parent_device_id and target.parent_device_id and source.parent_device_id != target.parent_device_id)
        if source.parent_device_id and not target.parent_device_id and source.parent_device_id != target:
            field_fill["parent_device_id"] = source.parent_device_id.id

        child_codes = {code for code in source.child_device_ids.mapped("code") if code}
        child_conflicts = target.child_device_ids.filtered(lambda child: child.code in child_codes)

        guard_reasons = []
        if not target.active:
            guard_reasons.append(_("Target device is inactive."))
        if target.state == "disabled":
            guard_reasons.append(_("Target device is disabled."))
        if target.merge_state == "merged":
            guard_reasons.append(_("Target device has already been merged."))
        if target.merge_state == "conflict":
            guard_reasons.append(_("Target device is already in merge conflict state."))
        if target.id == source.id:
            guard_reasons.append(_("A device cannot be merged into itself."))
        if source.merge_state == "merged":
            guard_reasons.append(_("This device has already been merged into another device."))
        if not source.entry_id or source.entry_id != target.entry_id:
            guard_reasons.append(_("The source device and target device must belong to the same gateway entry."))
        if parent_conflict:
            guard_reasons.append(_("The source and target parent devices do not match."))

        relationship_conflicts = {
            "target_is_child": target in source.child_device_ids,
            "child_parent_conflicts": child_conflicts.mapped("code"),
            "parent_conflict": parent_conflict,
        }
        if relationship_conflicts["target_is_child"]:
            guard_reasons.append(_("The target device is already a child of the source device."))
        if relationship_conflicts["child_parent_conflicts"]:
            guard_reasons.append(
                _("Child device conflict(s): %(codes)s")
                % {"codes": ", ".join(relationship_conflicts["child_parent_conflicts"])}
            )
        if field_conflicts:
            conflict_bits = [
                _("%(field)s: %(source)s != %(target)s")
                % {
                    "field": field_name,
                    "source": conflict["source"],
                    "target": conflict["target"],
                }
                for field_name, conflict in field_conflicts.items()
            ]
            guard_reasons.append(_("Field conflict(s): %(details)s") % {"details": "; ".join(conflict_bits)})

        return {
            "field_fill": field_fill,
            "field_conflicts": field_conflicts,
            "relationship_conflicts": relationship_conflicts,
            "guard_reasons": guard_reasons,
            "can_execute": not guard_reasons,
        }

    def _merge_preview_message(self, preview):
        target = preview.get("target", {})
        target_code = target.get("code") or _("unknown")
        if preview["can_execute"]:
            return {
                "message": _("Merge preview prepared for %(target)s.") % {"target": target_code},
                "type": "success",
                "sticky": False,
            }
        conflict_bits = preview["conflict_summary"]
        return {
            "message": _("Merge preview prepared for %(target)s, but conflicts must be resolved first: %(details)s")
            % {"target": target_code, "details": "; ".join(conflict_bits)},
            "type": "warning",
            "sticky": True,
        }

    def _merge_restore_values(self, snapshot):
        values = {
            "active": snapshot.get("active"),
            "state": snapshot.get("state"),
            "lifecycle_state": snapshot.get("lifecycle_state"),
            "discovery_state": snapshot.get("discovery_state"),
            "capability_state": snapshot.get("capability_state"),
            "point_sync_state": snapshot.get("point_sync_state"),
            "subscription_state": snapshot.get("subscription_state"),
            "probe_ready": snapshot.get("probe_ready"),
            "change_kind": snapshot.get("change_kind"),
            "state_version": snapshot.get("state_version"),
            "config_binding": snapshot.get("config_binding"),
            "last_transition_at": snapshot.get("last_transition_at"),
            "identifiers_json": snapshot.get("identifiers_json"),
            "connections_json": snapshot.get("connections_json"),
            "device_type": snapshot.get("device_type"),
            "workstation_ref": snapshot.get("workstation_ref"),
            "app_ref": snapshot.get("app_ref"),
            "external_ref": snapshot.get("external_ref"),
            "device_uid": snapshot.get("device_uid"),
            "protocol": snapshot.get("protocol"),
            "address": snapshot.get("address"),
            "parent_device_id": snapshot.get("parent_device_id") or False,
            "merge_target_id": snapshot.get("merge_target_id") or False,
            "merged_into_id": snapshot.get("merged_into_id") or False,
            "merge_state": snapshot.get("merge_state"),
            "merge_note": snapshot.get("merge_note"),
            "merge_preview_json": snapshot.get("merge_preview_json"),
            "merged_at": snapshot.get("merged_at"),
            "merged_by": snapshot.get("merged_by") or False,
            "disabled_by": snapshot.get("disabled_by"),
            "source_signal": snapshot.get("source_signal"),
            "source_payload_id": snapshot.get("source_payload_id"),
            "probe_session_id": snapshot.get("probe_session_id"),
            "config_json": snapshot.get("config_json"),
            "config_text": snapshot.get("config_text"),
            "diagnostic_state": snapshot.get("diagnostic_state"),
        }
        return values

    def _ensure_merge_target_ready(self, target):
        if not target:
            raise UserError(_("Select a merge target before previewing or executing a merge."))
        preview = self._merge_conflict_payload(self, target)
        if target.id == self.id:
            raise UserError(_("A gateway device cannot be merged into itself."))
        return preview

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
        "merge_target_id",
        "merged_into_id",
        "merge_state",
        "merge_note",
        "merge_preview_json",
        "merged_at",
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
            if record.merge_state == "merged" and record.merged_into_id:
                record.merge_summary = _("Merged into %(target)s at %(when)s") % {
                    "target": record.merged_into_id.code,
                    "when": record.merged_at or _("unknown time"),
                }
            elif record.merge_state == "conflict":
                record.merge_summary = _("Merge preview has conflicts and cannot be executed")
            elif record.merge_state == "preview":
                record.merge_summary = _("Merge preview is ready for target %(target)s") % {
                    "target": record.merge_target_id.code if record.merge_target_id else _("unknown"),
                }
            elif record.merge_target_id:
                record.merge_summary = _("Merge target %(target)s is prepared") % {
                    "target": record.merge_target_id.code,
                }
            elif record.merge_note:
                record.merge_summary = _("Merge note is available")
            else:
                record.merge_summary = _("No merge action prepared")

    def _merge_json_values(self, left_value, right_value):
        left_value = self._load_json(left_value)
        right_value = self._load_json(right_value)
        if isinstance(left_value, dict) and isinstance(right_value, dict):
            merged = dict(left_value)
            for key, value in right_value.items():
                if key not in merged or merged[key] in (None, False, "", [], {}):
                    merged[key] = value
                    continue
                if merged[key] == value:
                    continue
                existing = merged[key]
                if not isinstance(existing, list):
                    existing = [existing]
                extras = value if isinstance(value, list) else [value]
                serialized = {json.dumps(item, ensure_ascii=False, default=str, sort_keys=True) for item in existing}
                for extra in extras:
                    marker = json.dumps(extra, ensure_ascii=False, default=str, sort_keys=True)
                    if marker not in serialized:
                        existing.append(extra)
                        serialized.add(marker)
                merged[key] = existing
            return merged
        items = []
        for collection in (left_value, right_value):
            if isinstance(collection, (list, tuple, set)):
                items.extend(collection)
            elif collection not in (None, False, "", {}, []):
                items.append(collection)
        deduplicated = []
        seen = set()
        for item in items:
            marker = json.dumps(item, ensure_ascii=False, default=str, sort_keys=True)
            if marker in seen:
                continue
            seen.add(marker)
            deduplicated.append(item)
        return deduplicated

    def _build_merge_preview(self, target):
        self.ensure_one()
        if not target:
            raise UserError(_("Select a merge target before previewing or executing a merge."))
        conflicts = self._merge_conflict_payload(self, target)
        source_child_codes = {code for code in self.child_device_ids.mapped("code") if code}
        conflicting_children = target.child_device_ids.filtered(lambda child: child.code in source_child_codes)
        payload = {
            "source": {"id": self.id, "code": self.code, "name": self.name},
            "target": {"id": target.id, "code": target.code, "name": target.name},
            "source_snapshot": self._merge_snapshot_values(self),
            "target_snapshot": self._merge_snapshot_values(target),
            "signals_to_move": len(self.signal_ids),
            "commands_to_move": len(self.command_ids),
            "children_to_rebind": len(self.child_device_ids),
            "identifier_count": len(self._merge_json_values(target.identifiers_json, self.identifiers_json)),
            "connection_count": len(self._merge_json_values(target.connections_json, self.connections_json)),
            "field_fill": conflicts["field_fill"],
            "field_conflicts": conflicts["field_conflicts"],
            "conflicts": {
                "child_parent_conflicts": conflicting_children.mapped("code"),
                "target_is_child": conflicts["relationship_conflicts"]["target_is_child"],
                "relationship_conflicts": conflicts["relationship_conflicts"],
                "guard_reasons": conflicts["guard_reasons"],
            },
            "can_execute": conflicts["can_execute"],
        }
        payload["conflict_summary"] = conflicts["guard_reasons"]
        return payload

    def action_preview_merge(self):
        self.ensure_one()
        preview = self._build_merge_preview(self.merge_target_id)
        preview_message = self._merge_preview_message(preview)
        self.write(
            {
                "merge_state": "conflict" if not preview["can_execute"] else "preview",
                "merge_preview_json": json.dumps(preview, ensure_ascii=False, default=str, indent=2),
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Gateway Device"),
                "message": preview_message["message"],
                "type": preview_message["type"],
                "sticky": preview_message["sticky"],
            },
        }

    def action_execute_merge(self):
        self.ensure_one()
        target = self.merge_target_id
        preview = self._build_merge_preview(target)
        if not preview["can_execute"]:
            raise UserError(_("Resolve merge conflicts in the preview before executing the merge: %(details)s") % {
                "details": "; ".join(preview["conflict_summary"]),
            })
        source_snapshot = self._merge_snapshot_values(self)
        target_snapshot = self._merge_snapshot_values(target)
        moved_signal_ids = self.signal_ids.ids
        moved_command_ids = self.command_ids.ids
        moved_child_ids = self.child_device_ids.ids
        merged_identifiers = self._merge_json_values(target.identifiers_json, self.identifiers_json)
        merged_connections = self._merge_json_values(target.connections_json, self.connections_json)
        timestamp = fields.Datetime.now()
        audit_note = self.merge_note or _("Merged %(source)s into %(target)s") % {
            "source": self.code,
            "target": target.code,
        }
        target_values = {
            "identifiers_json": json.dumps(merged_identifiers, ensure_ascii=False, default=str),
            "connections_json": json.dumps(merged_connections, ensure_ascii=False, default=str),
            "state_version": int(target.state_version or 0) + 1,
            "change_kind": "identity",
            "last_transition_at": timestamp,
            "changed_fields_json": json.dumps(
                {
                    "merged_from": self.code,
                    "signals_moved": len(self.signal_ids),
                    "commands_moved": len(self.command_ids),
                    "children_rebound": len(self.child_device_ids),
                },
                ensure_ascii=False,
                default=str,
            ),
        }
        for field_name in ("external_ref", "device_uid", "protocol", "address", "device_type", "workstation_ref", "app_ref"):
            if getattr(self, field_name) and not getattr(target, field_name):
                target_values[field_name] = getattr(self, field_name)
        if self.parent_device_id and not target.parent_device_id and self.parent_device_id != target:
            target_values["parent_device_id"] = self.parent_device_id.id
        target.write(target_values)
        self.signal_ids.write({"device_id": target.id})
        self.command_ids.write({"device_id": target.id})
        self.child_device_ids.filtered(lambda child: child != target).write({"parent_device_id": target.id})
        self.write(
            {
                "active": False,
                "state": "disabled",
                "lifecycle_state": "removed",
                "discovery_state": "removed",
                "change_kind": "topology",
                "merged_into_id": target.id,
                "merge_state": "merged",
                "merge_preview_json": json.dumps(preview, ensure_ascii=False, default=str, indent=2),
                "merge_snapshot_json": json.dumps(
                    {
                        "source": source_snapshot,
                        "target": target_snapshot,
                        "moved": {
                            "signal_ids": moved_signal_ids,
                            "command_ids": moved_command_ids,
                            "child_device_ids": moved_child_ids,
                        },
                    },
                    ensure_ascii=False,
                    default=str,
                    indent=2,
                ),
                "merge_note": audit_note,
                "merged_at": timestamp,
                "merged_by": self.env.user.id,
                "config_binding": f"merged:{target.code}",
                "last_transition_at": timestamp,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Merged Gateway Device"),
            "res_model": "gateway.device",
            "view_mode": "form",
            "res_id": target.id,
            "target": "current",
        }

    def action_revert_merge(self):
        self.ensure_one()
        if self.merge_state != "merged" or not self.merged_into_id:
            raise UserError(_("Only merged devices can be reverted."))
        if not self.merge_snapshot_json:
            raise UserError(_("No merge snapshot is available for rollback."))

        snapshot = self._load_json(self.merge_snapshot_json)
        source_snapshot = snapshot.get("source") or {}
        target_snapshot = snapshot.get("target") or {}
        moved = snapshot.get("moved") or {}
        target = self.merged_into_id

        if source_snapshot.get("id") != self.id:
            raise UserError(_("Merge rollback aborted because the source snapshot no longer matches this record."))
        if target_snapshot.get("id") != target.id:
            raise UserError(_("Merge rollback aborted because the target device no longer matches the stored snapshot."))

        signal_ids = moved.get("signal_ids") or []
        command_ids = moved.get("command_ids") or []
        child_ids = moved.get("child_device_ids") or []

        if signal_ids:
            self.env["gateway.signal"].browse(signal_ids).write({"device_id": self.id})
        if command_ids:
            self.env["gateway.command"].browse(command_ids).write({"device_id": self.id})
        if child_ids:
            self.env["gateway.device"].browse(child_ids).write({"parent_device_id": self.id})

        target.write(self._merge_restore_values(target_snapshot))
        self.write(
            {
                **self._merge_restore_values(source_snapshot),
                "merge_target_id": source_snapshot.get("merge_target_id") or False,
                "merged_into_id": False,
                "merge_state": "draft",
                "merge_note": _("Merge reverted from %(target)s") % {"target": target.code},
                "merge_preview_json": False,
                "merge_snapshot_json": False,
                "merged_at": False,
                "merged_by": False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Reverted Gateway Device"),
            "res_model": "gateway.device",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_open_merge_target(self):
        self.ensure_one()
        if not self.merge_target_id:
            raise UserError(_("Select a merge target before opening it."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Merge Target"),
            "res_model": "gateway.device",
            "view_mode": "form",
            "res_id": self.merge_target_id.id,
            "target": "current",
        }

    def action_mark_ready(self):
        if self.merge_state == "merged":
            raise UserError(_("Revert the merge before changing the device state."))
        if self.merge_state == "conflict":
            raise UserError(_("Resolve the merge preview conflicts before changing the device state."))
        self.write({"state": "ready"})

    def action_mark_disabled(self):
        if self.merge_state == "merged":
            raise UserError(_("Revert the merge before changing the device state."))
        if self.merge_state == "conflict":
            raise UserError(_("Resolve the merge preview conflicts before changing the device state."))
        self.write({"state": "disabled"})

    def action_clear_parent_binding(self):
        self.ensure_one()
        if self.merge_state == "merged":
            raise UserError(_("Revert the merge before changing the device topology."))
        if self.merge_state == "conflict":
            raise UserError(_("Resolve the merge preview conflicts before changing the device topology."))
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

    @api.constrains("entry_id", "merge_target_id", "merged_into_id", "merge_state", "active", "state")
    def _check_merge_integrity(self):
        for record in self:
            if record.merge_target_id:
                if record.merge_target_id == record:
                    raise ValidationError(_("A gateway device cannot be merged into itself."))
                if record.entry_id and record.merge_target_id.entry_id != record.entry_id:
                    raise ValidationError(_("Merge target must belong to the same gateway entry."))
                if not record.merge_target_id.active:
                    raise ValidationError(_("Merge target must be active."))
                if record.merge_target_id.state == "disabled":
                    raise ValidationError(_("Merge target cannot be disabled."))
                if record.merge_target_id.merge_state == "merged":
                    raise ValidationError(_("Merge target cannot already be merged."))
            if record.merge_state == "merged":
                if not record.merged_into_id:
                    raise ValidationError(_("Merged devices must keep a merged target reference."))
                if not record.merge_snapshot_json:
                    raise ValidationError(_("Merged devices must keep a merge snapshot for rollback."))
            if record.merged_into_id and record.merge_state != "merged":
                raise ValidationError(_("Merged target references are only allowed for merged devices."))
            if record.merge_state in ("preview", "conflict") and not record.merge_target_id:
                raise ValidationError(_("Merge previews and conflicts must keep a merge target."))

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
