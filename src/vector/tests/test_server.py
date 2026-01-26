# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import Client, FastMCP
from types import SimpleNamespace
from actian_mcp_server.server import server_name, app_lifespan
import toons

actual_tools = ["execute_query"]
actual_resources = ["get_database_schema"]
actual_prompts = ["ask_question"]

@pytest.fixture
async def server(tmp_path):
    conf_string = '{"conn_string": "Driver={Actian VW};database=mcp_vector_db"}'
    conf_path = tmp_path / "conf.json"
    conf_path.write_text(conf_string)
    return FastMCP(
        server_name,
        lifespan=app_lifespan(SimpleNamespace(dbms="vector", transport="stdio", conf_file=str(conf_path))),
    )

@pytest.fixture
async def client(server):
    async with Client(server) as c:
        yield c

async def test_server_reachability(client):
    response = await client.ping()
    assert client

async def test_tools_list(client):
    tool_list = await client.list_tools()
    num_tools = len(tool_list)
    assert num_tools == len(actual_tools)
    tool_names = [t.name for t in tool_list]
    assert set(tool_names) == set(actual_tools)

async def test_resources_list(client):
    resource_list = await client.list_resources()
    num_resources = len(resource_list)
    assert num_resources == len(actual_resources)
    resource_names = [r.name for r in resource_list]
    assert set(resource_names) == set(actual_resources)

async def test_prompts_list(client):
    prompt_list = await client.list_prompts()
    num_prompts = len(prompt_list)
    assert num_prompts == len(actual_prompts)
    prompt_names = [p.name for p in prompt_list]
    assert set(prompt_names) == set(actual_prompts)

async def test_tool__execute_query(client):
    expected_result = toons.dumps([{'total_amount': '45.99'}])
    result = await client.call_tool("execute_query", {"query": "select total_amount from orders where order_id=52"})
    assert result.content[0].text == expected_result

async def test_resource__get_database_schema(client):
    expected_schema = {
        'customers': [{'customer_id': 'INTEGER'}, {'email': 'VARCHAR'}],
        'orders': [{'total_amount': 'MONEY'}, {'order_date': 'ANSIDATE'}, {'customer_id': 'INTEGER'}, {'order_id': 'INTEGER'}]
    }
    result = await client.read_resource("resource://database/schema")
    schema = toons.loads(result[0].text)

    assert expected_schema.keys() == schema.keys()
    for table in expected_schema:
        assert set(str(expected_schema[table])) == set(str(schema[table]))

async def test_prompt__ask_question(client):
    result = await client.get_prompt("ask_question", {"question": ""})
    assert result
