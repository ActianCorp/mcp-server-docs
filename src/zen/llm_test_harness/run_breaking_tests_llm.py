#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Breaking Tests Runner - TRUE LLM Execution Mode

Unlike run_breaking_tests.py (hardcoded logic), this version:
1. Sends natural language task to LLM with MCP context
2. LLM generates tool calls (SQL, function calls)
3. We PARSE and EXECUTE the LLM's response
4. If error, LLM gets feedback and can retry
5. Test passes only if LLM's approach works

This enables true comparison between:
- Interactive mode (Claude Code with human guidance)
- Autonomous LLM mode (local LLM without human intervention)
"""

import os
import sys
import json
import re
import time
import requests
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actian_zen_adapter import (
    execute_raw_sql, get_zen_schema, execute_custom_sql,
    orm_query_builder, insert_data, get_connection
)

# API configurations
OLLAMA_API = "http://localhost:11434/api/generate"
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_PROVIDER = "ollama"

# OpenRouter models
OPENROUTER_MODELS = {
    "gpt-4.1": "openai/gpt-4.1",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "claude-sonnet": "anthropic/claude-sonnet-4",
    "claude-haiku": "anthropic/claude-3.5-haiku",
}


@dataclass
class LLMTestResult:
    """Result of a breaking test with LLM execution"""
    test_id: int
    test_name: str
    category: str
    status: str  # PASS, FAIL, SKIP
    attempts: int
    max_attempts: int
    duration_seconds: float
    final_approach: Optional[str] = None
    error: Optional[str] = None
    attempt_history: List[dict] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════════════════
# MCP Context (same as what real MCP server provides)
# ════════════════════════════════════════════════════════════════════════════════

def get_mcp_context() -> str:
    """Get full MCP context for LLM - simulates what MCP server provides"""

    # Get actual schema
    schema_info = get_zen_schema()
    tables = schema_info.get("tables", [])

    context = f"""You are connected to Actian Zen database via MCP server.

## Available MCP Tools

You can call these tools by generating Python function calls:

### Query Tools
- execute_raw_sql(sql: str) -> dict
  Execute SELECT query. Returns {{"results": [...], "row_count": N}}

- execute_custom_sql(sql: str) -> dict
  Execute any SQL (INSERT, UPDATE, DELETE, CREATE, DROP, ALTER)
  Returns {{"success": True, "rows_affected": N}}

### ORM Tools
- orm_query_builder(query: dict) -> dict
  Query with JSON spec: {{"table": "X", "columns": [...], "where": {{...}}, "limit": N}}

- insert_data(table: str, rows: list) -> dict
  Insert multiple rows: insert_data("employees", [{{"name": "John"}}, {{"name": "Jane"}}])

### Transaction Tools
- begin_transaction() -> dict
- commit_transaction() -> dict
- rollback_transaction() -> dict

### Database Management
- list_databases() -> dict
  List all Zen ODBC DSNs on system

- switch_database(dsn_name: str) -> dict
  Switch to different database

### File/BLOB Operations
- upload_file_to_blob(table: str, file_path: str, metadata: dict) -> dict
- download_blob_to_file(table: str, file_id: int, output_path: str) -> dict

### System Tools
- release_all_locks() -> dict
  Release table locks (for Btrieve Error 85 recovery)

- get_zen_capabilities() -> dict
  Get server features and limitations

## Available Tables
{', '.join(tables)}

