# Phase 6: Bring NoSQL Authentication Into the Authentication Section — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal plan placed there would appear on docs.actian.com.

**Goal:** Make the Authentication section cover all five databases, so a reader
configuring OAuth is never sent out of it — and merge the parts that measurement shows
are genuinely shared.

**Architecture:** Merge the two *index* pages, using tabs where the configuration format
differs and sharing the certificate steps that NoSQL currently defers to the SQL guide
anyway. Do **not** merge the provider guides: measurement (below) shows Keycloak and
Auth0 for NoSQL are different procedures, not variants, so they move beside their SQL
counterparts as `authentication/keycloak/nosql.md` and `authentication/auth0/nosql.md`.
The SQL provider guides keep their paths; three redirects cover the NoSQL tree.

**Tech Stack:** MkDocs 1.6.1, mkdocs-material 9.6+ (`content.tabs.link`), mkdocs-redirects
1.2+, pymdown-extensions 10.21.2, GNU make

## Global Constraints

- Phases 1–5 are prerequisites and are complete as of commit `36532d6`.
- Verification after every task, all three must pass:
  ```bash
  python3 -m mkdocs build --strict     # no -q: it suppresses the warnings
  make check-templates
  python3 -m mkdocs build -q && make check-raw-md
  ```
- **Tab labels are fixed by §7.6 and must be reused verbatim:** `SQL databases` and
  `Actian NoSQL`. `content.tabs.link` matches on label text, so a typo breaks the
  switcher silently with no build error. This phase is the contract's second consumer.
- Verify rendered output by content, not by theme markup (spec §7.7). Parse the JSON,
  count the anchors, read the hrefs.
- Trust the build over the grep (spec §7.4), and check the **exit code**, not the output.
  Use `make check-build`. The `grep -E "WARNING|ERROR|Aborted"` pattern used through phases
  1–5 cannot see a plugin exception, and this phase proved it: deleting
  `docs/nosql/authentication/` while `docs/nosql/.pages` still listed it raised
  `NavEntryNotFound`, produced no site at all, and the gate reported success.
- **Deleting a directory and dropping its `.pages` entry must happen in the same task.**
  The original plan put the deletion in Task 2 and the nav fix in Task 3, so every
  verification step in Task 2 ran against a build that could not complete. Task 3's first
  two steps are folded into Task 2.
- `mkdocs-redirects` generates its redirect at the **source** path, so each moved file
  must be deleted, not left in place.
- Accepted limitation (spec §9.1): raw Markdown at the three old addresses will 404 after
  the move, while the `.html` redirects work. `copy_md_sources.py` walks `docs_dir`.

## Measured: the two trees are parallel, not duplicated

The spec's §6.1 said "Only realm creation, prerequisites, and end-to-end verification are
shared. With tabs at the four diverging steps the page grows to roughly 500 lines." Both
halves of that are wrong.

Comparing heading sets:

| Pair | Common | SQL only | NoSQL only |
|---|---|---|---|
| `index.md` | 4 | 9 | 2 |
| `keycloak/index.md` | 9 | 21 | 8 |
| `auth0/index.md` | 7 | 18 | 11 |

And the "common" headings are labels that coincide, not shared content. **The step
numbering diverges completely:**

| | SQL Keycloak | NoSQL Keycloak |
|---|---|---|
| Step 2 | Create a Keycloak Client | Create Keycloak **Clients** (two: authorization code + client credentials) |
| Step 3 | Add the Audience Mapper | Create Keycloak Users |
| Step 4 | Add the Sub Override Mapper | Configure and Start the Server |
| Step 5 | Add the Write Scope | — |
| Step 6 | Create Keycloak Users | — |
| Step 7 | Assemble the Final Configuration | — |

Auth0 diverges further — five steps against six, in a different order, and NoSQL has a
"Step 5: Enable Resource Parameter Compatibility" with no SQL counterpart.

Nor is the content identical where the headings match. Every candidate was checked:

```
keycloak  ## Quick Start                      different (14 vs 6 lines)
keycloak  ## Prerequisites                    different (9 vs 3 lines)
keycloak  ## Step 1: Create a Keycloak Realm  different (18 vs 18 lines)
keycloak  ## Staging versus Production        different (4 vs 4 lines)
auth0     ## Quick Start                      different (14 vs 9 lines)
auth0     ## Prerequisites                    different (3 vs 3 lines)
auth0     ## Staging versus Production        different (4 vs 4 lines)
```

