#!/usr/bin/env python3
"""
Unified LLM Test Runner for Actian Zen MCP Server

Supports multiple LLM providers with a single configuration file:
- Cloud: OpenRouter (GPT, Claude, Mistral, Llama, DeepSeek), Anthropic
- Local: Ollama, LM Studio

Usage:
    python run_llm_tests.py                           # Use config file
    python run_llm_tests.py --provider ollama         # Override provider
    python run_llm_tests.py --model qwen2.5-coder:14b # Override model
    python run_llm_tests.py --preset cloud            # Quick preset
    python run_llm_tests.py --list-models             # List available models
    python run_llm_tests.py --compare ollama,openrouter  # Compare providers
"""

import os
import sys
import json
import re
import time
import yaml
import argparse
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import adapter for database operations
from actian_zen_adapter import execute_raw_sql, get_zen_schema


# ════════════════════════════════════════════════════════════════════════════════
# Data Classes
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class TestResult:
    """Result of a single test"""
    test_id: int
    test_name: str
    success: bool
    error: Optional[str] = None
    sql_generated: Optional[str] = None
    execution_time_ms: float = 0
    tokens_used: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class TestSuiteResult:
    """Result of running a full test suite"""
    provider: str
    model: str
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    success_rate: float
    total_time_seconds: float
    total_tokens: int
    results: List[TestResult] = field(default_factory=list)

    def to_dict(self):
        return {
            **asdict(self),
            "results": [r.to_dict() for r in self.results]
        }


