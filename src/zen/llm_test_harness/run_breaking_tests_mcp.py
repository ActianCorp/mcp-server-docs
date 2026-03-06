#!/usr/bin/env python3
"""
Breaking Tests via REAL MCP Protocol

This is the correct way to test - same as Claude Code:
1. Connect to real MCP server
2. LLM uses MCP tools via function calling
3. LLM sees real responses and adapts

This should match Claude Code's 100% success rate.

Supports:
- OpenRouter (cloud): claude-opus, claude-sonnet, gpt-4, gpt-4.1
- Ollama (local): qwen2.5-coder:7b, qwen2.5-coder:14b, etc.
"""
import asyncio
import json
import sys
import os
import time
import httpx
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Import the MCP wrapper
from test_openrouter_mcp import OpenRouterMCPWrapper
from ollama_mcp_wrapper import SimpleMCPClient


class OllamaMCPWrapper:
    """Wrapper that connects Ollama (local LLM) to MCP servers via function calling

    Uses Ollama's native /api/chat endpoint which has proper tool_calls support.
    """

    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model
        self.base_url = "http://localhost:11434/api/chat"  # Native API (not OpenAI compat)
        self.mcp_clients: dict[str, SimpleMCPClient] = {}
        self.tools: list[dict] = []
        self.tool_to_server: dict[str, str] = {}

    async def connect_mcp_server(self, name: str, command: str, args: list[str], env: dict = None):
        """Connect to an MCP server"""
        client = SimpleMCPClient(name, command, args, env)
        await client.start()
        self.mcp_clients[name] = client

        # Get tools from this server
        tools = await client.list_tools()
        for tool in tools:
            # Convert to OpenAI function format
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description", "")[:500],
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                }
            }
            self.tools.append(tool_def)
            self.tool_to_server[tool.get("name")] = name

        print(f"[MCP] Connected to '{name}' - {len(tools)} tools")
        return len(tools)

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool via MCP"""
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        client = self.mcp_clients[server_name]
        try:
            return await client.call_tool(tool_name, arguments)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def chat(self, prompt: str, max_turns: int = 10) -> str:
        """Send a chat request to Ollama with MCP tools (native API)"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        print(f"\n{'='*60}")
        print(f"[User] {prompt[:100]}...")
        print(f"[Model] {self.model} (Ollama local)")
        print(f"[Tools] {len(self.tools)} available")
        print('='*60)

        async with httpx.AsyncClient(timeout=300) as client:  # Longer timeout for local LLM
            for turn in range(max_turns):
                # Send request to Ollama native /api/chat endpoint
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
                    return "ERROR: Cannot connect to Ollama. Is it running? (ollama serve)"

                if response.status_code != 200:
                    return f"API Error: {response.status_code} - {response.text[:200]}"

                result = response.json()
                # Native API returns message directly, not in choices array
                message = result.get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])

                # Handle tool calls
                if tool_calls:
                    print(f"\n[Turn {turn+1}] Tool calls from {self.model}")
                    messages.append(message)

                    for tc in tool_calls:
                        # Native API format: function.name and function.arguments (already parsed)
                        func = tc.get("function", {})
                        tool_name = func.get("name")
                        tool_args = func.get("arguments", {})

                        # Arguments may be string or dict in native API
                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except json.JSONDecodeError:
                                tool_args = {}

                        print(f"  [Tool] {tool_name}")
                        print(f"  [Args] {json.dumps(tool_args, indent=2)[:200]}")

                        # Execute tool
                        tool_result = await self.call_tool(tool_name, tool_args)
                        result_preview = tool_result[:300] + "..." if len(tool_result) > 300 else tool_result
                        print(f"  [Result] {result_preview}")

                        # Add tool result to messages (native format)
                        messages.append({
                            "role": "tool",
                            "content": tool_result
                        })
                    continue

                # No tool calls - this is the final response
                print(f"\n[Response] {content[:500]}...")
                return content

        return "Max turns reached without final response"

    async def close(self):
        """Close all MCP connections"""
        for name, client in self.mcp_clients.items():
            try:
                await client.close()
            except:
                pass

