# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import toons
from pytest_unordered import unordered

actual_tools = ["execute_query", "describe_table", "list_tables"]
actual_resources = ["get_database_schema"]
actual_prompts = ["ask_question"]

async def test_server_reachability(stdio_client):
    response = await stdio_client.ping()
    assert stdio_client

async def test_tools_list(stdio_client):
    tool_list = await stdio_client.list_tools()
    num_tools = len(tool_list)
    assert num_tools == len(actual_tools)
    tool_names = [t.name for t in tool_list]
    assert tool_names == unordered(actual_tools)

async def test_resources_list(stdio_client):
    resource_list = await stdio_client.list_resources()
    num_resources = len(resource_list)
    assert num_resources == len(actual_resources)
    resource_names = [r.name for r in resource_list]
    assert resource_names == unordered(actual_resources)

async def test_prompts_list(stdio_client):
    prompt_list = await stdio_client.list_prompts()
    num_prompts = len(prompt_list)
    assert num_prompts == len(actual_prompts)
    prompt_names = [p.name for p in prompt_list]
    assert prompt_names == unordered(actual_prompts)

async def test_tool__execute_query(stdio_client):
    expected_result = toons.dumps([{'total_amount': '45.99'}])
    result = await stdio_client.call_tool("execute_query", {"query": "SELECT total_amount FROM orders WHERE order_id=52"})
    assert result.content[0].text == expected_result

async def test_tool__list_tables(stdio_client):
    expected_result = [{'table_name': 'customers'}, {'table_name': 'orders'}]
    result = await stdio_client.call_tool("list_tables")
    tables = toons.loads(result.content[0].text)
    assert tables == unordered(expected_result)

async def test_tool__describe_table(stdio_client):
    expected_result = [
        {'column_name': 'customer_id', 'column_datatype': 'INTEGER', 'column_length': '4', 'allows_nulls': 'YES'},
        {'column_name': 'email', 'column_datatype': 'VARCHAR', 'column_length': '50', 'allows_nulls': 'YES'}
    ]
    result = await stdio_client.call_tool("describe_table", {"table_name": "customers"})
    table_schema = toons.loads(result.content[0].text)
    assert table_schema == unordered(expected_result)

async def test_resource__get_database_schema(stdio_client):
    expected_schema = {
        'customers': [{'customer_id': 'INTEGER'}, {'email': 'VARCHAR'}],
        'orders': [{'total_amount': 'MONEY'}, {'order_date': 'DATE'}, {'customer_id': 'INTEGER'}, {'order_id': 'INTEGER'}]
    }
    result = await stdio_client.read_resource("resource://database/schema")
    schema = toons.loads(result[0].text)

    assert expected_schema.keys() == schema.keys()
    for table in expected_schema:
        assert expected_schema[table] == unordered(schema[table])

async def test_prompt__ask_question(stdio_client):
    result = await stdio_client.get_prompt("ask_question", {"question": ""})
    assert result