Even realm creation, at an identical 18 lines, differs substantively: the realm is named
`actian-mcp` versus `actian-nosql-mcp`, and its *output* differs because the two servers
consume different keys — SQL needs `FASTMCP_SERVER_AUTH_CONFIG_URL` (the discovery URL),
NoSQL needs the issuer URL for `quarkus.oidc.auth-server-url`.

**Consequence: the maintenance burden the spec assumed does not exist.** Changing the SQL
Keycloak guide does not imply changing the NoSQL one, because they document different
flows against different configuration systems. This is not duplication; it is two
parallel guides. Merging them into one tabbed page would put two unrelated procedures
behind a switcher and make "Step 3" mean two different things.

### Design decision: merge the index, co-locate the providers

So this phase takes the spec's §6.1 fallback — with a better placement than the fallback
described. The real problem is not duplication but **placement**: NoSQL authentication
lives under `docs/nosql/`, so the Authentication section silently covers four of five
databases, and three pointers send NoSQL readers out of it.

- **The index pages do merge**, because they genuinely overlap (see the TLS finding below).
- **The provider guides co-locate**, becoming `authentication/keycloak/nosql.md` and
  `authentication/auth0/nosql.md`, matching the pattern `write-support/` and `extensions/`
  already follow. Their content is untouched apart from link rewrites.

## Three more admonitions, and a second mutual redirect

`docs/authentication/index.md` carries three pointers out of the section:

| Line | Pointer |
|---|---|
| 12 | "**Actian NoSQL users**: NoSQL uses a direct OAuth 2.0 flow with different configuration properties. See [NoSQL Authentication Guide]" |
| 98 | "**NoSQL**: Uses a direct OAuth 2.0 flow, a different authentication model. The `user_impersonation` field does not apply. See [NoSQL Authentication Guide]" |
| 153–154 | "**TLS configuration for NoSQL**: … uses different configuration properties. See [NoSQL TLS guide]" |

And `docs/nosql/authentication/index.md:102` points back: "For instructions on generating
a self-signed certificate and trusting it in the MCP client, see [Secure Remote
Deployments with HTTPS and TLS] in the main Authentication guide."

That is the second mutual redirect this restructure has found, after the client-guide one
in phase 5. It brings the running total of "this does not apply to you" pointers from four
to **seven**. Line 98 is at least accurate — it already states that `user_impersonation`
does not apply to NoSQL, which matches the §11.3 answer.

### The reverse pointer marks genuinely shared content

`nosql/authentication/index.md:102` defers certificate generation *and* client trust to
the SQL guide. So those two steps are shared in fact, and the merge can make that
structural instead of a cross-reference:

| TLS step | Shared? |
|---|---|
| Step 1: Generate a certificate (`openssl req -x509 …`) | **shared** |
| Step 2: Configure TLS | differs — `ssl_certfile`/`ssl_keyfile` in `conf.json` versus `quarkus.tls.key-store.pem.0.cert`/`.key` in `application.properties` |
| Step 3: Deploy the container | differs — mounts and ports (`8000` versus `8080` plus `8443`) |
| Step 4: Trust the certificate in the MCP client | **shared** |

Two of four steps shared, two tabbed. That is the honest use of tabs in this phase, and it
removes the reverse pointer by construction.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `docs/authentication/index.md` | Merged: shared concepts, tabbed config blocks, TLS with two shared and two tabbed steps | 1 |
| `docs/authentication/keycloak/nosql.md` | Moved from `docs/nosql/authentication/keycloak/index.md` | 2 |
| `docs/authentication/auth0/nosql.md` | Moved from `docs/nosql/authentication/auth0/index.md` | 2 |
| `docs/authentication/keycloak/.pages` | New — orders `index.md` before `nosql.md` | 2 |
| `docs/authentication/auth0/.pages` | New — same | 2 |
| `docs/nosql/authentication/**` | Deleted (6 files including `.pages`) | 2 |
| `mkdocs.yml` | Three more `redirect_maps` entries | 2 |
| `docs/nosql/.pages` | Loses `authentication` | 3 |
| `docs/nosql/index.md` | Two links to the moved section | 3 |
| `specs/2026-08-05-docs-by-database-design.md` | Records the measurement that overturned §6.1 | 4 |

