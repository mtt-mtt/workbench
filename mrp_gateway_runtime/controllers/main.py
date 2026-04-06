import json

from odoo import http
from odoo.http import request

from ..services.runtime_service import GatewayRuntimeService


class GatewayRuntimeController(http.Controller):
    def _edge_gateway_payload(self, payload=None):
        data = dict(payload or {})
        httprequest = getattr(request, "httprequest", None)
        if httprequest is None:
            return data
        json_payload = None
        try:
            json_payload = httprequest.get_json(silent=True)
        except TypeError:
            try:
                json_payload = httprequest.get_json()
            except Exception:
                json_payload = None
        except Exception:
            json_payload = None
        if isinstance(json_payload, dict):
            if isinstance(json_payload.get("params"), dict) and "jsonrpc" in json_payload:
                data.update(json_payload["params"])
                return data
            data.update(json_payload)
        elif isinstance(getattr(request, "jsonrequest", None), dict):
            json_request = dict(request.jsonrequest)
            if isinstance(json_request.get("params"), dict) and "jsonrpc" in json_request:
                data.update(json_request["params"])
                return data
            data.update(request.jsonrequest)
        elif getattr(httprequest, "form", None):
            data.update(httprequest.form.to_dict())
        elif getattr(httprequest, "args", None):
            data.update(httprequest.args.to_dict())
        nested_payload = data.get("payload")
        if isinstance(nested_payload, dict):
            flattened = dict(nested_payload)
            for key, value in data.items():
                if key == "payload":
                    continue
                flattened.setdefault(key, value)
            data = flattened
        return data

    def _edge_gateway_json_response(self, payload):
        body = json.dumps(payload, ensure_ascii=False, default=str)
        return request.make_response(body, headers=[("Content-Type", "application/json; charset=utf-8")])

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
        "/edge_gateway/heartbeat",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_heartbeat(self, **payload):
        payload = self._edge_gateway_payload(payload)
        return self._edge_gateway_json_response(GatewayRuntimeService(request.env).ingest_heartbeat(payload))

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
        "/edge_gateway/event",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_event(self, **payload):
        payload = self._edge_gateway_payload(payload)
        return self._edge_gateway_json_response(GatewayRuntimeService(request.env).ingest_event(payload))

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
        "/edge_gateway/register",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_register(self, **payload):
        return GatewayRuntimeService(request.env).register_adapter_definition(payload)

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

    @http.route(
        "/edge_gateway/command",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_command(self, **payload):
        payload = self._edge_gateway_payload(payload)
        return self._edge_gateway_json_response(GatewayRuntimeService(request.env).fetch_gateway_command(payload))

    @http.route(
        "/edge_gateway/command_ack",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_command_ack(self, **payload):
        payload = self._edge_gateway_payload(payload)
        return self._edge_gateway_json_response(GatewayRuntimeService(request.env).acknowledge_gateway_command(payload))

    @http.route(
        "/edge_gateway/actions",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_actions(self, **payload):
        payload = self._edge_gateway_payload(payload)
        return self._edge_gateway_json_response(GatewayRuntimeService(request.env).fetch_edge_actions(payload))

    @http.route(
        "/edge_gateway/action_ack",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def edge_gateway_action_ack(self, **payload):
        payload = self._edge_gateway_payload(payload)
        return self._edge_gateway_json_response(GatewayRuntimeService(request.env).acknowledge_edge_action(payload))
