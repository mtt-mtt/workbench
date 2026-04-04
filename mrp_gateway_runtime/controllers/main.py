from odoo import http
from odoo.http import request

from ..services.runtime_service import GatewayRuntimeService


class GatewayRuntimeController(http.Controller):
    @http.route(
        "/mrp_gateway_runtime/heartbeat",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def heartbeat(self, **payload):
        return GatewayRuntimeService(request.env).ingest_heartbeat(payload)

    @http.route(
        "/mrp_gateway_runtime/event",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def event(self, **payload):
        return GatewayRuntimeService(request.env).ingest_event(payload)

    @http.route(
        "/mrp_gateway_runtime/diagnostic",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def diagnostic(self, **payload):
        return GatewayRuntimeService(request.env).runtime_diagnostics(payload)

    @http.route(
        "/mrp_gateway_runtime/capability",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def capability(self, **payload):
        return {
            "ok": True,
            "data": GatewayRuntimeService(request.env).build_capability_payload(payload=payload),
            "message": {"type": "success", "text": "Runtime capability ready"},
        }

    @http.route(
        "/mrp_gateway_runtime/refresh",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def refresh(self, **payload):
        return GatewayRuntimeService(request.env).refresh_runtime(payload)

    @http.route(
        "/mrp_gateway_runtime/repair",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def repair(self, **payload):
        return GatewayRuntimeService(request.env).repair_runtime(payload)

    @http.route(
        "/mrp_gateway_runtime/load",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def load(self, **payload):
        return GatewayRuntimeService(request.env).load_runtime(payload)

    @http.route(
        "/mrp_gateway_runtime/unload",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def unload(self, **payload):
        return GatewayRuntimeService(request.env).unload_runtime(payload)

    @http.route(
        "/mrp_gateway_runtime/reload",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def reload(self, **payload):
        return GatewayRuntimeService(request.env).reload_runtime(payload)

    @http.route(
        "/mrp_gateway_runtime/dispatch",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def dispatch(self, **payload):
        return GatewayRuntimeService(request.env).dispatch_runtime_signal(payload)
