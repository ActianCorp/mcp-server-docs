# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

"""Demo extension: resources, a prompt, and the setup/teardown lifecycle hooks.

The other examples focus on tools; this one rounds out the surface by showing the
rest of what an extension can register:

  * setup(config) / teardown()  — optional startup/shutdown hooks. Here they own a
    small in-memory cache (the guide's stated use: "a cache, an HTTP client, a
    connection pool of your own"). They may be async or plain functions.
  * @server.resource(uri)       — readable, addressable data (static + templated).
  * @server.prompt              — a reusable prompt template.

Uses the same `products` table as the other examples (read-only — works in
read-only mode). See examples/extensions/README.md and the schema file for
your engine (schema.ingres.sql / schema.informix.sql / schema.zen.sql).

Two loader caveats worth knowing (different from tools):
  * Resource/prompt names are NOT collision-guarded — only tool names are. A
    duplicate resource URI is handled by FastMCP (not skipped-and-logged).
  * If register() raises partway, the loader rolls back the *tools* it registered,
    not resources/prompts — so register them without expecting that safety net.
"""

import json
import logging

from actian_mcp_server.extension_api import get_database

logger = logging.getLogger(__name__)

# A resource this extension "owns", opened in setup() and released in teardown().
_state: dict = {}


async def setup(config):
    """Open resources at startup (here: cache the configured threshold)."""
    _state["low_stock_threshold"] = int(config.get("low_stock_threshold", 10))
    logger.info("catalog_resources: setup complete (low_stock_threshold=%s)",
                _state["low_stock_threshold"])


async def teardown():
    """Release whatever setup() opened (called at shutdown, reverse load order)."""
    _state.clear()
    logger.info("catalog_resources: teardown complete")


def register(server, config):
    products_t = config.get("products_table", "products")

    @server.resource("catalog://low-stock")
    async def low_stock_resource() -> str:
        """Products at or below the configured low-stock threshold (read-only)."""
        threshold = _state.get("low_stock_threshold", 10)
        res = await get_database().query(
            f"SELECT product_id, name, stock_qty FROM {products_t} "
            f"WHERE stock_qty <= ? ORDER BY stock_qty", [threshold])
        return json.dumps(res, default=str)

    @server.resource("catalog://product/{product_id}")
    async def product_resource(product_id: int) -> str:
        """A single product by id (templated resource — {product_id} is the URI param)."""
        res = await get_database().query(
            f"SELECT product_id, name, unit_price, stock_qty FROM {products_t} "
            f"WHERE product_id = ?", [product_id])
        return json.dumps(res, default=str)

    @server.prompt
    def restock_advice(product_name: str) -> str:
        """A reusable prompt: ask the model to recommend a restock quantity."""
        return (
            f"You are an inventory analyst. Recommend a restock quantity for "
            f"'{product_name}', considering its current stock and typical demand, "
            f"and explain your reasoning briefly."
        )