---

## Task 0: Capture the baseline

**Files:** none

- [ ] **Step 1: Confirm phase 5 is in place and the tree is clean**

```bash
git status --short
ls docs/mcp-clients/python.md
grep -c 'content.tabs.link' mkdocs.yml
```

Expected: `git status` shows nothing except possibly `theme_overrides/.DS_Store`, a macOS
Finder artefact that is not part of this work — leave it. The file listed, and `1` from the
grep.

- [ ] **Step 2: Build the baseline**

```bash
python3 -m mkdocs build -q -d /tmp/phase6-baseline-site
```

- [ ] **Step 3: Record the six files and their sizes**

So Task 2 can prove nothing was lost in the move.

```bash
wc -l docs/authentication/index.md docs/authentication/keycloak/index.md \
  docs/authentication/auth0/index.md docs/nosql/authentication/index.md \
  docs/nosql/authentication/keycloak/index.md docs/nosql/authentication/auth0/index.md
```

Expected: `280`, `463`, `425`, `136`, `202`, `190` — `1696` total.

- [ ] **Step 4: Record the seven pointers this phase removes**

```bash
grep -c 'NoSQL Authentication Guide' docs/authentication/index.md
grep -c 'NoSQL TLS guide' docs/authentication/index.md
grep -c 'in the main Authentication guide' docs/nosql/authentication/index.md
```

Expected: `2`, `1`, `1` — the four pointers in the authentication trees. The other three
were removed in phases 2 and 4.

---

## Task 1: Merge the two index pages

**Files:**
- Modify: `docs/authentication/index.md`

**Interfaces:**
- Produces the anchors the moved provider guides link to:
  `#secure-remote-deployments-with-https-and-tls` and `#configuring-oauth-block`. Both must
  survive — Task 2's pages depend on the first, and phase 1 fixed six inbound links to the
  second.
- Establishes the tab labels `SQL databases` and `Actian NoSQL` on this page, per §7.6.

- [ ] **Step 1: Create the section-extraction helper**

Content tabs require their body indented by four spaces, and this task moves roughly 250
lines into tabs. Hand-indenting that is where mistakes happen, so use a tool. Blank lines
must stay empty rather than becoming four spaces of trailing whitespace, which this
handles.

```bash
cat > /tmp/tabify.py <<'PY'
"""Print a Markdown section's body, optionally indented for a content tab."""
import sys, pathlib
path, heading, indent = sys.argv[1], sys.argv[2], int(sys.argv[3])
lines = pathlib.Path(path).read_text().split("\n")
s = next(i for i, l in enumerate(lines) if l.strip() == heading)
lvl = len(heading) - len(heading.lstrip("#"))
e = next((i for i in range(s + 1, len(lines))
          if lines[i].startswith("#")
          and len(lines[i]) - len(lines[i].lstrip("#")) <= lvl), len(lines))
for l in lines[s + 1:e]:
    print((" " * indent + l) if l.strip() else "")
PY
python3 /tmp/tabify.py docs/nosql/authentication/index.md '### Configuration' 4 | head -5
```

Expected: the first lines of NoSQL's OAuth configuration, each indented four spaces.

- [ ] **Step 2: Replace the intro pointer with a statement of fact**

Line 12 reads, inside a list:

```markdown
    - **Actian NoSQL users**:  NoSQL uses a direct OAuth 2.0 flow with different configuration properties. See [NoSQL Authentication Guide](../nosql/authentication/index.md) for more information.
```

Replace it with:

```markdown
    - **Actian NoSQL**: uses a direct OAuth 2.0 flow with different configuration properties. Both are covered below — select your database in the tabs.
```

- [ ] **Step 3: Tab the OAuth configuration block**

**Do not retitle this section.** The heading must stay exactly `` ## Configuring `oauth` Block ``,
because phase 1 repaired six inbound links to its anchor `#configuring-oauth-block`.
Retitling would break all six, and `--strict` would fail in Step 8. The heading is a
published contract; better wording is not worth it.

Keep the heading and its opening sentence, then put both configuration formats under tabs.
Generate the two bodies:

```bash
python3 /tmp/tabify.py docs/authentication/index.md '## Configuring `oauth` Block' 4 > /tmp/tab-sql-oauth.md
python3 /tmp/tabify.py docs/nosql/authentication/index.md '### Configuration' 4 > /tmp/tab-nosql-oauth.md
wc -l /tmp/tab-sql-oauth.md /tmp/tab-nosql-oauth.md
```