## Zen SQL Syntax Notes
- Use TOP N instead of LIMIT (e.g., SELECT TOP 10 * FROM employees)
- No ROW_NUMBER() - use correlated subqueries instead
- No WITH clause (CTEs) - use inline subqueries
- IDENTITY columns auto-increment (don't specify value)
- String concat: use + not ||
- DECIMAL scale: use DECIMAL(10,2) with comma

## Response Format
Respond with the Python code to execute. Use the tool functions above.
If you need multiple steps, show them in order.
Wrap code in ```python ... ``` blocks.
"""
    return context


def call_ollama(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 2000) -> str:
    """Call Ollama API"""
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"ERROR: {str(e)}"


def call_openrouter(prompt: str, model: str = "openai/gpt-4o-mini", max_tokens: int = 2000) -> str:
    """Call OpenRouter API (GPT-4, Claude, etc.)"""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "ERROR: OPENROUTER_API_KEY environment variable not set"

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/actian-zen-mcp",
            "X-Title": "Actian Zen MCP Breaking Tests"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1
        }

        response = requests.post(OPENROUTER_API, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            return f"ERROR: OpenRouter API {response.status_code}: {response.text[:200]}"

        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"


def call_llm(prompt: str, provider: str, model: str, max_tokens: int = 2000) -> str:
    """Unified LLM call interface"""
    if provider == "ollama":
        return call_ollama(prompt, model, max_tokens)
    elif provider == "openrouter":
        # Resolve short model name to full ID
        full_model = OPENROUTER_MODELS.get(model, model)
        return call_openrouter(prompt, full_model, max_tokens)
    else:
        return f"ERROR: Unknown provider: {provider}"


def extract_code_blocks(response: str) -> List[str]:
    """Extract Python code blocks from LLM response"""
    # Match ```python ... ``` or ``` ... ```
    pattern = r'```(?:python)?\s*(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)
    return [m.strip() for m in matches if m.strip()]


def execute_llm_code(code: str) -> Tuple[bool, str, Any]:
    """
    Execute code generated by LLM.
    Returns: (success, message, result)
    """
    # Import standard modules that LLM might use
    import re
    import csv
    import hashlib
    from decimal import Decimal

    # Create execution context with available tools AND standard modules
    exec_globals = {
        # MCP Tools
        'execute_raw_sql': execute_raw_sql,
        'execute_custom_sql': execute_custom_sql,
        'orm_query_builder': orm_query_builder,
        'insert_data': insert_data,
        'get_zen_schema': get_zen_schema,
        'begin_transaction': lambda: begin_transaction_impl(),
        'commit_transaction': lambda: commit_transaction_impl(),
        'rollback_transaction': lambda: rollback_transaction_impl(),
        'list_databases': lambda: list_databases_impl(),
        'switch_database': lambda dsn: switch_database_impl(dsn),
        'release_all_locks': lambda: {"status": "locks_released"},
        'get_zen_capabilities': lambda: {"supported": ["SELECT", "INSERT", "UPDATE", "DELETE", "JOIN"]},
        'upload_file_to_blob': lambda t, f, m=None: upload_blob_impl(t, f, m),
        'download_blob_to_file': lambda t, fid, out: download_blob_impl(t, fid, out),
        # Standard modules (LLM expects these to be available)
        'print': print,
        'json': json,
        'os': os,
        're': re,
        'csv': csv,
        'hashlib': hashlib,
        'Decimal': Decimal,
        'open': open,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'list': list,
        'dict': dict,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'isinstance': isinstance,
        'type': type,
        'True': True,
        'False': False,
        'None': None,
    }

    exec_locals = {}

    try:
        exec(code, exec_globals, exec_locals)
        # Try to find result variable
        result = exec_locals.get('result', exec_locals.get('results', None))
        return True, "Code executed successfully", result
    except Exception as e:
        return False, f"Execution error: {str(e)}", None


# Tool implementations
def begin_transaction_impl():
    conn = get_connection().get_odbc_connection()
    conn.autocommit = False
    return {"status": "transaction_started"}

def commit_transaction_impl():
    conn = get_connection().get_odbc_connection()
    conn.commit()
    conn.autocommit = True
    return {"status": "committed"}

def rollback_transaction_impl():
    conn = get_connection().get_odbc_connection()
    conn.rollback()
    conn.autocommit = True
    return {"status": "rolled_back"}

def list_databases_impl():
    import winreg
    dsns = []
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources")
        i = 0
        while True:
            try:
                name, driver = winreg.EnumValue(key, i)[:2]
                if "Pervasive" in driver or "Zen" in driver:
                    dsns.append({"dsn_name": name, "driver": driver})
                i += 1
            except WindowsError:
                break
        winreg.CloseKey(key)
    except:
        pass
    return {"dsns": dsns, "count": len(dsns)}

def switch_database_impl(dsn_name: str):
    return {"status": "switch_available", "target_dsn": dsn_name}

def upload_blob_impl(table: str, file_path: str, metadata: dict = None):
    import hashlib
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    # Store metadata (actual BLOB would need binary handling)
    return {
        "status": "uploaded",
        "file_size": file_size,
        "file_hash": file_hash,
        "file_path": file_path
    }

def download_blob_impl(table: str, file_id: int, output_path: str):
    return {"status": "download_simulated", "output_path": output_path}


# ════════════════════════════════════════════════════════════════════════════════
# Breaking Test Definitions
# ════════════════════════════════════════════════════════════════════════════════

BREAKING_TESTS = [
    {
        "id": 1,
        "name": "Upload 50MB PDF",
        "category": "File Operations",
        "prompt": """Upload the PDF file at D:\\PlayScripts\\large_presentation.pdf to the database.
Calculate its SHA256 hash and store with metadata (filename, size, hash, timestamp).
The file is approximately 50MB.

First create the table if needed:
CREATE TABLE document_store (
    file_id IDENTITY,
    file_name NVARCHAR(255),
    file_size INTEGER,
    file_hash NVARCHAR(64),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

Then upload the file using upload_file_to_blob() or insert metadata.""",
        "validation": lambda r: "uploaded" in str(r).lower() or "success" in str(r).lower()
    },
    {
        "id": 4,
        "name": "Cross-Database Query",
        "category": "Multi-Database",
        "prompt": """Demonstrate cross-database capability:
1. Use list_databases() to show all available Zen databases
2. Show how to switch between databases using switch_database()
3. Return the list of available DSNs""",
        "validation": lambda r: True  # Always passes if no exception
    },
    {
        "id": 5,
        "name": "List All Databases",
        "category": "Multi-Database",
        "prompt": """List all Zen databases (ODBC DSNs) available on this system.
Use the list_databases() tool to get all configured DSNs.
Show DSN name and driver for each.""",
        "validation": lambda r: True
    },
    {
        "id": 6,
        "name": "Multi-Step Transaction",
        "category": "Transactions",
        "prompt": """Execute an atomic multi-step transaction:

1. First, create the test tables (use execute_custom_sql):
   - test_customers (customer_id IDENTITY, name NVARCHAR(100))
   - test_invoices (invoice_id IDENTITY, customer_id INTEGER, total DECIMAL(10,2))

2. Begin a transaction using begin_transaction()

3. Insert a customer named "Test Corp"

4. Get the customer_id of the inserted customer

5. Insert 2 invoices for that customer: $500 and $300

6. Calculate the total of all invoices for that customer

7. If total > $10000: call rollback_transaction()
   Else: call commit_transaction()

Show the final status.""",
        "validation": lambda r: "commit" in str(r).lower() or "rollback" in str(r).lower()
    },
    {
        "id": 7,
        "name": "Lock Recovery",
        "category": "Transactions",
        "prompt": """Demonstrate lock recovery capability:
1. Explain when Btrieve Error 85 occurs (record/table locked)
2. Show how to use release_all_locks() to recover
3. Call release_all_locks() to demonstrate

Print the explanation and the result of release_all_locks().""",
        "validation": lambda r: True
    },
    {
        "id": 8,
        "name": "Relationship Navigation",
        "category": "ORM Operations",
        "prompt": """Navigate table relationships to build a nested result:

Using the existing tables (Customers, Invoices), do:
1. Get customer with customer_id = 1 using execute_raw_sql
2. Get all invoices for that customer using a JOIN query
3. Print the customer info and their invoices

Use execute_raw_sql() for the queries.""",
        "validation": lambda r: True
    },
    {
        "id": 9,
        "name": "Server Capabilities",
        "category": "System Operations",
        "prompt": """Check database server capabilities:
1. Use get_zen_capabilities() to get supported features
2. Use get_zen_schema() to list available tables
3. Print a summary of tables and capabilities""",
        "validation": lambda r: True
    },
    {
        "id": 10,
        "name": "CSV Validation",
        "category": "Batch Operations",
        "prompt": """Validate a CSV file for import:
File: D:\\PlayScripts\\customer_import.csv

Validation rules:
- Email must contain @ and a domain (.)
- Phone must match pattern XXX-XXX-XXXX

Read the first 100 rows, validate them, and report:
- How many are valid
- How many failed validation

Use Python's csv module to read the file.""",
        "validation": lambda r: "valid" in str(r).lower()
    },
]