# ════════════════════════════════════════════════════════════════════════════════
# LLM Provider Interface
# ════════════════════════════════════════════════════════════════════════════════

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, config: Dict[str, Any], model: Optional[str] = None):
        self.config = config
        self.model = model or config.get("default_model")
        self.temperature = 0.1
        self.max_tokens = 500

    @abstractmethod
    def call(self, prompt: str) -> Tuple[str, int]:
        """
        Call the LLM with a prompt.

        Returns: (response_text, tokens_used)
        """
        pass

    @abstractmethod
    def check_connection(self) -> Tuple[bool, str]:
        """
        Check if the provider is available.

        Returns: (is_available, message)
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models"""
        pass


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (access to GPT, Claude, Mistral, etc.)"""

    def __init__(self, config: Dict[str, Any], model: Optional[str] = None):
        super().__init__(config, model)
        self.api_url = config.get("api_url", "https://openrouter.ai/api/v1/chat/completions")
        self.api_key = self._resolve_env(config.get("api_key", ""))

        # Resolve model ID to provider ID
        if model:
            self.model = self._resolve_model_id(model)
        else:
            self.model = config.get("default_model", "openai/gpt-4o-mini")

    def _resolve_env(self, value: str) -> str:
        """Resolve ${ENV_VAR} references"""
        if value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, "")
        return value

    def _resolve_model_id(self, model: str) -> str:
        """Resolve short model ID to full provider ID"""
        models = self.config.get("models", [])
        for m in models:
            if m.get("id") == model:
                return m.get("provider_id", model)
        # If not found, assume it's already a full ID
        return model

    def call(self, prompt: str) -> Tuple[str, int]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/actian-zen-mcp",
            "X-Title": "Actian Zen MCP Test"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return content, tokens

    def check_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "OPENROUTER_API_KEY not set"
        try:
            # Simple test call
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                return True, f"Connected (model: {self.model})"
            return False, f"API error: {response.status_code}"
        except Exception as e:
            return False, str(e)

    def list_models(self) -> List[str]:
        models = self.config.get("models", [])
        return [f"{m['id']} ({m.get('description', '')})" for m in models]


class AnthropicProvider(LLMProvider):
    """Direct Anthropic API provider"""

    def __init__(self, config: Dict[str, Any], model: Optional[str] = None):
        super().__init__(config, model)
        self.api_url = config.get("api_url", "https://api.anthropic.com/v1/messages")
        self.api_key = self._resolve_env(config.get("api_key", ""))

        if model:
            self.model = self._resolve_model_id(model)
        else:
            self.model = config.get("default_model", "claude-sonnet-4-20250514")

    def _resolve_env(self, value: str) -> str:
        if value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, "")
        return value

    def _resolve_model_id(self, model: str) -> str:
        models = self.config.get("models", [])
        for m in models:
            if m.get("id") == model:
                return m.get("provider_id", model)
        return model

    def call(self, prompt: str) -> Tuple[str, int]:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")

        data = response.json()
        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        return content, tokens

    def check_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "ANTHROPIC_API_KEY not set"
        return True, f"API key configured (model: {self.model})"

    def list_models(self) -> List[str]:
        models = self.config.get("models", [])
        return [f"{m['id']} ({m.get('description', '')})" for m in models]


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""

    def __init__(self, config: Dict[str, Any], model: Optional[str] = None):
        super().__init__(config, model)
        self.api_url = config.get("api_url", "http://localhost:11434/v1/chat/completions")
        self.models_url = config.get("models_url", "http://localhost:11434/v1/models")
        self.model = model or config.get("default_model", "qwen2.5-coder:14b")

    def call(self, prompt: str) -> Tuple[str, int]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }

        response = requests.post(self.api_url, json=payload, timeout=120)

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Filter out <think> blocks from reasoning models
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()

        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return content, tokens

    def check_connection(self) -> Tuple[bool, str]:
        try:
            response = requests.get(self.models_url, timeout=5)
            if response.status_code == 200:
                return True, f"Connected (model: {self.model})"
            return False, f"Ollama not responding: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Ollama not running. Start with: ollama serve"
        except Exception as e:
            return False, str(e)

    def list_models(self) -> List[str]:
        try:
            response = requests.get(self.models_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
        except:
            pass
        return ["(run 'ollama list' to see installed models)"]


class LMStudioProvider(LLMProvider):
    """LM Studio local LLM provider"""

    def __init__(self, config: Dict[str, Any], model: Optional[str] = None):
        super().__init__(config, model)
        self.api_url = config.get("api_url", "http://localhost:1234/v1/chat/completions")
        self.models_url = config.get("models_url", "http://localhost:1234/v1/models")
        self.model = model or config.get("default_model", "auto")

    def call(self, prompt: str) -> Tuple[str, int]:
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }

        # Only include model if not "auto"
        if self.model and self.model != "auto":
            payload["model"] = self.model

        response = requests.post(self.api_url, json=payload, timeout=120)

        if response.status_code != 200:
            raise Exception(f"LM Studio API error: {response.status_code} - {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return content, tokens

    def check_connection(self) -> Tuple[bool, str]:
        try:
            response = requests.get(self.models_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                if models:
                    model_name = models[0].get("id", "unknown")
                    return True, f"Connected (loaded: {model_name})"
                return True, "Connected (no model loaded)"
            return False, f"LM Studio not responding: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "LM Studio not running. Start the local server."
        except Exception as e:
            return False, str(e)

    def list_models(self) -> List[str]:
        try:
            response = requests.get(self.models_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
        except:
            pass
        return ["(load a model in LM Studio first)"]


# ════════════════════════════════════════════════════════════════════════════════
# Provider Factory
# ════════════════════════════════════════════════════════════════════════════════

def create_provider(provider_name: str, config: Dict[str, Any], model: Optional[str] = None) -> LLMProvider:
    """Factory function to create LLM provider"""
    providers_config = config.get("providers", {})
    provider_config = providers_config.get(provider_name, {})

    if provider_name == "openrouter":
        return OpenRouterProvider(provider_config, model)
    elif provider_name == "anthropic":
        return AnthropicProvider(provider_config, model)
    elif provider_name == "ollama":
        return OllamaProvider(provider_config, model)
    elif provider_name == "lmstudio":
        return LMStudioProvider(provider_config, model)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


# ════════════════════════════════════════════════════════════════════════════════
# Test Runner
# ════════════════════════════════════════════════════════════════════════════════

# 20 Regression Tests (from run_regression_tests.py)
REGRESSION_TESTS = [
    {"id": 1, "name": "Long-Tenure Employees", "sql": "SELECT employee_id, first_name, last_name, hire_date FROM employees WHERE hire_date < '2024-02-03' ORDER BY hire_date"},
    {"id": 2, "name": "Monthly Sales Summary", "sql": "SELECT YEAR(sale_date) AS year, MONTH(sale_date) AS month, COUNT(*) AS sales_count, SUM(amount) AS total_revenue FROM sales WHERE YEAR(sale_date) = 2023 GROUP BY YEAR(sale_date), MONTH(sale_date) ORDER BY year, month"},
    {"id": 3, "name": "Employee Contact List", "sql": "SELECT UPPER(first_name + ' ' + last_name) AS full_name, email, CHAR_LENGTH(email) AS email_length FROM employees WHERE email IS NOT NULL ORDER BY last_name, first_name"},
    {"id": 4, "name": "Above-Average Earners", "sql": "SELECT e.employee_id, e.first_name + ' ' + e.last_name AS name, e.salary, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE e.salary > (SELECT AVG(e2.salary) FROM employees e2 WHERE e2.department_id = e.department_id)"},
    {"id": 5, "name": "Salary Peer Analysis", "sql": "SELECT e1.first_name, e1.last_name, e1.salary, e2.first_name AS peer_first, e2.last_name AS peer_last, e2.salary AS peer_salary FROM employees e1 JOIN employees e2 ON e1.department_id = e2.department_id AND e1.employee_id <> e2.employee_id WHERE ABS(e1.salary - e2.salary) <= 5000"},
    {"id": 6, "name": "Projects Without Assignments", "sql": "SELECT p.project_id, p.project_name FROM projects p WHERE NOT EXISTS (SELECT 1 FROM project_assignments pa WHERE pa.project_id = p.project_id)"},
    {"id": 7, "name": "Sales-Employees Join", "sql": "SELECT e.first_name, e.last_name, COUNT(s.sale_id) AS total_sales, SUM(s.amount) AS total_revenue FROM employees e LEFT JOIN sales s ON e.employee_id = s.employee_id GROUP BY e.employee_id, e.first_name, e.last_name ORDER BY total_revenue DESC"},
    {"id": 8, "name": "Department Hierarchy", "sql": "SELECT d.department_name, COUNT(e.employee_id) AS employee_count, AVG(e.salary) AS avg_salary FROM departments d LEFT JOIN employees e ON d.department_id = e.department_id GROUP BY d.department_id, d.department_name"},
    {"id": 9, "name": "Multi-Table Report", "sql": "SELECT e.first_name, e.last_name, d.department_name, p.project_name FROM employees e JOIN departments d ON e.department_id = d.department_id LEFT JOIN project_assignments pa ON e.employee_id = pa.employee_id LEFT JOIN projects p ON pa.project_id = p.project_id"},
    {"id": 10, "name": "Rank by Salary (Subquery)", "sql": "SELECT e1.first_name, e1.last_name, e1.salary, (SELECT COUNT(*) + 1 FROM employees e2 WHERE e2.salary > e1.salary) AS salary_rank FROM employees e1 ORDER BY salary_rank"},
    {"id": 11, "name": "Conditional Aggregation", "sql": "SELECT department_id, COUNT(*) AS total, SUM(CASE WHEN salary > 50000 THEN 1 ELSE 0 END) AS high_earners FROM employees GROUP BY department_id"},
    {"id": 12, "name": "String Concatenation", "sql": "SELECT first_name + ' ' + last_name AS full_name, UPPER(SUBSTRING(first_name, 1, 1)) + LOWER(SUBSTRING(first_name, 2, 100)) AS proper_first FROM employees"},
    {"id": 13, "name": "Date Filtering", "sql": "SELECT employee_id, first_name, hire_date FROM employees WHERE hire_date >= '2020-01-01' AND hire_date < '2024-01-01'"},
    {"id": 14, "name": "NULL Handling", "sql": "SELECT employee_id, first_name, COALESCE(email, 'no-email@company.com') AS email FROM employees"},
    {"id": 15, "name": "DISTINCT Values", "sql": "SELECT DISTINCT department_id FROM employees ORDER BY department_id"},
    {"id": 16, "name": "TOP N Query", "sql": "SELECT TOP 5 employee_id, first_name, salary FROM employees ORDER BY salary DESC"},
    {"id": 17, "name": "HAVING Clause", "sql": "SELECT department_id, COUNT(*) AS emp_count FROM employees GROUP BY department_id HAVING COUNT(*) > 2"},
    {"id": 18, "name": "UNION Query", "sql": "SELECT first_name, 'Employee' AS type FROM employees UNION SELECT project_name, 'Project' AS type FROM projects"},
    {"id": 19, "name": "Nested Subquery", "sql": "SELECT * FROM employees WHERE department_id IN (SELECT department_id FROM departments WHERE department_name LIKE '%Sales%')"},
    {"id": 20, "name": "Complex Expression", "sql": "SELECT employee_id, first_name, salary, salary * 1.1 AS projected_salary, CASE WHEN salary > 60000 THEN 'Senior' WHEN salary > 40000 THEN 'Mid' ELSE 'Junior' END AS level FROM employees"},
]


def extract_sql(text: str) -> str:
    """Extract SQL from LLM response"""
    # Strip markdown code blocks
    if "```" in text:
        match = re.search(r"```(?:sql)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Clean up common prefixes
    text = text.strip()
    for prefix in ["SQL:", "Query:", "Here is the SQL:", "Here's the SQL:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    return text


def get_schema_context() -> str:
    """Get database schema for LLM context"""
    try:
        result = get_zen_schema(None)
        tables = result.get("tables", [])

        context = "DATABASE SCHEMA:\n"
        context += f"Available tables: {', '.join(tables[:15])}\n\n"

        # Get column info for key tables
        for table in ["employees", "departments", "sales", "projects"]:
            if table in tables:
                try:
                    schema = get_zen_schema(table)
                    columns = schema.get("columns", [])
                    context += f"Table '{table}':\n"
                    for col in columns[:10]:
                        context += f"  - {col['name']} ({col['type']})\n"
                    context += "\n"
                except:
                    pass

        return context
    except Exception as e:
        return f"Schema unavailable: {e}"


class UnifiedTestRunner:
    """Unified test runner for all LLM providers"""

    def __init__(self, provider: LLMProvider, verbose: bool = False):
        self.provider = provider
        self.verbose = verbose
        self.schema_context = get_schema_context()

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def run_single_test(self, test: Dict) -> TestResult:
        """Run a single SQL test"""
        test_id = test["id"]
        test_name = test["name"]
        expected_sql = test["sql"]

        start_time = time.time()

        prompt = f"""You are a SQL expert. Generate a SQL query for the following request.

