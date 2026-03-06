# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
Pytest fixtures for actian-zen MCP server testing.

Provides fixtures for testing via stdio, HTTP, and SSE transports.
Includes LLM integration via OpenRouter (configured in conf.json).
"""

import re
import pytest
import asyncio
import socket
import sys
import os
import json
import time
import httpx
from datetime import datetime
from pathlib import Path
from multiprocessing import Process
from types import SimpleNamespace

from fastmcp import Client, FastMCP


# ════════════════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════════════════

def load_config() -> dict:
    """Load configuration from conf.json."""
    config_path = Path(__file__).parent.parent / "conf.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {
        "database": {"dsn": "DEMODATA"},
        "llm": {
            "provider": "openrouter",
            "model": "anthropic/claude-sonnet-4",
            "api_key_env": "OPENROUTER_API_KEY",
            "max_turns": 10,
            "timeout": 120
        }
    }


CONFIG = load_config()
TEST_DSN = CONFIG.get("database", {}).get("dsn", "DEMODATA")
TEST_HOST = "127.0.0.1"


def get_free_port():
    """Find an available port for testing."""
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def _create_test_server(transport: str, port: int):
    """Create and run a test server instance."""
    import sys
    import os

    # Mock sys.argv to avoid argparse conflicts with pytest
    sys.argv = ['actian-zen', '--transport', transport]

    from zen.server import SERVER_NAME, create_lifespan, SERVER_INSTRUCTIONS
    from zen.core import ZenConfiguration

    config = ZenConfiguration()
    server = FastMCP(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        lifespan=create_lifespan(config)
    )

    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport=transport, host=TEST_HOST, port=port)


def _wait_for_server(host: str, port: int, timeout: float = 10):
    """Poll until the server accepts TCP connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"Server didn't start on {host}:{port} within {timeout}s")


def _start_server_process(transport: str, port: int) -> Process:
    """Start server in a separate process."""
    proc = Process(target=_create_test_server, args=(transport, port), daemon=True)
    proc.start()
    _wait_for_server(TEST_HOST, port)
    return proc


# ════════════════════════════════════════════════════════════════════════════════
# STDIO Fixtures
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def server_stdio():
    """Create a stdio server instance for testing."""
    import os
    from zen.server import SERVER_NAME, create_lifespan, SERVER_INSTRUCTIONS
    from zen.core import ZenConfiguration

    config = ZenConfiguration()
    server = FastMCP(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        lifespan=create_lifespan(config)
    )

    return server


@pytest.fixture()
async def stdio_client(server_stdio):
    """Create an async client connected via stdio."""
    # Save original argv and mock it during the entire client lifecycle
    # This is necessary because lifespan's parse_args() is called when client connects
    original_argv = sys.argv
    sys.argv = ['actian-zen', '--transport', 'stdio']

    try:
        async with Client(server_stdio) as client:
            yield client
    finally:
        sys.argv = original_argv


# ════════════════════════════════════════════════════════════════════════════════
# HTTP Fixtures
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def server_localhost_http():
    """Start HTTP server and return URL."""
    port = get_free_port()
    proc = _start_server_process("http", port)
    try:
        yield f"http://{TEST_HOST}:{port}/mcp"
    finally:
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=5)


# ════════════════════════════════════════════════════════════════════════════════
# SSE Fixtures
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def server_localhost_sse():
    """Start SSE server and return URL."""
    port = get_free_port()
    proc = _start_server_process("sse", port)
    try:
        yield f"http://{TEST_HOST}:{port}/sse"
    finally:
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=5)


# ════════════════════════════════════════════════════════════════════════════════
# Database Fixtures
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def db_connection():
    """Session-scoped database connection for setup/teardown."""
    from zen.core.connection import ZenConnection

    conn = ZenConnection(f"DSN={TEST_DSN}")
    yield conn
    # Cleanup handled by connection


# ════════════════════════════════════════════════════════════════════════════════
# Test Data Setup/Teardown (data-driven from markdown)
# ════════════════════════════════════════════════════════════════════════════════

