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
- First protocol adapters for `HTTP / MQTT / Modbus / OPC UA / S7 / ADS`
- Audit trail and runtime event chain

## Known Boundaries

This repository is not yet a production release.

Remaining work is planned for `V0.2`, including:

- `gateway.device` merge actions for `identifiers / connections`
- duplicate device conflict handling
- fuller dispatcher / listener lifecycle
- real protocol read/write and reconnect validation
- weak-network and offline recovery hardening
- terminal interaction polish