Then rewrite the section as:

```markdown
## Configuring `oauth` Block

The SQL engines take an `oauth` block in `conf.json`. Actian NoSQL takes individual
Quarkus properties in `application.properties` instead.

=== "SQL databases"

<contents of /tmp/tab-sql-oauth.md>

=== "Actian NoSQL"

<contents of /tmp/tab-nosql-oauth.md>
```

Also append NoSQL's `### Example` body — `python3 /tmp/tabify.py docs/nosql/authentication/index.md '### Example' 4` — inside the `Actian NoSQL` tab, after the property table, since that page keeps its example in a separate subsection.

- [ ] **Step 4: Tab user impersonation**

`## User Impersonation` is SQL-only, and line 98 says so by pointing away. §11.3 established
that NoSQL does not support it, so state that in a tab instead of redirecting.

```bash
python3 /tmp/tabify.py docs/authentication/index.md '## User Impersonation' 4 > /tmp/tab-sql-imp.md
wc -l /tmp/tab-sql-imp.md
```

The section becomes:

```markdown
## User Impersonation

=== "SQL databases"

<contents of /tmp/tab-sql-imp.md>

=== "Actian NoSQL"

    Actian NoSQL does not support user impersonation. The `user_impersonation` field does
    not apply, and statements run as the database user configured in
    `application.properties`.
```

That NoSQL tab states only what §11.3 established plus what the NoSQL configuration already
documents. Do not describe an impersonation mechanism for NoSQL — there is none.

Note the nested `### Extracting Username` inside the SQL content: it becomes a level-3
heading inside a tab, which Material renders but which does **not** get a table-of-contents
entry. That is acceptable; nothing links to it. Confirm with
`grep -c 'extracting-username' docs/` before and after if you want certainty.

- [ ] **Step 5: Restructure the TLS section into two shared and two tabbed steps**

This is the substantive merge. Generate the four bodies:

```bash
python3 /tmp/tabify.py docs/authentication/index.md '### Step 1: Generate a Certificate' 0 > /tmp/tls-1-shared.md
python3 /tmp/tabify.py docs/authentication/index.md '### Step 2: Configure TLS in `conf.json`' 4 > /tmp/tls-2-sql.md
python3 /tmp/tabify.py docs/authentication/index.md '### Step 3: Deploy the Docker' 4 > /tmp/tls-3-sql.md
python3 /tmp/tabify.py docs/authentication/index.md '### Step 4: Trust the Certificate in the MCP Client' 0 > /tmp/tls-4-shared.md
python3 /tmp/tabify.py docs/nosql/authentication/index.md '## Secure Remote Deployments with HTTPS and TLS' 4 > /tmp/tls-nosql-all.md
wc -l /tmp/tls-*.md
```

`/tmp/tls-nosql-all.md` holds NoSQL's whole TLS section: the property table, the Quarkus TLS
Registry note, and the `### Example` with its `application.properties` block and its
`docker run`. Split it by hand into the configure part (properties) and the deploy part
(`docker run`), and **drop its "Generating and trusting a self-signed certificate" note** —
that note is the cross-reference this merge eliminates, since steps 1 and 4 are now shared.

The section becomes:

````markdown
## Secure Remote Deployments with HTTPS and TLS

OAuth 2.0 requires HTTPS. If you configure OAuth, the server mandates HTTPS and refuses to
start unless you provide a certificate and a private key.

### Step 1: Generate a Certificate

<contents of /tmp/tls-1-shared.md — unchanged, now shared by both databases>

### Step 2: Configure TLS

=== "SQL databases"

<contents of /tmp/tls-2-sql.md>

=== "Actian NoSQL"

<the property table and Quarkus note from /tmp/tls-nosql-all.md, plus its
 application.properties block>

### Step 3: Deploy the Container

=== "SQL databases"

<contents of /tmp/tls-3-sql.md>

=== "Actian NoSQL"

<the docker run block from /tmp/tls-nosql-all.md — mounts application.properties and the
 certs directory, exposes ports 8080 and 8443>

### Step 4: Trust the Certificate in the MCP Client

<contents of /tmp/tls-4-shared.md — unchanged, now shared by both databases>
````

