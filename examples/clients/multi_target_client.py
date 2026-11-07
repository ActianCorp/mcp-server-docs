#!/usr/bin/env python3
# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""Demo MCP client for a multi-target Ingres/Analytics Engine server.

Demonstrates the thing that's actually new about multi-target: ONE token can
carry grants for several (host, instance, database) targets at once
(per-target OAuth scopes -- actian:{host}:{instance}:{database}:{read|write},
see the Multi-Target Deployments documentation), and one client session can walk across all
of them. It first calls list_accessible_targets (the authoritative "what can
this token reach" answer), then calls a tool against every target you pass on
the command line -- reporting which ones succeeded and which were denied.

Writes (INSERT/UPDATE/DELETE via execute_query) need three things at once:
the server in read-write query_mode, a `:write` grant for that specific
target/database (with only a `:read` grant the write is refused by the
tool, naming the missing `:write` scope), and human approval over MCP
**elicitation** -- like hitl_demo_client.py, this script prints the
approval request and asks YOU at the console. Approve or decline separately
for each target you list; declining just that target does not stop the
others from running.

Authentication: MCP_AUTH=oauth -- interactive browser login (authorization
code + PKCE) against the server's OAuth login (see the Auth0 or Keycloak
setup documentation). Opens your browser once; the same credentials are
then reused for every target you list, so walking several targets only
prompts once per run. This is the only authentication mode this script
supports: a server that runs the OAuth login itself does not accept a
pre-obtained bearer token presented directly.

Requires: pip install fastmcp httpx

Usage:
    python multi_target_client.py <base_url> <tool_name> <args_json> <host/instance/database> [more...]

`base_url` is the server's fixed base path (e.g. https://mcp.example.com/mcp)
-- NOT a routed path; this script builds each routed URL itself by appending
one `host/instance/database` spec at a time.

Interactive browser login, walking two targets with one login -- note
`hrdb` gets its own query, since it has an `employees` table, not `products`:
    export MCP_AUTH=oauth
    python multi_target_client.py https://mcp.example.com/mcp execute_query \\
        '{"query": "select count(*) from products"}' \\
        ingres-server/II/db1 ingres-server-2/II/salesdb
    python multi_target_client.py https://mcp.example.com/mcp execute_query \\
        '{"query": "select count(*) from employees"}' \\
        ingres-server-2/II/hrdb
    # -> opens your browser to log in once; every target in one run reuses it

A write, requiring a `:write` grant (not just `:read`) plus your approval at
the console when the server prompts:
    python multi_target_client.py https://mcp.example.com/mcp execute_query \\
        '{"query": "update products set price = 24.99 where product_id = 2"}' \\
        ingres-server-2/II/salesdb

Just checking reachability with list_tables across two targets:
    python multi_target_client.py https://mcp.example.com/mcp list_tables '{}' \\
        ingres-server/II/db1 ingres-server-2/II/salesdb

A target the token has no read grant for is refused with 403
insufficient_scope, naming the missing read scope -- identically to a target
that doesn't exist at all (so targets cannot be probed), so "denied" and
"unknown" are reported the same way here, by design:
    python multi_target_client.py https://mcp.example.com/mcp list_tables '{}' \\
        ingres-server-2/II/hrdb  # denied, or doesn't exist -- can't tell which

HTTPS against a self-signed server cert:
    export MCP_CA_CERT=/path/to/server.crt

Environment variables:
    MCP_AUTH=oauth      Do the OAuth browser login (required -- see above).
    MCP_CA_CERT=<path>  Server certificate to trust for TLS (needed only for
                        a self-signed HTTPS server).
"""
import asyncio
import json
import os
import re
import sys

import httpx

try:
    from fastmcp import Client
    from fastmcp.client.auth import OAuth
    from fastmcp.client.elicitation import ElicitResult
except ImportError as e:
    # Report the real error. A bare "not installed" message is misleading when
    # the package is present but one of its dependencies fails to load, for
    # example a binary wheel built for the wrong CPU architecture.
    print(f"Error importing dependencies: {e}", file=sys.stderr)
    print("If missing, run: pip install fastmcp httpx", file=sys.stderr)
    sys.exit(1)


async def _elicitation_handler(message, response_type, params, context):
    """Called when the server asks for approval before a write (MCP
    elicitation) -- same pattern as hitl_demo_client.py. Per target, not
    global: each target's write is approved or declined independently, so
    declining one doesn't affect the others in the same run.

    No client-side timeout here: request_write_confirmation() on the server
    already wraps its own wait in asyncio.wait_for() and fails closed if
    nobody answers in time, so a write can never hang open waiting on this.
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


class _OAuthWithoutStepUp(OAuth):
    """fastmcp's OAuth, minus the automatic re-login on a 403.

    The mcp SDK answers a 403 insufficient_scope by re-running the browser
    login asking for the scope in the challenge. Behind the server's OAuth login
    that fails: the client registered once, with the scopes the server
    advertises, and the proxy refuses a scope it was not registered with --
    "Client was not registered with scope ..." -- before any response reaches
    this script, so the real answer (the 403 and the scope it names) is never
    shown. Returning the 403 untouched lets _call_one_target print it.
    """

    async def async_auth_flow(self, request):
        flow = super().async_auth_flow(request)
        response = None
        try:
            while True:
                try:
                    outgoing = await flow.asend(response)
                except StopAsyncIteration:
                    return
                response = yield outgoing
                if (response.status_code == 403
                        and 'error="insufficient_scope"'
                        in response.headers.get("www-authenticate", "")):
                    return
        finally:
            await flow.aclose()


