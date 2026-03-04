# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import Client
import asyncio
import json

def get_json_result(result):
    content = result.content if hasattr(result, "content") else result
    return json.loads(content[0].text)

async def connect_http_clients(url):
    async with Client(url) as client:
        result = await client.call_tool("execute_query", {"query": "select total_amount from orders where order_id=52"})
        return get_json_result(result)

async def test_parallel_clients_http(server_localhost_http):
    num_http_clients = 100
    server_url = server_localhost_http
    expected_result = {"columns": ["total_amount"], "rows": [["45.99"]]}
    connections = [connect_http_clients(server_url) for _ in range(num_http_clients)]
    results = await asyncio.gather(*connections)
    
    assert len(results) == num_http_clients
    for result in results:
        assert result["columns"] == expected_result["columns"]
        assert result["rows"] == expected_result["rows"]

async def test_parallel_clients_sse(server_localhost_sse):
    num_http_clients = 100
    server_url = server_localhost_sse
    expected_result = {"columns": ["total_amount"], "rows": [["45.99"]]}
    connections = [connect_http_clients(server_url) for _ in range(num_http_clients)]
    results = await asyncio.gather(*connections)
    
    assert len(results) == num_http_clients
    for result in results:
        assert result["columns"] == expected_result["columns"]
        assert result["rows"] == expected_result["rows"]
