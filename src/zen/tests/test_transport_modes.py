# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
#
# Same assertions across stdio, HTTP, SSE -- catches transport-specific bugs.

import json
import pytest
from fastmcp import Client


EXPECTED_TOOL_COUNT = 9


def _parse(result):
    return json.loads(result.content[0].text)


async def _check_features(client, label):
    await client.ping()

    tools = await client.list_tools()
    names = [t.name for t in tools]
    assert len(names) == EXPECTED_TOOL_COUNT, f"[{label}] got {len(names)} tools: {names}"
    assert "execute_query" in names
    assert "list_tables" in names

    resources = await client.list_resources()
    assert len(resources) == 1

    data = _parse(await client.call_tool("list_tables", {}))
    assert "error" not in data
    assert data["count"] > 0

    data = _parse(await client.call_tool("database_manage", {"action": "capabilities"}))
    assert data["database"] == "Actian Zen"


# stdio

async def test_stdio_features(stdio_client):
    await _check_features(stdio_client, "stdio")


async def test_stdio_query(stdio_client):
    data = _parse(await stdio_client.call_tool(
        "execute_query", {"sql": "SELECT COUNT(*) AS cnt FROM Person"}
    ))
    assert "error" not in data


async def test_stdio_describe(stdio_client):
    data = _parse(await stdio_client.call_tool("describe_table", {"table": "Person"}))
    assert data["table_name"] == "Person"
    assert len(data["columns"]) > 0


# HTTP -- each test opens its own client since the fixture returns a URL

async def test_http_features(server_localhost_http):
    async with Client(server_localhost_http, timeout=10) as c:
        await _check_features(c, "http")


async def test_http_query(server_localhost_http):
    async with Client(server_localhost_http, timeout=10) as c:
        data = _parse(await c.call_tool(
            "execute_query", {"sql": "SELECT COUNT(*) AS cnt FROM Person"}
        ))
        assert "error" not in data


async def test_http_describe(server_localhost_http):
    async with Client(server_localhost_http, timeout=10) as c:
        data = _parse(await c.call_tool("describe_table", {"table": "Person"}))
        assert data["table_name"] == "Person"


# SSE -- deprecated transport but still need to verify it works

async def test_sse_features(server_localhost_sse):
    async with Client(server_localhost_sse, timeout=10) as c:
        await _check_features(c, "sse")


async def test_sse_query(server_localhost_sse):
    async with Client(server_localhost_sse, timeout=10) as c:
        data = _parse(await c.call_tool(
            "execute_query", {"sql": "SELECT COUNT(*) AS cnt FROM Person"}
        ))
        assert "error" not in data