{self.schema_context}

IMPORTANT:
- Use EXACT table and column names from the schema
- Use Zen SQL syntax (similar to SQL Server/T-SQL)
- For string length, use CHAR_LENGTH() not LEN()
- Return ONLY the SQL query, no explanation

Request: {test_name}

Expected behavior: This query should {test_name.lower()}
"""

        try:
            response, tokens = self.provider.call(prompt)
            sql = extract_sql(response)
            self._log(f"Generated: {sql[:60]}...")

            # Execute the generated SQL
            result = execute_raw_sql(sql)
            exec_time = (time.time() - start_time) * 1000

            if "results" in result or result.get("success"):
                return TestResult(
                    test_id=test_id,
                    test_name=test_name,
                    success=True,
                    sql_generated=sql,
                    execution_time_ms=exec_time,
                    tokens_used=tokens
                )
            else:
                return TestResult(
                    test_id=test_id,
                    test_name=test_name,
                    success=False,
                    error=result.get("error", "Unknown error"),
                    sql_generated=sql,
                    execution_time_ms=exec_time,
                    tokens_used=tokens
                )

        except Exception as e:
            exec_time = (time.time() - start_time) * 1000
            return TestResult(
                test_id=test_id,
                test_name=test_name,
                success=False,
                error=str(e),
                execution_time_ms=exec_time
            )

    def run_regression_tests(self) -> TestSuiteResult:
        """Run all regression tests"""
        start_time = time.time()
        results = []
        passed = 0
        total_tokens = 0

        print(f"\nRunning {len(REGRESSION_TESTS)} regression tests...")
        print(f"Provider: {self.provider.__class__.__name__}")
        print(f"Model: {self.provider.model}")
        print("-" * 60)

        for test in REGRESSION_TESTS:
            result = self.run_single_test(test)
            results.append(result)
            total_tokens += result.tokens_used

            if result.success:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"

            print(f"  [{status}] Test {result.test_id}: {result.test_name}")
            if not result.success and self.verbose:
                print(f"        Error: {result.error}")

        total_time = time.time() - start_time
        success_rate = (passed / len(REGRESSION_TESTS)) * 100

        print("-" * 60)
        print(f"Results: {passed}/{len(REGRESSION_TESTS)} passed ({success_rate:.1f}%)")
        print(f"Time: {total_time:.1f}s | Tokens: {total_tokens}")

        return TestSuiteResult(
            provider=self.provider.__class__.__name__,
            model=self.provider.model,
            timestamp=datetime.now().isoformat(),
            total_tests=len(REGRESSION_TESTS),
            passed=passed,
            failed=len(REGRESSION_TESTS) - passed,
            success_rate=success_rate,
            total_time_seconds=total_time,
            total_tokens=total_tokens,
            results=results
        )


# ════════════════════════════════════════════════════════════════════════════════
# Configuration Loading
# ════════════════════════════════════════════════════════════════════════════════

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    path = Path(config_path)
    if not path.exists():
        # Return default config
        return {
            "provider": "ollama",
            "providers": {
                "ollama": {
                    "api_url": "http://localhost:11434/v1/chat/completions",
                    "models_url": "http://localhost:11434/v1/models",
                    "default_model": "qwen2.5-coder:14b"
                },
                "openrouter": {
                    "api_url": "https://openrouter.ai/api/v1/chat/completions",
                    "api_key": "${OPENROUTER_API_KEY}",
                    "default_model": "openai/gpt-4o-mini"
                }
            }
        }

    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_results(result: TestSuiteResult, output_dir: str, format: str = "both"):
    """Save test results to file"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    provider = result.provider.lower().replace("provider", "")
    base_name = f"llm_test_{provider}_{timestamp}"

    if format in ["json", "both"]:
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nResults saved to: {json_path}")

    if format in ["markdown", "both"]:
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, "w") as f:
            f.write(f"# LLM Test Results\n\n")
            f.write(f"- **Provider**: {result.provider}\n")
            f.write(f"- **Model**: {result.model}\n")
            f.write(f"- **Date**: {result.timestamp}\n")
            f.write(f"- **Results**: {result.passed}/{result.total_tests} ({result.success_rate:.1f}%)\n")
            f.write(f"- **Time**: {result.total_time_seconds:.1f}s\n")
            f.write(f"- **Tokens**: {result.total_tokens}\n\n")
            f.write("## Test Results\n\n")
            f.write("| # | Test | Status | Time (ms) |\n")
            f.write("|---|------|--------|----------|\n")
            for r in result.results:
                status = "PASS" if r.success else "FAIL"
                f.write(f"| {r.test_id} | {r.test_name} | {status} | {r.execution_time_ms:.0f} |\n")
        print(f"Results saved to: {md_path}")


