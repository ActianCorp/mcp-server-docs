#!/usr/bin/env python3
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.
"""Interactive demo MCP client for human-in-the-loop (MCP elicitation).

Connects to an Actian MCP server, calls a tool, and when the tool asks for
approval (via request_write_confirmation -> MCP elicitation) it prints the
request and asks YOU at the console to approve or decline. Use it to exercise
the human-in-the-loop tools (adjust_stock, tag_vip_customer) on a server whose
normal client can't render the approval prompt (Claude Desktop, Copilot Chat).

Requires: pip install fastmcp

Usage:
    python hitl_demo_client.py <server_url> <tool_name> [json_args]

Plain HTTP, no auth (simplest):
    python hitl_demo_client.py http://localhost:8000/mcp execute_query "select * from customer limit 1"

HTTPS with OAuth browser login, trusting a self-signed server cert:
    export MCP_AUTH=oauth
    export MCP_CA_CERT=/path/to/server.crt   # the server's cert
    python hitl_demo_client.py https://<mcp-server-host>:8000/mcp execute_query "select * from customer limit 1"

Environment variables (all optional):
    MCP_AUTH=oauth      Do the OAuth browser login (for OIDCProxy/Auth0 servers).
    MCP_CA_CERT=<path>  CA/server cert to trust for TLS (needed for a self-signed
                        HTTPS server). Added on top of the system/certifi CAs, so
                        Auth0's real cert keeps validating too.
    MCP_SCOPES=<str>    Space-separated OAuth scopes to request
                        (default "openid email profile mcp:write"). The token only
                        carries mcp:write if your user is actually granted it, so
                        you can test the write-scope gate by logging in as users
                        with and without it.
    MCP_APPROVAL_TIMEOUT_SECS=<n>
                        Timeout for approval prompt input in seconds
                        (default 60).
"""
import asyncio
import json
import logging
import os
import ssl
import sys
import tempfile
import warnings
from typing import Any

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
    """Called when the server asks the user to approve something."""
    print("\n================ APPROVAL REQUESTED ================")
    print(message)
    print("===================================================")
    timeout_secs_raw = os.environ.get("MCP_APPROVAL_TIMEOUT_SECS", "60").strip()
    try:
        timeout_secs = float(timeout_secs_raw)
    except ValueError as exc:
        raise ValueError(
            f"MCP_APPROVAL_TIMEOUT_SECS must be numeric, got: {timeout_secs_raw!r}"
        ) from exc
    if timeout_secs <= 0:
        raise ValueError(f"MCP_APPROVAL_TIMEOUT_SECS must be > 0, got: {timeout_secs}")

    try:
        answer = (
            await asyncio.wait_for(
                asyncio.to_thread(input, f"Approve this write? [y/N] (timeout {timeout_secs:g}s): "),
                timeout=timeout_secs,
            )
        ).strip().lower()
    except asyncio.TimeoutError:
        print(f"\n>> TIMEOUT after {timeout_secs:g}s - automatically DECLINED\n")
        return ElicitResult(action="decline")

    if answer in ("y", "yes"):
        print(">> APPROVED\n")
        return ElicitResult(action="accept", content={})
    print(">> DECLINED\n")
    return ElicitResult(action="decline")


def _text(result):
    return "".join(getattr(b, "text", "") for b in result.content)


def _configure_ssl_trust():
    """Configure process TLS trust to include optional self-signed MCP cert.

    FastMCP 3.x no longer accepts a `verify=` kwarg on Client. To keep support
    for self-signed MCP servers, we build a CA bundle (certifi + MCP_CA_CERT)
    and point SSL_CERT_FILE to it.
    """
    cert = os.environ.get("MCP_CA_CERT")
    if not cert:
        # Helpful default for local Windows testing when env vars are not set.
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(os.getcwd(), "server.crt"),
            os.path.join(home, "server.crt"),
            os.path.join(home, "mcp-server.crt"),
        ]
        cert = next((p for p in candidates if os.path.exists(p)), None)
        if cert:
            print(f"Auto-detected cert: {cert}")
        else:
            return None
    if not os.path.exists(cert):
        raise FileNotFoundError(f"MCP_CA_CERT does not exist: {cert}")

    try:
        import certifi
        with open(certifi.where(), "r", encoding="utf-8") as f:
            bundle = f.read()
    except Exception:
        bundle = ""

    with open(cert, "r", encoding="utf-8") as f:
        extra = f.read()

    fd, bundle_path = tempfile.mkstemp(prefix="mcp_ca_bundle_", suffix=".pem")
    os.close(fd)
    with open(bundle_path, "w", encoding="utf-8") as f:
        if bundle:
            f.write(bundle.rstrip() + "\n")
        f.write(extra.strip() + "\n")

    os.environ["SSL_CERT_FILE"] = bundle_path
    os.environ["REQUESTS_CA_BUNDLE"] = bundle_path
    return bundle_path


