from odoo import http
from odoo.http import request

from ..services.mqtt_bridge_service import GatewayMqttBridgeService


class GatewayMqttController(http.Controller):
    @http.route(
        "/mrp_gateway_adapter_mqtt/topic_event",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def topic_event(self, **payload):
        return GatewayMqttBridgeService(request.env).ingest_topic_event(payload)

    @http.route(
        "/mrp_gateway_adapter_mqtt/topic_heartbeat",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def topic_heartbeat(self, **payload):
        return GatewayMqttBridgeService(request.env).ingest_topic_heartbeat(payload)

    @http.route(
        "/mrp_gateway_adapter_mqtt/sync_adapter",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def sync_adapter(self, **payload):
        return GatewayMqttBridgeService(request.env).register_adapter_from_payload(payload)
