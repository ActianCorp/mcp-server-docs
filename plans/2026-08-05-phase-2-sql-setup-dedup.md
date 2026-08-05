# Phase 2: Deduplicate the SQL Setup Pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal plan placed there would appear on docs.actian.com.

**Goal:** Turn the four SQL setup pages into structurally identical pages that share
every block which is provably identical, and turn `get-started/` into a
database-agnostic chooser so NoSQL stops being an exception other pages warn about.

**Architecture:** Extract the genuinely repeated blocks into `includes/` (created in
phase 1) and reference them from all four SQL setup pages. Align the four pages to
`templates/setup-sql-database.md.tmpl` so future edits stay diffable. Rewrite
`get-started/` as orientation plus a "which database do you have?" table, moving its
per-engine walkthrough content onto the per-engine pages where it belongs.

**Tech Stack:** MkDocs 1.6.1, mkdocs-material 9.6+, pymdown-extensions 10.21.2
(`pymdownx.snippets`), GNU make

## Global Constraints

- Phase 1 is a prerequisite and is complete as of commit `8be62b8`. `pymdownx.snippets`
  is enabled with `base_path: ['includes']` and `check_paths: true`; the raw-Markdown
  hook resolves includes; `make check-templates` and `make check-raw-md` exist;
  `mkdocs build --strict` fails on broken links and anchors.
- **This phase changes rendered output.** Unlike phase 1 there is no byte-identical
  gate. The criterion is *materially equivalent content, harmonized wording*: no fact
  may be added, removed, or altered except the corrections listed explicitly below.
- Verification after every task, all three must pass:
  ```bash
  python3 -m mkdocs build --strict     # no -q: it suppresses the warnings
  make check-templates
  python3 -m mkdocs build -q && make check-raw-md
  ```
- `pymdownx.snippets` has **no variable substitution.** A shared block cannot contain a
  per-engine value. This is why the `docker run` command is *not* an include: it
  contains the image name. Consistency there comes from the template and review, not
  from single-sourcing.
- Include paths are relative to `includes/`. Relative Markdown links *inside* an
  include resolve from the **including page's** location, because snippets inline the
  text before MkDocs rewrites links. Every include in this phase is consumed only by
  pages at depth 1 (`docs/<db>/index.md`), so `../authentication/index.md` is correct
  in all of them. **Do not** consume these includes from a page at another depth
  without re-checking every link.
- A row-fragment include (one that continues a Markdown table started by the page)
  must not begin or end with a blank line, or the table breaks in two.
- Informix image, resolved 2026-08-05: `actian/informix-mcp-server` from Docker Hub.
  The `docker load -i ifx_mcp_image.tar` step and the name
  `actian/informix-mcp-server-linux:1.0.0` are both wrong and get dropped.
- Verified facts this plan relies on (measured, do not re-derive):
  - `extensions` is worded **verbatim identically** on all four SQL pages.
  - `log_level` and `oauth` differ only in phrasing, not in content, on all four.
  - `ssl_certfile` / `ssl_keyfile` are present on Ingres, Informix and Analytics
    Engine, and **absent on Zen**.
  - `query_mode` / `write_confirmation` are present on Ingres and Analytics Engine
    only, and worded identically between those two.
  - Zen's `docker run` needs `--add-host=host.docker.internal:host-gateway`; the other
    three do not.

## Deferred: what this phase deliberately does not do

Four facts are unverified. Asserting them would put wrong statements on a customer
site, so the affected rows stay written out per page and move into a shared include
in a later phase, once answered. Each is tracked in §11 of the spec.

| Unverified | Consequence for this phase | Unblocks |
|---|---|---|
| Is `max_rows` `1000` a **hard cap** (as Ingres says) or a **default** (as the other three say)? | `max_rows` stays a per-page row; wording is **not** harmonized | Moving `max_rows` into `conf/common-optional-fields.md` |
| Does Zen support `ssl_certfile` / `ssl_keyfile`? | `conf/tls-fields.md` is consumed by three pages, not four | A fourth consumer |
| Do Informix and Zen use the same write semantics (spec §11.1)? | `conf/write-fields.md` is consumed by two pages, not four | Two more consumers |
| Which image tag is current — pages pin `:1.0.0` / `:latest` while the site banner announces 1.1 (spec §11.5)? | Existing tags are left exactly as they are | A single harmonized tag |

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `includes/conf/common-optional-fields.md` | The three optional `conf.json` rows common to all four SQL engines | 1 |
| `includes/conf/tls-fields.md` | The two TLS rows, for the three engines that document them | 1 |
| `includes/conf/write-fields.md` | The two write-mode rows, for the two engines that document them | 1 |
| `includes/docker/mount-path-note.md` | "Do not change the mount target path" admonition | 2 |
| `includes/verify-connection.md` | The three verification steps, currently only on `get-started/` | 3 |
| `docs/ingres/index.md` | Setup page, reference engine — matches the template most closely today | 1, 2, 3, 4 |
| `docs/analytics-engine/index.md` | Setup page | 1, 2, 3, 4 |
| `docs/hcl-informix/index.md` | Setup page; also loses the tarball instructions | 1, 2, 3, 4 |
| `docs/zen/index.md` | Setup page; keeps its networking note and `--add-host` | 1, 2, 3, 4 |
| `docs/get-started/index.md` | Becomes orientation + database chooser | 5 |

