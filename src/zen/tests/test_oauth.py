# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
OAuth authentication tests for actian-zen MCP server.

Tests that authenticated usernames are captured from JWT context
and logged per request. No external OAuth provider required.
"""

import json
import pytest
import logging
from unittest.mock import patch
from actian_mcp_server.oauth import current_username, get_current_username


# ---


def test_get_current_username_empty():
    assert get_current_username() is None


def test_get_current_username_set():
    token = current_username.set("alice")
    try:
        assert get_current_username() == "alice"
    finally:
        current_username.reset(token)


def test_contextvar_isolation():
    """Different ContextVar tokens are independent — simulates concurrent requests."""
    t1 = current_username.set("alice")
    t2 = current_username.set("bob")
    try:
        assert get_current_username() == "bob"
    finally:
        current_username.reset(t2)
        assert get_current_username() == "alice"
        current_username.reset(t1)
    assert get_current_username() is None


# ---


@pytest.mark.asyncio
async def test_execute_query_logs_username(stdio_client, caplog):
    """execute_query logs the authenticated username when present.

    FastMCP creates a new task context per request (correct isolation for
    production), so we mock get_current_username rather than set the ContextVar.
    """
    with patch("zen.features.tools.get_current_username", return_value="alice"), \
         caplog.at_level(logging.INFO, logger="zen.features.tools"):
        result = await stdio_client.call_tool(
            "execute_query",
            {"sql": "SELECT TOP 1 Name FROM Dept"}
        )
    data = json.loads(result.content[0].text)
    assert "error" not in data
    assert any("alice" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_execute_query_no_username(stdio_client, caplog):
    """execute_query works normally when no user is authenticated."""
    with patch("zen.features.tools.get_current_username", return_value=None), \
         caplog.at_level(logging.INFO, logger="zen.features.tools"):
        result = await stdio_client.call_tool(
            "execute_query",
            {"sql": "SELECT TOP 1 Name FROM Dept"}
        )
    data = json.loads(result.content[0].text)
    assert "error" not in data
    assert not any("authenticated user" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_username_not_enforced(stdio_client):
    """Zen has no SET SESSION AUTHORIZATION — any username still executes
    under the pool's DB credentials. Query succeeds regardless of username."""
    with patch("zen.features.tools.get_current_username", return_value="nonexistent_db_user"):
        result = await stdio_client.call_tool(
            "execute_query",
            {"sql": "SELECT TOP 1 Name FROM Dept"}
        )
    data = json.loads(result.content[0].text)
    assert "error" not in data
