{
    "name": "MRP Shopfloor Core",
    "version": "19.0.0.1.0",
    "category": "Manufacturing",
    "summary": "Core shopfloor configuration models for manufacturing execution",
    "author": "OpenAI",
    "license": "LGPL-3",
    "depends": ["base", "mrp"],
    "data": [
        "security/ir.model.access.csv",
        "data/shopfloor_demo_data.xml",
        "views/shopfloor_core_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
