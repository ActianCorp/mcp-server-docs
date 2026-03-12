# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest

from actian_mcp_server.server_utils import validate_readonly_query


@pytest.mark.parametrize(
    "query",
    [
        "SELECT 1",
        "WITH recent AS (SELECT CURRENT_DATE AS today) SELECT today FROM recent",
        "/* comment */ SELECT 'a;''b' -- trailing comment\n",
        "SELECT customer_id FROM orders LIMIT 10 OFFSET 5",
    ],
)
def test_validate_readonly_query_accepts_readonly_queries(query):
    assert validate_readonly_query(query) == (True, "")


@pytest.mark.parametrize(
    ("query", "expected_message"),
    [
        ("", "Empty query"),
        ("   ", "Empty query"),
        ("INSERT INTO orders VALUES (1)", "Only SELECT queries are permitted"),
        ("UPDATE orders SET total_amount = 1", "Only SELECT queries are permitted"),
        ("DELETE FROM orders", "Only SELECT queries are permitted"),
        ("SELECT 1; SELECT 2", "Multi-statement queries are not permitted"),
        ("SHOW TABLES", "Only SELECT queries are permitted"),
        ("CALL run_admin_task()", "Only SELECT queries are permitted"),
    ],
)
def test_validate_readonly_query_rejects_non_readonly_queries(query, expected_message):
    allowed, message = validate_readonly_query(query)

    assert allowed is False
    assert expected_message in message