def _parse_setup_teardown(md_path: str) -> tuple[list[str], list[str]]:
    """Extract ## SETUP and ## TEARDOWN SQL blocks from a markdown file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    def _extract(section: str) -> list[str]:
        pattern = rf'^## {section}\s*\n.*?```sql\s*\n(.*?)```'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if not match:
            return []
        return [s.strip() for s in match.group(1).split(';') if s.strip()]

    return _extract('SETUP'), _extract('TEARDOWN')


_TEST_DATA_MD = Path(__file__).parent.parent / "llm_test_harness" / "model_dialogs" / "sql_requests.md"

# public aliases used by test_natural_language.py
parse_setup_teardown = _parse_setup_teardown


async def _execute_sql_list(mcp_client, statements):
    for sql in statements:
        try:
            result = await mcp_client.call_tool("execute_query", {"sql": sql})
            text = result.content[0].text if hasattr(result, 'content') and result.content else str(result)
            data = json.loads(text)
            if "error" in data and not sql.strip().upper().startswith("DROP"):
                raise RuntimeError(f"SETUP failed: {data['error']}  SQL: {sql}")
        except json.JSONDecodeError:
            pass


@pytest.fixture(scope="session", autouse=True)
def test_data_setup_teardown():
    """Create test tables from sql_requests.md SETUP block, drop via TEARDOWN."""
    import pyodbc

    setup_stmts, teardown_stmts = _parse_setup_teardown(str(_TEST_DATA_MD))
    conn = pyodbc.connect(f"DSN={TEST_DSN}", autocommit=True)
    cursor = conn.cursor()

    for sql in setup_stmts:
        try:
            cursor.execute(sql)
        except pyodbc.Error:
            if not sql.strip().upper().startswith("DROP"):
                raise

    yield

    for sql in teardown_stmts:
        try:
            cursor.execute(sql)
        except pyodbc.Error:
            pass

    cursor.close()
    conn.close()


# ════════════════════════════════════════════════════════════════════════════════
# LLM Client Fixtures (OpenRouter)
# ════════════════════════════════════════════════════════════════════════════════

class MCPLLMClient:
    """
    LLM client that connects to MCP server via real function calling.

    Supports:
    - Ollama (local): provider="ollama", uses native /api/chat endpoint
    - OpenRouter (cloud): provider="openrouter", requires OPENROUTER_API_KEY

    Configuration in conf.json.
    """

    def __init__(self, mcp_client: Client, config: dict):
        self.mcp_client = mcp_client
        self.config = config
        self.llm_config = config.get("llm", {})

        self.provider = self.llm_config.get("provider", "ollama")
        self.model = self.llm_config.get("model", "llama3.1:8b")
        self.max_turns = self.llm_config.get("max_turns", 10)
        self.timeout = self.llm_config.get("timeout", 300)

        # Set base URL based on provider
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
        self.trace = []

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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
            except httpx.ConnectError:
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
        self.trace = []
        messages = [{"role": "user", "content": prompt}]

        for turn in range(self.max_turns):
            # Call appropriate provider
            if self.provider == "ollama":
                content, tool_calls, message = await self._chat_ollama(messages)
            else:
                content, tool_calls, message = await self._chat_openrouter(messages)

            # Handle tool calls
            if tool_calls:
                messages.append(message)
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    tool_args = func.get("arguments", {})

                    # Parse arguments if string (OpenRouter returns string, Ollama returns dict)
                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            tool_args = {}

                    tool_result = await self.call_tool(tool_name, tool_args)

                    # Record tool call in trace
                    self.trace.append({
                        "turn": turn + 1,
                        "type": "tool_call",
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result_preview": tool_result[:500] if tool_result else ""
                    })

                    # Add tool result (format differs by provider)
                    if self.provider == "ollama":
                        messages.append({"role": "tool", "content": tool_result})
                    else:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "content": tool_result
                        })
                continue

            # Record final response in trace
            self.trace.append({
                "turn": turn + 1,
                "type": "response",
                "content_preview": (content or "")[:500]
            })
            return content

        return "Max turns reached"

    def get_trace_record(self, test_id: str, prompt: str, success: bool) -> dict:
        """Return structured trace record for logging."""
        return {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "provider": self.provider,
            "test_id": test_id,
            "prompt": prompt,
            "success": success,
            "turns": len([t for t in self.trace if t["type"] == "response"]) +
                     len([t for t in self.trace if t["type"] == "tool_call"]),
            "tools_used": [t["tool"] for t in self.trace if t["type"] == "tool_call"],
            "trace": self.trace
        }


@pytest.fixture()
def llm_config():
    """Return LLM configuration from conf.json."""
    return CONFIG


@pytest.fixture()
async def llm_client(stdio_client, llm_config):
    """
    Create LLM client connected to MCP server.

    Uses model from conf.json via OpenRouter.
    Requires OPENROUTER_API_KEY environment variable.
    """
    client = MCPLLMClient(stdio_client, llm_config)
    await client.initialize()
    yield client
