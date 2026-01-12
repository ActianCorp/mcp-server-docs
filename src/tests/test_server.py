# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import Client
from actian_mcp_server.server import server
from actian_mcp_server.tools import initialize_tools
from actian_mcp_server.resources import initialize_resources
from actian_mcp_server.prompts import initialize_prompts

actual_tools = ["print_text"]
actual_resources = ["read_text"]
actual_prompts = ["ask_question"]

@pytest.fixture
async def client():
    initialize_tools(server)
    initialize_resources(server)
    initialize_prompts(server)
    async with Client(server) as c:
        yield c

async def test_server_reachability(client):
    response = await client.ping()
    assert client

async def test_tools_list(client):
    tool_list = await client.list_tools()
    num_tools = len(tool_list)
    assert num_tools == len(actual_tools)
    for i in range(num_tools):
        assert tool_list[i].name == actual_tools[i]

async def test_resources_list(client):
    resource_list = await client.list_resources()
    num_resources = len(resource_list)
    assert num_resources == len(actual_resources)
    for i in range(num_resources):
        assert resource_list[i].name == actual_resources[i]

async def test_prompts_list(client):
    prompt_list = await client.list_prompts()
    num_prompts = len(prompt_list)
    assert num_prompts == len(actual_prompts)
    for i in range(num_prompts):
        assert prompt_list[i].name == actual_prompts[i]

async def test_tool__print_text(client):
    result = await client.call_tool("print_text", {"text": "hello world"})
    assert result.content[0].text == "hello world"

async def test_resource__read_text(client):
    result = await client.read_resource("read://text")
    assert result[0].text == "hello world"

async def test_prompt__ask_question(client):
    result = await client.get_prompt("ask_question", {"question": ""})
    assert result