def _resolve_auth(base_url: str):
    """Returns whatever fastmcp.Client's `auth=` parameter accepts. Resolved
    ONCE per run and reused for every Client() call below (the accessible-
    targets check and every per-target call) -- one browser login this way
    covers every target, rather than prompting once per target.

    MCP_AUTH=oauth is the only mode this script supports -- see the module
    docstring for why a pre-obtained bearer token isn't offered as an
    alternative: it doesn't work against a server that runs the OAuth login itself.
    """
    if os.environ.get("MCP_AUTH", "").lower() != "oauth":
        raise RuntimeError(
            "Set MCP_AUTH=oauth. This script only supports the interactive "
            "browser login -- see the module docstring for why a bearer "
            "token isn't offered as an alternative."
        )
    # Bound to base_url once, up front -- passing this SAME object to
    # Client() for every routed target URL (rather than the "oauth"
    # shortcut string, which would build a fresh, unbound provider with
    # its own empty in-memory token cache per Client instance) is what
    # makes one browser login cover every target this run touches. The
    # token itself isn't tied to the specific routed path, only to the
    # audience the server was configured with, so reusing it across
    # different target paths on the same server is correct.
    return _OAuthWithoutStepUp(mcp_url=base_url)


def _parse_target_spec(spec: str) -> str:
    parts = spec.split("/")
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"Target spec must be host/instance/database, got {spec!r}")
    return "/".join(parts)


async def _show_accessible_targets(base_url: str, auth) -> None:
    """The authoritative answer to "what can this identity reach" -- an
    ordinary tool, callable at the server's fixed base path (never a routed
    one)."""
    try:
        async with Client(base_url, auth=auth, elicitation_handler=_elicitation_handler) as client:
            result = await client.call_tool("list_accessible_targets", {})
            print("Accessible targets (list_accessible_targets):")
            print(" ", _text(result))
    except Exception as e:
        # Not fatal -- a flat/single-target deployment doesn't register this
        # tool at all, and that's a normal, expected shape too.
        print(f"(list_accessible_targets unavailable or failed: {type(e).__name__}: {e})")


async def _call_one_target(base_url: str, target_spec: str, tool: str, args: dict, auth) -> tuple[str, bool, str]:
    url = f"{base_url.rstrip('/')}/{target_spec}"
    try:
        async with Client(url, auth=auth, elicitation_handler=_elicitation_handler) as client:
            result = await client.call_tool(tool, args)
            return target_spec, True, _text(result)
    except httpx.HTTPStatusError as e:
        # A routed target the server rejects (unknown, or a real target this
        # token has no read grant for) answers 403 insufficient_scope, and the
        # WWW-Authenticate header names the scope that would allow it. The
        # server answers "doesn't exist" and "exists but not granted" the same
        # way on purpose, so targets cannot be probed -- not a bug in this script.
        challenge = e.response.headers.get("www-authenticate", "")
        if e.response.status_code == 403 and 'error="insufficient_scope"' in challenge:
            described = re.search(r'error_description="([^"]*)"', challenge)
            detail = described.group(1) if described else "insufficient scope"
            return target_spec, False, (
                f"denied (403) -- {detail}. Either this token lacks that grant, "
                "or the target does not exist")
        return target_spec, False, f"{type(e).__name__}: {str(e)[:200]}"
    except Exception as e:
        return target_spec, False, f"{type(e).__name__}: {str(e)[:200]}"


async def main():
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)
    base_url, tool = sys.argv[1], sys.argv[2]
    try:
        args = _parse_tool_args(sys.argv[3])
    except Exception as e:
        print(f"Argument error: {e}", file=sys.stderr)
        print('Tool args must be a JSON object, e.g. \'{"query": "select 1"}\'', file=sys.stderr)
        sys.exit(2)

    try:
        target_specs = [_parse_target_spec(s) for s in sys.argv[4:]]
    except ValueError as e:
        print(f"Argument error: {e}", file=sys.stderr)
        sys.exit(2)

    cert = os.environ.get("MCP_CA_CERT")
    if cert:
        if not os.path.exists(cert):
            print(f"MCP_CA_CERT does not exist: {cert}", file=sys.stderr)
            sys.exit(1)
        os.environ["SSL_CERT_FILE"] = cert

    try:
        auth = _resolve_auth(base_url)
    except Exception as e:
        print(f"Authentication setup failed: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        await _show_accessible_targets(base_url, auth)
        print()

        print(f"Calling {tool}({args}) against {len(target_specs)} target(s):")
        all_ok = True
        # Sequential, not gathered concurrently -- so output prints in the
        # order given and one target's error can't get interleaved with
        # another's, which matters when eyeballing this by hand. It also
        # means the browser-login prompt (first call only -- see
        # _resolve_auth) can't get raced by a second target's own attempt.
        for spec in target_specs:
            target_spec, ok, detail = await _call_one_target(base_url, spec, tool, args, auth)
            status = "OK  " if ok else "FAIL"
            print(f"  [{status}] {target_spec}: {detail}")
            all_ok = all_ok and ok

        os._exit(0 if all_ok else 1)
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
            print("Check MCP_AUTH=oauth and retry.", file=sys.stderr)
            sys.exit(4)
        raise


if __name__ == "__main__":
    asyncio.run(main())
