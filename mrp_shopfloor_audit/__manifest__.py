{
    "name": "MRP Shopfloor Audit",
    "version": "19.0.0.1.0",
    "category": "Manufacturing",
    "summary": "Audit trail for Shopfloor actions and gateway commands",
    "license": "LGPL-3",
    "author": "OpenAI",
    "depends": ["mrp", "mrp_shopfloor_core"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/shopfloor_audit_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
