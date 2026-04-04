from odoo import http
from odoo.http import request

from ..services.execution_service import ShopfloorExecutionService


class ShopfloorExecutionController(http.Controller):
    @http.route(
        "/mrp_shopfloor_execution/boot",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def boot(self, **payload):
        service = ShopfloorExecutionService(request.env)
        return service.boot_payload(payload)

    @http.route(
        "/mrp_shopfloor_execution/action",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def action(self, **payload):
        service = ShopfloorExecutionService(request.env)
        return service.apply_action(payload)

    @http.route(
        "/mrp_shopfloor_execution/state",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def state(self, **payload):
        service = ShopfloorExecutionService(request.env)
        return service.state_payload(payload)

    @http.route(
        "/mrp_shopfloor_execution/exception",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def exception(self, **payload):
        service = ShopfloorExecutionService(request.env)
        return service.report_exception(payload)
