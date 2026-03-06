#!/usr/bin/env python3
# Standalone runner for natural language tests against OpenRouter + ActianMCP.

import asyncio
import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from prompt_parser import parse_prompt_file
from conftest import parse_setup_teardown


def _load_conf() -> dict:
    conf_path = Path(__file__).parent.parent.parent.parent / "zen_config.json"
    if conf_path.exists():
        with open(conf_path, encoding='utf-8') as f:
            return json.load(f)
    return {}


async def run_all():
    conf = _load_conf()
    llm_conf = conf.get("llm", {})

    parser = argparse.ArgumentParser(description="Run natural language tests")
    parser.add_argument("--model", default=None,
                        help="OpenRouter model (default: from zen_config.json)")
    parser.add_argument("--api-key", default=None,
                        help="OpenRouter API key (or set OPENROUTER_API_KEY)")
    parser.add_argument("--prompt-file", default=None,
                        help="Markdown prompt file (default: natural_language_requests.md)")
    parser.add_argument("--max-turns", type=int, default=None,
                        help="Max LLM conversation turns (default: from zen_config.json)")
    parser.add_argument("--timeout", type=int, default=None,
                        help="HTTP timeout in seconds (default: from zen_config.json)")
    args = parser.parse_args()

    # Resolve from CLI > zen_config.json > defaults
    model = args.model or llm_conf.get("model", "anthropic/claude-sonnet-4.5")
    max_turns = args.max_turns or llm_conf.get("max_turns", 10)
    timeout = args.timeout or llm_conf.get("timeout", 120)

    api_key = args.api_key
    if not api_key:
        api_key_env = llm_conf.get("api_key_env", "OPENROUTER_API_KEY")
        api_key = os.environ.get(api_key_env, "")
    if not api_key:
        api_key = llm_conf.get("api_key", "")
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY, use --api-key, or set api_key in zen_config.json")
        sys.exit(1)

    prompt_file = args.prompt_file or str(Path(__file__).parent / "natural_language_requests.md")

    # Parse tests
    tests = parse_prompt_file(prompt_file)
    print(f"Loaded {len(tests)} tests from {prompt_file}")

    # Setup MCP server (ActianMCP path: server.py → zen/tools.py → actian_zen.bridge)
    from types import SimpleNamespace
    from fastmcp import Client, FastMCP
    from actian_mcp_server.server import server_name, app_lifespan

    ZEN_CONF_ARGS = {
        "driver": "{Pervasive ODBC Interface}",
        "server": "",
        "database": "DEMODATA",
        "max_connections": 5,
        "host": "127.0.0.1",
        "port": 0,
    }

    server = FastMCP(
        server_name,
        lifespan=app_lifespan(
            SimpleNamespace(dbms="zen", transport="stdio", username=None, password=None),
            conf_file_args=ZEN_CONF_ARGS,
        ),
    )

    async with Client(server) as mcp_client:
        # Run SETUP SQL
        setup_stmts, teardown_stmts = parse_setup_teardown(prompt_file)
        if setup_stmts:
            print(f"Running SETUP ({len(setup_stmts)} statements)...")
            for sql in setup_stmts:
                try:
                    result = await mcp_client.call_tool("execute_query", {"sql": sql})
                    text = result.content[0].text if hasattr(result, 'content') and result.content else str(result)
                    data = json.loads(text)
                    if "error" in data and not sql.strip().upper().startswith("DROP"):
                        print(f"  SETUP WARNING: {data['error'][:80]}")
                except Exception:
                    pass
            print("SETUP complete.")

        # Get MCP tools
        tools_list = await mcp_client.list_tools()
        tools = []
        for tool in tools_list:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": (tool.description or "")[:500],
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {"type": "object", "properties": {}}
                }
            })
        print(f"MCP tools available: {len(tools)}")

        # Setup trace log
        os.makedirs("results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_path = os.path.join("results", f"natural_language_{timestamp}.jsonl")

        import httpx

        # Run tests
        print(f"\n{'='*70}")
        print(f"MODEL: {model}")
        print(f"{'='*70}\n")

        results = []
        for i, test in enumerate(tests, 1):
            start = time.time()
            test_id = test["id"]
            test_name = test["name"]
            prompt = test["prompt"]
            keywords = test.get("keywords", [])

            print(f"[{i:2d}/{len(tests)}] TEST {test_id}: {test_name}...", end=" ", flush=True)

            # Multi-turn LLM conversation
            messages = [{"role": "user", "content": prompt}]
            response_text = ""
            tool_calls_total = 0
            tools_used_set = set()
            trace = []
            error_msg = None

            try:
                for turn in range(max_turns):
                    async with httpx.AsyncClient(timeout=timeout) as http:
                        resp = await http.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "https://github.com/actian-zen",
                                "X-Title": "ActianMCP NL Tests"
                            },
                            json={
                                "model": model,
                                "messages": messages,
                                "tools": tools if tools else None,
                                "tool_choice": "auto"
                            }
                        )

                    if resp.status_code != 200:
                        error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                        break

                    data = resp.json()
                    message = data.get("choices", [{}])[0].get("message", {})
                    content = message.get("content", "")
                    tool_calls = message.get("tool_calls", [])

                    if tool_calls:
                        messages.append(message)
                        tool_calls_total += len(tool_calls)
                        for tc in tool_calls:
                            func = tc.get("function", {})
                            tool_name = func.get("name")
                            tool_args = func.get("arguments", {})
                            if isinstance(tool_args, str):
                                try:
                                    tool_args = json.loads(tool_args)
                                except json.JSONDecodeError:
                                    tool_args = {}
                            tools_used_set.add(tool_name)
                            try:
                                tool_result = await mcp_client.call_tool(tool_name, tool_args)
                                result_text = tool_result.content[0].text if hasattr(tool_result, 'content') and tool_result.content else str(tool_result)
                            except Exception as e:
                                result_text = json.dumps({"error": str(e)})
                            trace.append({
                                "tool": tool_name,
                                "args": tool_args,
                                "result_preview": result_text[:200]
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.get("id"),
                                "content": result_text
                            })
                        continue

                    response_text = content or ""
                    break
                else:
                    response_text = "Max turns reached"

            except Exception as e:
                error_msg = str(e)

            elapsed_ms = (time.time() - start) * 1000

            # Validate
            resp_lower = (response_text or "").lower()
            is_error = error_msg is not None or ("error" in resp_lower[:50])
            matched_kw = [kw for kw in keywords if kw.lower() in resp_lower]
            keyword_pass = len(matched_kw) > 0 if keywords else True
            success = not is_error and keyword_pass and len(response_text) > 0

            status = "PASS" if success else "FAIL"
            print(f"[{status}] {elapsed_ms:.0f}ms, {tool_calls_total} tools, {len(response_text)} chars")
            if error_msg:
                print(f"         ERROR: {error_msg[:100]}")
            if not keyword_pass and not is_error:
                print(f"         Keywords missed: {keywords}")

            record = {
                "timestamp": datetime.now().isoformat(),
                "test_id": test_id,
                "test_name": test_name,
                "prompt": prompt[:200],
                "response_length": len(response_text),
                "response_preview": response_text[:200] if response_text else "",
                "elapsed_ms": round(elapsed_ms),
                "tool_calls": tool_calls_total,
                "tools_used": sorted(tools_used_set),
                "trace": trace,
                "is_error": is_error,
                "error_message": error_msg,
                "keywords": keywords,
                "matched_keywords": matched_kw,
                "keyword_pass": keyword_pass,
                "success": success,
                "model": model,
            }
            results.append(record)

            with open(trace_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, default=str) + '\n')

        # Run TEARDOWN
        if teardown_stmts:
            print(f"\nRunning TEARDOWN ({len(teardown_stmts)} statements)...")
            for sql in teardown_stmts:
                try:
                    await mcp_client.call_tool("execute_query", {"sql": sql})
                except Exception:
                    pass
            print("TEARDOWN complete.")

        # Summary
        total = len(results)
        passed = sum(1 for r in results if r["success"])
        failed = total - passed
        avg_ms = sum(r["elapsed_ms"] for r in results) / total if total else 0
        avg_tools = sum(r["tool_calls"] for r in results) / total if total else 0

        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Model:        {model}")
        print(f"Total:        {total}")
        print(f"Passed:       {passed}")
        print(f"Failed:       {failed}")
        print(f"Success rate: {passed/total*100:.1f}%")
        print(f"Avg time:     {avg_ms:.0f}ms")
        print(f"Avg tools:    {avg_tools:.1f}")
        print(f"Trace log:    {trace_path}")
        print(f"{'='*70}")

        if failed > 0:
            print(f"\nFailed tests:")
            for r in results:
                if not r["success"]:
                    reason = r.get("error_message") or "keyword mismatch"
                    print(f"  TEST {r['test_id']}: {r['test_name']} — {reason[:80]}")


if __name__ == "__main__":
    asyncio.run(run_all())
