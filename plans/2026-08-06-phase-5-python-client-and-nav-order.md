# Phase 5: Merge the Python Client Guide and Reorder the Navigation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal plan placed there would appear on docs.actian.com.

**Goal:** Break the mutual redirect between the client guide and the NoSQL setup page by
giving the Python client one page that covers both, and put the navigation into the order
the spec's target structure calls for.

**Architecture:** The Python client is documented twice today — once on
`docs/mcp-clients/index.md` for the SQL engines and once on `docs/nosql/index.md` for
NoSQL — and each copy sends the other's readers away. Merge them into
`docs/mcp-clients/python.md`, using content tabs only where the code genuinely differs.
Enable `content.tabs.link` so the reader's choice follows them across pages. Then reorder
`docs/.pages` so the five databases sit directly after Get started, with the cross-cutting
topics below them.

**Tech Stack:** MkDocs 1.6.1, mkdocs-material 9.6+ (`content.tabs.link`,
`pymdownx.tabbed`), pymdown-extensions 10.21.2, GNU make

## Global Constraints

- Phases 1–4 are prerequisites and are complete as of commit `e1c6e5f`.
- Verification after every task, all three must pass:
  ```bash
  python3 -m mkdocs build --strict     # no -q: it suppresses the warnings
  make check-templates
  python3 -m mkdocs build -q && make check-raw-md
  ```
- **Tab labels must be word-for-word identical everywhere.** `content.tabs.link`
  synchronises tabs by their label text across the whole site and across page
  navigations, which is what turns them into a database switcher. This phase establishes
  exactly two labels, and phase 6 must reuse them verbatim:
  - `SQL databases`
  - `Actian NoSQL`
- `pymdownx.tabbed` with `alternate_style: true` is already enabled (it has been since
  before this project). Only `content.tabs.link` is new.
- Trust the build over the grep — a lesson from phase 4, where an inventory missed a
  sibling-relative link that `--strict` then caught. Every link-touching step here ends
  with a strict build.

## Measured: two copies that send readers to each other

| | `docs/mcp-clients/index.md` | `docs/nosql/index.md` |
|---|---|---|
| Section | `## Connect Using Python Client` (lines 126–272) | `## Connect Using a Python Client` (lines 107–243) |
| Prerequisites | numbered list, two `pip` blocks | one `pip` block with an inline comment |
| Basic example | port `8000`, first call `list_tables` | port `8080`, first call `list_classes` |
| OAuth example | inline `httpx` lambda, `auth="oauth"` | named `make_httpx_client`, `OAuth(client_id=…)` |
| Parameter names | table: Zen uses `sql`/`table`, the others `query`/`table_name` | not applicable |

Structurally the same guide, twice. The imports and the transport construction are
identical; the basic example differs only in port and first tool call.

### The mutual redirect

- `docs/mcp-clients/index.md:128-129` — a **warning**: "Actian NoSQL uses different tools
  … For a NoSQL-specific Python client example, see [the NoSQL page]".
- `docs/nosql/index.md:109-110` — a **note**: "For connecting AI clients such as Claude
  Desktop, Cursor, fast-agent, and Codex, see the [Connecting MCP Clients] guide".

A NoSQL reader on the client page is sent to the NoSQL page; a reader on the NoSQL page
looking for client configuration is sent back. Spec §1.1 catalogued the NoSQL side of this
loop but not the other, so this is the **fourth** admonition of the class the restructure
set out to remove — after the two in `get-started/` (phase 2) and the extensions one
(phase 4).

## Two verified defects in the code examples

Both are fixed as part of the merge. Neither is a judgement call; both were checked.

### 1. The SQL OAuth example trusts the wrong certificates

`docs/mcp-clients/index.md:240` builds its TLS context as:

```python
ssl_ctx = ssl.create_default_context(cafile="/path/to/server.crt")
```

Passing `cafile` **replaces** the trust store rather than adding to it. Measured:

