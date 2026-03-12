# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import FastMCP

from actian_mcp_server import server
from tests.mock_plugin import MockPlugin
from tests.conftest import MOCK_DBMS, MOCK_PLUGIN_PATH, MOCK_SERVER_NAME, make_config


def test_load_plugin_imports_registered_generic_plugin(monkeypatch):
    monkeypatch.setattr(server, "PLUGINS", {MOCK_DBMS: MOCK_PLUGIN_PATH})
    plugin = server.load_plugin(MOCK_DBMS, make_config("stdio"))

    assert isinstance(plugin, MockPlugin)
    assert plugin.config["dbms"] == MOCK_DBMS


def test_load_plugin_rejects_unsupported_dbms(monkeypatch):
    monkeypatch.setattr(server, "PLUGINS", {MOCK_DBMS: MOCK_PLUGIN_PATH})

    with pytest.raises(ValueError, match="Unsupported DBMS"):
        server.load_plugin("unsupported", make_config("stdio"))


async def test_app_lifespan(monkeypatch):
    monkeypatch.setattr(server, "PLUGINS", {MOCK_DBMS: MOCK_PLUGIN_PATH})
    plugin = server.load_plugin(MOCK_DBMS, make_config("stdio"))
    monkeypatch.setattr(server, "load_plugin", lambda dbms, config: plugin)
    lifespan = server.app_lifespan(make_config("stdio"))

    async with lifespan(FastMCP(MOCK_SERVER_NAME)):
        assert plugin.calls == [
            "register_tools",
            "register_resources",
            "register_prompts",
            "lifespan_enter",
        ]

    assert plugin.calls == [
        "register_tools",
        "register_resources",
        "register_prompts",
        "lifespan_enter",
        "lifespan_exit",
    ]
