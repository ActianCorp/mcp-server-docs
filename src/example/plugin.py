# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.
#
# ExamplePlugin — reference implementation showing how to add a new database.
#
# To add a real database:
# 1. Copy this file to src/<dbms>/plugin.py
# 2. Replace the stub session/client with your real driver
# 3. Implement register_tools, register_resources, register_prompts
# 4. Register your plugin in PLUGINS in actian_mcp_server/server.py

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.plugin import MCPPlugin
import json

logger = get_logger("ExamplePlugin")


class _StubSession:
    """Stand-in for a real database driver/client."""

    def __init__(self, config: dict):
        self.config = config
        self._store: dict = {}

    async def connect(self):
        host = self.config.get("host", "localhost")
        logger.info(f"ExamplePlugin: connected to {host}")

    async def get(self, collection: str, obj_id: str) -> dict | None:
        return self._store.get(f"{collection}/{obj_id}")

    async def put(self, collection: str, obj_id: str, document: dict):
        self._store[f"{collection}/{obj_id}"] = document

    async def close(self):
        logger.info("ExamplePlugin: disconnected")


class ExamplePlugin(MCPPlugin):
    """
    Example plugin demonstrating how a document/NoSQL-style database
    can be integrated into the Actian MCP Server framework.

    This plugin stores documents in memory; replace _StubSession with
    a real driver (e.g. pymongo, boto3 DynamoDB, aiohttp for a REST API).

    Required config keys:
        host  — database host (any string is accepted by this stub)
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.session: _StubSession | None = None

    def register_tools(self, server: FastMCP):
        plugin = self

        @server.tool(name="get_object")
        async def get_object(collection: str, obj_id: str) -> str:
            """Fetch a document/object by collection and ID."""
            result = await plugin.session.get(collection, obj_id)
            if result is None:
                return f"Not found: {collection}/{obj_id}"
            return json.dumps(result)

        @server.tool(name="put_object")
        async def put_object(collection: str, obj_id: str, document: str) -> str:
            """Store a JSON document by collection and ID."""
            try:
                doc = json.loads(document)
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON — {e}"
            await plugin.session.put(collection, obj_id, doc)
            return f"Stored {collection}/{obj_id}"

    def register_resources(self, server: FastMCP):
        plugin = self

        @server.resource(uri="resource://example/info")
        async def get_info() -> str:
            """Return connection info for the example database."""
            return json.dumps({
                "host": plugin.config.get("host", "localhost"),
                "driver": "ExampleStub",
            })

    def register_prompts(self, server: FastMCP):
        @server.prompt
        def ask_question(question: str) -> str:
            return f"You are a database expert. Answer the following question: {question}"

    @asynccontextmanager
    async def lifespan(self, server: FastMCP) -> AsyncIterator[None]:
        self.session = _StubSession(self.config)
        await self.session.connect()
        try:
            yield
        finally:
            await self.session.close()
            self.session = None
