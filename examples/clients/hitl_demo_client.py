#!/usr/bin/env python3
# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""Interactive demo MCP client for human-in-the-loop (MCP elicitation).

Connects to an Actian MCP server, calls a tool, and when the tool asks for
approval (via request_write_confirmation -> MCP elicitation) it prints the
request and asks YOU at the console to approve or decline. Use it to exercise
the human-in-the-loop tools (adjust_stock, tag_vip_customer) on a server whose
normal client cannot render the approval prompt (Claude Desktop, Copilot Chat).

Requires: pip install fastmcp

Usage:
    python hitl_demo_client.py <server_url> <tool_name> ['{"json": "args"}']

Tool args can also come from a file or stdin. This approach avoids shell
quoting issues for JSON that contains SQL:
    python hitl_demo_client.py <url> execute_write_query @args.json
    Get-Content args.json | python hitl_demo_client.py <url> execute_write_query -

In PowerShell, always quote this argument. A bare @ is the splatting operator,
so the line fails to parse before Python starts:
    python hitl_demo_client.py <url> execute_write_query "@args.json"

Plain HTTP, no auth:
    python hitl_demo_client.py http://localhost:8000/mcp execute_query '{"query": "select * from customer limit 1"}'

HTTPS against a self-signed server cert:
    export MCP_CA_CERT=/path/to/server.crt
    python hitl_demo_client.py https://<mcp-server-host>:8000/mcp execute_query '{"query": "select 1"}'

Against an OAuth-protected server, self-signed cert:
    export MCP_AUTH=oauth
    export MCP_CA_CERT=/path/to/server.crt
    python hitl_demo_client.py https://<mcp-server-host>:8000/mcp execute_query '{"query": "select 1"}'
    # -> opens your browser to log in; the script continues once the token
    #    exchange completes

Environment variables (all optional):
    MCP_AUTH=oauth      Do the OAuth browser login (for servers that require it).
                        Without this the client sends no credentials.
    MCP_CA_CERT=<path>  Server certificate to trust for TLS (needed only for a
                        self-signed HTTPS server).
"""
import asyncio
import json
import logging
import os
import sys
import warnings

try:
    from fastmcp import Client
    from fastmcp.client.elicitation import ElicitResult
except ImportError as e:
    # Report the real error. A bare "not installed" message is misleading when
    # fastmcp is present but one of its dependencies fails to load, for example
    # a binary wheel built for the wrong CPU architecture.
    print(f"Error importing fastmcp: {e}", file=sys.stderr)
    print("If fastmcp is not installed, run: pip install fastmcp", file=sys.stderr)
    sys.exit(1)


async def elicitation_handler(message, response_type, params, context):
    """Called when the server asks the user to approve something.

    No client-side timeout here: request_write_confirmation() on the server
    already wraps its own wait in asyncio.wait_for() and fails closed if
    nobody answers in time, so the write can never hang open. Blocking
    indefinitely on input() just means an unattended terminal sits idle
    until Ctrl-C -- not a correctness or security concern.
    """
    print("\n================ APPROVAL REQUESTED ================")
    print(message)
    print("===================================================")
    answer = (await asyncio.to_thread(input, "Approve this write? [y/N]: ")).strip().lower()
    if answer in ("y", "yes"):
        print(">> APPROVED\n")
        return ElicitResult(action="accept", content={})
    print(">> DECLINED\n")
    return ElicitResult(action="decline")


def _text(result):
    return "".join(getattr(b, "text", "") for b in result.content)


def _parse_tool_args(raw: str) -> dict:
    if not raw:
        return {}
    # PowerShell mangles nested quotes badly enough that inline JSON with SQL in
    # it is close to unusable, so take the args from a file or stdin instead.
    if raw == "-":
        raw = sys.stdin.read().strip()
    elif raw.startswith("@"):
        with open(raw[1:], "r", encoding="utf-8-sig") as handle:
            raw = handle.read().strip()
    if not raw:
        return {}
    raw = raw.lstrip("﻿")   # Set-Content -Encoding utf8 writes a BOM
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Tool args must be a JSON object")
    return data


async def main():
    # Suppress BrokenResourceError logging from SSE cleanup
    logging.getLogger("mcp.client.streamable_http").setLevel(logging.CRITICAL)
    logging.getLogger("anyio").setLevel(logging.CRITICAL)

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    url, tool = sys.argv[1], sys.argv[2]
    try:
        args = _parse_tool_args(" ".join(sys.argv[3:]).strip())
    except Exception as e:
        print(f"Argument error: {e}", file=sys.stderr)
        print('Tool args must be a JSON object, e.g. \'{"product_id": 1, "delta": 5}\'', file=sys.stderr)
        sys.exit(2)

    cert = os.environ.get("MCP_CA_CERT")
    if cert:
        if not os.path.exists(cert):
            print(f"MCP_CA_CERT does not exist: {cert}", file=sys.stderr)
            sys.exit(1)
        # The server's own cert is sufficient trust for talking to that one
        # server -- this client makes no other HTTPS calls that would need
        # the system/certifi CAs too.
        os.environ["SSL_CERT_FILE"] = cert

    # Suppress BrokenResourceError warnings from SSE cleanup
    warnings.filterwarnings("ignore", category=ResourceWarning)

    client_auth = "oauth" if os.environ.get("MCP_AUTH", "").lower() == "oauth" else None

    ok = True
    try:
        async with Client(url, elicitation_handler=elicitation_handler, auth=client_auth) as client:
            names = sorted(t.name for t in await client.list_tools())
            print(f"Connected to {url} ({len(names)} tools): {', '.join(names)}")
            print(f"Calling {tool}({args}) ...")
            try:
                result = await client.call_tool(tool, args)
                print("Result:", _text(result))
            except Exception as e:  # tool errors surface here
                print("Tool error:", type(e).__name__, str(e)[:200])
                ok = False

            # Give a moment for cleanup
            await asyncio.sleep(0.1)

        # Force exit (skipping normal interpreter shutdown) to avoid hanging on
        # a background thread still blocked in input() -- notably on Windows.
        os._exit(0 if ok else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        message = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in message:
            print("TLS verification failed for a self-signed server certificate.", file=sys.stderr)
            print("Set MCP_CA_CERT to your server's cert path, then retry.", file=sys.stderr)
            sys.exit(3)
        if "401 Unauthorized" in message or ("HTTPStatusError" in type(e).__name__ and "401" in message):
            print("Authentication failed: server returned 401 Unauthorized.", file=sys.stderr)
            print("If this server requires auth, set MCP_AUTH=oauth and retry.", file=sys.stderr)
            sys.exit(4)
        raise


if __name__ == "__main__":
    asyncio.run(main())
