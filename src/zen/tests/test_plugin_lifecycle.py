# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
#
# Plugin lifecycle tests -- uses a MockPlugin so no database needed.

import json
import pytest
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastmcp import Client, FastMCP
from actian_mcp_server import server
from actian_mcp_server.plugin import MCPPlugin


MOCK_DBMS = "mock"
MOCK_PLUGIN_PATH = "zen.tests.test_plugin_lifecycle:MockPlugin"
MOCK_SERVER_NAME = "Mock MCP Server"


class MockPlugin(MCPPlugin):

    def __init__(self, config: dict):
        super().__init__(config)
        self.calls = []
        self.running = False

    def register_tools(self, srv: FastMCP):
        self.calls.append("register_tools")

        @srv.tool(name="mock_health")
        async def mock_health() -> str:
            return json.dumps({"running": self.running, "dbms": self.config.get("dbms")})

    def register_resources(self, srv: FastMCP):
        self.calls.append("register_resources")
        @srv.resource(uri="resource://mock/info")
        async def mock_info() -> str:
            return json.dumps({"running": self.running})

    def register_prompts(self, srv: FastMCP):
        self.calls.append("register_prompts")
        @srv.prompt
        def mock_prompt(question: str) -> str:
            return f"mock: {question}"

    @asynccontextmanager
    async def lifespan(self, srv: FastMCP) -> AsyncIterator[None]:
        self.running = True
        self.calls.append("lifespan_enter")
        try:
            yield
        finally:
            self.running = False
            self.calls.append("lifespan_exit")


def _cfg():
    return {"dbms": MOCK_DBMS, "transport": "stdio"}


def _inject_mock(monkeypatch):
    monkeypatch.setattr(server, "PLUGINS", {MOCK_DBMS: MOCK_PLUGIN_PATH})


# lifecycle order -- the whole point of this file

async def test_lifecycle_order(monkeypatch):
    """lifespan_enter must happen BEFORE register_* (connection needed first)."""
    _inject_mock(monkeypatch)
    plugin = server.load_plugin(MOCK_DBMS, _cfg())
    monkeypatch.setattr(server, "load_plugin", lambda dbms, config: plugin)

    lifespan = server.app_lifespan(_cfg())
    async with lifespan(FastMCP(MOCK_SERVER_NAME)):
        assert plugin.calls == [
            "lifespan_enter",
            "register_tools",
            "register_resources",
            "register_prompts",
        ]

    assert plugin.calls[-1] == "lifespan_exit"


async def test_lifespan_exit_on_shutdown(monkeypatch):
    _inject_mock(monkeypatch)
    plugin = server.load_plugin(MOCK_DBMS, _cfg())
    monkeypatch.setattr(server, "load_plugin", lambda dbms, config: plugin)

    lifespan = server.app_lifespan(_cfg())
    async with lifespan(FastMCP(MOCK_SERVER_NAME)):
        assert plugin.running is True

    assert plugin.running is False
    assert "lifespan_exit" in plugin.calls


# plugin loading

def test_load_plugin_correct_type(monkeypatch):
    _inject_mock(monkeypatch)
    plugin = server.load_plugin(MOCK_DBMS, _cfg())
    assert type(plugin).__name__ == "MockPlugin"
    assert plugin.config["dbms"] == MOCK_DBMS


def test_load_plugin_rejects_unknown_dbms(monkeypatch):
    _inject_mock(monkeypatch)
    with pytest.raises(ValueError, match="Unsupported DBMS"):
        server.load_plugin("nonexistent", _cfg())


# tools/resources/prompts accessible via client

async def test_mock_tools_accessible(monkeypatch):
    _inject_mock(monkeypatch)
    app = FastMCP(MOCK_SERVER_NAME, lifespan=server.app_lifespan(_cfg()))

    async with Client(app) as client:
        tools = await client.list_tools()
        assert any(t.name == "mock_health" for t in tools)

        result = await client.call_tool("mock_health")
        data = json.loads(result.content[0].text)
        assert data["running"] is True


async def test_mock_resources_accessible(monkeypatch):
    _inject_mock(monkeypatch)
    app = FastMCP(MOCK_SERVER_NAME, lifespan=server.app_lifespan(_cfg()))

    async with Client(app) as client:
        resources = await client.list_resources()
        assert any("mock" in str(r.uri) for r in resources)


async def test_mock_prompts_accessible(monkeypatch):
    _inject_mock(monkeypatch)
    app = FastMCP(MOCK_SERVER_NAME, lifespan=server.app_lifespan(_cfg()))
    async with Client(app) as client:
        prompts = await client.list_prompts()
        assert len(prompts) >= 1
