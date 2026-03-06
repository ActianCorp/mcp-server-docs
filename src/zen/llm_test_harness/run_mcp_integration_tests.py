#!/usr/bin/env python3
"""
MCP Integration Tests for Actian Zen

These tests simulate FULL MCP interaction:
1. LLM receives prompt + MCP resources (schema, capabilities, query-patterns)
2. LLM generates SQL
3. SQL is executed on Zen database
4. If error, LLM receives error + hint and can retry
5. Test passes if correct results returned (within max_attempts)

This tests the complete error-recovery loop that real MCP clients experience.

Usage:
    python run_mcp_integration_tests.py
    python run_mcp_integration_tests.py --provider openrouter --model claude-sonnet-4
    python run_mcp_integration_tests.py --max-attempts 3
"""

import os
import sys
import json
import time
import yaml
import argparse
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from unified test runner
from run_llm_tests import (
    LLMProvider, create_provider, load_config,
    OpenRouterProvider, AnthropicProvider, OllamaProvider, LMStudioProvider
)


def resolve_env_vars(config: dict) -> dict:
    """Resolve environment variables in config values"""
    import re

    def resolve_value(value):
        if isinstance(value, str) and "${" in value:
            # Replace ${VAR_NAME} with environment variable
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, value)
            for var_name in matches:
                env_value = os.environ.get(var_name, "")
                value = value.replace(f"${{{var_name}}}", env_value)
        return value

    def resolve_dict(d):
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = resolve_dict(value)
            elif isinstance(value, list):
                result[key] = [resolve_value(v) if isinstance(v, str) else v for v in value]
            else:
                result[key] = resolve_value(value)
        return result

    return resolve_dict(config)

# Import adapter for database operations
from actian_zen_adapter import execute_raw_sql, get_zen_schema


# ════════════════════════════════════════════════════════════════════════════════
# MCP Resources (simulated - in real MCP client must request via resources/read)
# ════════════════════════════════════════════════════════════════════════════════

