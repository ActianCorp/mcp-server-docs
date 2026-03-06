#!/usr/bin/env python3
"""
Ollama MCP Wrapper - Generic wrapper connecting Ollama LLMs to MCP servers
Parses JSON tool calls from Ollama and executes them via MCP protocol

The SimpleMCPClient and OllamaMCPWrapper classes are fully generic and work
with any MCP server. Server configurations can be provided via JSON file.

Usage:
    python ollama_mcp_wrapper.py [server_preset] [7b|14b] [query]
    python ollama_mcp_wrapper.py --config config.json [server_name] [query]

Built-in presets: zen, serena

Examples:
    python ollama_mcp_wrapper.py zen "What tables are in the database?"
    python ollama_mcp_wrapper.py serena "List Python files"
    python ollama_mcp_wrapper.py serena 14b "Find the main function"
    python ollama_mcp_wrapper.py zen -i  # Interactive mode
    python ollama_mcp_wrapper.py --config my_servers.json myserver "query"

Config file format (JSON):
{
    "preset_name": {
        "server_name": {
            "command": "python",
            "args": ["-m", "module_name"],
            "env": {"KEY": "VALUE"},
            "startup_delay": 0.5
        }
    }
}
"""
import json
import sys
import os

# Force unbuffered output for better debugging
sys.stdout.reconfigure(line_buffering=True)
import asyncio
import subprocess
import re
from typing import Any
import httpx


