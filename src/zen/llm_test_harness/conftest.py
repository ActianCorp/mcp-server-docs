# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
Pytest fixtures for actian-zen LLM test harness.

Provides:
- Session-scoped MCP server + client (shared across all tests)
- Module-scoped SETUP/TEARDOWN from markdown files
- Markdown test file parser
- LLM client for language mode tests
- Custom CLI options: --provider, --model
"""

import re
import sys
import os
import json
import pytest
import pytest_asyncio
from pathlib import Path
from dataclasses import dataclass, field

from fastmcp import Client, FastMCP

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))


# ════════════════════════════════════════════════════════════════════════════════
# Data Models
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class TestCase:
    """Parsed test case from markdown."""
    id: str
    name: str = ""
    description: str = ""
    sql: str = ""
    prompt: str = ""
    keywords: list = field(default_factory=list)
    validate_rows: str = ""
    validate_columns: list = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════════════════
# Markdown Parser
# ════════════════════════════════════════════════════════════════════════════════

def parse_test_file(path: str) -> list[TestCase]:
    """Parse a markdown file into TestCase objects.

    Format:
        ## TEST R01
        **Name:** Long-Tenure Employees
        **Description:** Show employees working >2 years
        **Validate:** rows > 0, columns: employee_id, first_name
        **Keywords:** dsn, driver, demodata

        **Prompt:**
        Multi-line prompt text...

        ```sql
        SELECT ...
        ```
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    tests = []
    blocks = re.split(r'(?=^## TEST )', content, flags=re.MULTILINE)

    for block in blocks:
        match = re.match(r'^## TEST\s+(\S+)', block)
        if not match:
            continue

        tc = TestCase(id=match.group(1))

        name_match = re.search(r'\*\*Name:\*\*\s*(.+)', block)
        if name_match:
            tc.name = name_match.group(1).strip()

        desc_match = re.search(r'\*\*Description:\*\*\s*(.+)', block)
        if desc_match:
            tc.description = desc_match.group(1).strip()

        val_match = re.search(r'\*\*Validate:\*\*\s*(.+)', block)
        if val_match:
            val_text = val_match.group(1).strip()
            rows_match = re.search(r'rows\s*>\s*(\d+)', val_text)
            if rows_match:
                tc.validate_rows = f"rows > {rows_match.group(1)}"
            cols_match = re.search(r'columns:\s*(.+)', val_text)
            if cols_match:
                tc.validate_columns = [c.strip() for c in cols_match.group(1).split(',')]

        kw_match = re.search(r'\*\*Keywords:\*\*\s*(.+)', block)
        if kw_match:
            tc.keywords = [k.strip() for k in kw_match.group(1).split(',')]

        sql_match = re.search(r'```sql\s*\n(.*?)```', block, re.DOTALL)
        if sql_match:
            tc.sql = sql_match.group(1).strip()

        prompt_match = re.search(r'\*\*Prompt:\*\*\s*\n(.*?)(?=\n## |\n────|\Z)', block, re.DOTALL)
        if prompt_match:
            tc.prompt = prompt_match.group(1).strip()

        tests.append(tc)

    return tests


