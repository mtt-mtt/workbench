from odoo import http
from odoo.http import request

from ..services.modbus_service import GatewayModbusService


class GatewayModbusController(http.Controller):
    @http.route(
        "/mrp_gateway_adapter_modbus/register_snapshot",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def register_snapshot(self, **payload):
        return GatewayModbusService(request.env).ingest_register_snapshot(payload)

    @http.route(
        "/mrp_gateway_adapter_modbus/write_ack",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def write_ack(self, **payload):
        return GatewayModbusService(request.env).ingest_write_ack(payload)