class SimpleMCPClient:
    """Simple MCP client using subprocess and JSON-RPC"""

    def __init__(self, name: str, command: str, args: list[str], env: dict = None, startup_delay: float = 0.5):
        self.name = name
        self.command = command
        self.args = args
        self.env = {**os.environ, **(env or {})}
        self.process = None
        self.request_id = 0
        self.startup_delay = startup_delay  # Configurable delay for slow-starting servers

    async def start(self):
        """Start the MCP server process"""
        self.process = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env
        )

        # Wait for process to start (configurable for slow servers like Serena)
        await asyncio.sleep(self.startup_delay)

        # Check if process exited immediately (bad command, missing deps, etc.)
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            raise Exception(f"Process exited with code {self.process.returncode}: {stderr.decode()}")

        # Initialize the MCP connection
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ollama-mcp-wrapper", "version": "1.0.0"}
        })

        # Send initialized notification
        await self._send_notification("notifications/initialized", {})

    async def _send_request(self, method: str, params: dict = None, timeout: int = 30) -> dict:
        """Send a JSON-RPC request and get response"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()

        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=timeout
            )
            if response_line:
                return json.loads(response_line.decode())
        except asyncio.TimeoutError:
            raise Exception(f"Timeout waiting for response to {method}")
        return {}

    async def _send_notification(self, method: str, params: dict = None):
        """Send a JSON-RPC notification (no response expected)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        notification_str = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_str.encode())
        await self.process.stdin.drain()

    async def list_tools(self) -> list[dict]:
        """Get available tools from the MCP server"""
        response = await self._send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool on the MCP server"""
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        result = response.get("result", {})
        content = result.get("content", [])
        if content:
            texts = [c.get("text", "") for c in content if c.get("type") == "text"]
            return "\n".join(texts) if texts else str(content)
        if "error" in response:
            return json.dumps({"error": response["error"]})
        return str(result)

    async def close(self):
        """Close the MCP server process"""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                self.process.kill()  # Force kill if terminate doesn't work


class OllamaMCPWrapper:
    """Wrapper that connects Ollama to MCP servers"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.mcp_clients: dict[str, SimpleMCPClient] = {}
        self.tools: list[dict] = []
        self.tool_to_server: dict[str, str] = {}

    async def connect_mcp_server(self, name: str, command: str, args: list[str], env: dict = None, startup_delay: float = 0.5):
        """Connect to an MCP server"""
        client = SimpleMCPClient(name, command, args, env, startup_delay)
        await client.start()
        self.mcp_clients[name] = client

        # Get tools from this server
        tools = await client.list_tools()
        for tool in tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
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

    def parse_tool_calls(self, content: str) -> list[dict]:
        """Parse tool calls from Ollama response content"""
        tool_calls = []

        if not content:
            return tool_calls

        content = content.strip()

        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()

        # Try parsing as direct JSON
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "name" in parsed:
                tool_calls.append({
                    "name": parsed["name"],
                    "arguments": parsed.get("arguments", parsed.get("parameters", {}))
                })
                return tool_calls
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "name" in item:
                        tool_calls.append({
                            "name": item["name"],
                            "arguments": item.get("arguments", item.get("parameters", {}))
                        })
                return tool_calls
        except json.JSONDecodeError:
            pass

        # Try finding JSON objects in text
        json_pattern = r'\{[^{}]*"name"[^{}]*\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if "name" in parsed:
                    tool_calls.append({
                        "name": parsed["name"],
                        "arguments": parsed.get("arguments", parsed.get("parameters", {}))
                    })
            except json.JSONDecodeError:
                continue

        # Try finding nested JSON with arguments
        if not tool_calls:
            # Pattern for {"name": "...", "arguments": {...}}
            nested_pattern = r'\{"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{[^}]+\})\}'
            matches = re.findall(nested_pattern, content)
            for name, args_str in matches:
                try:
                    args = json.loads(args_str)
                    tool_calls.append({"name": name, "arguments": args})
                except json.JSONDecodeError:
                    tool_calls.append({"name": name, "arguments": {}})

        return tool_calls

    async def chat(self, prompt: str, model: str = "qwen2.5-coder:7b-instruct-q4_K_M", max_turns: int = 5) -> str:
        """Send a chat request to Ollama with MCP tools"""

        # Build tool list for system prompt
        tool_names = [t['function']['name'] for t in self.tools[:15]]  # Limit to first 15

        messages = [
            {"role": "system", "content": f"""You are a database assistant. Use the available tools to answer questions.

IMPORTANT RULES:
1. To see what tables exist, use: get_zen_schema or get_database_context
2. To run SQL queries, use: execute_raw_sql with {{"query": "SELECT ..."}}
3. Always respond with a single JSON tool call when you need data
4. Available tools: {', '.join(tool_names)}

When calling a tool, respond ONLY with JSON like:
{{"name": "tool_name", "arguments": {{"param": "value"}}}}"""},
            {"role": "user", "content": prompt}
        ]

        print(f"\n{'='*60}")
        print(f"[User] {prompt}")
        print(f"[Model] {model}")
        print(f"[Tools] {len(self.tools)} available")
        print('='*60)

        async with httpx.AsyncClient(timeout=300) as client:
            for turn in range(max_turns):
                # Send request to Ollama
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "tools": self.tools if self.tools else None,
                        "stream": False
                    }
                )
                result = response.json()
                message = result.get("message", {})
                content = message.get("content", "")
                native_tool_calls = message.get("tool_calls", [])

                # Check for native tool calls first
                if native_tool_calls:
                    print(f"\n[Turn {turn+1}] Native tool calls detected")
                    for tc in native_tool_calls:
                        func = tc.get("function", {})
                        tool_name = func.get("name")
                        tool_args = func.get("arguments", {})
                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except:
                                tool_args = {}

                        print(f"  [Tool] {tool_name}")
                        print(f"  [Args] {json.dumps(tool_args, indent=2)}")

                        # Execute tool
                        tool_result = await self.call_tool(tool_name, tool_args)
                        print(f"  [Result] {tool_result[:200]}..." if len(tool_result) > 200 else f"  [Result] {tool_result}")

                        # Add to messages
                        messages.append({"role": "assistant", "content": "", "tool_calls": [tc]})
                        messages.append({"role": "tool", "content": tool_result})
                    continue

                # Try parsing tool calls from content
                tool_calls = self.parse_tool_calls(content)

                if tool_calls:
                    print(f"\n[Turn {turn+1}] Parsed tool calls from content")
                    for tc in tool_calls:
                        tool_name = tc["name"]
                        tool_args = tc["arguments"]
                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except:
                                tool_args = {}

                        print(f"  [Tool] {tool_name}")
                        print(f"  [Args] {json.dumps(tool_args, indent=2)}")

                        # Execute tool
                        tool_result = await self.call_tool(tool_name, tool_args)
                        print(f"  [Result] {tool_result[:200]}..." if len(tool_result) > 200 else f"  [Result] {tool_result}")

                        # Add tool result to messages for next turn
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "user", "content": f"Tool '{tool_name}' returned: {tool_result}\n\nPlease provide your final answer based on this result."})
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


