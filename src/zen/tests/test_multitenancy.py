# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
Multitenancy and load tests for actian-zen MCP server.

Tests parallel client connections via HTTP and SSE transports.
Based on Alternative MCP stress testing patterns.
"""

import asyncio
import json
import pytest
from fastmcp import Client


async def connect_and_query(url: str) -> dict:
    """
    Single client: connect, execute query, return result.

    Args:
        url: Server URL (HTTP or SSE endpoint)

    Returns:
        Query result or error dict
    """
    try:
        async with Client(url) as client:
            result = await client.call_tool(
                "execute_query",
                {"sql": "SELECT TOP 1 employee_id, first_name FROM employees"}
            )
            return json.loads(result.content[0].text)
    except Exception as e:
        return {"error": str(e)}


async def connect_and_ping(url: str) -> bool:
    """
    Single client: connect and ping.

    Args:
        url: Server URL

    Returns:
        True if ping successful
    """
    try:
        async with Client(url) as client:
            await client.ping()
            return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════════
# HTTP Transport Stress Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@pytest.mark.slow
async def test_parallel_clients_http_10(server_localhost_http):
    """Test 10 parallel HTTP clients."""
    num_clients = 10
    server_url = server_localhost_http

    connections = [connect_and_query(server_url) for _ in range(num_clients)]
    results = await asyncio.gather(*connections, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception) and "error" not in r]
    failed = num_clients - len(successful)

    assert len(successful) >= num_clients * 0.9, \
        f"Too many failures: {failed}/{num_clients} failed"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_parallel_clients_http_50(server_localhost_http):
    """Test 50 parallel HTTP clients."""
    num_clients = 50
    server_url = server_localhost_http

    connections = [connect_and_query(server_url) for _ in range(num_clients)]
    results = await asyncio.gather(*connections, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception) and "error" not in r]
    failed = num_clients - len(successful)

    assert len(successful) >= num_clients * 0.9, \
        f"Too many failures: {failed}/{num_clients} failed"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_parallel_clients_http_100(server_localhost_http):
    """Test 100 parallel HTTP clients (stress test)."""
    num_clients = 100
    server_url = server_localhost_http

    connections = [connect_and_query(server_url) for _ in range(num_clients)]
    results = await asyncio.gather(*connections, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception) and "error" not in r]
    failed = num_clients - len(successful)

    # Allow 10% failure rate for stress test
    assert len(successful) >= num_clients * 0.9, \
        f"Too many failures: {failed}/{num_clients} failed"


# ════════════════════════════════════════════════════════════════════════════════
# SSE Transport Stress Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@pytest.mark.slow
async def test_parallel_clients_sse_10(server_localhost_sse):
    """Test 10 parallel SSE clients."""
    num_clients = 10
    server_url = server_localhost_sse

    connections = [connect_and_query(server_url) for _ in range(num_clients)]
    results = await asyncio.gather(*connections, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception) and "error" not in r]
    failed = num_clients - len(successful)

    assert len(successful) >= num_clients * 0.9, \
        f"Too many failures: {failed}/{num_clients} failed"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_parallel_clients_sse_50(server_localhost_sse):
    """Test 50 parallel SSE clients."""
    num_clients = 50
    server_url = server_localhost_sse

    connections = [connect_and_query(server_url) for _ in range(num_clients)]
    results = await asyncio.gather(*connections, return_exceptions=True)

    successful = [r for r in results if not isinstance(r, Exception) and "error" not in r]
    failed = num_clients - len(successful)

    assert len(successful) >= num_clients * 0.9, \
        f"Too many failures: {failed}/{num_clients} failed"


# ════════════════════════════════════════════════════════════════════════════════
# Connection Pool Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@pytest.mark.slow
async def test_sequential_connections_http(server_localhost_http):
    """Test sequential connect/disconnect cycles."""
    num_cycles = 20
    server_url = server_localhost_http

    for i in range(num_cycles):
        result = await connect_and_query(server_url)
        assert "error" not in result, f"Cycle {i+1} failed: {result.get('error')}"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_ping_storm_http(server_localhost_http):
    """Test rapid ping requests."""
    num_pings = 50
    server_url = server_localhost_http

    pings = [connect_and_ping(server_url) for _ in range(num_pings)]
    results = await asyncio.gather(*pings, return_exceptions=True)

    successful = [r for r in results if r is True]
    assert len(successful) >= num_pings * 0.9, \
        f"Too many ping failures: {num_pings - len(successful)}/{num_pings}"
