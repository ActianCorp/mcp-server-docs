# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.

"""Demo extension: human-in-the-loop (HITL) approval before a write.

Shows the opt-in confirmation gate. `request_write_confirmation()` presents the
proposed change to the user over the MCP elicitation protocol and returns True
only on explicit approval; a decline / cancel / timeout / no-context all return
False (fail-closed). The framework does NOT prompt automatically — the extension
decides when and what to confirm, then writes only if approval came back True.

Requires the server in read-write mode for the actual write.
Expected schema: products(product_id, name, stock_qty) — see order_ops.py.
"""

import json

from actian_mcp_server.extension_api import (
    get_current_user,
    get_database,
    request_write_confirmation,
)


def register(server, config):
    products_t = config.get("products_table", "products")

    @server.tool(name="adjust_stock")
    async def adjust_stock(product_id: int, delta: int) -> str:
        """Adjust a product's stock by `delta`, but only after a human approves.

        The tool asks for confirmation first; it performs the UPDATE only if the
        user explicitly approves. If they decline (or don't respond), nothing is
        written.
        """
        approved = await request_write_confirmation(
            description=f"Adjust stock for product {product_id} by {delta:+d}",
            details={"table": products_t, "product_id": product_id,
                     "delta": delta, "requested_by": get_current_user()},
        )
        if not approved:
            # No approval came back: the user declined, or the client can't show
            # the prompt (some MCP clients don't support elicitation). Fail closed.
            return json.dumps({"success": False, "status": "cancelled",
                               "reason": "write not approved (declined, or this client "
                                         "cannot show an approval prompt)"})

        # Writes go through a transaction (a single write is a one-statement txn).
        async with get_database().transaction() as tx:
            res = await tx.write(
                f"UPDATE {products_t} SET stock_qty = stock_qty + ? WHERE product_id = ?",
                [delta, product_id])
            if res["row_count"] == 0:
                return json.dumps({"success": False, "error": f"product {product_id} does not exist"})
            new = await tx.query(
                f"SELECT name, stock_qty FROM {products_t} WHERE product_id = ?", [product_id])
        name, new_stock = new["rows"][0]
        return json.dumps({"success": True, "status": "applied", "product_id": product_id,
                           "product": name, "delta": delta, "new_stock": new_stock},
                          default=str)