# ════════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ════════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Unified LLM Test Runner for Actian Zen MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_llm_tests.py                           # Use config file
  python run_llm_tests.py --provider ollama         # Use Ollama
  python run_llm_tests.py --provider openrouter     # Use OpenRouter
  python run_llm_tests.py --model qwen2.5-coder:14b # Specific model
  python run_llm_tests.py --list-models             # List models
  python run_llm_tests.py --check                   # Check connection
        """
    )

    parser.add_argument("--config", default="llm_test_config.yaml",
                        help="Path to config file (default: llm_test_config.yaml)")
    parser.add_argument("--provider", choices=["openrouter", "anthropic", "ollama", "lmstudio"],
                        help="Override provider from config")
    parser.add_argument("--model", help="Override model from config")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--check", action="store_true", help="Check provider connection")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", default="./results", help="Output directory")

    args = parser.parse_args()

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), args.config)
    config = load_config(config_path)

    # Determine provider
    provider_name = args.provider or config.get("provider", "ollama")

    # Create provider
    try:
        provider = create_provider(provider_name, config, args.model)
    except Exception as e:
        print(f"Error creating provider: {e}")
        sys.exit(1)

    # Handle --list-models
    if args.list_models:
        print(f"\nAvailable models for {provider_name}:")
        for model in provider.list_models():
            print(f"  - {model}")
        sys.exit(0)

    # Handle --check
    if args.check:
        ok, msg = provider.check_connection()
        if ok:
            print(f"[OK] {msg}")
        else:
            print(f"[FAIL] {msg}")
        sys.exit(0 if ok else 1)

    # Check connection before running tests
    ok, msg = provider.check_connection()
    if not ok:
        print(f"[ERROR] Cannot connect to {provider_name}: {msg}")
        sys.exit(1)

    # Run tests
    runner = UnifiedTestRunner(provider, verbose=args.verbose)
    result = runner.run_regression_tests()

    # Save results
    output_format = config.get("output", {}).get("format", "both")
    save_results(result, args.output, output_format)


if __name__ == "__main__":
    main()
