# -*- coding: utf-8 -*-
{
    "name": "MRP Shopfloor Frontend",
    "version": "19.0.0.1.0",
    "category": "Manufacturing",
    "summary": "Frontend shell for the Shopfloor SPA V0.1",
    "license": "LGPL-3",
    "author": "OpenAI",
    "website": "",
    "depends": ["web", "mrp", "mrp_shopfloor_core", "mrp_shopfloor_execution"],
    "data": [
        "views/mrp_shopfloor_frontend_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mrp_shopfloor_frontend/static/src/app/**/*",
        ],
    },
    "application": True,
    "installable": True,
}
