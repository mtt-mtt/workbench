# Odoo 19 Shopfloor + Device Gateway Modules

This repository contains the local Odoo 19 modules for the Shopfloor and device gateway stack.

## Status

- Version: `V0.1`
- Positioning: internal baseline / integration build
- Odoo target: `19.0`

## Module Layout

### Shopfloor

- `mrp_shopfloor_core`
- `mrp_shopfloor_execution`
- `mrp_shopfloor_frontend`
- `mrp_shopfloor_audit`

### Gateway

- `mrp_gateway_core`
- `mrp_gateway_runtime`
- `mrp_gateway_adapter_http`
- `mrp_gateway_adapter_mqtt`
- `mrp_gateway_adapter_modbus`
- `mrp_gateway_adapter_opcua`
- `mrp_gateway_adapter_s7`
- `mrp_gateway_adapter_ads`

### Meta Module

- `mrp_shopfloor`

`mrp_shopfloor` is a meta module. It is intentionally lightweight and exists to install the full V0.1 stack in one step.

## Installation

Add this repository path to the Odoo `addons_path`, update the apps list, then install:

- `MRP Shopfloor`

Or upgrade from command line:

```powershell
.\.venv\Scripts\python.exe .\src\odoo\odoo-bin -c .\odoo.conf -d Workbench1 --stop-after-init -u mrp_shopfloor
```

## Current Scope

The current baseline includes:

- Shopfloor SPA shell and execution flow
- Gateway runtime, diagnostics, repairs, issues, and probe sessions
- Protocol runtime shells, first adapters, and a unified `adapter_type -> protocol runtime shell` assembly entry for `HTTP / MQTT / Modbus / OPC UA / S7 / ADS`, now also aligned through `RuntimeManager`
- Protocol runtime summaries now begin flowing into edge diagnostics, heartbeat payloads, platform serialization, and shopfloor operator panels, so edge-side `state / counts / summary` is no longer only visible locally
- Shopfloor operator surfaces now also normalize and show `edge_protocol_runtime*` in dashboard, workspace shell, and nav rail, so protocol runtime state can be read without opening the raw adapter record
- Platform adapter views now also surface `edge_protocol_runtime_state / edge_protocol_runtime_summary / edge_protocol_runtime_count`, so the operator can inspect protocol runtime visibility directly from `gateway.runtime.adapter`
- Protocol runtime `attention / issue routing` now also feeds the platform operator path, so `attention_route_summary`, `console_attention_summary`, and the runtime issue views can jump straight to the right adapter or issue instead of leaving protocol runtime attention mixed into generic driver diagnostics
- Protocol runtime event semantics now also flow into execution/timeline/notice, and the current round 80 baseline keeps that wording explicit, so `recent_runtime_activity`, `timeline`, and the panel notice can show protocol runtime state changes as first-class runtime updates rather than generic events
- Protocol runtime dedupe/merge semantics now also collapse repeated execution/store updates into a single activity/timeline entry, so identical protocol runtime state changes do not keep refreshing the operator stream
- Protocol runtime shared KPI semantics now also flow into dashboard overview tiles, shared metrics, workspace/nav attention labels, dashboard status panel, inspector response card, and panel notice, all of which now prefer `protocolRuntimeAttention` before falling back to local state counts, so protocol runtime state can be read consistently from the common frontend shell instead of only from isolated cards
- The current round 85 baseline continues that direction into boot / log surfaces, especially `buildIdleResponseSummary`, `buildIdleGatewayRuntimeSummary`, and `buildLogEntries`, while still keeping the wording explicit that this is shared summary propagation rather than real protocol linkage completion
- The current round 86 baseline continues that direction into seed timeline / activity fallback surfaces, especially `buildSeedTimelineEntries()` and the `createShopfloorStore()` seed/fallback assembly path, while still keeping the wording explicit that this is shared summary propagation rather than real protocol linkage completion
- The current round 87 baseline continues that direction into operator feedback detail surfaces, especially `dashboard_status_panel`, `execution_detail_panel`, `queue_detail`, `device_detail`, `exception_card`, and `exception_actions`, while still keeping the wording explicit that this is shared summary propagation rather than real protocol linkage completion
- The current round 88 baseline continues that direction into compact preview surfaces, especially `dashboard_latest_execution` and `execution_log_preview`, which now prefer structured protocol runtime entries over ad-hoc title matching, while still keeping the wording explicit that this is shared summary propagation rather than real protocol linkage completion
- The current round 89 baseline continues that direction into log/timeline companion surfaces, especially `device_action_log`, `dashboard_status_panel`, `dashboard_latest_execution`, and `execution_log_preview`, while still keeping the wording explicit that this is shared summary propagation rather than real protocol linkage completion
- The current round 90 baseline continues that direction into inspector card and detail feed surfaces, especially `shopfloor_inspector`, `shopfloor_timeline_card`, `shopfloor_activity_card`, `devices_screen`, `queue_screen`, `execution_detail_panel`, `exceptions_screen`, `device_detail`, and `queue_detail`, which now prefer shared protocol runtime feedback and structured `protocol-runtime / protocol_runtime` entries before falling back to generic runtime summaries or empty-state wording
- Audit trail and runtime event chain

## Known Boundaries

This repository is not yet a production release.

Remaining work for `V0.2` is now focused on:

- formal bring-up and validation for the protocol runtime registry/factory, runtime host, and runtime manager assembly, followed by full protocol validation for `HTTP / MQTT / Modbus / OPC UA / ADS / S7`
- continue the bring-up path for protocol runtime summary visibility and issue/attention routing in edge diagnostics / heartbeat / platform serialization / shopfloor frontend, while keeping the current baseline wording and not claiming real protocol linkage completion yet
- continue the bring-up path for protocol runtime event semantics in execution/timeline/notice, while keeping the current baseline wording and not claiming real protocol linkage completion yet
- continue the bring-up path for protocol runtime shared summary semantics across response summary / timeline / KPI surfaces, payload / fallback utility surfaces, boot / log surfaces, seed timeline / activity fallback surfaces, operator feedback detail surfaces, compact preview surfaces, log/timeline companion surfaces, and inspector card surfaces, while keeping the current baseline wording and not claiming real protocol linkage completion yet
- final field verification of offline recovery, replay visibility, and diagnostics flows
- edge and terminal polish around operator-facing summaries, acknowledgements, and exceptions
- closing any remaining printer / barcode integration gaps in the package-weight flow
