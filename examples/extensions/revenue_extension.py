# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

"""Reference extension for the Actian MCP Server — portable across all engines
(Analytics Engine / Ingres / Informix / Zen).

A small, runnable example of the extension contract:
  * a read tool using get_database().query()
  * a write tool that opts into human approval: it calls
    request_write_confirmation() itself, then writes in a transaction
  * a transaction tool that updates two tables atomically with
    get_database().transaction()
  * use of the authenticated identity and the extension's own config

The SQL here is deliberately plain ANSI so this file runs unmodified on every
engine — no dialect-specific syntax and no per-engine branching. (Top-N results
are limited in Python rather than with a FETCH FIRST / SELECT FIRST / TOP clause,
which differ across engines; see top_customers_by_revenue.)

Mount this file into a running container under /app/extensions/ and reference it
by module name in conf.json (the write and transaction tools also need
"query_mode": "read-write"):

    docker run ... \
      -v ./revenue_extension.py:/app/extensions/revenue_extension.py:ro ...

    { "extensions": [
        { "module": "revenue_extension",
          "config": { "default_region": "NA", "revenue_table": "customer_revenue",
                      "customers_table": "customers", "sales_table": "sales" } } ] }

Expected schema (see examples/extensions/README.md and the schema file for your
engine — schema.ingres.sql / schema.informix.sql / schema.zen.sql):
    customer_revenue(customer_id PK, customer_name, region, total_revenue)
    customers(customer_id PK, vip)
    sales(customer_id, amount)   -- distinct from order_ops' 'orders' table

(Optional setup(config) / teardown() hooks are also supported; omitted here
since this example owns no resources of its own.)
"""

import json

from actian_mcp_server.extension_api import (
    get_current_user,
    get_database,
    request_write_confirmation,
)


def register(server, config):
    """Register the extension's tools. Called once at startup.

    `config` is this extension's scoped settings (no DB/OAuth secrets).
    """
    default_region = config.get("default_region", "NA")
    revenue_table = config.get("revenue_table", "customer_revenue")
    customers_table = config.get("customers_table", "customers")
    # Distinct from order_ops' 'orders' table so both examples can share one DB.
    sales_table = config.get("sales_table", "sales")

    @server.tool(name="top_customers_by_revenue")
    async def top_customers_by_revenue(region: str = default_region, limit: int = 5) -> str:
        """Return the highest-revenue customers in a region (read-only)."""
        limit = max(1, min(limit, 100))
        # Portable across all engines: ORDER BY plus a client-side limit, avoiding
        # each engine's own top-N clause (FETCH FIRST / SELECT FIRST / TOP). For
        # large tables in production, prefer your engine's native top-N instead.
        sql = (
            f"SELECT customer_name, total_revenue "
            f"FROM {revenue_table} WHERE region = ? "
            f"ORDER BY total_revenue DESC"
        )
        res = await get_database().query(sql, [region])
        if not res["success"]:
            return json.dumps(res, default=str)
        top_rows = res["rows"][:limit]
        return json.dumps({
            "success": True, "region": region,
            "customers": [{"customer": r[0], "total_revenue": r[1]} for r in top_rows],
            "requested_by": get_current_user(),  # None unless OAuth + user_impersonation
        }, default=str)

    @server.tool(name="tag_vip_customer")
    async def tag_vip_customer(customer_id: int) -> str:
        """Tag a customer as VIP (requires read-write mode).

        This extension chooses to gate the write behind human approval: it asks
        first and only writes if approved. The framework does not force this —
        the confirmation call is the extension's decision and placement.
        """
        approved = await request_write_confirmation(
            description=f"Tag customer {customer_id} as VIP",
            details={"table": customers_table, "customer_id": customer_id},
        )
        if not approved:
            return json.dumps({"success": False,
                               "error": "write not approved (declined, or this client "
                                        "cannot show an approval prompt)"})

        # Writes go through a transaction (a single write is a one-statement txn).
        async with get_database().transaction() as tx:
            res = await tx.write(
                f"UPDATE {customers_table} SET vip = 1 WHERE customer_id = ?", [customer_id])
            if res["row_count"] == 0:
                return json.dumps({"success": False, "error": f"customer {customer_id} not found"})
        return json.dumps({"success": True, "customer_id": customer_id, "vip": True})

    @server.tool(name="record_customer_sale")
    async def record_customer_sale(customer_id: int, amount: float) -> str:
        """Record a sale across two tables atomically (requires read-write mode).

        Inserts a sale row AND bumps the customer's running revenue total. Both
        succeed or neither does. Used as a context manager, the transaction commits
        on a clean exit and rolls back if any statement raises — so a failed second
        write leaves the first one undone.

        (For step-by-step control you can instead drive it explicitly:
            tx = await get_database().transaction().begin()
            try:
                await tx.write(...); await tx.commit()
            except Exception:
                await tx.rollback(); raise)
        """
        async with get_database().transaction() as tx:
            await tx.write(
                f"INSERT INTO {sales_table} (customer_id, amount) VALUES (?, ?)",
                [customer_id, amount],
            )
            await tx.write(
                f"UPDATE {revenue_table} SET total_revenue = total_revenue + ? "
                f"WHERE customer_id = ?",
                [amount, customer_id],
            )
        # Reached only if both writes succeeded and the transaction committed.
        return json.dumps({"success": True, "customer_id": customer_id, "amount": amount})
