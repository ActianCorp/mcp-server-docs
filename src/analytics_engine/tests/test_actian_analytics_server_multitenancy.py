# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
import json

import pytest
from fastmcp import Client


SERVER_MODES = ["localhost-http", "containerized"]

def get_json_result(result):
    content = result.content if hasattr(result, "content") else result
    return json.loads(content[0].text)

async def _connect_http_clients(server):
    async with Client(server) as client:
        result = await client.call_tool("execute_query", {"query": "select total_amount from orders where order_id=52"})
        return get_json_result(result)

async def _test_parallel_clients(server):
    num_http_clients = 100
    expected_result = {"columns": ["total_amount"], "rows": [["45.99"]]}
    connections = [_connect_http_clients(server) for _ in range(num_http_clients)]
    results = await asyncio.gather(*connections)

    assert len(results) == num_http_clients
    for result in results:
        assert result["columns"] == expected_result["columns"]
        assert result["rows"] == expected_result["rows"]


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_parallel_clients(server):
    await _test_parallel_clients(server)
