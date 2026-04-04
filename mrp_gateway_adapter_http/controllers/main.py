import json

from odoo import http
from odoo.http import request

from ..services.bridge_service import GatewayHttpBridgeService


class GatewayHttpAdapterController(http.Controller):
    def _payload(self):
        data = request.httprequest.get_json(silent=True)
        if isinstance(data, dict):
            data = dict(data)
            data.setdefault("bridge_code", request.httprequest.headers.get("X-HTTP-Bridge-Code"))
            data.setdefault("bridge_key", request.httprequest.headers.get("X-HTTP-Bridge-Key"))
            data.setdefault("bridge_secret", request.httprequest.headers.get("X-HTTP-Bridge-Secret"))
            data.setdefault("endpoint_code", request.httprequest.headers.get("X-HTTP-Endpoint-Code"))
            return data
        params = dict(request.params or {})
        params.setdefault("bridge_code", request.httprequest.headers.get("X-HTTP-Bridge-Code"))
        params.setdefault("bridge_key", request.httprequest.headers.get("X-HTTP-Bridge-Key"))
        params.setdefault("bridge_secret", request.httprequest.headers.get("X-HTTP-Bridge-Secret"))
        params.setdefault("endpoint_code", request.httprequest.headers.get("X-HTTP-Endpoint-Code"))
        if params:
            return params
        return {}

    def _service(self):
        return GatewayHttpBridgeService(request.env)

    def _json_response(self, payload, status=200):
        return request.make_json_response(payload, status=status)

    @http.route(
        "/mrp_gateway_adapter_http/push",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def push(self, **kwargs):
        payload = self._payload()
        payload.update(kwargs)
        result = self._service().push_payload(payload)
        status = 200 if result.get("ok") else result.get("status", 400)
        return self._json_response(result, status=status)

    @http.route(
        "/mrp_gateway_adapter_http/heartbeat",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def heartbeat(self, **kwargs):
        payload = self._payload()
        payload.update(kwargs)
        result = self._service().heartbeat_payload(payload)
        status = 200 if result.get("ok") else result.get("status", 400)
        return self._json_response(result, status=status)