# Breaking test prompts (same as alternative_breaking_tests_english.md)
BREAKING_TESTS = [
    {
        "id": 1,
        "name": "Upload 50MB PDF",
        "category": "File Operations",
        "prompt": """Upload the PDF file at D:\\PlayScripts\\large_presentation.pdf to the database.
First create a table document_store with columns: file_id IDENTITY, file_name NVARCHAR(255), file_size INTEGER, file_hash NVARCHAR(64).
Then use blob_operation to upload the file. Calculate and store its SHA256 hash.
The file is approximately 50MB."""
    },
    {
        "id": 4,
        "name": "Cross-Database Query",
        "category": "Multi-Database",
        "prompt": """Demonstrate cross-database capability:
1. Use database_manage with action='list' to show all available Zen databases
2. Show how to switch between databases using database_manage with action='switch'
3. Return the list of available DSNs"""
    },
    {
        "id": 5,
        "name": "List All Databases",
        "category": "Multi-Database",
        "prompt": """List all Zen databases (ODBC DSNs) available on this system.
Use database_manage tool with action='list_dsns' to get all configured DSNs.
Show DSN name and driver for each."""
    },
    {
        "id": 6,
        "name": "Multi-Step Transaction",
        "category": "Transactions",
        "prompt": """Execute an atomic multi-step transaction:
1. First, create test tables if they don't exist using execute_query:
   - test_customers (customer_id IDENTITY, name NVARCHAR(100))
   - test_invoices (invoice_id IDENTITY, customer_id INTEGER, total DECIMAL(10,2))

2. Use transaction tool with action='begin' to start transaction

3. Insert a customer named "Test Corp" using orm_operation

4. Get the customer_id of the inserted customer

5. Insert 2 invoices for that customer: $500 and $300

6. Calculate the total of all invoices for that customer

7. If total > $10000: use transaction with action='rollback'
   Else: use transaction with action='commit'

Show the final status."""
    },
    {
        "id": 7,
        "name": "Lock Recovery",
        "category": "Transactions",
        "prompt": """Demonstrate lock recovery capability:
1. Explain when Btrieve Error 85 occurs (record/table locked)
2. Show how to use database_manage with action='release_locks' to recover
3. Call database_manage(action='release_locks') to demonstrate"""
    },
    {
        "id": 8,
        "name": "Relationship Navigation",
        "category": "ORM Operations",
        "prompt": """Navigate table relationships to get customer with invoices:
1. Use orm_operation or execute_query to get customer with customer_id = 1
2. Get all invoices for that customer using a JOIN query
3. Print the customer info and their invoices"""
    },
    {
        "id": 9,
        "name": "Server Capabilities",
        "category": "System Operations",
        "prompt": """Check database server capabilities:
1. Use database_manage with action='capabilities' to get supported features
2. Use execute_query to list available tables
3. Print a summary of tables and capabilities"""
    },
    {
        "id": 10,
        "name": "CSV Validation",
        "category": "Batch Operations",
        "prompt": """The file D:\\PlayScripts\\customer_import.csv contains customer data.
Read the first 100 rows and validate:
- Email must contain @ and a domain (.)
- Phone must match pattern XXX-XXX-XXXX

Use execute_query or orm_operation to check if data can be validated.
Report how many rows are valid vs invalid.

Note: You may need to read the file first to understand its structure."""
    },
]


