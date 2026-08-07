# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.

"""Demo extension: read-only catalog analytics.

A second, simpler customer-authored extension showing the read side of the API:
plain queries via get_database().query(), the extension's own scoped config, and
the authenticated identity. It performs no writes, so it works in the default
read-only mode (no ``query_mode`` needed).

Expected schema: products(product_id, name, unit_price, stock_qty) — same table as order_ops.
"""

import json

from actian_mcp_server.extension_api import get_current_user, get_database


def register(server, config):
    products_t = config.get("products_table", "products")
    default_threshold = int(config.get("low_stock_threshold", 10))

    @server.tool(name="low_stock_products")
    async def low_stock_products(threshold: int = default_threshold) -> str:
        """List products at or below a stock threshold (read-only)."""
        res = await get_database().query(
            f"SELECT product_id, name, stock_qty FROM {products_t} "
            f"WHERE stock_qty <= ? ORDER BY stock_qty",
            [int(threshold)])
        if not res["success"]:
            return json.dumps(res, default=str)
        return json.dumps({
            "success": True,
            "threshold": int(threshold),
            "products": [{"product_id": r[0], "name": r[1], "stock_qty": r[2]}
                         for r in res["rows"]],
            "checked_by": get_current_user(),  # None unless OAuth + impersonation
        }, default=str)

    @server.tool(name="inventory_value")
    async def inventory_value() -> str:
        """Aggregate stock across the catalog (read-only)."""
        res = await get_database().query(
            f"SELECT COUNT(*) AS products, SUM(stock_qty) AS total_units FROM {products_t}")
        if not res["success"]:
            return json.dumps(res, default=str)
        row = res["rows"][0]
        return json.dumps({"success": True, "products": row[0], "total_units": row[1]},
                          default=str)