def parse_setup_teardown(path: str) -> tuple[list[str], list[str]]:
    """Extract SETUP and TEARDOWN SQL blocks from a markdown file.

    Returns (setup_statements, teardown_statements) — each a list of
    individual SQL statements split on ';'.
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    def _extract_sql(section_name: str) -> list[str]:
        pattern = rf'^## {section_name}\s*\n.*?```sql\s*\n(.*?)```'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if not match:
            return []
        raw = match.group(1)
        stmts = [s.strip() for s in raw.split(';') if s.strip()]
        return stmts

    return _extract_sql('SETUP'), _extract_sql('TEARDOWN')


# ════════════════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════════════════

def load_config(overrides: dict | None = None) -> dict:
    """Load configuration from conf.json with optional CLI overrides."""
    config_path = Path(__file__).parent.parent / "conf.json"
    if config_path.exists():
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "database": {"dsn": "DEMODATA"},
            "llm": {
                "provider": "ollama",
                "model": "llama3.1:8b",
                "max_turns": 10,
                "timeout": 300
            }
        }

    if overrides:
        if overrides.get("provider"):
            config.setdefault("llm", {})["provider"] = overrides["provider"]
        if overrides.get("model"):
            config.setdefault("llm", {})["model"] = overrides["model"]

    return config


# ════════════════════════════════════════════════════════════════════════════════
# pytest CLI options
# ════════════════════════════════════════════════════════════════════════════════

def pytest_addoption(parser):
    parser.addoption("--provider", action="store", default=None,
                     help="LLM provider override (ollama, openrouter)")
    parser.addoption("--model", action="store", default=None,
                     help="LLM model name override")


# ════════════════════════════════════════════════════════════════════════════════
# MCP Client Fixture (session-scoped)
# ════════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def mcp_client():
    """In-process MCP server connected via stdio — shared across all tests."""
    from actian_zen.server import SERVER_NAME, create_lifespan, SERVER_INSTRUCTIONS
    from actian_zen.core import ZenConfiguration

    original_argv = sys.argv
    sys.argv = ['actian-zen', '--transport', 'stdio']

    try:
        config = ZenConfiguration()
        server = FastMCP(
            SERVER_NAME,
            instructions=SERVER_INSTRUCTIONS,
            lifespan=create_lifespan(config)
        )

        async with Client(server) as client:
            yield client
    finally:
        sys.argv = original_argv


# ════════════════════════════════════════════════════════════════════════════════
# SETUP / TEARDOWN Fixtures (module-scoped)
# ════════════════════════════════════════════════════════════════════════════════

async def _execute_sql_list(mcp_client, statements: list[str]):
    """Execute a list of SQL statements, ignoring DROP errors."""
    for sql in statements:
        try:
            result = await mcp_client.call_tool("execute_query", {"sql": sql})
            text = result.content[0].text if hasattr(result, 'content') and result.content else str(result)
            data = json.loads(text)
            # Ignore errors on DROP TABLE (table may not exist)
            if "error" in data and not sql.strip().upper().startswith("DROP"):
                raise RuntimeError(f"SETUP failed: {data['error']}  SQL: {sql}")
        except json.JSONDecodeError:
            pass


@pytest_asyncio.fixture(scope="module", loop_scope="session", autouse=True)
async def setup_teardown_sql(mcp_client, request):
    """Run SETUP SQL from the associated .md file before tests, TEARDOWN after."""
    # Determine which .md file to use based on markers on collected items
    markers = set()
    for item in request.session.items:
        if item.module == request.module:
            for marker in item.iter_markers():
                markers.add(marker.name)

    harness_dir = Path(__file__).parent
    if "sql" in markers:
        md_path = harness_dir / "model_dialogs" / "sql_requests.md"
    elif "language" in markers:
        md_path = harness_dir / "model_dialogs" / "language.md"
    else:
        yield
        return

    if not md_path.exists():
        yield
        return

    setup_stmts, teardown_stmts = parse_setup_teardown(str(md_path))

    # SETUP
    await _execute_sql_list(mcp_client, setup_stmts)

    yield

    # TEARDOWN
    await _execute_sql_list(mcp_client, teardown_stmts)


# ════════════════════════════════════════════════════════════════════════════════
# LLM Client
# ════════════════════════════════════════════════════════════════════════════════

class MCPLLMClient:
    """LLM client that connects to MCP server via real function calling.

    Supports:
    - Ollama (local): provider="ollama", uses native /api/chat endpoint
    - OpenRouter (cloud): provider="openrouter", requires OPENROUTER_API_KEY
    """

    def __init__(self, mcp_client, config: dict):
        import httpx
        self.httpx = httpx
        self.mcp_client = mcp_client
        self.config = config
        self.llm_config = config.get("llm", {})

        self.provider = self.llm_config.get("provider", "ollama")
        self.model = self.llm_config.get("model", "llama3.1:8b")
        self.max_turns = self.llm_config.get("max_turns", 10)
        self.timeout = self.llm_config.get("timeout", 300)

        if self.provider == "ollama":
            self.base_url = "http://localhost:11434/api/chat"
            self.api_key = None
        else:
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.api_key = self.llm_config.get("api_key", "")
            if not self.api_key:
                api_key_env = self.llm_config.get("api_key_env", "OPENROUTER_API_KEY")
                self.api_key = os.environ.get(api_key_env, "")

        self.tools = []
        self.tool_map = {}

    async def initialize(self):
        """Load tools from MCP server."""
        tools_list = await self.mcp_client.list_tools()
        for tool in tools_list:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": (tool.description or "")[:500],
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                }
            }
            self.tools.append(tool_def)
            self.tool_map[tool.name] = tool

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Execute MCP tool and return result as string."""
        result = await self.mcp_client.call_tool(name, arguments)
        if hasattr(result, 'content') and result.content:
            return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
        return str(result)

    async def _chat_ollama(self, messages: list) -> tuple:
        """Send request to Ollama native API."""
        async with self.httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "tools": self.tools if self.tools else None,
                        "stream": False
                    }
                )
            except self.httpx.ConnectError:
                raise Exception("Cannot connect to Ollama. Is it running? (ollama serve)")

            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code} - {response.text[:200]}")

            result = response.json()
            message = result.get("message", {})
            return message.get("content", ""), message.get("tool_calls", []), message

    async def _chat_openrouter(self, messages: list) -> tuple:
        """Send request to OpenRouter API."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        async with self.httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/actian-zen",
                    "X-Title": "Actian Zen MCP Tests"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": self.tools if self.tools else None,
                    "tool_choice": "auto"
                }
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter error: {response.status_code} - {response.text[:200]}")

            result = response.json()
            message = result.get("choices", [{}])[0].get("message", {})
            return message.get("content", ""), message.get("tool_calls", []), message

    async def chat(self, prompt: str) -> str:
        """Send prompt to LLM with MCP tools, return final response."""
        messages = [{"role": "user", "content": prompt}]

        for turn in range(self.max_turns):
            if self.provider == "ollama":
                content, tool_calls, message = await self._chat_ollama(messages)
            else:
                content, tool_calls, message = await self._chat_openrouter(messages)

            if tool_calls:
                messages.append(message)
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    tool_args = func.get("arguments", {})

                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            tool_args = {}

                    tool_result = await self.call_tool(tool_name, tool_args)

                    if self.provider == "ollama":
                        messages.append({"role": "tool", "content": tool_result})
                    else:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "content": tool_result
                        })
                continue

            return content or ""

        return "Max turns reached"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def llm_client(mcp_client, request):
    """LLM client for language mode tests. Initialized lazily."""
    overrides = {
        "provider": request.config.getoption("--provider"),
        "model": request.config.getoption("--model"),
    }
    config = load_config(overrides)
    client = MCPLLMClient(mcp_client, config)
    await client.initialize()
    return client
