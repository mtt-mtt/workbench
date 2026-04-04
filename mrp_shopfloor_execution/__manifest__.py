{
    "name": "MRP Shopfloor Execution",
    "version": "19.0.0.1.0",
    "category": "Manufacturing",
    "summary": "Execution transactions and service layer for Shopfloor operations",
    "license": "LGPL-3",
    "author": "OpenAI",
    "depends": ["mrp", "mrp_shopfloor_core"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/shopfloor_execution_views.xml",
    ],
    "installable": True,
    "application": False,
}
