# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
import json

import pytest
from fastmcp import Client


async def _assert_client_features(client, expected_transport: str):
    await client.ping()

    tool_names = {tool.name for tool in await client.list_tools()}
    assert tool_names == {"check_health"}

    resource_names = {resource.name for resource in await client.list_resources()}
    assert resource_names == {"get_config"}

    prompt_names = {prompt.name for prompt in await client.list_prompts()}
    assert prompt_names == {"ask_question"}

    tool_result = await client.call_tool("check_health")
    payload = json.loads(tool_result.content[0].text)
    assert payload == {
        "dbms": "mock",
        "transport": expected_transport,
        "is_running": True,
    }

    resource_result = await client.read_resource("resource://tests/config")
    resource_payload = json.loads(resource_result[0].text)
    assert resource_payload["is_running"] is True


async def _connect_client_to_localhost_server(target, expected_transport: str):
    num_retries = 3
    last_error = None
    for _ in range(num_retries):
        try:
            async with Client(target, timeout=5) as client:
                await _assert_client_features(client, expected_transport)
                return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.25)

    raise AssertionError(f"Failed to connect to target {target}: {last_error}")


async def test_stdio_client_connection_and_features_usage(stdio_client):
    await _assert_client_features(stdio_client, "stdio")


@pytest.mark.parametrize("transport", ["http", "sse", "streamable-http"])
async def test_network_clients_connection_and_features_usage(localhost_server, transport):
    url = localhost_server(transport)
    await _connect_client_to_localhost_server(url, transport)