Two headings become database-neutral: `` ### Step 2: Configure TLS in `conf.json` `` becomes
`### Step 2: Configure TLS`, and `### Step 3: Deploy the Docker` becomes
`### Step 3: Deploy the Container`. Those two anchors change; Step 8 checks for inbound
links to them.

- [ ] **Step 6: Remove the TLS pointer**

Lines 153–154 are now redundant — the NoSQL configuration sits in the tab above:

```markdown
!!! note "TLS configuration for NoSQL"
    The Actian MCP Server for NoSQL uses different configuration properties. See [NoSQL TLS guide](../nosql/authentication/index.md#secure-remote-deployments-with-https-and-tls) for more information.
```

Delete both lines.

- [ ] **Step 7: Leave Provider Setup Guides alone for now**

It links the two SQL guides. Task 2 creates the two NoSQL ones; linking them before they
exist fails `--strict`. Task 2 Step 6 extends this section.

- [ ] **Step 8: Verify the anchors other pages depend on**

```bash
python3 -m mkdocs build -q -d /tmp/phase6-t1
for a in configuring-oauth-block secure-remote-deployments-with-https-and-tls user-impersonation; do
  printf "  %-48s %s\n" "$a" "$(grep -c "id=\"$a\"" /tmp/phase6-t1/authentication/index.html)"
done
grep -rn -e 'configure-tls-in-confjson' -e 'deploy-the-docker' docs/; echo "(empty above = good)"
```

Expected: `1` for each of the three anchors, and no inbound link to the two renamed step
anchors. A `0` on `configuring-oauth-block` means Step 3's warning was ignored and six links
are broken — `--strict` in Step 11 would catch it too.

- [ ] **Step 9: Verify the tabs render with the contracted labels**

```bash
grep -c 'querySelectorAll(".tabbed-set")' /tmp/phase6-t1/authentication/index.html
grep -o 'data-tabs="[^"]*"' /tmp/phase6-t1/authentication/index.html
grep -oE '(SQL databases|Actian NoSQL|SQL Databases|Actian Nosql)' \
  /tmp/phase6-t1/authentication/index.html | sort -u
```

Expected: `1` for the synchronisation script; four `data-tabs` attributes, each ending `:2`
(OAuth block, user impersonation, TLS step 2, TLS step 3); and the last command listing
**only** `Actian NoSQL` and `SQL databases`. A case variant silently breaks the switcher.

- [ ] **Step 10: Verify no NoSQL content was dropped**

Every distinctive NoSQL string from the source page must now be on the merged page.

```bash
python3 - <<'PY'
import pathlib
merged = pathlib.Path("docs/authentication/index.md").read_text()
markers = ["quarkus.tls.key-store.pem.0.cert", "quarkus.tls.key-store.pem.0.key",
           "quarkus.http.insecure-requests", "application.properties",
           "8443", "Quarkus TLS Registry", "insecure-requests"]
for m in markers:
    print(f"  {m:38} {'present' if m in merged else 'MISSING'}")
PY
```

Expected: `present` on every line. Anything missing was left behind in the source page,
which Task 2 deletes — so fix it here.

- [ ] **Step 11: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/authentication/index.md
git commit -m "docs: merge NoSQL authentication into the authentication index"
```

---

## Task 2: Co-locate the two provider guides

**Files:**
- Create: `docs/authentication/keycloak/nosql.md` (moved)
- Create: `docs/authentication/auth0/nosql.md` (moved)
- Create: `docs/authentication/keycloak/.pages`
- Create: `docs/authentication/auth0/.pages`
- Delete: `docs/nosql/authentication/index.md`, `docs/nosql/authentication/.pages`, and the
  two provider directories
- Modify: `docs/authentication/index.md` (Provider Setup Guides)
- Modify: `mkdocs.yml` (`redirect_maps`)

**Interfaces:**
- Consumes `docs/authentication/index.md#secure-remote-deployments-with-https-and-tls`,
  which both moved pages link to.
- Produces `docs/authentication/keycloak/nosql.md` and `docs/authentication/auth0/nosql.md`
  with frontmatter `title: Actian NoSQL`, matching the pattern `write-support/nosql.md` and
  `extensions/nosql.md` already use.

- [ ] **Step 1: Move both provider guides with git, so history follows**

```bash
git mv docs/nosql/authentication/keycloak/index.md docs/authentication/keycloak/nosql.md
git mv docs/nosql/authentication/auth0/index.md docs/authentication/auth0/nosql.md
```

