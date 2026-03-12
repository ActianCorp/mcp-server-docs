# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.

# Pytest harness for natural language prompt tests against MCP.

import os
import json
import pytest
from pathlib import Path
from datetime import datetime

from prompt_parser import parse_prompt_file
from conftest import parse_setup_teardown, _execute_sql_list


def _get_prompt_file(config) -> str:
    prompt_file = config.getoption("--prompt-file", default=None)
    if not prompt_file:
        prompt_file = str(Path(__file__).parent / "natural_language_requests.md")
    return prompt_file


def _load_test_cases(config) -> list[dict]:
    return parse_prompt_file(_get_prompt_file(config))


def pytest_generate_tests(metafunc):
    if "test_case" in metafunc.fixturenames:
        cases = _load_test_cases(metafunc.config)
        ids = [f"TEST-{c['id']}-{c['name']}" for c in cases]
        metafunc.parametrize("test_case", cases, ids=ids)


# --- trace logging

@pytest.fixture(scope="module")
def trace_log_path():
    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join("results", f"natural_language_{timestamp}.jsonl")


def _write_trace(path: str, record: dict):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, default=str) + '\n')


# --- setup/teardown from prompt file

@pytest.fixture(scope="module", autouse=True)
def setup_teardown_from_prompt_file(request):
    # MCP server is readonly — setup must go through a direct connection
    import pyodbc
    from conftest import TEST_DSN

    md_path = _get_prompt_file(request.config)
    if not os.path.exists(md_path):
        yield
        return

    setup_stmts, teardown_stmts = parse_setup_teardown(md_path)

    conn = pyodbc.connect(f"DSN={TEST_DSN}", autocommit=True)
    cur = conn.cursor()
    for sql in setup_stmts:
        try:
            cur.execute(sql)
        except pyodbc.Error:
            if not sql.strip().upper().startswith("DROP"):
                raise

    yield

    for sql in teardown_stmts:
        try:
            cur.execute(sql)
        except pyodbc.Error:
            pass
    cur.close()
    conn.close()


@pytest.mark.language
@pytest.mark.asyncio
async def test_natural_language(llm_client, test_case, trace_log_path):
    start = datetime.now()

    response = await llm_client.chat(test_case["prompt"])

    elapsed_ms = (datetime.now() - start).total_seconds() * 1000

    # Basic validation: non-empty, non-error response
    assert response, f"Empty response for TEST {test_case['id']}: {test_case['name']}"

    response_lower = response.lower()
    is_error = ("error" in response_lower and "error" in response_lower[:50])

    # Keyword validation (if keywords provided)
    keywords = test_case.get("keywords", [])
    matched_keywords = [kw for kw in keywords if kw.lower() in response_lower]
    keyword_pass = len(matched_keywords) > 0 if keywords else True

    # Row validation (if validate_rows provided)
    validate_rows = test_case.get("validate_rows", "")
    row_pass = True  # default: any non-error response = success

    # Write trace record
    _write_trace(trace_log_path, {
        "timestamp": datetime.now().isoformat(),
        "test_id": test_case["id"],
        "test_name": test_case["name"],
        "prompt": test_case["prompt"][:200],
        "response_length": len(response),
        "elapsed_ms": round(elapsed_ms),
        "is_error": is_error,
        "keywords": keywords,
        "matched_keywords": matched_keywords,
        "keyword_pass": keyword_pass,
        "validate_rows": validate_rows,
        "success": not is_error and keyword_pass and row_pass,
    })

    if is_error:
        pytest.fail(f"Error response for TEST {test_case['id']}: {response[:200]}")

    if not keyword_pass:
        pytest.fail(
            f"No keywords matched for TEST {test_case['id']}. "
            f"Expected any of {keywords}, response: {response[:200]}"
        )