### Deviation from the spec's include inventory

The spec (§7.1) listed `get-started/` as a consumer of `conf/common-fields.md` and
`docker/run-sql.md`. It is not, in this plan. A chooser page should not carry a
configuration reference — that is exactly the duplication being removed. `get-started/`
ends up consuming no includes at all, which also removes the depth-of-relative-links
concern for every fragment in this phase.

The spec also listed a single `conf/common-fields.md` covering eight fields as "already
verbatim identical 4×". Measurement disproved that: only three rows are common to all
four engines. Hence three separate includes, each with exactly the consumer set the
evidence supports.

---

## Task 0: Capture the baseline

**Files:** none

**Interfaces:**
- Produces: `/tmp/phase2-baseline-site`, the rendered site before any phase 2 change.
  Later tasks diff against it to confirm that only intended pages changed.

- [ ] **Step 1: Confirm phase 1 is in place and the tree is clean**

```bash
git status --short
grep -c 'pymdownx.snippets' mkdocs.yml
ls includes/conf/protection-note.md
```

Expected: no output from `git status`, `1` from the grep, and the file listed. If any
of the three fails, phase 1 is not complete — stop.

- [ ] **Step 2: Build the baseline**

```bash
python3 -m mkdocs build -q -d /tmp/phase2-baseline-site
```

Expected: a Material for MkDocs banner on stderr, nothing else.

- [ ] **Step 3: Record which pages this phase is allowed to change**

```bash
echo "docs/ingres/index.md docs/hcl-informix/index.md docs/zen/index.md docs/analytics-engine/index.md docs/get-started/index.md"
```

Any other page appearing in a later diff is a mistake, with one intended exception
noted in Task 5.

---

## Task 1: Share the config-table rows that are provably identical

The four "Optional fields" tables overlap but are not identical. This task extracts
the overlap into three includes, each with the consumer set the evidence supports, and
harmonizes the phrasing of the shared rows to one wording.

**Files:**
- Create: `includes/conf/common-optional-fields.md`
- Create: `includes/conf/tls-fields.md`
- Create: `includes/conf/write-fields.md`
- Modify: `docs/ingres/index.md` (Optional Fields table, around line 88-97)
- Modify: `docs/analytics-engine/index.md` (Optional fields table, around line 88-97)
- Modify: `docs/hcl-informix/index.md` (Optional fields table, around line 88-94)
- Modify: `docs/zen/index.md` (Optional fields table, around line 81-84)

**Interfaces:**
- Produces three row-fragment includes. Each is a sequence of Markdown table rows with
  **no header row and no surrounding blank lines**, designed to continue a table the
  consuming page has already opened with
  `| Field | Type | Default | Description |` and its separator line. Later phases add
  consumers as the deferred questions get answered.

- [ ] **Step 1: Create the common-rows include**