- [ ] **Step 2: Set the nav titles**

Both moved files have `title: Keycloak Setup Guide` and `title: Auth0 Setup Guide`, which
would collide with their SQL siblings in the sidebar. Change each to:

```yaml
title: Actian NoSQL
```

- [ ] **Step 3: Rewrite the outbound links in both moved pages**

Each page moved from depth 3 (`docs/nosql/authentication/<provider>/`) to depth 2
(`docs/authentication/<provider>/`), so every relative link needs one level fewer — except
one, which needs care.

| Target | Was (depth 3) | Now (depth 2) |
|---|---|---|
| `docs/nosql/index.md#start-the-server` | `../../index.md#start-the-server` | `../../nosql/index.md#start-the-server` |
| `docs/mcp-clients/index.md` | `../../../mcp-clients/index.md` | `../../mcp-clients/index.md` |
| The TLS section | `../index.md#secure-remote-…` | `../index.md#secure-remote-…` — **unchanged text, different target** |

The third row is the trap: `../index.md` used to mean
`docs/nosql/authentication/index.md` and now means `docs/authentication/index.md`. The
string does not change, but its meaning does — and the new target is the correct one,
because Task 1 merged that content in. Do not "fix" it.

```bash
for f in docs/authentication/keycloak/nosql.md docs/authentication/auth0/nosql.md; do
  sed -i.bak \
    -e 's|\.\./\.\./index\.md#start-the-server|../../nosql/index.md#start-the-server|g' \
    -e 's|\.\./\.\./\.\./mcp-clients/index\.md|../../mcp-clients/index.md|g' "$f"
done
find docs -name '*.bak' -delete
```

- [ ] **Step 4: Verify every link in both moved pages resolves**

```bash
grep -on '](\.\.[^)]*' docs/authentication/keycloak/nosql.md docs/authentication/auth0/nosql.md
```

Expected: only `../../nosql/index.md#start-the-server`, `../../mcp-clients/index.md`, and
`../index.md#secure-remote-deployments-with-https-and-tls`. No `../../../` anywhere — that
would be a leftover from the old depth. `--strict` in Step 9 is the real check.

- [ ] **Step 5: Create the two `.pages` files**

`docs/authentication/keycloak/.pages`:

```yaml
title: Keycloak
nav:
  - index.md
  - nosql.md
```

`docs/authentication/auth0/.pages`:

```yaml
title: Auth0
nav:
  - index.md
  - nosql.md
```

- [ ] **Step 6: Extend Provider Setup Guides to four entries**

Now that the NoSQL pages exist, update `## Provider Setup Guides` in
`docs/authentication/index.md` to list all four, grouped so the pairing is obvious:

```markdown
## Provider Setup Guides

| Provider | SQL databases | Actian NoSQL |
|----------|---------------|--------------|
| Keycloak | [Keycloak setup](keycloak/index.md) | [Keycloak for NoSQL](keycloak/nosql.md) |
| Auth0 | [Auth0 setup](auth0/index.md) | [Auth0 for NoSQL](auth0/nosql.md) |

The NoSQL guides are separate rather than tabbed because they document different
procedures, not variants of one — different step sequences, different client setups, and a
different configuration system.
```

- [ ] **Step 7: Delete what remains of the NoSQL authentication tree**

Only `index.md` and the `.pages` files are left; their content moved into
`docs/authentication/index.md` in Task 1.

```bash
git rm docs/nosql/authentication/index.md docs/nosql/authentication/.pages \
  docs/nosql/authentication/keycloak/.pages docs/nosql/authentication/auth0/.pages
find docs/nosql/authentication -type d -empty -delete
ls docs/nosql/ 2>&1
```

Expected: `docs/nosql/` no longer contains `authentication`.

- [ ] **Step 8: Add the three redirects**

In `mkdocs.yml`, extend `redirect_maps` — it currently holds the one entry from phase 4:

```yaml
  - redirects:
      redirect_maps:
        'intro/write-support.md': 'write-support/index.md'
        'nosql/authentication/index.md': 'authentication/index.md'
        'nosql/authentication/keycloak/index.md': 'authentication/keycloak/nosql.md'
        'nosql/authentication/auth0/index.md': 'authentication/auth0/nosql.md'
```

