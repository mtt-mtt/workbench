/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ShopfloorFrontendAction } from "./shopfloor_app";

export const SHOPFLOOR_CLIENT_ACTION = "mrp_shopfloor_frontend.client_action";

registry.category("actions").add(SHOPFLOOR_CLIENT_ACTION, ShopfloorFrontendAction);
