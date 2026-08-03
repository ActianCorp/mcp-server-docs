# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

"""Demo extension: order processing with multi-table transactions.

A customer-authored MCP extension that uses ONLY the public extension_api — no
framework internals, no connection handling. It is mounted into a running
container as a volume (see this folder's README.md) and referenced by module name
in conf.json. Requires the server in read-write mode (``"query_mode": "read-write"``).

The point of this example is a single tool call that changes SEVERAL tables
atomically inside one transaction: INSERT + INSERT + UPDATE + DELETE all commit
together, or none of them do. The tools take only natural inputs and look up the
rest themselves (price, stock, the next order id), and return tidy results.

Expected schema (table names are configurable — see register()):
    products(product_id PK, name, unit_price, stock_qty)
    orders(order_id PK, customer_id, status, total)
    order_items(order_id, product_id, qty, line_total, PK(order_id, product_id))
    cart(customer_id, product_id, qty, PK(customer_id, product_id))
"""

import json

from actian_mcp_server.extension_api import get_current_user, get_database


def register(server, config):
    """Register the order tools. `config` is this extension's scoped settings."""
    orders_t = config.get("orders_table", "orders")
    items_t = config.get("order_items_table", "order_items")
    products_t = config.get("products_table", "products")
    cart_t = config.get("cart_table", "cart")

    @server.tool(name="place_order")
    async def place_order(customer_id: int, product_id: int, quantity: int) -> str:
        """Place an order for `quantity` units of a product.

        You only supply who is ordering, what, and how much — the tool looks up
        the product's price and available stock, assigns the next order id, and
        computes the total. It then writes FOUR tables in one transaction:
        INSERT the order header, INSERT the line item, decrement stock, and clear
        the item from the customer's cart. Either all succeed or none do.
        """
        if quantity <= 0:
            return json.dumps({"success": False, "error": "quantity must be a positive number"})

        db = get_database()
        # Look up price + stock (read; no order id or price from the caller).
        prod = await db.query(
            f"SELECT name, unit_price, stock_qty FROM {products_t} WHERE product_id = ?",
            [product_id])
        # query() reports failure in the result dict rather than raising, so check
        # success before indexing: a failed read has no "rows" key.
        if not prod["success"]:
            return json.dumps(prod, default=str)
        if not prod["rows"]:
            return json.dumps({"success": False, "error": f"product {product_id} does not exist"})
        name, unit_price, stock = prod["rows"][0]
        unit_price, stock = float(unit_price), int(stock)
        if stock < quantity:
            return json.dumps({"success": False,
                               "error": f"insufficient stock for '{name}': "
                                        f"{stock} available, {quantity} requested"})
        total = round(quantity * unit_price, 2)

        async with db.transaction() as tx:
            # Next order id. (Demo: production would use a DB sequence/identity column.)
            mx = await tx.query(f"SELECT MAX(order_id) FROM {orders_t}")
            last = mx["rows"][0][0]
            order_id = int(last) + 1 if last is not None else 1
            await tx.write(
                f"INSERT INTO {orders_t} (order_id, customer_id, status, total) "
                f"VALUES (?, ?, ?, ?)", [order_id, customer_id, "PLACED", total])
            await tx.write(
                f"INSERT INTO {items_t} (order_id, product_id, qty, line_total) "
                f"VALUES (?, ?, ?, ?)", [order_id, product_id, quantity, total])
            # A schema-level guard (where the engine supports one) still covers
            # an oversell race here.
            await tx.write(
                f"UPDATE {products_t} SET stock_qty = stock_qty - ? WHERE product_id = ?",
                [quantity, product_id])
            await tx.write(
                f"DELETE FROM {cart_t} WHERE customer_id = ? AND product_id = ?",
                [customer_id, product_id])
        # Reached only after all four statements committed.
        return json.dumps({"success": True, "order_id": order_id, "customer_id": customer_id,
                           "product": name, "product_id": product_id, "quantity": quantity,
                           "unit_price": unit_price, "total": total,
                           "placed_by": get_current_user()})

    @server.tool(name="cancel_order")
    async def cancel_order(order_id: int) -> str:
        """Cancel an order and restore its stock, atomically.

        Reads the order's line items, adds each quantity back to product stock,
        then deletes the line items and the order header — all in one transaction.
        Demonstrates mixing reads and writes within a transaction.
        """
        async with get_database().transaction() as tx:
            header = await tx.query(
                f"SELECT order_id FROM {orders_t} WHERE order_id = ?", [order_id])
            if not header["rows"]:
                return json.dumps({"success": False, "error": f"order {order_id} not found"})
            lines = await tx.query(
                f"SELECT product_id, qty FROM {items_t} WHERE order_id = ?", [order_id])
            for product_id, qty in lines["rows"]:
                await tx.write(
                    f"UPDATE {products_t} SET stock_qty = stock_qty + ? WHERE product_id = ?",
                    [qty, product_id])
            await tx.write(f"DELETE FROM {items_t} WHERE order_id = ?", [order_id])
            await tx.write(f"DELETE FROM {orders_t} WHERE order_id = ?", [order_id])
        return json.dumps({"success": True, "cancelled_order": order_id,
                           "restored_lines": lines["row_count"]})

    @server.tool(name="order_summary")
    async def order_summary(order_id: int) -> str:
        """Return an order with its line items (read-only), as a tidy object."""
        db = get_database()
        header = await db.query(
            f"SELECT order_id, customer_id, status, total FROM {orders_t} "
            f"WHERE order_id = ?", [order_id])
        if not header["success"]:
            return json.dumps(header, default=str)
        if not header["rows"]:
            return json.dumps({"success": False, "error": f"order {order_id} not found"})
        h = header["rows"][0]
        items = await db.query(
            f"SELECT product_id, qty, line_total FROM {items_t} WHERE order_id = ?",
            [order_id])
        if not items["success"]:
            return json.dumps(items, default=str)
        return json.dumps({
            "success": True,
            "order": {"order_id": h[0], "customer_id": h[1], "status": h[2], "total": h[3]},
            "items": [{"product_id": r[0], "quantity": r[1], "line_total": r[2]}
                      for r in items["rows"]],
        }, default=str)
