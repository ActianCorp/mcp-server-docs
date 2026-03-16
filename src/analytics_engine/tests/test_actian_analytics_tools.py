# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import json

import pytest
from pytest_unordered import unordered

SERVER_MODES = ["stdio", "localhost-http", "localhost-sse", "containerized"]

EXPECTED_TOOLS = ["execute_query", "describe_table", "list_tables", "list_functions"]


def get_json_result(result):
    content = result.content if hasattr(result, "content") else result
    return json.loads(content[0].text)


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_analytics_engine_tools_list(client, server):
    tool_list = await client.list_tools()
    num_tools = len(tool_list)
    assert num_tools == len(EXPECTED_TOOLS)
    tool_names = [t.name for t in tool_list]
    assert tool_names == unordered(EXPECTED_TOOLS)


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_analytics_engine_tool__execute_query(client, server):
    expected_result = {"columns": ["total_amount"], "rows": [["45.99"]]}
    result = await client.call_tool("execute_query", {"query": "SELECT total_amount FROM orders WHERE order_id=52"})
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == unordered(expected_result["rows"])


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_analytics_engine_tool__list_tables(client, server):
    expected_result = {"columns": ["table_name"], "rows": [["customers"], ["orders"]]}
    result = await client.call_tool("list_tables")
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == unordered(expected_result["rows"])


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_analytics_engine_tool__describe_table(client, server):
    expected_result = {"columns": ["column_name", "column_datatype", "column_length", "column_scale", "column_comment"],
                       "rows": [["customer_id", "INTEGER", "4", "0", None], ["email", "VARCHAR", "50", "0", None]]}
    result = await client.call_tool("describe_table", {"table_name": "customers"})
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == unordered(expected_result["rows"])


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_analytics_engine_tool__list_functions(client, server):
    expected_result = {"columns": ["function_name", "function_ddl"],
                       "rows": [["is_date", "create procedure  is_date(a VARCHAR(24)) RETURN (VARCHAR(24)) AS BEGIN return if(a IS DATE,\'YES\',\'NO\') END"],
                                ["sum_int", "create function  sum_int(a INT, b INT) RETURN (INT) AS BEGIN return a+b END"]]}
    result = await client.call_tool("list_functions")
    result = get_json_result(result)
    assert result["columns"] == expected_result["columns"]
    assert result["rows"] == unordered(expected_result["rows"])