def load_mcp_config(config_file: str = None) -> dict:
    """Load MCP server configuration from JSON file or use defaults"""
    # Default configurations (built-in presets)
    default_configs = {
        "zen": {
            "zen-database": {
                "command": "python",
                "args": ["-m", "zen_sqlalchemy_mcp_server"],
                "env": {"ZEN_DSN": "ZenCC DEMODATA"},
                "startup_delay": 0.5
            }
        },
        "serena": {
            "serena": {
                "command": "C:\\Python313\\Scripts\\uvx.exe",
                "args": [
                    "--from", "git+https://github.com/oraios/serena.git",
                    "serena",
                    "start-mcp-server",
                    "--project", "D:\\ZenMCP\\DB_MCP_PILOT\\llm_test_harness"
                ],
                "startup_delay": 5.0
            }
        }
    }

    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return default_configs


async def main():
    """Main entry point"""
    wrapper = OllamaMCPWrapper()

    # Load configuration (can be overridden with --config file.json)
    config_file = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--config" and i + 2 < len(sys.argv):
            config_file = sys.argv[i + 2]
            break

    all_configs = load_mcp_config(config_file)

    # Parse MCP server selection from command line
    mcp_server_type = "zen"  # default
    for arg in sys.argv[1:]:
        if arg in all_configs:
            mcp_server_type = arg
            break

    mcp_servers = all_configs.get(mcp_server_type, all_configs.get("zen", {}))

    # Connect to MCP servers
    print(f"\n[Connecting to MCP server: {mcp_server_type}...]")
    for name, config in mcp_servers.items():
        try:
            await wrapper.connect_mcp_server(
                name,
                config["command"],
                config["args"],
                config.get("env"),
                config.get("startup_delay", 0.5)
            )
        except Exception as e:
            print(f"[ERROR] Failed to connect to {name}: {e}")

    if not wrapper.tools:
        print("[ERROR] No tools available. Check MCP server configuration.")
        await wrapper.close()
        return

    print(f"\n[Available tools: {len(wrapper.tools)}]")
    for tool in wrapper.tools[:10]:  # Show first 10
        print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")
    if len(wrapper.tools) > 10:
        print(f"  ... and {len(wrapper.tools) - 10} more")

    # Parse command line arguments (skip server type args already processed)
    model = "qwen2.5-coder:7b-instruct-q4_K_M"
    default_query = "What tables are in the database?" if mcp_server_type == "zen" else "List the Python files in this project"
    query = default_query

    # Filter out server type args for further parsing
    remaining_args = [arg for arg in sys.argv[1:] if arg not in ["zen", "serena"]]

    for i, arg in enumerate(remaining_args):
        if arg in ["14b", "qwen14b"]:
            model = "qwen2.5-coder:14b-instruct-q4_K_M"
        elif arg in ["7b", "qwen7b"]:
            model = "qwen2.5-coder:7b-instruct-q4_K_M"
        elif arg in ["llama", "llama3", "llama3.1", "llama8b"]:
            model = "llama3.1:8b"
        elif arg in ["qwen3", "qwen3-4b"]:
            model = "qwen3:4b"
        elif arg in ["llama3.2", "llama3b"]:
            model = "llama3.2:3b"
        elif arg in ["mistral", "mistral7b"]:
            model = "mistral:latest"
        elif arg in ["mistral-nemo", "nemo", "mistral12b"]:
            model = "mistral-nemo:latest"
        elif arg not in ["--interactive", "-i"] and not arg.startswith("-"):
            query = arg
            break

    # Check for interactive mode
    interactive_mode = "--interactive" in remaining_args or "-i" in remaining_args

    # Interactive mode or single query
    if interactive_mode:
        print("\n[Interactive mode - type 'quit' to exit]")
        while True:
            try:
                user_input = input("\n> ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                if not user_input:
                    continue
                await wrapper.chat(user_input, model)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[Error] {e}")
    else:
        await wrapper.chat(query, model)

    await wrapper.close()
    print("\n[Done]")


if __name__ == "__main__":
    asyncio.run(main())
