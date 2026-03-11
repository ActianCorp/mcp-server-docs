# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import json

import pytest
from pytest_unordered import unordered

SERVER_MODES = ["stdio", "localhost-http", "localhost-sse", "containerized"]

EXPECTED_RESOURCES = ["get_database_schema"]


def get_json_result(result):
    content = result.content if hasattr(result, "content") else result
    return json.loads(content[0].text)


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_vector_resources_list(client, server):
    resource_list = await client.list_resources()
    num_resources = len(resource_list)
    assert num_resources == len(EXPECTED_RESOURCES)
    resource_names = [r.name for r in resource_list]
    assert resource_names == unordered(EXPECTED_RESOURCES)


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_vector_resource__get_database_schema(client, server):
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
    result = await client.read_resource("resource://database/schema")
    result = get_json_result(result)
    assert expected_schema == result