- [ ] **Step 9: Verify the redirects and run the gates**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
python3 -m mkdocs build -q -d /tmp/phase6-t2
for p in nosql/authentication/index nosql/authentication/keycloak/index nosql/authentication/auth0/index; do
  printf "  %-44s %s\n" "$p" "$(grep -o 'url=[^"]*' /tmp/phase6-t2/$p.html)"
done
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: no build warnings, and each redirect pointing at its new target.

- [ ] **Step 10: Verify nothing was lost**

The four moved/merged files totalled 528 lines. Confirm the content landed:

```bash
wc -l docs/authentication/index.md docs/authentication/keycloak/nosql.md \
  docs/authentication/auth0/nosql.md
grep -c 'Client Credentials Flow' docs/authentication/keycloak/nosql.md
grep -c 'Resource Parameter Compatibility' docs/authentication/auth0/nosql.md
```

Expected: the index grown from 280 to roughly 380, the two provider pages at roughly 202
and 190, and `1` from each grep — those are the NoSQL-only sections that prove the
distinctive content survived.

- [ ] **Step 11: Commit**

```bash
git add -A docs/ mkdocs.yml
git commit -m "docs: co-locate the NoSQL provider guides in the authentication section"
```

---

## Task 3: Fix the navigation and the remaining links

**Files:**
- Modify: `docs/nosql/.pages`
- Modify: `docs/nosql/index.md`

- [ ] **Step 1: Remove `authentication` from the NoSQL nav**

`docs/nosql/.pages` becomes:

```yaml
title: NoSQL
nav:
  - index.md
  - tools
  - resources
  - prompts
```

- [ ] **Step 2: Fix the two links on the NoSQL setup page**

Both point into the removed subtree, relative to `docs/nosql/`:

- line 52, inside a note: `[Authentication](authentication/index.md)`
- line 115, a Next steps card: `[Authentication](authentication/index.md)`

Both become `../authentication/index.md`:

```bash
sed -i.bak 's|](authentication/index\.md)|](../authentication/index.md)|g' docs/nosql/index.md
rm -f docs/nosql/index.md.bak
grep -n 'authentication/index.md' docs/nosql/index.md
```

Expected: two lines, both `../authentication/index.md`.

- [ ] **Step 3: Verify the section now covers five databases**

```bash
python3 -m mkdocs build -q -d /tmp/phase6-t3
python3 - <<'PY'
import re, pathlib
h = pathlib.Path("/tmp/phase6-t3/authentication/index.html").read_text()
for target in ["keycloak/index.html", "keycloak/nosql.html", "auth0/index.html", "auth0/nosql.html"]:
    print(f"  {target:26} {'linked' if target in h else 'MISSING'}")
PY
```

Expected: `linked` on all four.

- [ ] **Step 4: Verify no pointer out of the section survives**

```bash
grep -rn -e 'NoSQL Authentication Guide' -e 'NoSQL TLS guide' \
  -e 'in the main Authentication guide' docs/; echo "(empty above = good)"
grep -rn 'nosql/authentication' docs/; echo "(empty above = good)"
```

Expected: no output from either. The second confirms no link still targets the old tree.

- [ ] **Step 5: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/nosql/.pages docs/nosql/index.md
git commit -m "docs: point the NoSQL page at the merged authentication section"
```

- [ ] **Step 6: Follow the NoSQL path end to end**

The automated checks cannot judge whether the section reads as one guide. Serve the site
and walk it:

```bash
python3 -m mkdocs serve -a 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/get-started/index.html`, pick NoSQL, set it up, then go to
Authentication and configure Keycloak. The test: does the NoSQL reader stay inside the
Authentication section, and does the tab selection they made on the index page still show
NoSQL when they land on other tabbed pages? That second part is what `content.tabs.link`
buys, and it only shows up in a browser.

---

## Task 4: Record the measurement that overturned §6.1

**Files:**
- Modify: `specs/2026-08-05-docs-by-database-design.md`

- [ ] **Step 1: Replace §6.1 with what was measured**

§6.1 currently predicts a tabbed ~500-line page and offers a fallback. Replace its body
with the finding and the decision taken:

```markdown
### 6.1 Measured: the authentication trees are parallel, not duplicated

An earlier draft of this section said "Only realm creation, prerequisites, and end-to-end
verification are shared. With tabs at the four diverging steps the page grows to roughly
500 lines." Measurement in phase 6 disproved both halves.

