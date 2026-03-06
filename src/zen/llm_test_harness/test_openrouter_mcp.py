#!/usr/bin/env python3
"""
Test MCP servers with GPT-4 via OpenRouter
"""
import asyncio
import json
import sys
import os
import httpx

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
print("[Starting test...]", flush=True)

# Import the MCP client from wrapper
from ollama_mcp_wrapper import SimpleMCPClient


class OpenRouterMCPWrapper:
    """Wrapper that connects OpenRouter (GPT-4) to MCP servers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
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
                    "description": tool.get("description", "")[:500],  # Truncate long descriptions
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

    async def chat(self, prompt: str, model: str = "openai/gpt-4o", max_turns: int = 5) -> str:
        """Send a chat request to OpenRouter with MCP tools"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        print(f"\n{'='*60}")
        print(f"[User] {prompt}")
        print(f"[Model] {model}")
        print(f"[Tools] {len(self.tools)} available")
        print('='*60)

        async with httpx.AsyncClient(timeout=120) as client:
            for turn in range(max_turns):
                # Send request to OpenRouter
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/test",
                        "X-Title": "MCP Test"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "tools": self.tools if self.tools else None,
                        "tool_choice": "auto"
                    }
                )

                if response.status_code != 200:
                    print(f"[ERROR] API returned {response.status_code}: {response.text}")
                    return f"API Error: {response.status_code}"

                result = response.json()
                message = result.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])

                # Handle tool calls (OpenAI native format)
                if tool_calls:
                    print(f"\n[Turn {turn+1}] Tool calls from GPT-4")
                    messages.append(message)  # Add assistant message with tool calls

                    for tc in tool_calls:
                        tool_name = tc.get("function", {}).get("name")
                        tool_args_str = tc.get("function", {}).get("arguments", "{}")

                        try:
                            tool_args = json.loads(tool_args_str)
                        except json.JSONDecodeError:
                            tool_args = {}

                        print(f"  [Tool] {tool_name}")
                        print(f"  [Args] {json.dumps(tool_args, indent=2)[:200]}")

                        # Execute tool
                        tool_result = await self.call_tool(tool_name, tool_args)
                        result_preview = tool_result[:300] + "..." if len(tool_result) > 300 else tool_result
                        print(f"  [Result] {result_preview}")

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "content": tool_result
                        })
                    continue

                # No tool calls - this is the final response
                print(f"\n[Response] {content}")
                return content

        return "Max turns reached without final response"

    async def close(self):
        """Close all MCP connections"""
        for name, client in self.mcp_clients.items():
            try:
                await client.close()
            except:
                pass


async def main():
    """Main entry point"""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    wrapper = OpenRouterMCPWrapper(api_key)

    # Choose MCP server
    mcp_server = sys.argv[1] if len(sys.argv) > 1 else "zen"

    if mcp_server == "zen":
        # Zen database MCP (new actian-zen server)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mcp_config = {
            "zen-database": {
                "command": "python",
                "args": [os.path.join(script_dir, "run_zen_mcp_server.py"), "--dsn", "DEMODATA"],
                "env": {}
            }
        }
        default_query = "What tables are in the database? Show the first 3 employees."
    elif mcp_server == "serena":
        # Serena MCP
        mcp_config = {
            "serena": {
                "command": "C:\\Python313\\Scripts\\uvx.exe",
                "args": [
                    "--from", "git+https://github.com/oraios/serena.git",
                    "serena",
                    "start-mcp-server",
                    "--project", "D:\\ZenMCP\\DB_MCP_PILOT\\llm_test_harness"
                ]
            }
        }
        default_query = "List the Python files in this project"
    else:
        print(f"Unknown MCP server: {mcp_server}")
        print("Usage: python test_openrouter_mcp.py [zen|serena] [query]")
        return

    # Connect to MCP server
    print(f"\n[Connecting to MCP server: {mcp_server}...]")
    for name, config in mcp_config.items():
        try:
            await wrapper.connect_mcp_server(
                name,
                config["command"],
                config["args"],
                config.get("env")
            )
        except Exception as e:
            print(f"[ERROR] Failed to connect to {name}: {e}")
            await wrapper.close()
            return

    if not wrapper.tools:
        print("[ERROR] No tools available.")
        await wrapper.close()
        return

    print(f"\n[Available tools: {len(wrapper.tools)}]")
    for tool in wrapper.tools[:10]:
        print(f"  - {tool['function']['name']}")
    if len(wrapper.tools) > 10:
        print(f"  ... and {len(wrapper.tools) - 10} more")

    # Parse model from args
    model = "openai/gpt-4o"  # default
    query = default_query

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ["zen", "serena"]:
            continue
        elif arg in ["sonnet", "claude-sonnet", "sonnet4"]:
            model = "anthropic/claude-sonnet-4"
        elif arg in ["opus", "claude-opus", "opus4"]:
            model = "anthropic/claude-opus-4"
        elif arg in ["gpt4", "gpt-4", "gpt4o"]:
            model = "openai/gpt-4o"
        elif arg in ["gpt4.1", "gpt-4.1", "gpt41"]:
            model = "openai/gpt-4.1"
        elif arg in ["gpt4-turbo", "gpt4turbo"]:
            model = "openai/gpt-4-turbo"
        elif not arg.startswith("-"):
            query = arg

    # Run query
    await wrapper.chat(query, model=model)
    await wrapper.close()
    print("\n[Done]")


if __name__ == "__main__":
    asyncio.run(main())