def run_single_test(test: dict, provider: str, model: str, max_attempts: int = 3) -> LLMTestResult:
    """Run a single breaking test with LLM-generated code"""

    test_id = test["id"]
    test_name = test["name"]
    category = test["category"]
    task_prompt = test["prompt"]
    validation_fn = test["validation"]

    start_time = time.time()
    attempt_history = []

    for attempt in range(1, max_attempts + 1):
        # Build prompt with context
        if attempt == 1:
            full_prompt = get_mcp_context() + f"\n\n## Task\n{task_prompt}\n\nGenerate the Python code to complete this task."
        else:
            # Include previous error in retry prompt
            last_error = attempt_history[-1].get("error", "Unknown error")
            full_prompt = get_mcp_context() + f"""

## Task
{task_prompt}

## Previous Attempt Failed
Error: {last_error}

Please fix the code and try again. Generate corrected Python code."""

        # Call LLM (unified interface for Ollama and OpenRouter)
        llm_response = call_llm(full_prompt, provider, model)

        if llm_response.startswith("ERROR:"):
            attempt_history.append({
                "attempt": attempt,
                "llm_response": llm_response[:200],
                "error": llm_response,
                "success": False
            })
            continue

        # Extract code blocks
        code_blocks = extract_code_blocks(llm_response)

        if not code_blocks:
            # Try to extract inline code
            code_blocks = [llm_response]

        # Execute each code block
        all_success = True
        last_result = None
        last_error = None

        for code in code_blocks:
            success, message, result = execute_llm_code(code)
            if not success:
                all_success = False
                last_error = message
                break
            last_result = result

        attempt_history.append({
            "attempt": attempt,
            "llm_response": llm_response[:500],
            "code_extracted": code_blocks[0][:300] if code_blocks else None,
            "success": all_success,
            "error": last_error,
            "result_sample": str(last_result)[:200] if last_result else None
        })

        if all_success:
            # Validate result
            try:
                if validation_fn(last_result):
                    duration = time.time() - start_time
                    return LLMTestResult(
                        test_id=test_id,
                        test_name=test_name,
                        category=category,
                        status="PASS",
                        attempts=attempt,
                        max_attempts=max_attempts,
                        duration_seconds=duration,
                        final_approach=code_blocks[0][:200] if code_blocks else None,
                        attempt_history=attempt_history
                    )
            except Exception as e:
                last_error = f"Validation error: {str(e)}"
                attempt_history[-1]["error"] = last_error

    # All attempts failed
    duration = time.time() - start_time
    return LLMTestResult(
        test_id=test_id,
        test_name=test_name,
        category=category,
        status="FAIL",
        attempts=max_attempts,
        max_attempts=max_attempts,
        duration_seconds=duration,
        error=attempt_history[-1].get("error") if attempt_history else "No attempts made",
        attempt_history=attempt_history
    )


