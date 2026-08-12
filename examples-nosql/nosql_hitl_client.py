#!/usr/bin/env python3
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.
"""Console client for approving Actian NoSQL writes (MCP elicitation).

Calls a tool on an Actian MCP Server for Actian NoSQL and, when the server asks for
confirmation before a write, prints the request and asks YOU at the console to
approve or decline.

The server registers its write tools only for clients that advertise the MCP
elicitation capability, and FastMCP advertises it only when an elicitation handler
is supplied. Use this client to exercise create_objects, update_objects, and
delete_objects from something that can answer the prompt: Claude Desktop and
GitHub Copilot cannot.

This client sends no credentials. Point it at a server running with authentication
disabled.

Requires: pip install fastmcp

Usage:
    python nosql_hitl_client.py <server_url> <tool_name> [json_args]

Read the class list:
    python nosql_hitl_client.py http://localhost:8080/mcp list_classes

Create an object, answering the confirmation prompt at the console:
    python nosql_hitl_client.py http://localhost:8080/mcp create_objects \
        '{"className": "Employee", "objects": [{"name": "Ada Lovelace"}]}'

Answer the prompt promptly: the server rejects the write once its own confirmation
window closes (nsql.writes.confirmation-timeout-seconds, 60 by default).
"""
import asyncio
import json
import sys

try:
    from fastmcp import Client
    from fastmcp.client.elicitation import ElicitResult
    from fastmcp.client.transports import StreamableHttpTransport
except ImportError as e:
    # Report the real error: "not installed" is misleading when fastmcp is present but one
    # of its dependencies fails to load.
    print(f"Error importing fastmcp: {e}", file=sys.stderr)
    print("If fastmcp is not installed, run: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

WRITE_TOOLS = ("create_objects", "update_objects", "delete_objects")


async def elicitation_handler(message, response_type, params, context):
    """Answer the server's confirmation request at the console."""
    print("\n=============== CONFIRMATION REQUESTED ===============")
    print(message)
    print("======================================================")
    print("The server rejects the write if you do not answer within its confirmation window")
    print("(nsql.writes.confirmation-timeout-seconds, 60 by default).")

    # input() runs on a worker thread so the connection stays responsive while it waits.
    answer = await asyncio.to_thread(input, "Approve this write? [y/N]: ")

    if answer.strip().lower() in ("y", "yes"):
        print(">> APPROVED\n")
        # The server declares one required boolean, `confirm`, and validates it: an accepted
        # prompt that does not carry it counts as unconfirmed and the write is refused.
        return ElicitResult(action="accept", content={"confirm": True})

    print(">> DECLINED\n")
    return ElicitResult(action="decline")


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    url, tool = sys.argv[1], sys.argv[2]

    raw_args = " ".join(sys.argv[3:]).strip()
    try:
        args = json.loads(raw_args) if raw_args else {}
    except json.JSONDecodeError as e:
        sys.exit(f"Tool arguments must be a JSON object: {e}")
    if not isinstance(args, dict):
        sys.exit("Tool arguments must be a JSON object.")

    transport = StreamableHttpTransport(url)
    async with Client(transport, elicitation_handler=elicitation_handler) as client:
        names = sorted(t.name for t in await client.list_tools())
        print(f"Connected to {url} - {len(names)} tools available.")
        print(f"Tools: {', '.join(names)}")

        missing = [name for name in WRITE_TOOLS if name not in names]
        if missing:
            print(f"\nNote: these write tools are not registered on this connection: "
                  f"{', '.join(missing)}.")
            print("Either writes are disabled server-side (nsql.writes.enabled), or the server")
            print("did not see this client's elicitation capability. Calling one of them below")
            print("will fail as an unknown tool.")

        print(f"\nCalling {tool}...")
        try:
            result = await client.call_tool(tool, args)
        except Exception as e:
            print(f"Tool error: {type(e).__name__}: {e}")
            sys.exit(1)

        if result.structured_content is not None:
            print(json.dumps(result.structured_content, indent=2))
        else:
            print("".join(getattr(block, "text", "") for block in result.content))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