The wording is chosen from the existing variants: `log_level` takes the
"Valid values:" form used by Informix and Zen (two pages against Ingres and Analytics
Engine's "Valid values are"), `oauth` takes the deep link to the anchor fixed in phase
1, and `extensions` is copied verbatim since all four already agree.

Create `includes/conf/common-optional-fields.md` — three lines, no blank line at the
start or end:

```markdown
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. For more information, see [OAuth configuration](../authentication/index.md#configuring-oauth-block). |
| `extensions` | `array` | — | Extension modules to load, each an object with a required `module` and an optional `config`. For more information, see [Extensions](../extensions/index.md). |
```

- [ ] **Step 2: Create the TLS-rows include**

Wording takes the "Add … in the container" form used by Analytics Engine, which reads
better than Ingres's "Set" and avoids Informix's "inside".

Create `includes/conf/tls-fields.md` — two lines, no surrounding blank lines:

```markdown
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. Add `/app/server.crt` in the container. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. Add `/app/server.key` in the container. |
```

- [ ] **Step 3: Create the write-rows include**

Ingres and Analytics Engine already word these identically, so this is a verbatim
copy with the trailing period normalized.

Create `includes/conf/write-fields.md` — two lines, no surrounding blank lines:

```markdown
| `query_mode` | `string` | `read-only` | Controls whether data-modifying SQL is permitted. Valid values are `read-only` and `read-write`. See [Write support](../intro/write-support.md). |
| `write_confirmation` | `boolean` | `true` | Whether a write requires human approval before it runs. Set to `false` only for clients that cannot display the approval prompt. See [Write support](../intro/write-support.md#skipping-the-approval-prompt). |
```

Note: `../intro/write-support.md` is the path **today**. Phase 4 moves that page to
`write-support/index.md` and updates this include in one place — which is the point of
extracting it.

- [ ] **Step 4: Rewire the Ingres table**

In `docs/ingres/index.md`, the Optional Fields table currently has eight rows. Keep the
header, the separator, and the `max_rows` row (deferred — see above). Replace the
other seven rows with the three includes in this order:

```markdown
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | The maximum number of rows returned in a single query response. Maximum value: `1000` |
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
--8<-- "conf/write-fields.md"
```

The `max_rows` row is copied unchanged, including its "Maximum value" claim, which
differs from the other three pages. Do not harmonize it.

- [ ] **Step 5: Rewire the Analytics Engine table**

Same three includes, same order. In `docs/analytics-engine/index.md`:

```markdown
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. Default is `1000`.|
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
--8<-- "conf/write-fields.md"
```

- [ ] **Step 6: Rewire the Informix table**

Informix documents no `query_mode` / `write_confirmation`, so it gets two includes, not
three. In `docs/hcl-informix/index.md`:

```markdown
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. |
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
```

- [ ] **Step 7: Rewire the Zen table**

Zen documents no TLS fields and no write fields, so it gets one include. It also has an
engine-specific `database` row that stays. In `docs/zen/index.md`:

```markdown
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database` | `string` | — | Logical database name used for display purposes. |
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. Default is `1000`. |
--8<-- "conf/common-optional-fields.md"
```

- [ ] **Step 8: Verify the tables still render as single tables**

The row-fragment approach fails silently if a blank line sneaks in — the table splits
and the second half renders as literal pipes. Check the rendered HTML rather than
eyeballing the Markdown:

```bash
python3 -m mkdocs build -q -d /tmp/phase2-t1
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s tables=%s stray-pipes=%s\n" "$p" \
    "$(grep -c '<table>' /tmp/phase2-t1/$p/index.html)" \
    "$(grep -c '^<p>| ' /tmp/phase2-t1/$p/index.html)"
done
```

Expected: `stray-pipes=0` for all four. The `tables=` count must match the baseline:

```bash
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s before=%s after=%s\n" "$p" \
    "$(grep -c '<table>' /tmp/phase2-baseline-site/$p/index.html)" \
    "$(grep -c '<table>' /tmp/phase2-t1/$p/index.html)"
done
```

Expected: `before` equals `after` on every line. A higher `after` means a table split.

- [ ] **Step 9: Verify every field row survived**

Content must be equivalent, so no field may have been dropped. Compare the set of
field names rendered in each page's optional table:

```bash
for p in ingres hcl-informix zen analytics-engine; do
  echo "=== $p ==="
  diff <(grep -oE '<code>[a-z_]+</code>' /tmp/phase2-baseline-site/$p/index.html | sort -u) \
       <(grep -oE '<code>[a-z_]+</code>' /tmp/phase2-t1/$p/index.html | sort -u) \
    && echo "  same field set"
done
```

Expected: `same field set` for all four. Any `<` line is a field that got lost.

- [ ] **Step 10: Verify only the four intended pages changed**

```bash
diff -rq -I 'git-revision-date-localized-plugin-date' \
  /tmp/phase2-baseline-site /tmp/phase2-t1 | sed 's|/tmp/phase2-[a-z0-9]*||g' | sort
```

Expected: exactly eight lines — `index.html` and `index.md` for `ingres`,
`hcl-informix`, `zen` and `analytics-engine`. Nothing else.

- [ ] **Step 11: Run the gates**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: no warnings, both guards silent.

- [ ] **Step 12: Commit**

```bash
git add includes/conf/ docs/ingres/index.md docs/analytics-engine/index.md \
  docs/hcl-informix/index.md docs/zen/index.md
git commit -m "docs: share the identical conf.json optional-field rows"
```

---

## Task 2: Harmonize "Start the server" and drop the Informix tarball

Four pages describe the same operation four ways, and one of them is wrong. The
`docker run` command stays per-page (it names the image, and snippets cannot
substitute), but the prose around it converges and the mount-path note becomes an
include.

**Files:**
- Create: `includes/docker/mount-path-note.md`
- Modify: `docs/ingres/index.md` (Start the Server section)
- Modify: `docs/analytics-engine/index.md` (Start the Server section)
- Modify: `docs/hcl-informix/index.md` (Start the Server section)
- Modify: `docs/zen/index.md` (Start the Server section)

**Interfaces:**
- Consumes: `includes/conf/protection-note.md` from phase 1, which currently has only
  `get-started/` as a consumer. After this task the four setup pages consume it too.
- Produces: `includes/docker/mount-path-note.md`, a standalone admonition block
  (blank-line-safe, unlike the row fragments in Task 1).

- [ ] **Step 1: Create the mount-path note include**

Analytics Engine and Informix both carry this note in different words; Ingres and Zen
lack it. One wording, applied to all four:

Create `includes/docker/mount-path-note.md`:

```markdown
!!! note "Mount target path"
    The container reads its configuration from `/app/conf.json`. Do not change the mount target path.
```

- [ ] **Step 2: Rewrite the Ingres section**

Replace the whole `## Start the Server` section in `docs/ingres/index.md` — from the
heading down to and including the `--- ` separator before `## Next Steps` — with:

````markdown
## Start the server

With `conf.json` ready, start the container and mount the configuration file as a
read-only volume:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/ingres-mcp-server:1.0.0
```

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"
````

Note the heading case change, `## Start the Server` to `## Start the server`, which
Task 4 applies to every heading on all four pages. The image tag `:1.0.0` is left
exactly as it was — see the deferred table.

Include paths are relative to `includes/`, so it is `docker/mount-path-note.md`, **not**
`includes/docker/mount-path-note.md`. Getting this wrong fails the build rather than
rendering literal text, because phase 1 set `check_paths: true`.

- [ ] **Step 3: Confirm the include resolved**

```bash
python3 -m mkdocs build -q -d /tmp/phase2-t2-probe 2>&1 | grep -i snippet; echo "(empty above = good)"
grep -c 'Mount target path' /tmp/phase2-t2-probe/ingres/index.html
```

Expected: no snippet error, and `1` from the grep.

- [ ] **Step 4: Rewrite the Analytics Engine section**

In `docs/analytics-engine/index.md`, replace the `## Start the Server` section
including its `!!! important` note and the sentence after it:

````markdown
## Start the server

With `conf.json` ready, start the container and mount the configuration file as a
read-only volume:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/analytics-engine-mcp-server:1.0.0
```

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"
````

- [ ] **Step 5: Rewrite the Informix section**

This is the corrective edit. Three things go: the `docker load -i ifx_mcp_image.tar`
step, the image name `actian/informix-mcp-server-linux:1.0.0`, and the mount source
`conf_temp.json` (every other page and the whole rest of the docs say `conf.json`).
The `,Z` SELinux mount label is also dropped, since no other page needs it and the
image is now the same Docker Hub image as the others.

In `docs/hcl-informix/index.md`, replace the `## Start the Server` section:

````markdown
## Start the server

Set `host` to `0.0.0.0` in `conf.json` so the server is reachable from outside the
container. Then start the container and mount the configuration file as a read-only
volume:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/informix-mcp-server:1.0.0
```

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"
````

The tag `:1.0.0` is kept because that is what the page said; only the image *name* was
wrong. If the correct Informix tag turns out to differ, that falls under the deferred
image-tag question.

- [ ] **Step 6: Rewrite the Zen section**

Zen keeps `--add-host` and its networking note, both genuinely engine-specific:

````markdown
## Start the server

With `conf.json` ready, start the container and mount the configuration file as a
read-only volume:

```bash
docker run -d \
    --name=actian-mcp \
    -p 8000:8000 \
    --add-host=host.docker.internal:host-gateway \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    actian/zen-mcp-server:latest
```

!!! note "Container networking"
    `-p 8000:8000` exposes the server port on the host. `--add-host=host.docker.internal:host-gateway` allows the container to reach services on the host machine (such as the Zen engine on port 1583). Docker Desktop on Windows and macOS resolves `host.docker.internal` automatically; Linux requires the `--add-host` flag.

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"
````

The container name changes from `zen-mcp` to `actian-mcp` so all four pages agree; the
verification steps added in Task 3 filter on that name and must match.

- [ ] **Step 7: Verify the tarball instructions are gone**

```bash
grep -rn -e 'ifx_mcp_image' -e 'informix-mcp-server-linux' -e 'conf_temp.json' docs/
echo "(empty above = good)"
```

Expected: no output. These were the wrong instructions resolved on 2026-08-05.

- [ ] **Step 8: Verify the container name is consistent**

```bash
grep -rhoE '\--name[= ]\S+' docs/ | sort -u
```

Expected: exactly one line, `--name=actian-mcp`.

- [ ] **Step 9: Verify only the four intended pages changed**

```bash
python3 -m mkdocs build -q -d /tmp/phase2-t2
diff -rq -I 'git-revision-date-localized-plugin-date' \
  /tmp/phase2-baseline-site /tmp/phase2-t2 | sed 's|/tmp/phase2-[a-z0-9]*||g' | sort
```

Expected: eight lines, the same four pages as Task 1.

- [ ] **Step 10: Run the gates**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: no warnings, both guards silent.

- [ ] **Step 11: Commit**

```bash
git add includes/docker/ docs/ingres/index.md docs/analytics-engine/index.md \
  docs/hcl-informix/index.md docs/zen/index.md
git commit -m "docs: harmonize container startup and drop the wrong Informix image"
```

---

## Task 3: Put the verification steps on every setup page

The three verification steps exist only on `get-started/`. A reader who goes straight
to their engine's page never sees how to confirm the server works. This adds them to
all four, from one source — and it is a prerequisite for Task 5, which removes them
from `get-started/`.

**Files:**
- Create: `includes/verify-connection.md`
- Modify: `docs/ingres/index.md` (new section before `## Next steps`)
- Modify: `docs/analytics-engine/index.md` (new section, replacing `## Usage`)
- Modify: `docs/hcl-informix/index.md` (new section before `## Next Steps`)
- Modify: `docs/zen/index.md` (new section, replacing `## Usage`)

**Interfaces:**
- Produces: `includes/verify-connection.md`, a full section body (no heading — the
  consuming page supplies `## Verify the connection`). It references the container name
  `actian-mcp` set in Task 2 and port `8000`, both identical across the four SQL
  engines, so it needs no substitution.

- [ ] **Step 1: Create the include**

Adapted from `docs/get-started/index.md` steps 5.1–5.3. The container name matches
Task 2's `--name=actian-mcp`. The concrete port `8000` replaces `<port>`, since all
four SQL pages use it and a copy-pasteable command beats a placeholder.

Create `includes/verify-connection.md`:

````markdown
**1. Verify the container status**

```bash
docker ps --filter "name=actian-mcp"
```

Confirm that the container status is `Up`.

**2. Verify the endpoint**

Ping the server to confirm that it is listening for requests:

```bash
curl -i http://localhost:8000/mcp
```

If the server is ready, it returns a `200` or `307` status code instead of a
`connection refused` error.

**3. Test the client integration**

Open the configured MCP client. It automatically detects the Actian MCP Server and
displays its available tools. Prompt the AI with a standard database request, such as:

> "List all tables in the database"

The client invokes the server's `list_tables` tool. If it returns a list of the
database tables, the end-to-end connection is working.
````

- [ ] **Step 2: Add the section to the Ingres page**

In `docs/ingres/index.md`, between the `## Start the server` section and
`## Next Steps`, insert:

```markdown
## Verify the connection

--8<-- "verify-connection.md"
```

- [ ] **Step 3: Add the section to the Informix page**

Identical insertion in `docs/hcl-informix/index.md`, between `## Start the server` and
`## Next Steps`:

```markdown
## Verify the connection

--8<-- "verify-connection.md"
```

- [ ] **Step 4: Replace the Analytics Engine `## Usage` section**

`docs/analytics-engine/index.md` has a `## Usage` section — four bullets of generic
advice ("Inspect before querying", "Run a query", "Explore functions", "Summarize
results") that say nothing engine-specific and duplicate what the tools page covers.
Replace the whole section with the verification section:

```markdown
## Verify the connection

--8<-- "verify-connection.md"
```

This drops those four bullets. That is intentional: they are the only content removed
in this phase, they are not facts, and Ingres and Informix never had them.

- [ ] **Step 5: Replace the Zen `## Usage` section**

`docs/zen/index.md` has the same kind of `## Usage` section, with "Explore
relationships" instead of "Explore functions". Replace it the same way:

```markdown
## Verify the connection

--8<-- "verify-connection.md"
```

- [ ] **Step 6: Verify all four pages now carry the steps**

```bash
python3 -m mkdocs build -q -d /tmp/phase2-t3
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s verify-heading=%s docker-ps=%s curl=%s\n" "$p" \
    "$(grep -c 'id="verify-the-connection"' /tmp/phase2-t3/$p/index.html)" \
    "$(grep -c 'docker ps --filter' /tmp/phase2-t3/$p/index.html)" \
    "$(grep -c 'curl -i http' /tmp/phase2-t3/$p/index.html)"
done
```

Expected: `1 1 1` on every line.

- [ ] **Step 7: Verify the `## Usage` sections are gone and nothing else vanished**

```bash
grep -rn '^## Usage' docs/; echo "(empty above = good)"
```

Expected: no output.

- [ ] **Step 8: Verify only the four intended pages changed**

```bash
diff -rq -I 'git-revision-date-localized-plugin-date' \
  /tmp/phase2-baseline-site /tmp/phase2-t3 | sed 's|/tmp/phase2-[a-z0-9]*||g' | sort
```

Expected: eight lines, the same four pages.

- [ ] **Step 9: Run the gates**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: no warnings, both guards silent.

- [ ] **Step 10: Commit**

```bash
git add includes/verify-connection.md docs/ingres/index.md \
  docs/analytics-engine/index.md docs/hcl-informix/index.md docs/zen/index.md
git commit -m "docs: add connection verification to every SQL setup page"
```

---

## Task 4: Align the four pages to the template

After Tasks 1–3 the pages share their content but still differ in headings and section
order, so a reviewer cannot diff two of them usefully. This is a pure structural pass:
no sentence changes, only headings and ordering.

**Files:**
- Modify: `templates/setup-sql-database.md.tmpl`
- Modify: `docs/ingres/index.md`
- Modify: `docs/analytics-engine/index.md`
- Modify: `docs/hcl-informix/index.md`
- Modify: `docs/zen/index.md`

**Interfaces:**
- Consumes: `templates/setup-sql-database.md.tmpl`, whose heading set is the target.
- Produces: four pages with an identical heading sequence, so
  `diff <(grep '^#' a) <(grep '^#' b)` is empty for any pair.

- [ ] **Step 0: Make the template truthful first**

Phase 1 wrote the template before the includes existed, so it references two that this
phase does not create: `conf/common-fields.md` (the measured reality is three separate
includes) and `docker/run-sql.md` (impossible — the `docker run` block names the image
and snippets cannot substitute). It also puts `conf/protection-note.md` in the
configuration section, whereas Task 2 places it with the startup command.

Comparing pages against a template that references non-existent files would be
meaningless, so fix the template before using it as the target. In
`templates/setup-sql-database.md.tmpl`, replace everything from `**Optional fields**`
down to and including the `--8<-- "verify-connection.md"` line with:

````markdown
**Optional fields**

<!-- TODO(fill): the engine-specific optional rows go here, directly after the header,
     before the shared includes. max_rows is engine-specific for now: Ingres documents
     1000 as a hard cap, the others as a default. -->

| Field | Type | Default | Description |
|-------|------|---------|-------------|
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
--8<-- "conf/write-fields.md"

## Start the server

<!-- TODO(fill): one sentence, then the docker run block for this engine. The command
     cannot be an include: it names the image and snippets has no substitution. Keep
     the flags in the same order as the other engines. -->

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"
## Verify the connection

--8<-- "verify-connection.md"
````

Drop `--8<-- "conf/tls-fields.md"` or `--8<-- "conf/write-fields.md"` when filling the
template for an engine that does not document those fields — Zen documents neither,
Informix documents TLS but not write mode.

Also update the template's header comment, which still lists the old include names:

```markdown
<!-- Template: SQL/ODBC setup page. Target: docs/{{DB_SLUG}}/index.md
     Expects includes: conf/common-optional-fields.md, conf/tls-fields.md,
     conf/write-fields.md, conf/protection-note.md, docker/mount-path-note.md,
     verify-connection.md -->
```

Verify the template still trips no guard — it lives outside `docs/`, so
`check-templates` must stay silent even though the file is full of markers:

```bash
make check-templates && echo "guard correctly ignores templates/"
```

Expected: `guard correctly ignores templates/`.

- [ ] **Step 1: Read the target heading sequence**

```bash
grep -E '^#{1,3} ' templates/setup-sql-database.md.tmpl
```

The target sequence, from the template:

```
# Actian MCP Server for <engine>
## Capabilities
## Prerequisites
## Configuration
### Create the configuration file
### Configuration reference
## Start the server
## Verify the connection
## Next steps
```

- [ ] **Step 2: See how far each page currently deviates**

```bash
for p in ingres hcl-informix zen analytics-engine; do
  echo "=== $p ==="; grep -E '^#{1,3} ' docs/$p/index.md
done
```

The known deviations to fix: Ingres has `### Create Configuration File` and
`**Required Fields**` / `**Optional Fields**` in title case; Analytics Engine and
Informix use `## Next Steps`; Zen has `### Connection Formats` instead of
`### Create the configuration file`; all four capitalize `## Next Steps`.

- [ ] **Step 3: Rename headings on the Ingres page**

In `docs/ingres/index.md`:

- `### Create Configuration File` → `### Create the configuration file`
- `### Configuration Reference` → `### Configuration reference`
- `**Required Fields**` → `**Required fields**`
- `**Optional Fields**` → `**Optional fields**`
- `## Next Steps` → `## Next steps`

Also delete the three stray `---` horizontal rules (after Capabilities, after
Prerequisites, and after the configuration reference). No other page has them and the
template does not.

- [ ] **Step 4: Rename headings on the Analytics Engine page**

In `docs/analytics-engine/index.md`:

- `### Create the Configuration File` → `### Create the configuration file`
- `### Configuration Reference` → `### Configuration reference`
- `## Next Steps` → `## Next steps`

- [ ] **Step 5: Rename headings on the Informix page**

In `docs/hcl-informix/index.md`:

- `### Configuration Reference` → `### Configuration reference`
- `## Next Steps` → `## Next steps`

Add `### Create the configuration file` above the `conf.json` example if the page has
the example under a bare paragraph rather than its own heading.

- [ ] **Step 6: Rename headings on the Zen page**

In `docs/zen/index.md`:

- `### Connection Formats` → `### Create the configuration file`
- `### Configuration Reference` → `### Configuration reference`
- `## Next Steps` → `## Next steps`

Zen's two connection formats (DSN and full driver string) stay as bold sub-paragraphs
inside that section — they are genuinely engine-specific and the template's
`### Create the configuration file` is the right home for them.

- [ ] **Step 7: Verify all four heading sequences are now identical**

The engine name in the H1 differs, so compare from `## Capabilities` down:

```bash
for p in hcl-informix zen analytics-engine; do
  printf "ingres vs %-18s " "$p"
  diff <(grep -E '^#{2,3} ' docs/ingres/index.md) \
       <(grep -E '^#{2,3} ' docs/$p/index.md) > /dev/null \
    && echo "identical" || echo "DIFFERS"
done
```

Expected: `identical` on all three lines. If one differs, run the same `diff` without
`> /dev/null` to see which heading is off.

- [ ] **Step 8: Verify no prose changed**

A structural pass must not alter sentences. This task's changes are still uncommitted,
so `HEAD` is Task 3's commit — the correct reference. Compare the non-heading,
non-blank, non-rule body text of each page against it:

```bash
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s " "$p"
  diff <(git show HEAD:docs/$p/index.md | grep -vE '^#|^\s*$|^---\s*$' | sort) \
       <(grep -vE '^#|^\s*$|^---\s*$' docs/$p/index.md | sort) \
    > /dev/null && echo "prose unchanged" || echo "PROSE CHANGED - review"
done
```

Expected: `prose unchanged` on all four. Bold run-in labels like `**Required Fields**`
are body text, not headings, so the case changes in Steps 3–6 will show up here — that
is expected, and they are the only body lines allowed to differ. Anything else is a
mistake.

- [ ] **Step 9: Run the gates**

Heading renames change anchors, so this step is where `--strict` earns its keep: any
inbound link to a renamed heading now fails the build.

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: no warnings. If `--strict` reports a missing anchor, some other page links to
a heading renamed here — fix the *link*, not the heading, and note which page it was.

- [ ] **Step 10: Commit**

```bash
git add templates/setup-sql-database.md.tmpl docs/ingres/index.md \
  docs/analytics-engine/index.md docs/hcl-informix/index.md docs/zen/index.md
git commit -m "docs: align the four SQL setup pages to the page template"
```

---

## Task 5: Turn Get started into a database chooser

`get-started/` currently walks through a six-step SQL setup and warns NoSQL readers
away twice. Tasks 1–3 moved everything engine-specific onto the engine pages, so this
page can become what the restructure is for: orientation, then "which database do you
have?".

**Files:**
- Modify: `docs/get-started/index.md` (full rewrite, 154 lines → ~70)
- Modify: `docs/nosql/index.md:20-21` **only if** Step 6 finds a link that breaks

**Interfaces:**
- Consumes: nothing. This page deliberately references no includes — a chooser must not
  carry a configuration reference, which is the duplication being removed.
- Produces: `docs/get-started/index.md#which-database-do-you-have`, the anchor other
  pages can link to when pointing a reader at the chooser.

- [ ] **Step 1: Record what currently links into this page**

Heading changes here can break inbound anchors. Capture them first:

```bash
grep -rn 'get-started/index.md#' docs/ || echo "(no inbound anchor links)"
```

Note the result. If any exist, Step 7's `--strict` run will catch a break, and the fix
is to update the linking page.

- [ ] **Step 2: Replace the page**

Replace the entire contents of `docs/get-started/index.md` with:

```markdown
---
title: Get Started
description: Choose your Actian database and set up the Actian MCP Server for it.
---

# Getting started with the Actian MCP Server

The Actian MCP Server connects an MCP-compatible AI client to an Actian database. It is
distributed as Docker container images, one per supported database. Each database has
its own image and its own configuration, so setup starts by picking yours.

## What you need

- **Container runtime**: Docker or Podman on the host machine
- **Database access**: network connectivity to a supported Actian database
- **AI client**: an MCP-compatible client such as Claude Desktop, Cursor, GitHub
  Copilot, or Codex

## How it works

Setting up any of the servers follows the same four steps. What differs per database is
the image, the configuration format, and the port.

1. **Configure** — write a configuration file with your connection details
2. **Start** — run the container with that file mounted
3. **Verify** — confirm the container is up and the endpoint answers
4. **Connect** — point your AI client at the server endpoint

## Which database do you have?

| Database | Container image | Configuration file | Default port | Set up |
|----------|----------------|--------------------|--------------|--------|
| Actian Ingres | [`actian/ingres-mcp-server`](https://hub.docker.com/r/actian/ingres-mcp-server) | `conf.json` | `8000` | [Set up Ingres](../ingres/index.md) |
| HCL Informix® | [`actian/informix-mcp-server`](https://hub.docker.com/r/actian/informix-mcp-server) | `conf.json` | `8000` | [Set up HCL Informix®](../hcl-informix/index.md) |
| Actian Zen | [`actian/zen-mcp-server`](https://hub.docker.com/r/actian/zen-mcp-server) | `conf.json` | `8000` | [Set up Zen](../zen/index.md) |
| Actian Analytics Engine | [`actian/analytics-engine-mcp-server`](https://hub.docker.com/r/actian/analytics-engine-mcp-server) | `conf.json` | `8000` | [Set up Analytics Engine](../analytics-engine/index.md) |
| Actian NoSQL | [`actian/nsql-mcp-server`](https://hub.docker.com/r/actian/nsql-mcp-server) | `application.properties` | `8080` | [Set up NoSQL](../nosql/index.md) |

!!! info "One server per database"
    Each database needs its own server instance, which means one server, one database,
    and one MCP endpoint. To reach two databases, run two containers.

## After the server is running

Your database's setup page ends with a running, verified server. These apply to all of
them:

<div class="grid cards" markdown>

- :material-connection: **[Connect a client](../mcp-clients/index.md)**
  Configuration examples for Claude Desktop, Cursor, GitHub Copilot, Codex, and
  fast-agent.

- :material-shield-check: **[Secure the server](../authentication/index.md)**
  OAuth 2.0 with an external identity provider, and TLS for remote deployments.

- :material-database-edit: **[Write support](../intro/write-support.md)**
  Allow `INSERT`, `UPDATE`, and `DELETE`, gated by an OAuth scope and human approval.

- :material-puzzle: **[Extensions](../extensions/index.md)**
  Add your own tools, resources, and prompts in Python.

</div>
```

- [ ] **Step 3: Verify both NoSQL warnings are gone**

These were the clearest symptom of the old structure — a page that sends one of five
readers away.

```bash
grep -n 'Actian NoSQL users' docs/get-started/index.md; echo "(empty above = good)"
grep -c 'different startup command' docs/get-started/index.md
```

Expected: no output from the first, `0` from the second.

- [ ] **Step 4: Verify NoSQL is now a peer in the chooser**

```bash
python3 -m mkdocs build -q -d /tmp/phase2-t5
grep -c 'Set up NoSQL' /tmp/phase2-t5/get-started/index.html
grep -o 'application.properties' /tmp/phase2-t5/get-started/index.html | head -1
grep -o '8080' /tmp/phase2-t5/get-started/index.html | head -1
```

Expected: `1`, then `application.properties`, then `8080`. NoSQL appears as a row like
the others, with its two genuine differences stated rather than hidden behind a
warning.

- [ ] **Step 5: Verify the page no longer duplicates the config reference**

The old page carried a twelve-row `conf.json` field table that also lives on all four
SQL setup pages. It must be gone.

```bash
grep -c 'write_confirmation' docs/get-started/index.md
grep -c 'ssl_certfile' docs/get-started/index.md
```

Expected: `0` for both.

- [ ] **Step 6: Verify every chooser link resolves**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
```

Expected: no output. `--strict` validates all five setup links, the four grid-card
links, and any inbound anchors recorded in Step 1. If a warning names
`get-started/index.md#step-...`, another page links to a step heading this rewrite
removed — update that link to `#which-database-do-you-have`.

- [ ] **Step 7: Verify the changed-page set**

```bash
diff -rq -I 'git-revision-date-localized-plugin-date' \
  /tmp/phase2-baseline-site /tmp/phase2-t5 | sed 's|/tmp/phase2-[a-z0-9]*||g' | sort
```

Expected: ten lines — `index.html` and `index.md` for the four setup pages plus
`get-started`. An eleventh appears only if Step 6 required fixing a link on another
page, which is the one intended exception noted in Task 0 Step 3.

- [ ] **Step 8: Run the remaining gates**

```bash
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: both silent.

- [ ] **Step 9: Read the result end to end**

The automated checks cannot judge whether the page answers the question. Open the
built site and follow one database's path:

```bash
python3 -m mkdocs serve -a 127.0.0.1:8000
```

Visit `http://127.0.0.1:8000/get-started/index.html`, pick Zen, and read through to the
end of the Zen setup page. The test: can you get from "I have a Zen database" to a
running, verified server without jumping back out? Note anything that forces a detour —
that is phase 2's real acceptance criterion and the reason the phase exists.

- [ ] **Step 10: Commit**

```bash
git add docs/get-started/index.md
git commit -m "docs: turn Get started into a database chooser"
```

---

## Phase 2 done — state afterwards

| Include | Consumers | Grows to 4 when |
|---|---|---|
| `conf/protection-note.md` | 4 setup pages | already complete |
| `conf/common-optional-fields.md` | 4 setup pages | already complete |
| `docker/mount-path-note.md` | 4 setup pages | already complete |
| `verify-connection.md` | 4 setup pages | already complete |
| `conf/tls-fields.md` | 3 setup pages | Zen's TLS support is confirmed |
| `conf/write-fields.md` | 2 setup pages | spec §11.1 is answered |

Still open after this phase, all tracked in spec §11: the `max_rows` cap-versus-default
contradiction, Zen TLS support, Informix and Zen write semantics, `list_functions` on
Zen, `user_impersonation` on NoSQL, and the image tag inconsistency. The first four
block phase 3.