Heading-set overlap: `index.md` 4 common against 9 SQL-only and 2 NoSQL-only;
`keycloak/index.md` 9 against 21 and 8; `auth0/index.md` 7 against 18 and 11. And the
common headings are labels that coincide, not shared content — every candidate section
differed when compared, including `## Step 1: Create a Keycloak Realm`, which is 18 lines
on both sides but names a different realm and produces a different output value, because
the two servers consume different configuration keys.

The step *numbering* diverges outright: SQL Keycloak runs seven steps, NoSQL four, and
"Step 3" means "Add the Audience Mapper" on one and "Create Keycloak Users" on the other.
Auth0 diverges further, with a NoSQL-only "Enable Resource Parameter Compatibility".

So the maintenance burden this section assumed does not exist: changing the SQL guide does
not imply changing the NoSQL one. These are two parallel guides for two implementations,
not two copies. Tabbing them would put unrelated procedures behind one switcher.

**Decision taken in phase 6:** merge the index pages, which do overlap, and co-locate the
provider guides as `authentication/keycloak/nosql.md` and `authentication/auth0/nosql.md`
— the pattern `write-support/` and `extensions/` already follow. The real problem was
placement, not duplication: NoSQL authentication lived under `docs/nosql/`, so the
Authentication section silently covered four of five databases while three pointers sent
NoSQL readers out of it.

The index merge is real, not cosmetic. `nosql/authentication/index.md:102` deferred
certificate generation *and* client trust to the SQL guide, so TLS steps 1 and 4 were
shared in fact; the merge makes that structural and removes the cross-reference. Steps 2
and 3 — configuring TLS and deploying — are tabbed, because `ssl_certfile`/`ssl_keyfile` in
`conf.json` and `quarkus.tls.key-store.pem.0.*` in `application.properties` are genuinely
different.
```

- [ ] **Step 2: Add the last three admonitions to §1.1**

The table lists five after phase 5. Add the three found here, so the record of the original
problem is complete:

```markdown
| `docs/authentication/index.md:12` | "**Actian NoSQL users**: NoSQL uses a direct OAuth 2.0 flow … See [NoSQL Authentication Guide]" |
| `docs/authentication/index.md:98` | "**NoSQL**: Uses a direct OAuth 2.0 flow … See [NoSQL Authentication Guide]" |
| `docs/authentication/index.md:153-154` | "**TLS configuration for NoSQL** … See [NoSQL TLS guide]" — the other half of a mutual redirect with `docs/nosql/authentication/index.md:102` |
```

Then note the total: seven pointers out of a section, all removed across phases 2, 4, 5
and 6.

- [ ] **Step 3: Update §9.1's redirect map to the final four**

```yaml
  - redirects:
      redirect_maps:
        'intro/write-support.md': 'write-support/index.md'
        'nosql/authentication/index.md': 'authentication/index.md'
        'nosql/authentication/keycloak/index.md': 'authentication/keycloak/nosql.md'
        'nosql/authentication/auth0/index.md': 'authentication/auth0/nosql.md'
```

- [ ] **Step 4: Mark the phase table complete and update the status**

In §10, mark phase 6 done. Change the document status line to:

```markdown
- **Status:** All six phases implemented. Open items are content, tracked in §11.
```

- [ ] **Step 5: Commit**

```bash
git add specs/
git commit -m "docs: record the phase 6 measurement and mark the restructure complete"
```

---

## Phase 6 done — the restructure is complete

| Section | SQL | NoSQL |
|---|---|---|
| Authentication | `authentication/index.md` + `keycloak/index.md` + `auth0/index.md` | same index, tabbed + `keycloak/nosql.md` + `auth0/nosql.md` |
| Write support | `write-support/index.md` | `write-support/nosql.md` — stub |
| Extensions | `extensions/index.md` | `extensions/nosql.md` — stub |
| Connect a client | `mcp-clients/index.md` + `python.md` | same pages, tabbed |

Every cross-cutting section now covers all five databases. All seven "this does not apply
to you" pointers are gone. Four redirects cover every moved page.

Still open, all content rather than structure: NoSQL write and extension detail for the two
stubs (§11.7), Zen's worked write example (§11.8), and whether Zen supports
`ssl_certfile`/`ssl_keyfile`, which holds `conf/tls-fields.md` at three consumers.
