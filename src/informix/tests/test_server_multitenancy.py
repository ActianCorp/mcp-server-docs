# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import Client
import asyncio
import toons

async def connect_http_clients(url):
    async with Client(url) as client:
        result = await client.call_tool("execute_query", {"query": "select total_amount from orders where order_id=52"})
        return result.content[0].text

async def test_parallel_clients_http(server_localhost_http):
    num_http_clients = 100
    server_url = server_localhost_http
    expected_result = toons.dumps([{'total_amount': '45.99'}])
    connections = [connect_http_clients(server_url) for _ in range(num_http_clients)]
    results = await asyncio.gather(*connections)
    
    assert len(results) == num_http_clients
    for result in results:
        assert result == expected_result

async def test_parallel_clients_sse(server_localhost_sse):
    num_http_clients = 100
    server_url = server_localhost_sse
    expected_result = toons.dumps([{'total_amount': '45.99'}])
    connections = [connect_http_clients(server_url) for _ in range(num_http_clients)]
    results = await asyncio.gather(*connections)
    
    assert len(results) == num_http_clients
    for result in results:
        assert result == expected_result