def get_schema_resource() -> str:
    """Get database schema as MCP resource - FULL schema with all columns"""
    try:
        # First get list of tables
        tables_info = get_zen_schema()
        tables = tables_info.get("tables", [])

        # Then get detailed schema for each table
        full_schema = {"tables": {}}
        for table in tables:
            table_schema = get_zen_schema(table)
            if "columns" in table_schema:
                full_schema["tables"][table] = {
                    "columns": [col["name"] for col in table_schema["columns"]],
                    "column_details": table_schema["columns"],
                    "primary_key": table_schema.get("primary_key", [])
                }

        return json.dumps(full_schema, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_capabilities_resource() -> str:
    """Get Zen capabilities as MCP resource"""
    return json.dumps({
        "supported": [
            "SELECT", "INSERT", "UPDATE", "DELETE",
            "JOIN (INNER, LEFT, RIGHT)",
            "Subqueries (scalar, IN, EXISTS)",
            "Correlated subqueries",
            "GROUP BY", "HAVING", "ORDER BY",
            "TOP N", "DISTINCT",
            "CASE WHEN", "COALESCE", "NULLIF",
            "String functions (UPPER, LOWER, SUBSTRING, CHAR_LENGTH)",
            "Date functions (YEAR, MONTH, DAY, DATEPART)",
            "Aggregate functions (COUNT, SUM, AVG, MIN, MAX)"
        ],
        "not_supported": [
            "Window functions (ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD)",
            "OVER clause (PARTITION BY, ORDER BY)",
            "CTEs (WITH clause)",
            "LIMIT/OFFSET (use TOP instead)",
            "FULL OUTER JOIN",
            "LATERAL joins",
            "GROUPING SETS, CUBE, ROLLUP"
        ],
        "syntax_differences": [
            "CAST(x AS DECIMAL(10:2)) - use COLON not comma for scale",
            "String concatenation: use + not ||",
            "TOP N goes after SELECT: SELECT TOP 10 * FROM ...",
            "Date literals: '2024-01-15' (ISO format)"
        ]
    }, indent=2)


def get_query_patterns_resource() -> str:
    """Get Zen query patterns/workarounds as MCP resource"""
    return json.dumps({
        "window_function_workarounds": {
            "ROW_NUMBER_simple": {
                "problem": "ROW_NUMBER() OVER (ORDER BY col) not supported",
                "workaround": "Use correlated subquery with COUNT",
                "example": {
                    "standard_sql": "SELECT name, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rank FROM employees",
                    "zen_sql": "SELECT e1.first_name, (SELECT COUNT(*) + 1 FROM employees e2 WHERE e2.salary > e1.salary) AS rank FROM employees e1 ORDER BY rank"
                }
            },
            "ROW_NUMBER_partition": {
                "problem": "ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary) not supported",
                "workaround": "Use correlated subquery with partition condition",
                "example": {
                    "standard_sql": "SELECT name, dept, ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS dept_rank FROM employees",
                    "zen_sql": "SELECT e1.first_name, e1.department_id, (SELECT COUNT(*) + 1 FROM employees e2 WHERE e2.department_id = e1.department_id AND e2.salary > e1.salary) AS dept_rank FROM employees e1"
                }
            },
            "AVG_OVER_partition": {
                "problem": "AVG(col) OVER (PARTITION BY dept) not supported",
                "workaround": "Use correlated subquery for partition average",
                "example": {
                    "standard_sql": "SELECT name, salary, AVG(salary) OVER (PARTITION BY department_id) AS dept_avg FROM employees",
                    "zen_sql": "SELECT e.first_name, e.salary, (SELECT AVG(e2.salary) FROM employees e2 WHERE e2.department_id = e.department_id) AS dept_avg FROM employees e"
                }
            }
        },
        "cte_workarounds": {
            "simple_cte": {
                "problem": "WITH clause not supported",
                "workaround": "Use inline subquery in FROM clause",
                "example": {
                    "standard_sql": "WITH dept_avg AS (SELECT department_id, AVG(salary) AS avg_sal FROM employees GROUP BY department_id) SELECT e.* FROM employees e JOIN dept_avg d ON e.department_id = d.department_id WHERE e.salary > d.avg_sal",
                    "zen_sql": "SELECT e.* FROM employees e JOIN (SELECT department_id, AVG(salary) AS avg_sal FROM employees GROUP BY department_id) d ON e.department_id = d.department_id WHERE e.salary > d.avg_sal"
                }
            }
        }
    }, indent=2)


# ════════════════════════════════════════════════════════════════════════════════
# MCP Integration Test Definition
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class MCPIntegrationTest:
    """Definition of an MCP integration test"""
    id: int
    name: str
    prompt: str  # Natural language request
    validation: dict  # How to validate results
    requires_tables: List[str] = field(default_factory=list)  # Tables that must exist
    max_attempts: int = 3  # Max LLM retries

    def to_dict(self):
        return asdict(self)


@dataclass
class MCPTestResult:
    """Result of an MCP integration test"""
    test_id: int
    test_name: str
    success: bool
    attempts: int
    final_sql: Optional[str] = None
    error: Optional[str] = None
    results_sample: Optional[List[dict]] = None
    execution_time_ms: float = 0
    tokens_used: int = 0
    attempt_history: List[dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ════════════════════════════════════════════════════════════════════════════════
# Test Definitions
# ════════════════════════════════════════════════════════════════════════════════

MCP_INTEGRATION_TESTS = [
    MCPIntegrationTest(
        id=1,
        name="Department Average (Window Function Workaround)",
        prompt="Show each employee's salary alongside their department's average salary in the same row",
        validation={
            "type": "columns_exist",
            "required_columns": ["salary", "dept_avg"],
            "min_rows": 1
        },
        requires_tables=["employees"]
    ),
    MCPIntegrationTest(
        id=2,
        name="Salary Rank (Correlated Subquery)",
        prompt="Rank all employees by salary from highest to lowest, showing their name and rank number",
        validation={
            "type": "columns_exist",
            "required_columns": ["rank"],
            "min_rows": 1
        },
        requires_tables=["employees"]
    ),
    MCPIntegrationTest(
        id=3,
        name="Top N Per Department",
        prompt="Show the top 3 highest paid employees in each department",
        validation={
            "type": "result_logic",
            "check": "max_per_group",
            "group_column": "department_id",
            "max_per_group": 3
        },
        requires_tables=["employees"]
    ),
    MCPIntegrationTest(
        id=4,
        name="Above Department Average",
        prompt="Find employees who earn more than the average salary of their department",
        validation={
            "type": "columns_exist",
            "required_columns": ["first_name", "salary"],
            "min_rows": 0  # Could be 0 if all earn below average
        },
        requires_tables=["employees"]
    ),
    MCPIntegrationTest(
        id=5,
        name="CTE Alternative (Inline Subquery)",
        prompt="Show employees with their department's total employee count, but only for departments with more than 2 employees",
        validation={
            "type": "columns_exist",
            "required_columns": ["first_name"],
            "min_rows": 0
        },
        requires_tables=["employees", "departments"]
    ),
]


# ════════════════════════════════════════════════════════════════════════════════
# MCP Integration Test Runner
# ════════════════════════════════════════════════════════════════════════════════

class MCPIntegrationTestRunner:
    """Runs MCP integration tests with full error-recovery loop"""

    def __init__(self, provider: LLMProvider, max_attempts: int = 3, verbose: bool = False):
        self.provider = provider
        self.max_attempts = max_attempts
        self.verbose = verbose

        # Load MCP resources once
        self.schema = get_schema_resource()
        self.capabilities = get_capabilities_resource()
        self.query_patterns = get_query_patterns_resource()

    def build_system_prompt(self) -> str:
        """Build system prompt with MCP resources"""
        return f"""You are a SQL expert working with Actian Zen database via MCP server.

## DATABASE SCHEMA
{self.schema}

## ZEN CAPABILITIES
{self.capabilities}

## QUERY PATTERNS (Zen-specific workarounds)
{self.query_patterns}

## INSTRUCTIONS
1. Generate SQL that works with Zen database
2. Use correlated subqueries instead of window functions (OVER clause)
3. Use inline subqueries instead of CTEs (WITH clause)
4. Return ONLY the SQL query, no explanations

If your SQL fails, I will show you the error and you should fix it.
"""

    def run_single_test(self, test: MCPIntegrationTest) -> MCPTestResult:
        """Run a single MCP integration test with retry loop"""
        start_time = time.time()
        attempts = []
        total_tokens = 0
        last_error = None

        # Build full prompt with system context
        system_prompt = self.build_system_prompt()

        for attempt in range(1, self.max_attempts + 1):
            attempt_record = {"attempt": attempt}

            # Build prompt for this attempt
            if attempt == 1:
                # First attempt: system prompt + user request
                full_prompt = f"""{system_prompt}

USER REQUEST: {test.prompt}

Generate a SELECT query that answers this request. Use ONLY the column names from the schema above.
Return ONLY the SQL, no explanations."""
            else:
                # Retry: include error and ask to fix
                full_prompt = f"""{system_prompt}

USER REQUEST: {test.prompt}

PREVIOUS ATTEMPT FAILED with error:
{last_error}

Please fix the SQL. Remember:
- Use ONLY column names from the schema above (e.g., first_name, NOT name or employee_name)
- Use correlated subqueries instead of window functions (OVER clause)
- Return ONLY a SELECT query, no explanations."""

            # Get SQL from LLM
            try:
                response, tokens = self.provider.call(full_prompt)
                total_tokens += tokens
                attempt_record["llm_response"] = response

                # Extract SQL
                sql = self._extract_sql(response)
                attempt_record["sql"] = sql

                if not sql:
                    attempt_record["error"] = "No SQL found in response"
                    attempts.append(attempt_record)
                    last_error = "No SQL found in response"
                    continue

            except Exception as e:
                attempt_record["error"] = f"LLM call failed: {str(e)}"
                attempts.append(attempt_record)
                last_error = str(e)
                continue

            # Execute SQL
            try:
                result = execute_raw_sql(sql)
                attempt_record["db_result"] = result

                if "error" in result:
                    attempt_record["error"] = result["error"]
                    attempts.append(attempt_record)
                    last_error = result["error"]
                    continue

                # Validate results
                validation_result = self._validate_results(result, test.validation)
                attempt_record["validation"] = validation_result

                if validation_result["valid"]:
                    # Success!
                    attempts.append(attempt_record)
                    return MCPTestResult(
                        test_id=test.id,
                        test_name=test.name,
                        success=True,
                        attempts=attempt,
                        final_sql=sql,
                        results_sample=result.get("results", [])[:3],
                        execution_time_ms=(time.time() - start_time) * 1000,
                        tokens_used=total_tokens,
                        attempt_history=attempts
                    )
                else:
                    attempt_record["error"] = validation_result["reason"]
                    attempts.append(attempt_record)
                    last_error = validation_result["reason"]

            except Exception as e:
                attempt_record["error"] = f"Execution failed: {str(e)}"
                attempts.append(attempt_record)
                last_error = str(e)

        # All attempts failed
        return MCPTestResult(
            test_id=test.id,
            test_name=test.name,
            success=False,
            attempts=self.max_attempts,
            error=last_error,
            execution_time_ms=(time.time() - start_time) * 1000,
            tokens_used=total_tokens,
            attempt_history=attempts
        )

    def _extract_sql(self, text: str) -> Optional[str]:
        """Extract SQL from LLM response"""
        import re

        # Try markdown code block first
        if "```" in text:
            match = re.search(r"```(?:sql)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Try to find SELECT statement
        match = re.search(r"(SELECT\s+.+?)(?:;|$)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def _validate_results(self, result: dict, validation: dict) -> dict:
        """Validate query results against test criteria"""
        results = result.get("results", [])

        if validation["type"] == "columns_exist":
            required = validation.get("required_columns", [])
            min_rows = validation.get("min_rows", 1)

            if len(results) < min_rows:
                return {"valid": False, "reason": f"Expected at least {min_rows} rows, got {len(results)}"}

            if results:
                actual_columns = [c.lower() for c in results[0].keys()]
                for col in required:
                    # Check if column exists (case-insensitive, partial match)
                    if not any(col.lower() in ac for ac in actual_columns):
                        return {"valid": False, "reason": f"Missing required column: {col}"}

            return {"valid": True, "reason": "All columns present"}

        elif validation["type"] == "result_logic":
            # Custom validation logic
            check = validation.get("check")
            if check == "max_per_group":
                # Verify max N per group
                group_col = validation.get("group_column")
                max_per = validation.get("max_per_group", 3)

                groups = {}
                for row in results:
                    group_key = str(row.get(group_col, row.get("department_id", "unknown")))
                    groups[group_key] = groups.get(group_key, 0) + 1

                for group, count in groups.items():
                    if count > max_per:
                        return {"valid": False, "reason": f"Group {group} has {count} rows, max is {max_per}"}

                return {"valid": True, "reason": f"All groups have <= {max_per} rows"}

        return {"valid": True, "reason": "No validation required"}

    def run_all_tests(self, tests: List[MCPIntegrationTest] = None) -> dict:
        """Run all MCP integration tests"""
        if tests is None:
            tests = MCP_INTEGRATION_TESTS

        print(f"\nRunning {len(tests)} MCP Integration Tests...")
        print(f"Provider: {self.provider.__class__.__name__}")
        print(f"Model: {self.provider.model}")
        print(f"Max attempts per test: {self.max_attempts}")
        print("-" * 60)

        results = []
        passed = 0
        total_tokens = 0
        start_time = time.time()

        for test in tests:
            result = self.run_single_test(test)
            results.append(result)
            total_tokens += result.tokens_used

            if result.success:
                passed += 1
                status = f"PASS (attempt {result.attempts})"
            else:
                status = f"FAIL (after {result.attempts} attempts)"

            print(f"  [{status}] Test {result.test_id}: {result.test_name}")
            if not result.success and self.verbose:
                print(f"        Error: {result.error}")
                if result.attempt_history:
                    for h in result.attempt_history:
                        print(f"        Attempt {h['attempt']}: {h.get('error', 'OK')}")

        total_time = time.time() - start_time
        success_rate = (passed / len(tests)) * 100

        print("-" * 60)
        print(f"Results: {passed}/{len(tests)} passed ({success_rate:.1f}%)")
        print(f"Time: {total_time:.1f}s | Tokens: {total_tokens}")

        return {
            "provider": self.provider.__class__.__name__,
            "model": self.provider.model,
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "passed": passed,
            "failed": len(tests) - passed,
            "success_rate": success_rate,
            "total_time_seconds": total_time,
            "total_tokens": total_tokens,
            "max_attempts_per_test": self.max_attempts,
            "results": [r.to_dict() for r in results]
        }


# ════════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ════════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="MCP Integration Tests for Actian Zen")
    parser.add_argument("--config", default="llm_test_config.yaml", help="Config file path")
    parser.add_argument("--provider", help="Override provider (ollama, openrouter, anthropic, lmstudio)")
    parser.add_argument("--model", help="Override model")
    parser.add_argument("--max-attempts", type=int, default=3, help="Max retry attempts per test")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--save", action="store_true", help="Save results to file")

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    config = resolve_env_vars(config)

    # Override from command line
    provider_name = args.provider or config.get("provider", "ollama")
    model = args.model

    # Create provider
    provider = create_provider(provider_name, config, model)

    # Run tests
    runner = MCPIntegrationTestRunner(
        provider=provider,
        max_attempts=args.max_attempts,
        verbose=args.verbose
    )

    results = runner.run_all_tests()

    # Save results
    if args.save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mcp_integration_{provider_name}_{timestamp}"

        os.makedirs("results", exist_ok=True)

        with open(f"results/{filename}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)  # Handle date objects
        print(f"\nResults saved to: results/{filename}.json")

    return 0 if results["passed"] == results["total_tests"] else 1


if __name__ == "__main__":
    sys.exit(main())