```
create_default_context(cafile=certifi.where())  ->  137 certificates
create_default_context()            [system]   ->  128 certificates
load_verify_locations() afterwards             ->  137 grows to 181
```

So that context trusts *only* the self-signed MCP server certificate. Requests to the
identity provider, which uses a public CA, fail verification — in the one scenario the
example exists to document (OAuth over HTTPS with a self-signed server certificate). The
NoSQL example already does it correctly: start from `certifi.where()`, then
`load_verify_locations()` the self-signed certificate. The merged page uses that pattern
for both.

### 2. The NoSQL OAuth example is not valid Python

`docs/nosql/index.md:195` reads:

```python
CALLBACK_PORT = <callback-port>   # must match the redirect URI registered in your identity provider
```

`<callback-port>` is a syntax error, so the example fails on import before it does
anything. The merged page uses a concrete port with the explanation in the comment.

## Deferred: what this phase does not decide

| Deferred | Why |
|---|---|
| Which OAuth client approach to recommend | The SQL example uses `auth="oauth"`; the NoSQL example constructs `OAuth(client_id=…, callback_port=…)`. These are different FastMCP usages implying different identity-provider setups (dynamic registration versus a pre-registered client). Both are kept as they are. Picking one, or explaining when to use which, is a product statement this repository does not establish. |
| Merging the two OAuth examples into one | Follows from the above. While the auth approaches differ, the examples stay in separate tabs. |

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `docs/mcp-clients/python.md` | The single Python client guide, tabbed where the code differs | 1 |
| `mkdocs.yml` | Adds `content.tabs.link` to `theme.features` | 1 |
| `docs/mcp-clients/.pages` | New — orders `index.md` before `python.md` | 1 |
| `docs/mcp-clients/index.md` | Loses its Python section and its NoSQL warning | 2 |
| `docs/nosql/index.md` | Loses its Python section and its client-guide note | 2 |
| `docs/.pages` | Reordered to the spec's target structure | 3 |
| `specs/2026-08-05-docs-by-database-design.md` | Records the fourth admonition and the two code fixes | 4 |

---

## Task 0: Capture the baseline

**Files:** none

- [ ] **Step 1: Confirm phase 4 is in place and the tree is clean**

```bash
git status --short
ls docs/write-support/nosql.md docs/extensions/nosql.md includes/stub-notice.md
```

Expected: `git status` shows nothing except possibly `theme_overrides/.DS_Store`, a macOS
Finder artefact that is not part of this work — leave it. All three files listed.

- [ ] **Step 2: Build the baseline**

```bash
python3 -m mkdocs build -q -d /tmp/phase5-baseline-site
```

- [ ] **Step 3: Record what the two Python sections contain**

So Task 2's deletion can be checked for accidental over-reach.

```bash
sed -n '126,272p' docs/mcp-clients/index.md | wc -l
sed -n '107,243p' docs/nosql/index.md | wc -l
grep -c 'list_tables\|list_classes' docs/mcp-clients/index.md docs/nosql/index.md
```

Expected: `147` and `137` lines respectively, and a non-zero count for each file.

---

## Task 1: Create the merged Python client page

**Files:**
- Create: `docs/mcp-clients/python.md`
- Create: `docs/mcp-clients/.pages`
- Modify: `mkdocs.yml` (`theme.features`)

**Interfaces:**
- Produces `docs/mcp-clients/python.md` with two tab labels, `SQL databases` and
  `Actian NoSQL`, which phase 6 must reuse verbatim for the switcher to work across pages.
- Produces the anchors `#prerequisites`, `#tool-and-parameter-names`,
  `#connect-to-the-server` and `#connect-with-oauth`. Task 2 needs the last two when it
  redirects the removed sections' readers.

- [ ] **Step 1: Enable linked content tabs**

In `mkdocs.yml`, add to the `theme.features` list, after `content.code.annotate`:

```yaml
    - content.tabs.link
```

Without this, each tabbed block remembers its own selection and the tabs do not act as a
switcher.

- [ ] **Step 2: Create the page**

