# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json

from fastmcp import FastMCP

from actian_mcp_server.plugin import MCPPlugin


class MockPlugin(MCPPlugin):
    def __init__(self, config: dict):
        super().__init__(config)
        self.calls: list[str] = []
        self.running = False

    def register_tools(self, server: FastMCP):
        self.calls.append("register_tools")
        @server.tool(name="check_health")
        async def check_health() -> str:
            return json.dumps(
                {
                    "dbms": self.config["dbms"],
                    "transport": self.config["transport"],
                    "is_running": self.running,
                }
            )

    def register_resources(self, server: FastMCP):
        self.calls.append("register_resources")
        @server.resource(uri="resource://tests/config")
        async def get_config() -> str:
            return json.dumps(
                {
                    "host": self.config.get("host"),
                    "port": self.config.get("port"),
                    "is_running": self.running,
                }
            )

    def register_prompts(self, server: FastMCP):
        self.calls.append("register_prompts")
        @server.prompt
        def ask_question(question: str) -> str:
            return f"mock prompt: {question}"

    @asynccontextmanager
    async def lifespan(self, server: FastMCP) -> AsyncIterator[None]:
        self.running = True
        self.calls.append("lifespan_enter")
        try:
            yield
        finally:
            self.running = False
            self.calls.append("lifespan_exit")
