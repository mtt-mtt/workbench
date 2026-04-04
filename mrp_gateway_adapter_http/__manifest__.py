{
    "name": "MRP Gateway Adapter HTTP",
    "version": "19.0.0.1.0",
    "category": "Manufacturing/Configuration",
    "author": "OpenAI",
    "summary": "HTTP bridge module for runtime gateway pushes and heartbeats",
    "license": "LGPL-3",
    "depends": ["mrp_gateway_runtime"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/http_bridge_actions.xml",
        "views/http_bridge_menus.xml",
        "views/http_bridge_views.xml",
        "views/http_endpoint_views.xml",
    ],
    "application": False,
    "installable": True,
}