Create `docs/mcp-clients/python.md` with exactly this content. The prose is shared; only
the two code sections are tabbed. Both defects from the section above are fixed here.

````markdown
---
title: Python Client
description: Connect to the Actian MCP Server from Python with the FastMCP client.
---

# Connect a Python client

The [FastMCP](https://pypi.org/project/fastmcp/) Python client talks to any Actian MCP
Server. Use it to script against the server, to test a deployment, or to build your own
agent instead of using a desktop AI client.

The connection itself is the same for every database. What differs is the port the server
listens on and the tools it exposes, so pick your database in the tabs below.

## Prerequisites

Install the client:

```bash
pip install fastmcp
```

OAuth authentication additionally needs `httpx` and `certifi`:

```bash
pip install httpx certifi
```

## Tool and parameter names

The SQL engines expose the same tools, but two parameter names differ on Zen:

| Tool | Ingres / HCL Informix® / Analytics Engine | Zen |
|------|------------------------------------------|-----|
| `execute_query` | `query` | `sql` |
| `describe_table` | `table_name` | `table` |

The examples below use the Ingres, HCL Informix® and Analytics Engine names. For Zen,
substitute from this table.

Actian NoSQL exposes a different set of tools entirely — `list_classes`,
`describe_class`, LOID lookups, and JPQL queries. See
[NoSQL tools](../nosql/tools/index.md).

## Connect to the server

=== "SQL databases"

    ```python
    """Actian MCP Server — Python client example."""

    import asyncio
    import json
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport


    async def main():
        server_url = "http://localhost:8000/mcp"

        transport = StreamableHttpTransport(url=server_url)

        async with Client(transport, timeout=60) as client:

            # 1. Discover available tools and their parameters
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}")

            # 2. List the tables in the database
            result = await client.call_tool("list_tables", {})
            print(f"\nTables:\n{json.dumps(result.structured_content, indent=2)}")

            # 3. Run a read-only query
            result = await client.call_tool(
                "execute_query", {"query": "SELECT CURRENT_USER"}
            )
            print(f"\nCurrent user:\n{json.dumps(result.structured_content, indent=2)}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

=== "Actian NoSQL"

    ```python
    """Actian MCP Server for Actian NoSQL — Python client example."""

    import asyncio
    import json
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport


    async def main():
        server_url = "http://localhost:8080/mcp"

        transport = StreamableHttpTransport(url=server_url)

        async with Client(transport, timeout=60) as client:

            # 1. Discover available tools and their parameters
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}")

            # 2. List all classes in the database
            result = await client.call_tool("list_classes", {})
            print(f"\nClasses:\n{json.dumps(result.structured_content, indent=2)}")

            # 3. Describe a specific class
            # Replace "Employee" with a class name from your database
            result = await client.call_tool(
                "describe_class", {"className": "Employee"}
            )
            print(f"\nEmployee class schema:\n{json.dumps(result.structured_content, indent=2)}")

            # 4. Execute a read-only JPQL query
            # Replace class and field names to match your schema
            result = await client.call_tool(
                "execute_query",
                {"jpql": "select e from Employee e"},
            )
            print(f"\nQuery results:\n{json.dumps(result.structured_content, indent=2)}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

## Connect with OAuth

When the server runs with OAuth enabled over HTTPS, the client needs both the
authentication flow and a TLS context.

!!! warning "Trust both certificate sources"
    If the MCP server uses a self-signed certificate, do **not** pass it as
    `ssl.create_default_context(cafile=…)`. That *replaces* the trust store, so requests to
    your identity provider — which uses a public certificate authority — then fail
    verification. Start from `certifi.where()` and add the self-signed certificate with
    `load_verify_locations()`, as both examples below do.

=== "SQL databases"

    ```python
    """Actian MCP Server — Python client with OAuth and TLS."""

    import asyncio
    import ssl
    import httpx
    import certifi
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport


    # Replace with your values
    MCP_URL = "https://mcp.example.com:8000/mcp"
    CA_CERT = "/path/to/server.crt"   # self-signed certificate of the MCP server


    def make_httpx_client(**kwargs) -> httpx.AsyncClient:
        """Trust both the identity provider and the MCP server certificate."""
        # Public certificate authorities, for the identity provider
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        # Plus the server's own certificate
        ssl_ctx.load_verify_locations(cafile=CA_CERT)
        return httpx.AsyncClient(verify=ssl_ctx, **kwargs)


    async def main():
        transport = StreamableHttpTransport(
            url=MCP_URL,
            auth="oauth",
            httpx_client_factory=make_httpx_client,
        )

        async with Client(transport, timeout=120) as client:
            tools = await client.list_tools()
            print(f"Connected — {len(tools)} tools available")

            # Verify the authenticated database user
            # For Zen, use {"sql": "..."} instead of {"query": "..."}
            result = await client.call_tool(
                "execute_query", {"query": "SELECT CURRENT_USER"}
            )
            print(f"Current user: {result.content[0].text}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

=== "Actian NoSQL"

    ```python
    """Actian MCP Server for Actian NoSQL — Python client with OAuth and TLS."""

    import asyncio
    import json
    import ssl
    import httpx
    import certifi
    from fastmcp import Client
    from fastmcp.client.auth import OAuth
    from fastmcp.client.transports import StreamableHttpTransport


    # Replace with your values
    MCP_URL = "https://mcp.example.com:8443/mcp"
    CLIENT_ID = "<your-client-id>"    # OAuth 2.0 client ID registered in your identity provider
    CALLBACK_PORT = 8765              # must match the redirect URI registered in your identity provider
    CA_CERT = "/path/to/server.crt"   # self-signed certificate of the MCP server


    def make_httpx_client(**kwargs) -> httpx.AsyncClient:
        """Trust both the identity provider and the MCP server certificate."""
        # Public certificate authorities, for the identity provider
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        # Plus the server's own certificate
        ssl_ctx.load_verify_locations(cafile=CA_CERT)
        return httpx.AsyncClient(verify=ssl_ctx, **kwargs)


    async def main():
        oauth = OAuth(
            client_id=CLIENT_ID,
            callback_port=CALLBACK_PORT,
            httpx_client_factory=make_httpx_client,
        )

        transport = StreamableHttpTransport(
            url=MCP_URL,
            auth=oauth,
            httpx_client_factory=make_httpx_client,
        )

        async with Client(transport, timeout=120) as client:
            tools = await client.list_tools()
            print(f"Connected — {len(tools)} tools available")

            result = await client.call_tool(
                "execute_query",
                {"jpql": "select e from Employee e"},
            )
            print(f"Results:\n{json.dumps(result.structured_content, indent=2)}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

!!! tip
    The FastMCP OAuth flow opens a browser window for login. Run the client on a machine
    that has a browser available.

## Next steps

<div class="grid cards" markdown>

- :material-connection: **[Connect an AI client](index.md)**  
  Configuration for Claude Desktop, Cursor, GitHub Copilot, Codex, and fast-agent.

- :material-shield-check: **[Secure the server](../authentication/index.md)**  
  Set up OAuth 2.0 with Keycloak or Auth0.

</div>
````

- [ ] **Step 3: Verify both code examples are valid Python**

The NoSQL original was not. Extract every Python block and compile it:

```bash
python3 - <<'PY'
import re, pathlib, ast, textwrap
src = pathlib.Path("docs/mcp-clients/python.md").read_text()
blocks = re.findall(r"```python\n(.*?)```", src, re.S)
print(f"{len(blocks)} Python blocks")
for i, b in enumerate(blocks, 1):
    try:
        ast.parse(textwrap.dedent(b))
        print(f"  block {i}: parses")
    except SyntaxError as e:
        print(f"  block {i}: SYNTAX ERROR line {e.lineno}: {e.msg}")
PY
```

Expected: `4 Python blocks` and `parses` on all four. A syntax error here means the
indentation inside a tab was mangled — tab content must be indented by exactly four
spaces relative to the `===` marker.

- [ ] **Step 4: Create the section's `.pages`**

`docs/mcp-clients/.pages`:

```yaml
title: Connect a Client
nav:
  - index.md
  - python.md
```

- [ ] **Step 5: Verify the tabs render and are linked**

```bash
python3 -m mkdocs build -q -d /tmp/phase5-t1
grep -c 'class="tabbed-set"' /tmp/phase5-t1/mcp-clients/python.html
grep -o 'data-tabs="[^"]*"' /tmp/phase5-t1/mcp-clients/python.html | head -4
grep -c 'content.tabs.link\|tabbed-labels' /tmp/phase5-t1/mcp-clients/python.html
```

Expected: `2` tabbed sets (connect, OAuth), `data-tabs` attributes present, and a non-zero
count for the labels. The `data-tabs` attribute is what `content.tabs.link` uses to
synchronise; if it is absent, Step 1 did not take effect.

- [ ] **Step 6: Verify the tab labels are exactly the two agreed strings**

Phase 6 depends on these matching character for character.

Match the label text itself rather than Material's markup, which has changed shape
between releases:

```bash
for label in "SQL databases" "Actian NoSQL"; do
  printf "  %-16s %s occurrences\n" "$label" \
    "$(grep -c "$label" /tmp/phase5-t1/mcp-clients/python.html)"
done
grep -oE '(SQL databases|Actian NoSQL|SQL Databases|Actian Nosql)' \
  /tmp/phase5-t1/mcp-clients/python.html | sort -u
```

Expected: a non-zero count for each, and the second command listing **only**
`Actian NoSQL` and `SQL databases` — no case variants. A variant means a typo that would
silently break tab synchronisation, since `content.tabs.link` matches on label text and
the build raises no error for it.

- [ ] **Step 7: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/mcp-clients/python.md docs/mcp-clients/.pages mkdocs.yml
git commit -m "docs: add a single Python client guide covering all five databases"
```

---

## Task 2: Remove the duplicates and break the redirect loop

**Files:**
- Modify: `docs/mcp-clients/index.md` (remove lines 126–272 and the NoSQL warning)
- Modify: `docs/nosql/index.md` (remove lines 107–243 and the client-guide note)

**Interfaces:**
- Consumes the anchors Task 1 produced. The removed sections are replaced by pointers to
  `python.md`, not deleted outright, because both pages are linked from elsewhere.

- [ ] **Step 1: Remove the Python section from the client page**

In `docs/mcp-clients/index.md`, delete everything from `## Connect Using Python Client`
(line 126) up to but **not** including `## Deployment Considerations` (line 273). That
removes the NoSQL warning admonition along with it, since the warning sits inside the
section.

In its place, put a pointer that names all five databases rather than warning one of them
away:

```markdown
## Connect from Python

To script against the server or build your own agent, use the FastMCP Python client. It
works with every Actian database. See [Connect a Python client](python.md).
```

- [ ] **Step 2: Remove the Python section from the NoSQL page**

In `docs/nosql/index.md`, delete everything from `## Connect Using a Python Client`
(line 107) up to but **not** including `## Next Steps` — capital S on this page, see the
next step. This removes the note pointing at
the client guide, which is the other half of the loop.

Nothing replaces it inline: the page's `## Next Steps` cards are where a reader continues,
and phase 2 already gave every setup page a `Connect a client` card there. Verify that is
true for NoSQL rather than assuming — the phase 2 card was added to the four SQL pages
only:

```bash
grep -c 'mcp-clients' docs/nosql/index.md
```

If this returns `0` after the deletion, add the card to the NoSQL page's `## Next Steps`
grid as its first entry, matching the wording the SQL pages use:

```markdown
- :material-connection: **[Connect a client](../mcp-clients/index.md)**  
  Point Claude Desktop, Cursor, GitHub Copilot, Codex, or fast-agent at the server
  endpoint.
```

- [ ] **Step 3: Align the NoSQL page's last heading**

`docs/nosql/index.md` writes `## Next Steps` while the four SQL setup pages and the new
`python.md` write `## Next steps`. Phase 2's structural alignment covered the SQL pages
only, so this one was left behind. Since this task is already editing the page, fix it:

```bash
sed -i.bak 's|^## Next Steps$|## Next steps|' docs/nosql/index.md
rm -f docs/nosql/index.md.bak
grep -n '^## Next' docs/nosql/index.md
```

Expected: `## Next steps`. This is the only structural difference being touched — the
NoSQL page is not template-aligned in general, because its configuration and startup
sections legitimately differ from the SQL template.

- [ ] **Step 4: Verify both halves of the loop are gone**

```bash
grep -rn 'NoSQL uses different tools' docs/; echo "(empty above = good)"
grep -rn 'For connecting AI clients' docs/; echo "(empty above = good)"
grep -rn 'nosql/index.md#connect-using-a-python-client' docs/; echo "(empty above = good)"
```

Expected: no output from any of the three.

- [ ] **Step 5: Verify no Python example survives outside the new page**

```bash
grep -rln 'StreamableHttpTransport' docs/
```

Expected: exactly `docs/mcp-clients/python.md`.

- [ ] **Step 6: Verify both source pages still build and shrank as expected**

```bash
wc -l docs/mcp-clients/index.md docs/nosql/index.md
python3 -m mkdocs build -q -d /tmp/phase5-t2
diff -rq -I 'git-revision-date-localized-plugin-date' \
  /tmp/phase5-baseline-site /tmp/phase5-t2 | sed 's|/tmp/phase5-[a-z0-9]*||g' | sort
```

Expected: `mcp-clients/index.md` down from 279 to roughly 137 lines and
`nosql/index.md` from 260 to roughly 125. The diff lists the two edited pages, the two new
files, `search/search_index.json`, and — because the nav gained a page — every page's HTML,
since Material renders the sidebar into each one. That last part is expected; it is why
this task does not try to bound the changed-file set.

- [ ] **Step 7: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/mcp-clients/index.md docs/nosql/index.md
git commit -m "docs: remove the duplicated Python guides and the redirect loop"
```

---

## Task 3: Put the navigation into the target order

**Files:**
- Modify: `docs/.pages`

**Interfaces:**
- Produces the top-level order the spec's §5 target structure specifies. Nothing consumes
  it, but the chooser table in `get-started/` lists the databases in the same order and
  the two must agree.

- [ ] **Step 1: Check the current order against the chooser**

The nav and the chooser table should list the databases identically, or the reader who
picks from the table finds a differently ordered sidebar.

```bash
grep -A14 '^nav:' docs/.pages
grep -oE '^\| (Actian|HCL) [^|]*' docs/get-started/index.md | sed 's/|//g'
```

Expected: the nav currently has `nosql` before `analytics-engine`, while the chooser lists
Ingres, HCL Informix®, Zen, Analytics Engine, NoSQL. They disagree today; Step 2 fixes it.

- [ ] **Step 2: Rewrite `docs/.pages`**

The five databases move up to sit directly after Get started, and the cross-cutting topics
move below them — because a reader consults those *after* their server runs. NoSQL goes
last among the databases, matching the chooser.

```yaml
title: Actian MCP Server
nav:
  - index.md
  - intro
  - get-started
  - ingres
  - hcl-informix
  - zen
  - analytics-engine
  - nosql
  - mcp-clients
  - authentication
  - write-support
  - extensions
```

- [ ] **Step 3: Verify the rendered order**

`.pages` is the source of truth, but confirm Material honoured it rather than falling back
to alphabetical:

```bash
python3 -m mkdocs build -q -d /tmp/phase5-t3
python3 - <<'PY'
import re, pathlib
h = pathlib.Path("/tmp/phase5-t3/index.html").read_text()
nav = re.search(r'<nav class="md-nav md-nav--primary".*?</nav>', h, re.S)
items = re.findall(r'md-nav__link[^>]*>\s*(?:<[^>]+>\s*)*([A-Z][^<\n]{2,40})', nav.group(0))
seen, order = set(), []
for i in items:
    i = i.strip()
    if i and i not in seen:
        seen.add(i); order.append(i)
print("\n".join(f"  {n}. {t}" for n, t in enumerate(order[:12], 1)))
PY
```

Expected, in this order: Home, Introduction, Get Started, Ingres, HCL Informix®, Zen,
Analytics Engine, NoSQL, Connect a Client, Authentication, Write Support, Extensions.

- [ ] **Step 4: Verify the nav and the chooser agree**

```bash
python3 - <<'PY'
import re, pathlib
pages = pathlib.Path("docs/.pages").read_text()
nav_db = [l.strip("  - ") for l in pages.split("\n")
          if l.strip("  - ") in ("ingres","hcl-informix","zen","analytics-engine","nosql")]
chooser = re.findall(r"\[Set up ([^\]]+)\]", pathlib.Path("docs/get-started/index.md").read_text())
slug = {"Ingres":"ingres","HCL Informix®":"hcl-informix","Zen":"zen",
        "Analytics Engine":"analytics-engine","NoSQL":"nosql"}
print("nav:     ", nav_db)
print("chooser: ", [slug[c] for c in chooser])
print("agree:   ", nav_db == [slug[c] for c in chooser])
PY
```

Expected: `agree: True`.

- [ ] **Step 5: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/.pages
git commit -m "docs: reorder the navigation around the reader's database"
```

---

## Task 4: Record the findings in the spec

**Files:**
- Modify: `specs/2026-08-05-docs-by-database-design.md`

- [ ] **Step 1: Add the fourth admonition to §1.1**

The table in §1.1 lists three admonitions. Add the one this phase found, so the record of
the problem is complete:

```markdown
| `docs/mcp-clients/index.md:128-129` | "Actian NoSQL uses different tools … For a NoSQL-specific Python client example, see [the NoSQL page]" — the other half of a mutual redirect with the row above |
```

- [ ] **Step 2: Record the two code fixes in §6**

Update the `nosql/index.md` row of the content mapping:

```markdown
| `nosql/index.md` | unchanged path | **Done (phase 5).** Its Python client section moved to `mcp-clients/python.md`, merged with the SQL copy that lived on `mcp-clients/index.md`. Two defects in those examples were fixed in the merge: the SQL one replaced the TLS trust store instead of adding to it, so identity-provider requests would fail; the NoSQL one contained `CALLBACK_PORT = <callback-port>`, which is a syntax error. |
```

- [ ] **Step 3: Add a §7.6 on the tab-label contract**

```markdown
### 7.6 Tab labels are a cross-page contract

`content.tabs.link` synchronises content tabs by their **label text**, across the whole
site and across page navigations. That is what makes the tabs a database switcher rather
than a per-block widget — and it means a typo in a label silently breaks the
synchronisation for that block, with no build error.

Two labels are established, first used in `docs/mcp-clients/python.md`:

- `SQL databases`
- `Actian NoSQL`

Any page that adds tabs must reuse these verbatim. Phase 6's authentication merge is the
next consumer.
```

- [ ] **Step 4: Commit**

```bash
git add specs/
git commit -m "docs: record the fourth admonition, the code fixes, and the tab contract"
```

---

## Phase 5 done — state afterwards

The navigation now reads as the driving question does: orientation, then *your* database
end to end, then everything you consult afterwards.

All four "this does not apply to you" admonitions are gone. The Python client is
documented once, for five databases, in one page whose tabs follow the reader.

Remaining: phase 6, the authentication merge — `docs/nosql/authentication/**` folds into
`docs/authentication/**` with tabs at the four diverging steps, removing the worst
duplication in the repository (Keycloak 463 + 202 lines, Auth0 425 + 190). It is the
riskiest step and deliberately last. It is also the first consumer of the tab labels this
phase established.

Still open on content: NoSQL write and extension detail for the two stubs (§11.7), Zen's
worked write example (§11.8), and Zen TLS support.
