# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from pytest_unordered import unordered
import json

actual_tools = ["execute_query", "describe_table", "list_tables", "list_functions"]
actual_resources = ["get_database_schema"]
actual_prompts = ["ask_question"]

def get_json_result(result):
    content = result.content if hasattr(result, "content") else result
    return json.loads(content[0].text)

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
    expected_result = {"columns": ["total_amount"], "rows": [["45.99"]]}
    result = await stdio_client.call_tool("execute_query", {"query": "SELECT total_amount FROM orders WHERE order_id=52"})
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == expected_result["rows"]

async def test_tool__list_tables(stdio_client):
    expected_result = {"columns": ["table_name"], "rows": [["customers"], ["orders"]]}
    result = await stdio_client.call_tool("list_tables")
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == expected_result["rows"]

async def test_tool__describe_table(stdio_client):
    expected_result = {"columns": ["column_name", "column_datatype", "column_length", "column_scale", "column_comment"],
                       "rows": [["customer_id", "INTEGER", "4", "0", None], ["email", "VARCHAR", "50", "0", None]]}
    result = await stdio_client.call_tool("describe_table", {"table_name": "customers"})
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == expected_result["rows"]

async def test_tool__list_functions(stdio_client):
    expected_result = {"columns": ["function_name", "function_ddl"],
                       "rows": [["is_date", "create procedure  is_date(a VARCHAR(24)) RETURN (VARCHAR(24)) AS BEGIN return if(a IS DATE,\'YES\',\'NO\') END"],
                                ["sum_int", "create function  sum_int(a INT, b INT) RETURN (INT) AS BEGIN return a+b END"]]}
    result = await stdio_client.call_tool("list_functions")
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == expected_result["rows"]

async def test_resource__get_database_schema(stdio_client):
    expected_schema = \
    {
        "customers":
        {
            "columns": {"email": {"dtype": "VARCHAR", "comment": None},
                        "customer_id": {"dtype": "INTEGER", "comment": None}},
            "keys": [],
            "comment": None
        },
        "orders":
        {
            "columns": {"order_id": {"dtype": "INTEGER", "comment": None},
                        "order_date": {"dtype": "ANSIDATE", "comment": None},
                        "customer_id": {"dtype": "INTEGER", "comment": None},
                        "total_amount": {"dtype": "MONEY", "comment": None}},
            "keys": [],
            "comment": None
        }
    }
    result = await stdio_client.read_resource("resource://database/schema")
    result = get_json_result(result)
    assert expected_schema == result

async def test_prompt__ask_question(stdio_client):
    result = await stdio_client.get_prompt("ask_question", {"question": ""})
    assert result