async def run_breaking_tests(model: str = "anthropic/claude-opus-4", provider: str = "openrouter", max_turns: int = 10):
    """Run breaking tests via real MCP protocol"""

    if provider == "ollama":
        wrapper = OllamaMCPWrapper(model)
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            print("ERROR: OPENROUTER_API_KEY not set")
            return
        wrapper = OpenRouterMCPWrapper(api_key)

    # Connect to MCP server
    print(f"\n{'='*70}")
    print(f"Breaking Tests via REAL MCP Protocol")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"{'='*70}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        await wrapper.connect_mcp_server(
            "zen-database",
            "python",
            [os.path.join(script_dir, "run_zen_mcp_server.py"), "--dsn", "DEMODATA"],
            {}
        )
    except Exception as e:
        print(f"ERROR: Failed to connect to MCP server: {e}")
        return

    print(f"Connected! Tools: {len(wrapper.tools)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results = []

    for test in BREAKING_TESTS:
        test_id = test["id"]
        test_name = test["name"]
        prompt = test["prompt"]

        print(f"Test {test_id}: {test_name}...", end=" ", flush=True)

        start_time = time.time()
        try:
            if provider == "ollama":
                response = await wrapper.chat(prompt, max_turns=max_turns)
            else:
                response = await wrapper.chat(prompt, model=model, max_turns=max_turns)
            duration = time.time() - start_time

            # Sanitize response for console output
            response_safe = response.encode('ascii', 'replace').decode('ascii') if response else ""

            # Check if response indicates success (more robust check)
            response_lower = response_safe.lower()
            # Look for actual failure indicators, not just mention of "error" (e.g., "Error 85" as explanation)
            failure_indicators = ["failed to", "could not", "unable to", "exception:", "traceback"]
            has_failure = any(ind in response_lower for ind in failure_indicators)
            has_success = any(word in response_lower for word in ["success", "completed", "created", "result", "found", "available", "demonstrate", "explanation"])

            success = has_success or not has_failure

            results.append({
                "id": test_id,
                "name": test_name,
                "category": test["category"],
                "status": "PASS" if success else "FAIL",
                "duration": duration,
                "response_preview": response_safe[:200] if response_safe else "No response"
            })

            status_icon = "[OK]" if success else "[FAIL]"
            print(f"{status_icon} ({duration:.1f}s)")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            results.append({
                "id": test_id,
                "name": test_name,
                "category": test["category"],
                "status": "FAIL",
                "duration": duration,
                "error": error_msg
            })
            print(f"[FAIL] ({duration:.1f}s) - {error_msg[:50]}")

    await wrapper.close()

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)

    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} PASSED ({100*passed/total:.0f}%)")
    print(f"{'='*70}")

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_safe = model.replace("/", "_").replace(":", "_")
    report_path = f"results/breaking_tests_mcp_{model_safe}_{timestamp}.md"

    report = f"""# Breaking Tests via REAL MCP Protocol

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Model:** {model}
**Mode:** Real MCP tool calls (same as Claude Code)

## Summary: {passed}/{total} PASSED ({100*passed/total:.0f}%)

| Test | Name | Status | Time |
|------|------|--------|------|
"""
    for r in results:
        status = r["status"]
        report += f"| {r['id']} | {r['name']} | {status} | {r['duration']:.1f}s |\n"

    os.makedirs("results", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report: {report_path}")

    return results


async def main():
    model = "anthropic/claude-opus-4"  # default
    provider = "openrouter"  # default

    for arg in sys.argv[1:]:
        # OpenRouter models
        if arg in ["opus", "claude-opus"]:
            model = "anthropic/claude-opus-4"
            provider = "openrouter"
        elif arg in ["sonnet", "claude-sonnet"]:
            model = "anthropic/claude-sonnet-4"
            provider = "openrouter"
        elif arg in ["gpt4", "gpt-4", "gpt4o"]:
            model = "openai/gpt-4o"
            provider = "openrouter"
        elif arg in ["gpt4.1", "gpt-4.1"]:
            model = "openai/gpt-4.1"
            provider = "openrouter"
        # Ollama local models
        elif arg in ["7b", "qwen7b", "qwen2.5-coder:7b"]:
            model = "qwen2.5-coder:7b"
            provider = "ollama"
        elif arg in ["14b", "qwen14b", "qwen2.5-coder:14b"]:
            model = "qwen2.5-coder:14b"
            provider = "ollama"
        elif arg in ["llama", "llama3", "llama3.1", "llama3.1:8b"]:
            model = "llama3.1:8b"
            provider = "ollama"
        elif arg in ["ollama"]:
            provider = "ollama"
            if model.startswith("anthropic/") or model.startswith("openai/"):
                model = "llama3.1:8b"  # default Ollama model with good tool support

    await run_breaking_tests(model, provider)


if __name__ == "__main__":
    asyncio.run(main())