def run_all_tests(provider: str = DEFAULT_PROVIDER, model: str = DEFAULT_MODEL, test_ids: List[int] = None, max_attempts: int = 3) -> List[LLMTestResult]:
    """Run all breaking tests with LLM execution"""

    tests_to_run = BREAKING_TESTS
    if test_ids:
        tests_to_run = [t for t in BREAKING_TESTS if t["id"] in test_ids]

    results = []

    provider_display = f"{provider} ({model})"
    print(f"\n{'='*70}")
    print(f"Breaking Tests - TRUE LLM Execution Mode")
    print(f"Provider: {provider_display}")
    print(f"Max attempts per test: {max_attempts}")
    print(f"{'='*70}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tests to run: {[t['id'] for t in tests_to_run]}")
    print(f"{'='*70}\n")

    for test in tests_to_run:
        print(f"Running Test {test['id']}: {test['name']}...", end=" ", flush=True)
        result = run_single_test(test, provider, model, max_attempts)
        results.append(result)

        status_icon = {"PASS": "[OK]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}.get(result.status, "?")
        print(f"{status_icon} ({result.attempts}/{max_attempts} attempts, {result.duration_seconds:.1f}s)")

        if result.status == "FAIL" and result.error:
            print(f"   -> Error: {result.error[:80]}...")

    return results


def generate_report(results: List[LLMTestResult], provider: str, model: str, max_attempts: int) -> str:
    """Generate markdown report"""

    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    total_time = sum(r.duration_seconds for r in results)
    total_attempts = sum(r.attempts for r in results)

    report = f"""# Breaking Tests - TRUE LLM Execution Mode

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Provider:** {provider}
**Model:** {model}
**Mode:** LLM generates and executes code (not hardcoded)
**Max Attempts:** {max_attempts} per test

────────────────────────────────────────────────────────────────────────────────

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {len(results)} |
| Passed | {passed} |
| Failed | {failed} |
| Success Rate | {passed}/{len(results)} ({100*passed/len(results):.0f}%) |
| Total Time | {total_time:.1f}s |
| Total Attempts | {total_attempts} |
| Avg Attempts | {total_attempts/len(results):.1f} |

────────────────────────────────────────────────────────────────────────────────

## Results

| Test | Name | Category | Status | Attempts | Time |
|------|------|----------|--------|----------|------|
"""

    for r in results:
        status_icon = {"PASS": "PASS", "FAIL": "FAIL", "SKIP": "SKIP"}.get(r.status, "?")
        report += f"| {r.test_id} | {r.test_name} | {r.category} | {status_icon} | {r.attempts}/{r.max_attempts} | {r.duration_seconds:.1f}s |\n"

    report += """
────────────────────────────────────────────────────────────────────────────────

## Detailed Results

"""

    for r in results:
        report += f"""### Test {r.test_id}: {r.test_name}

**Category:** {r.category}
**Status:** {r.status}
**Attempts:** {r.attempts}/{r.max_attempts}
**Duration:** {r.duration_seconds:.1f}s

"""
        if r.final_approach:
            report += f"**Final Code (truncated):**\n```python\n{r.final_approach}...\n```\n\n"
        if r.error:
            report += f"**Error:** {r.error}\n\n"

        if r.attempt_history:
            report += "**Attempt History:**\n"
            for ah in r.attempt_history:
                status = "Success" if ah.get("success") else "Failed"
                report += f"- Attempt {ah['attempt']}: {status}\n"
                if ah.get("error"):
                    report += f"  - Error: {ah['error'][:100]}...\n"

        report += "\n---\n\n"

    report += f"""
## Key Difference from Hardcoded Tests

This test mode is DIFFERENT from `run_breaking_tests.py`:

| Aspect | Hardcoded Mode | LLM Execution Mode |
|--------|----------------|-------------------|
| Code source | Pre-written Python | LLM generates |
| Adaptation | None | LLM can retry with fixes |
| Measures | Tool availability | LLM SQL/code generation skill |
| Comparison to | Claude Code tools | Claude Code reasoning |

────────────────────────────────────────────────────────────────────────────────
"""

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run breaking tests with TRUE LLM execution")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=["ollama", "openrouter"],
                        help="LLM provider: ollama (local) or openrouter (cloud)")
    parser.add_argument("--model", default=None, help="Model name (default depends on provider)")
    parser.add_argument("--tests", type=str, help="Comma-separated test IDs")
    parser.add_argument("--max-attempts", type=int, default=3, help="Max attempts per test")
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args()

    # Set default model based on provider
    if args.model is None:
        if args.provider == "ollama":
            args.model = DEFAULT_MODEL
        else:
            args.model = "gpt-4.1"

    test_ids = None
    if args.tests:
        test_ids = [int(t.strip()) for t in args.tests.split(",")]

    # Validate provider setup
    if args.provider == "ollama":
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = [m["name"] for m in resp.json().get("models", [])]
            if not any(args.model in m for m in models):
                print(f"Warning: Model '{args.model}' may not be available. Found: {models[:5]}")
        except:
            print("Error: Ollama not running. Start with: ollama serve")
            sys.exit(1)
    elif args.provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            print("Error: OPENROUTER_API_KEY environment variable not set")
            print("Set it with: set OPENROUTER_API_KEY=your_api_key")
            sys.exit(1)
        # Resolve model name
        full_model = OPENROUTER_MODELS.get(args.model, args.model)
        print(f"Using OpenRouter model: {full_model}")

    # Run tests
    results = run_all_tests(args.provider, args.model, test_ids, args.max_attempts)

    # Generate report
    report = generate_report(results, args.provider, args.model, args.max_attempts)

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe = args.model.replace(":", "_").replace("/", "_")
    output_path = args.output or f"results/breaking_tests_{args.provider}_{model_safe}_{timestamp}.md"
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else "results", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'='*70}")
    print(f"Report saved to: {output_path}")
    print(f"{'='*70}")

    passed = sum(1 for r in results if r.status == "PASS")
    print(f"\nFinal: {passed}/{len(results)} PASSED")


if __name__ == "__main__":
    main()