def _parse_tool_args(argv: list[str], tool: str) -> dict:
    """Parse tool args from CLI.

    Accepted forms:
    - JSON object: '{"query": "SELECT 1"}'
    - JSON file:   @args.json
    - Raw SQL for SQL tools: SELECT * FROM t WHERE email = 'a@b.com'
    """
    if len(argv) <= 3:
        return {}

    raw = " ".join(argv[3:]).strip()
    if not raw:
        return {}

    # Support @file path that contains a JSON object
    if raw.startswith("@"):
        json_path = raw[1:]
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("JSON args file must contain an object")
        return data

    # Prefer JSON when possible.
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON args must be an object")
        return data
    except json.JSONDecodeError:
        pass

    # Fall back to raw SQL for common SQL tools.
    if tool in {"execute_query", "request_sql_execution"}:
        return {"query": raw}

    raise ValueError(
        "Could not parse args. Pass a JSON object, @json_file, or raw SQL for execute_query/request_sql_execution."
    )


async def main():
    # Suppress BrokenResourceError logging from SSE cleanup
    logging.getLogger("mcp.client.streamable_http").setLevel(logging.CRITICAL)
    logging.getLogger("anyio").setLevel(logging.CRITICAL)
    
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    url, tool = sys.argv[1], sys.argv[2]
    try:
        args = _parse_tool_args(sys.argv, tool)
    except Exception as e:
        print(f"Argument error: {e}", file=sys.stderr)
        sys.exit(2)

    client_kwargs: dict[str, Any] = {"elicitation_handler": elicitation_handler}

    if os.environ.get("MCP_AUTH", "").lower() == "oauth":
        # Browser-based OAuth (DCR) against an OIDCProxy/Auth0 server. FastMCP
        # applies `verify` (below) to the OAuth flow's HTTPS calls too.
        from fastmcp.client.auth import OAuth
        scopes = os.environ.get("MCP_SCOPES", "openid email profile mcp:write")
        client_kwargs["auth"] = OAuth(mcp_url=url, scopes=scopes.split())

    bundle_path = _configure_ssl_trust()
    if bundle_path:
        print(f"Using custom CA bundle: {bundle_path}")

    # Suppress BrokenResourceError warnings from SSE cleanup
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    try:
        async with Client(url, **client_kwargs) as client:
            names = sorted(t.name for t in await client.list_tools())
            print(f"Connected to {url} ({len(names)} tools).")
            print(f"Calling {tool}({args}) ...")
            print(f"Available tools: {', '.join(names)}")
            try:
                result = await client.call_tool(tool, args)
                print("Result:", _text(result))
            except Exception as e:  # tool errors surface here
                print("Tool error:", type(e).__name__, str(e)[:200])
            
            # Give a moment for cleanup
            await asyncio.sleep(0.1)
        
        # Force exit to avoid hanging on Windows input() thread
        os._exit(0)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        message = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in message:
            print("TLS verification failed for a self-signed server certificate.", file=sys.stderr)
            print("Set MCP_CA_CERT to your server cert path, then retry.", file=sys.stderr)
            print("PowerShell example:", file=sys.stderr)
            print("  $env:MCP_CA_CERT = 'C:/path/to/server.crt'", file=sys.stderr)
            print(
                f"  python hitl_demo_client.py {url} {tool} \"{' '.join(sys.argv[3:])}\"",
                file=sys.stderr,
            )
            sys.exit(3)
        if "401 Unauthorized" in message or ("HTTPStatusError" in type(e).__name__ and "401" in message):
            print("Authentication failed: server returned 401 Unauthorized.", file=sys.stderr)
            print("If this server uses OAuth, enable MCP_AUTH=oauth and retry.", file=sys.stderr)
            print("PowerShell example:", file=sys.stderr)
            print("  $env:MCP_AUTH = 'oauth'", file=sys.stderr)
            print("  $env:MCP_SCOPES = 'openid email profile mcp:write'", file=sys.stderr)
            print("  $env:MCP_CA_CERT = 'C:/path/to/server.crt'", file=sys.stderr)
            print(
                f"  python hitl_demo_client.py {url} {tool} \"{' '.join(sys.argv[3:])}\"",
                file=sys.stderr,
            )
            sys.exit(4)
        raise


if __name__ == "__main__":
    asyncio.run(main())