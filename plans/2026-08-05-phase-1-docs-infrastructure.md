# Phase 1: Documentation Infrastructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal plan placed there would appear on docs.actian.com.

**Goal:** Install the single-sourcing and verification infrastructure that phases 2–6 of
`specs/2026-08-05-docs-by-database-design.md` depend on, without changing a single
rendered page.

**Architecture:** Enable `pymdownx.snippets` with includes living in `includes/` at the
repo root (outside `docs_dir`, so fragments are never built as pages nor published as
raw URLs). Teach `hooks/copy_md_sources.py` to resolve those includes before it copies
raw Markdown into `site/`, reusing the snippets preprocessor itself rather than a
second regex implementation. Add authoring templates plus a `make` guard that keeps
unfilled placeholders out of `docs/`. Finally, promote MkDocs anchor validation to a
warning so `--strict` becomes a real gate, and fix the six broken anchors that
promotion exposes.

**Tech Stack:** MkDocs 1.6.1, mkdocs-material 9.6+, pymdown-extensions 10.21.2,
Python-Markdown 3.9, mkdocs-redirects (new), GNU make, Python 3.10+

## Global Constraints

- **Tasks 1–4 must not change any rendered output.** The built site must be identical
  to a baseline built from commit `fb9347e`, apart from files that did not exist
  before, verified with:

  ```bash
  diff -r -I 'git-revision-date-localized-plugin-date' /tmp/phase1-baseline-site <build>
  ```

  The `-I` is **required**, not cosmetic. `git-revision-date-localized` renders each
  page's last-commit date into its footer, so committing a source file changes that
  page's HTML even when the content is untouched. Plain `diff -rq` therefore reports a
  false positive for every page whose source this phase commits. `-I` excludes changes
  whose only differing lines match that pattern, and still catches every real change —
  verified during execution.
- **Task 5 is the only task that changes rendered output**, and only by fixing six
  anchor targets. It runs last, after the byte-identical gate has passed.
- Baseline commit: `fb9347e` (`docs: add design spec for database-first doc restructure`).
- Includes live in `includes/` at the repo root. Never in `docs/`, for the reason in
  the Architecture note.
- `pymdownx.snippets` resolves `base_path` relative to the **current working
  directory**, not relative to `mkdocs.yml`. Every build must therefore be run from
  the repo root. `makefile` already does this (`cd /docs && mkdocs serve`).
- `pymdownx.snippets` ships with `pymdown-extensions`, a dependency of
  `mkdocs-material`. Do **not** add it to `requirements.txt`.
- New dependency, exact line: `mkdocs-redirects>=1.2`
- Placeholder markers, exact strings: `{{DB_NAME}}` style for values,
  `<!-- TODO(fill): … -->` for prose that needs product knowledge,
  `<!-- STUB: pending product input -->` for deliberately unfinished published pages.
  The guard rejects the first two and permits the third.
- Verified pre-conditions (do not re-derive):
  - Two consecutive `mkdocs build` runs on `fb9347e` produce byte-identical output.
  - `docs/` currently contains zero occurrences of `{{` and zero of `TODO`, so the
    guard cannot produce a false positive on existing content.
  - `markdown.Markdown(extensions=["pymdownx.snippets"]).preprocessors["snippet"]`
    is the correct registry key, and its `run()` resets its own recursion state, so a
    single instance is safe to reuse across all files.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `mkdocs.yml` | Enable `pymdownx.snippets`; register `redirects`; enable anchor validation | 1, 3, 5 |
| `includes/conf/protection-note.md` | First real shared fragment — the `chmod 600` admonition | 1 |
| `docs/get-started/index.md` | First consumer of that fragment | 1 |
| `hooks/copy_md_sources.py` | Resolve includes before publishing raw Markdown | 2 |
| `requirements.txt` | Add `mkdocs-redirects` | 3 |
| `templates/README.md` | Authoring guide: what each placeholder means, how to use a template | 4 |
| `templates/setup-sql-database.md.tmpl` | Skeleton for a SQL setup page | 4 |
| `templates/tools-sql-database.md.tmpl` | Skeleton for a SQL tools page | 4 |
| `templates/write-support.md.tmpl` | Skeleton for a write-support variant | 4 |
| `templates/extensions.md.tmpl` | Skeleton for an extensions variant | 4 |
| `makefile` | `check-templates` and `check-raw-md` guards | 4 |
| `docs/{ingres,hcl-informix,analytics-engine}/index.md` | Fix `#configuring-oauth-block` anchor | 5 |
| `docs/authentication/index.md` | Fix NoSQL TLS anchor | 5 |
| `docs/authentication/auth0/index.md` | Fix TLS anchor | 5 |
| `docs/mcp-clients/index.md` | Fix TLS anchor | 5 |

---

## Task 0: Capture the baseline

This is not a code change. It produces the reference the next four tasks are checked
against. Do it once; keep the directory until Task 4 passes.

**Files:** none

**Interfaces:**
- Produces: a baseline site tree at `/tmp/phase1-baseline-site`, built from commit
  `fb9347e`. Tasks 1–4 diff against it.

- [ ] **Step 1: Create a worktree at the baseline commit**

```bash
git worktree add /tmp/phase1-baseline fb9347e
```

Expected: `Preparing worktree (detached HEAD fb9347e)` followed by `HEAD is now at fb9347e`.

- [ ] **Step 2: Build the baseline site from inside that worktree**

The `cd` matters: `pymdownx.snippets` and the relative `hooks:` path both resolve
against the working directory.

```bash
(cd /tmp/phase1-baseline && python3 -m mkdocs build -q -d /tmp/phase1-baseline-site)
```

Expected: a Material for MkDocs banner about MkDocs 2.0 on stderr, then nothing.
The banner is noise, not an error.

- [ ] **Step 3: Confirm the baseline is non-empty and self-consistent**

```bash
ls /tmp/phase1-baseline-site/get-started/index.html /tmp/phase1-baseline-site/get-started/index.md
find /tmp/phase1-baseline-site -name '*.md' | wc -l
```

Expected: both files listed, and `34` Markdown files (the hook publishes one raw `.md`
per page).

---

## Task 1: Enable snippets and prove it with one real fragment

The fragment is chosen so the resolved Markdown is **character-for-character** what
the page contained before. That makes the byte-identical gate prove the whole pipeline
rather than just prove that nothing happened.

**Files:**
- Modify: `mkdocs.yml` (markdown_extensions block, after the `pymdownx.superfences` entry)
- Create: `includes/conf/protection-note.md`
- Modify: `docs/get-started/index.md:58-60`

**Interfaces:**
- Consumes: the baseline at `/tmp/phase1-baseline-site` from Task 0.
- Produces: `includes/` as the snippets `base_path`. Every later include in phases 2–6
  is addressed relative to it, e.g. `--8<-- "conf/common-fields.md"` resolves to
  `includes/conf/common-fields.md`.

- [ ] **Step 1: Add the snippets extension to `mkdocs.yml`**

Insert directly after the `pymdownx.superfences` block and before `- admonition`:

```yaml
  - pymdownx.snippets:
      base_path: ['includes']
      check_paths: true
```

`check_paths: true` is not optional. Without it a mistyped include path renders as
literal text in the page and no build error is raised.

- [ ] **Step 2: Create the fragment**

The file must contain exactly two lines plus a trailing newline. The trailing newline
is load-bearing — it supplies the blank line that separated the admonition from the
following heading in the original page.

Create `includes/conf/protection-note.md`:

```markdown
!!! note "Configuration File Protection"
    The configuration file contains database credentials. Set restrictive permissions on the host (`chmod 600 conf.json`) and avoid committing it to version control.
```

- [ ] **Step 3: Replace the inline admonition with the include**

In `docs/get-started/index.md`, lines 58–60 currently read:

```markdown
!!! note "Configuration File Protection"
    The configuration file contains database credentials. Set restrictive permissions on the host (`chmod 600 conf.json`) and avoid committing it to version control.

```

Replace all three lines (the two admonition lines **and** the blank line after them)
with this single line:

```markdown
--8<-- "conf/protection-note.md"
```

Line 57 (blank) and the `## Step 3: Start the Container` heading that followed stay
untouched. After the edit, line 58 is the directive and line 59 is the heading.

- [ ] **Step 4: Build and verify the HTML is byte-identical**

```bash
python3 -m mkdocs build -q -d /tmp/phase1-check
diff -r -I 'git-revision-date-localized-plugin-date' /tmp/phase1-baseline-site /tmp/phase1-check
```

Expected: `diff` reports **only** this one difference and nothing else:

```
Files /tmp/phase1-baseline-site/get-started/index.md and /tmp/phase1-check/get-started/index.md differ
```

The `.html` files must be identical — that proves snippets resolved correctly during
the build. The raw `.md` differs because the hook still copies the source verbatim,
so it now contains the unresolved `--8<--` directive. That is exactly the bug Task 2
fixes.

- [ ] **Step 5: Confirm the raw Markdown is currently broken, so Task 2 has a real red state**

```bash
grep -c '8<' /tmp/phase1-check/get-started/index.md
```

Expected: `1`. An unresolved snippet directive is being published. Record this — it is
the failing state Task 2 must clear.

- [ ] **Step 6: Verify `check_paths` actually fails on a bad path**

```bash
sed -i.bak 's|conf/protection-note.md|conf/does-not-exist.md|' docs/get-started/index.md
python3 -m mkdocs build -q -d /tmp/phase1-badpath 2>&1 | tail -5
```

Expected: the build fails with a `SnippetMissingError` naming `conf/does-not-exist.md`.
If it instead succeeds, `check_paths` is not in effect — go back to Step 1.

Restore the file:

```bash
mv docs/get-started/index.md.bak docs/get-started/index.md
```

- [ ] **Step 7: Commit**

```bash
git add mkdocs.yml includes/conf/protection-note.md docs/get-started/index.md
git commit -m "build: enable pymdownx.snippets with includes/ outside docs_dir"
```

---

## Task 2: Publish resolved Markdown instead of raw directives

**Files:**
- Modify: `hooks/copy_md_sources.py` (full rewrite, 30 lines → 48)

**Interfaces:**
- Consumes: `config["mdx_configs"]["pymdownx.snippets"]` — the extension config as
  MkDocs parsed it from `mkdocs.yml`, so `base_path` stays configured in exactly one
  place.
- Produces: `site/**/*.md` with all `--8<--` directives expanded. Every later phase
  relies on this; without it every include leaks into the public raw Markdown.

- [ ] **Step 1: Confirm the failing state**

```bash
grep -n '8<' /tmp/phase1-check/get-started/index.md
```

Expected: line 58 shows the unresolved directive. This is the red state.

- [ ] **Step 2: Rewrite the hook**

Replace the entire contents of `hooks/copy_md_sources.py` with:

```python
"""
MkDocs hook: after each build, copy every source .md file from docs/ into
site/ at the same relative path, with pymdownx.snippets includes resolved.

This makes raw Markdown available at predictable public URLs on the deployed
site (e.g. https://docs.actian.com/mcp-server/getting-started.md),
so they can be used by:
  - in-app docs browsers that need Markdown endpoints
  - users who want to copy-paste page content into Claude / ChatGPT

Includes are expanded with pymdownx.snippets' own preprocessor, configured from
mkdocs.yml, so the published Markdown matches what the HTML build rendered and
there is no second snippet-syntax implementation that can drift.
"""
import os

import markdown


def _snippet_preprocessor(config):
    """Build a snippets preprocessor from the project's own mkdocs.yml settings."""
    snippet_config = config["mdx_configs"].get("pymdownx.snippets", {})
    md = markdown.Markdown(
        extensions=["pymdownx.snippets"],
        extension_configs={"pymdownx.snippets": snippet_config},
    )
    return md.preprocessors["snippet"]


def on_post_build(config):
    docs_dir = config["docs_dir"]
    site_dir = config["site_dir"]
    # run() clears its own recursion state, so one instance serves every file.
    preprocessor = _snippet_preprocessor(config)

    for root, _dirs, files in os.walk(docs_dir):
        for filename in files:
            if not filename.endswith(".md"):
                continue

            src_path = os.path.join(root, filename)
            rel_path = os.path.relpath(src_path, docs_dir)
            dst_path = os.path.join(site_dir, rel_path)

            with open(src_path, encoding="utf-8") as handle:
                # split("\n") rather than splitlines() so the trailing newline
                # survives the join below and files without includes round-trip
                # byte-for-byte.
                lines = handle.read().split("\n")

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            with open(dst_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(preprocessor.run(lines)))
```

- [ ] **Step 3: Build and verify the raw Markdown is now fully resolved**

```bash
python3 -m mkdocs build -q -d /tmp/phase1-check2
grep -rn '8<' /tmp/phase1-check2 --include='*.md'
```

Expected: no output at all. Every directive was expanded.

- [ ] **Step 4: Verify the whole site is now byte-identical to the baseline**

This is the payoff step. The raw `.md` difference from Task 1 must now be gone,
because the hook reproduces the original text exactly.

```bash
diff -r -I 'git-revision-date-localized-plugin-date' /tmp/phase1-baseline-site /tmp/phase1-check2 && echo "IDENTICAL"
```

Expected: `IDENTICAL` with no preceding lines.

If `get-started/index.md` still differs, the cause is almost certainly whitespace
around the include. Inspect it with:

```bash
diff /tmp/phase1-baseline-site/get-started/index.md /tmp/phase1-check2/get-started/index.md
```

A single extra blank line means `includes/conf/protection-note.md` has a trailing
blank line beyond its single trailing newline; a missing blank line means the blank
line after the directive in `docs/get-started/index.md` was not removed in Task 1
Step 3.

- [ ] **Step 5: Verify files without includes round-trip untouched**

```bash
diff /tmp/phase1-baseline-site/ingres/index.md /tmp/phase1-check2/ingres/index.md && echo "round-trip clean"
```

Expected: `round-trip clean`. This proves the read/split/join path is lossless for the
33 pages that contain no directives.

- [ ] **Step 6: Commit**

```bash
git add hooks/copy_md_sources.py
git commit -m "fix: resolve snippet includes in published raw Markdown"
```

---

## Task 3: Install the redirects plugin with an empty map

The plugin is installed now so phases 4 and 6 only have to add map entries. It is
registered with no redirects, because a `redirect_maps` entry pointing at a page that
does not exist yet is invalid.

**Files:**
- Modify: `requirements.txt`
- Modify: `mkdocs.yml` (plugins block, after the `meta-descriptions` entry)

**Interfaces:**
- Produces: a registered `redirects` plugin. Phase 4 adds
  `'intro/write-support.md': 'write-support/index.md'`; phase 6 adds the three
  `nosql/authentication/**` entries.

- [ ] **Step 1: Add the dependency**

Append to `requirements.txt`:

```
mkdocs-redirects>=1.2
```

- [ ] **Step 2: Install it**

```bash
python3 -m pip install -r requirements.txt
```

Expected: `mkdocs-redirects` is installed. Confirm:

```bash
python3 -c "import mkdocs_redirects; print('ok')"
```

Expected: `ok`.

- [ ] **Step 3: Register the plugin**

In `mkdocs.yml`, add as the last entry of the `plugins:` list, after
`- meta-descriptions`:

```yaml
  - redirects:
      redirect_maps: {}
```

- [ ] **Step 4: Verify the site is still byte-identical**

```bash
python3 -m mkdocs build -q -d /tmp/phase1-check3
diff -r -I 'git-revision-date-localized-plugin-date' /tmp/phase1-baseline-site /tmp/phase1-check3 && echo "IDENTICAL"
```

Expected: `IDENTICAL`. An empty map must emit no files.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt mkdocs.yml
git commit -m "build: register mkdocs-redirects with an empty redirect map"
```

---

## Task 4: Authoring templates and the placeholder guard

**Files:**
- Create: `templates/README.md`
- Create: `templates/setup-sql-database.md.tmpl`
- Create: `templates/tools-sql-database.md.tmpl`
- Create: `templates/write-support.md.tmpl`
- Create: `templates/extensions.md.tmpl`
- Modify: `makefile`

**Interfaces:**
- Consumes: `includes/` from Task 1 — templates reference fragments that phases 2 and 3
  will create, listed in each template's header comment so the author knows what to
  add first.
- Produces: `make check-templates` and `make check-raw-md`. Phases 2–6 run both before
  committing.

- [ ] **Step 1: Write the authoring guide**

Create `templates/README.md`:

```markdown
# Page templates

Skeletons for pages that must exist once per database backend. They live outside
`docs/` so MkDocs never builds them and `hooks/copy_md_sources.py` never publishes
them.

Using one: copy it into place under `docs/`, drop the `.tmpl` suffix, then replace
every marker. `make check-templates` fails while any value or prose marker is left.

## Markers

| Marker | Meaning | May ship? |
|---|---|---|
| `{{DB_NAME}}`, `{{IMAGE}}`, `{{PORT}}`, `{{DB_SLUG}}`, `{{VARIANT_TITLE}}` | Substitute a value. Mechanical. | No |
| `<!-- TODO(fill): … -->` | Write prose. Needs product knowledge. | No |
| `<!-- STUB: pending product input -->` | Deliberately unfinished but published page. | Yes |

The split between `TODO(fill)` and `STUB` is the point. Published stubs are wanted, so
"unfinished" cannot be banned outright — but *accidentally* unfinished must be.
`make check-templates` rejects `{{` and `TODO(fill)`, and permits `STUB`.

## Marker values

| Marker | Ingres | HCL Informix | Zen | Analytics Engine | NoSQL |
|---|---|---|---|---|---|
| `{{DB_NAME}}` | Actian Ingres | HCL Informix® | Actian Zen | Actian Analytics Engine | Actian NoSQL |
| `{{DB_SLUG}}` | `ingres` | `hcl-informix` | `zen` | `analytics-engine` | `nosql` |
| `{{IMAGE}}` | `actian/ingres-mcp-server` | see note | `actian/zen-mcp-server` | `actian/analytics-engine-mcp-server` | `actian/nsql-mcp-server` |
| `{{PORT}}` | `8000` | `8000` | `8000` | `8000` | `8080` |

`{{VARIANT_TITLE}}` is used only by the two variant templates. Its values are
`SQL databases` and `Actian NoSQL`.

The Informix image is unresolved: the landing page and Get Started say
`actian/informix-mcp-server` from Docker Hub, while `docs/hcl-informix/index.md` says
`docker load -i ifx_mcp_image.tar` and `actian/informix-mcp-server-linux:1.0.0`. See
§11.4 of `specs/2026-08-05-docs-by-database-design.md`. Do not fill `{{IMAGE}}` for
Informix until that is settled.

## Shared fragments

Templates include fragments from `includes/`, addressed relative to it. Only
`conf/protection-note.md` exists after phase 1; phases 2 and 3 add the rest. Each
template lists the fragments it expects in a comment at the top.
```

- [ ] **Step 2: Write the SQL setup page template**

Create `templates/setup-sql-database.md.tmpl`:

```markdown
<!-- Template: SQL/ODBC setup page. Target: docs/{{DB_SLUG}}/index.md
     Expects includes (phase 2): conf/common-fields.md, conf/protection-note.md,
     docker/run-sql.md, docker/mount-path-note.md, verify-connection.md -->
---
title: {{DB_NAME}}
description: Use the Actian MCP Server to connect MCP clients to {{DB_NAME}}.
---

# Actian MCP Server for {{DB_NAME}}

<!-- TODO(fill): one paragraph. What the reader connects, what they can do once
     connected, and what the server handles for them. Keep to four sentences. -->

## Capabilities

<!-- TODO(fill): capability table. Engine-specific on purpose — do not copy another
     engine's table. One row per operation the server exposes for this engine. -->

| Action | Description |
| :--- | :--- |

## Prerequisites

<!-- TODO(fill): engine-specific prerequisites. Deliberately not shared: Informix
     mentions Podman, Zen needs --add-host, NoSQL needs no ODBC driver. -->

## Configuration

The server runs as a Docker container. To configure it, mount `conf.json` into the
container at `/app/conf.json`.

### Create the configuration file

<!-- TODO(fill): the conf.json example for this engine, with its connection fields. -->

### Configuration reference

**Required fields**

<!-- TODO(fill): only the connection fields specific to this engine. The fields shared
     across all SQL engines come from the include below — do not repeat them here. -->

| Field | Type | Description |
|-------|------|-------------|

**Optional fields**

--8<-- "conf/common-fields.md"

--8<-- "conf/protection-note.md"
## Start the server

--8<-- "docker/run-sql.md"

--8<-- "docker/mount-path-note.md"
## Verify the connection

--8<-- "verify-connection.md"
## Next steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  The MCP tools available for {{DB_NAME}}.

- :material-folder-open: **[Resources](resources/index.md)**  
  Schema metadata exposed as MCP resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Prompt templates for common workflows.

- :material-puzzle: **[Extensions](../extensions/index.md)**  
  Add your own tools with a Python extension.

</div>
```

- [ ] **Step 3: Write the SQL tools page template**

Create `templates/tools-sql-database.md.tmpl`:

```markdown
<!-- Template: SQL/ODBC tools page. Target: docs/{{DB_SLUG}}/tools/index.md
     Expects includes (phase 3): tools/execute-query-sql.md, tools/list-tables.md,
     tools/describe-table.md, tools/list-functions.md, tools/write-example-sql.md -->
---
title: Tools
description: MCP tools exposed by the Actian MCP Server for {{DB_NAME}}.
---

# {{DB_NAME}} tools

## Available tools

<!-- TODO(fill): summary table of the tools below, plus any engine-specific tools.
     Drop rows for tools this engine does not expose. -->

| Tool | Purpose |
|------|---------|

--8<-- "tools/execute-query-sql.md"

--8<-- "tools/write-example-sql.md"

--8<-- "tools/list-tables.md"

--8<-- "tools/describe-table.md"

--8<-- "tools/list-functions.md"

<!-- TODO(fill): engine-specific tools, written out in full. Zen adds orm_operation,
     blob_operation and database_manage. Other engines add nothing today.
     Delete this comment if the engine has no extra tools. -->

## Next steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Schema metadata exposed as MCP resources.

- :material-database-edit: **[Write support](../../write-support/index.md)**  
  How `query_mode`, the `mcp:write` scope, and write approval work.

</div>
```

- [ ] **Step 4: Write the write-support variant template**

Create `templates/write-support.md.tmpl`:

```markdown
<!-- Template: write-support variant page.
     Target: docs/write-support/index.md (SQL family) or docs/write-support/nosql.md
     Expects includes (phase 3): write/authorization-flow.md -->
---
title: {{VARIANT_TITLE}}
description: Enable data-modifying operations on the Actian MCP Server for {{VARIANT_TITLE}}.
---

# Write support for {{VARIANT_TITLE}}

<!-- TODO(fill): one paragraph. Off by default, what turns it on, and where that
     setting lives for this variant (conf.json vs application.properties). -->

## Enabling write mode

<!-- TODO(fill): the setting, its valid values, and a config example. -->

## How a write is authorized

--8<-- "write/authorization-flow.md"

## Skipping the approval prompt

<!-- TODO(fill): the setting that disables the prompt, plus a warning admonition
     covering what oversight is lost. -->

## Next steps

<!-- TODO(fill): grid cards linking the setup pages this variant applies to,
     authentication, and the MCP clients page for elicitation support. -->
```

- [ ] **Step 5: Write the extensions variant template**

Create `templates/extensions.md.tmpl`:

```markdown
<!-- Template: extensions variant page.
     Target: docs/extensions/index.md (SQL family) or docs/extensions/nosql.md -->
---
title: {{VARIANT_TITLE}}
description: Add your own tools, resources, and prompts to the Actian MCP Server for {{VARIANT_TITLE}}.
---

# Extensions for {{VARIANT_TITLE}}

<!-- TODO(fill): one paragraph. What an extension is, what language it is written in,
     and how it reaches the server. -->

## Write the module

<!-- TODO(fill): a minimal complete example, with the import path of the public API. -->

## Mount it and register it

<!-- TODO(fill): the mount path inside the container and the config entry that loads
     the module. -->

## What the server handles for you

<!-- TODO(fill): transport, auth, connection pooling, error mapping. -->

## Security controls that apply to your extension

<!-- TODO(fill): which controls are enforced regardless of extension code — write
     scope, user identity, approval prompts. -->

## Rules and gotchas

<!-- TODO(fill): what an extension must not do, and the failure modes authors hit. -->
```

- [ ] **Step 6: Add both guards to the `makefile`**

Append to `makefile`. The leading whitespace must be a **tab**, not spaces — make
rejects spaces with `missing separator`.

```make
check-templates:
	@! grep -rn -e '{{' -e 'TODO(fill)' docs/ --include='*.md' \
	  || (echo "Unfilled template placeholder in docs/" && exit 1)

# Guards against a missing site/ on purpose: grep exits non-zero on a missing
# directory, which the leading "!" would otherwise turn into a silent pass.
check-raw-md:
	@test -d site || (echo "site/ not built - run 'mkdocs build' first" && exit 1)
	@! grep -rn -e '--8<--' site/ --include='*.md' \
	  || (echo "Unresolved snippet include in published raw Markdown" && exit 1)
```

- [ ] **Step 7: Verify both guards pass on the current tree**

`check-raw-md` inspects `site/`, so build to the default output directory first:

```bash
python3 -m mkdocs build -q
make check-templates && echo "templates ok"
make check-raw-md && echo "raw md ok"
```

Expected: `templates ok` then `raw md ok`. `docs/` contains no `{{` and no `TODO`
today, and Task 2 made every published `.md` fully resolved.

- [ ] **Step 8: Verify `check-templates` actually catches a violation**

A guard that has never failed is not known to work.

```bash
printf '\n{{DB_NAME}}\n' >> docs/get-started/index.md
make check-templates; echo "exit: $?"
```

Expected: the offending line is printed, followed by
`Unfilled template placeholder in docs/` and `exit: 1`.

Undo the probe:

```bash
git checkout docs/get-started/index.md
make check-templates && echo "restored and passing"
```

Expected: `restored and passing`.

- [ ] **Step 9: Verify the templates are not published**

```bash
python3 -m mkdocs build -q -d /tmp/phase1-check4
find /tmp/phase1-check4 -name '*.tmpl' -o -name 'README.md' | grep -c . || echo "none published"
```

Expected: `none published`. `templates/` sits outside `docs_dir`, so neither MkDocs
nor the hook touches it.

- [ ] **Step 10: The phase gate — verify the site is still unchanged**

```bash
diff -r -I 'git-revision-date-localized-plugin-date' /tmp/phase1-baseline-site /tmp/phase1-check4 && echo "IDENTICAL"
```

Expected: `IDENTICAL`. This is the acceptance criterion for the whole
infrastructure half of phase 1. Do not proceed to Task 5 until it passes.

- [ ] **Step 11: Commit**

```bash
git add templates/ makefile
git commit -m "docs: add page templates and placeholder guards"
```

---

## Task 5: Make `--strict` a real gate and fix the anchors it exposes

MkDocs 1.6 reports broken anchors at `INFO` level, so `--strict` currently passes
while six links are broken. Promoting anchors to `warn` makes `--strict` meaningful
for every later phase — and immediately exposes the six.

This is the only task in phase 1 that changes rendered output.

**Files:**
- Modify: `mkdocs.yml` (new top-level `validation` block)
- Modify: `docs/ingres/index.md:94`
- Modify: `docs/hcl-informix/index.md:94`
- Modify: `docs/analytics-engine/index.md:94`
- Modify: `docs/authentication/index.md:154`
- Modify: `docs/authentication/auth0/index.md:322`
- Modify: `docs/mcp-clients/index.md:279`

**Interfaces:**
- Produces: `mkdocs build --strict` fails on any broken internal anchor. Phases 2–6
  rely on this as their link-integrity check.

- [ ] **Step 1: Enable anchor validation**

Add to `mkdocs.yml` as a new top-level block. Put it directly after the
`markdown_extensions:` block and before `# Copyright`:

```yaml
# Treat broken internal anchors as warnings so --strict fails on them.
validation:
  anchors: warn
```

- [ ] **Step 2: Run the strict build and watch it fail**

Do **not** pass `-q` here. It suppresses the warning lines, so the build still aborts
but gives no indication why.

```bash
python3 -m mkdocs build --strict -d /tmp/phase1-anchors 2>&1 | grep -E "WARNING|Aborted"
```

Expected: six `WARNING` lines followed by `Aborted with 6 warnings in strict mode!`
This is the red state. The six are:

| File:line | Broken anchor | Correct anchor |
|---|---|---|
| `docs/analytics-engine/index.md:94` | `#the-oauth-configuration-block` | `#configuring-oauth-block` |
| `docs/hcl-informix/index.md:94` | `#the-oauth-configuration-block` | `#configuring-oauth-block` |
| `docs/ingres/index.md:94` | `#the-oauth-configuration-block` | `#configuring-oauth-block` |
| `docs/authentication/index.md:154` | `#tls` | `#secure-remote-deployments-with-https-and-tls` |
| `docs/authentication/auth0/index.md:322` | `#https-tls-for-remote-deployments` | `#secure-remote-deployments-with-https-and-tls` |
| `docs/mcp-clients/index.md:279` | `#https-tls-for-remote-deployments` | `#secure-remote-deployments-with-https-and-tls` |

The correct anchors were read from the built HTML (`<h2 id="…">` in
`site/authentication/index.html`), not inferred from the heading text.

- [ ] **Step 3: Fix the three `oauth` block anchors**

All three occurrences are the same string in a table cell. Replace
`#the-oauth-configuration-block` with `#configuring-oauth-block`:

```bash
sed -i.bak 's|index.md#the-oauth-configuration-block|index.md#configuring-oauth-block|' \
  docs/ingres/index.md docs/hcl-informix/index.md docs/analytics-engine/index.md
rm -f docs/ingres/index.md.bak docs/hcl-informix/index.md.bak docs/analytics-engine/index.md.bak
```

Verify all three changed:

```bash
grep -rn 'configuring-oauth-block' docs --include='*.md'
```

Expected: three lines, one per file.

- [ ] **Step 4: Fix the two TLS anchors that point at `authentication/index.md`**

```bash
sed -i.bak 's|#https-tls-for-remote-deployments|#secure-remote-deployments-with-https-and-tls|' \
  docs/mcp-clients/index.md docs/authentication/auth0/index.md
rm -f docs/mcp-clients/index.md.bak docs/authentication/auth0/index.md.bak
```

- [ ] **Step 5: Fix the NoSQL TLS anchor**

In `docs/authentication/index.md:154`, change the link target from
`../nosql/authentication/index.md#tls` to
`../nosql/authentication/index.md#secure-remote-deployments-with-https-and-tls`.

The line reads:

```markdown
    The Actian MCP Server for NoSQL uses different configuration properties. See [NoSQL TLS guide](../nosql/authentication/index.md#tls) for more information.
```

Note for phase 6: this link's *target file* disappears when
`docs/nosql/authentication/` is merged away. Fixing the anchor now is still correct —
phase 6 will retarget the link, and until then it works.

- [ ] **Step 6: Run the strict build and watch it pass**

```bash
python3 -m mkdocs build --strict -d /tmp/phase1-anchors2 2>&1 | grep -E "WARNING|Aborted" ; echo "grep found nothing above = good"
```

Expected: no `WARNING` and no `Aborted` lines. The build completes.

- [ ] **Step 7: Confirm the only site changes are the six links**

```bash
diff -rq -I 'git-revision-date-localized-plugin-date' /tmp/phase1-baseline-site /tmp/phase1-anchors2
```

Expected: exactly twelve `differ` lines — the `.html` and the raw `.md` for each of the
six touched pages:

```
Files …/analytics-engine/index.html and …/analytics-engine/index.html differ
Files …/analytics-engine/index.md and …/analytics-engine/index.md differ
Files …/authentication/auth0/index.html … differ
Files …/authentication/auth0/index.md … differ
Files …/authentication/index.html … differ
Files …/authentication/index.md … differ
Files …/hcl-informix/index.html … differ
Files …/hcl-informix/index.md … differ
Files …/ingres/index.html … differ
Files …/ingres/index.md … differ
Files …/mcp-clients/index.html … differ
Files …/mcp-clients/index.md … differ
```

Any thirteenth difference means something unintended changed — investigate before
committing.

- [ ] **Step 8: Run both guards**

```bash
make check-templates && make check-raw-md && echo "guards ok"
```

Expected: `guards ok`.

- [ ] **Step 9: Commit**

```bash
git add mkdocs.yml docs/ingres/index.md docs/hcl-informix/index.md \
  docs/analytics-engine/index.md docs/authentication/index.md \
  docs/authentication/auth0/index.md docs/mcp-clients/index.md
git commit -m "fix: repair six broken doc anchors and fail strict builds on them"
```

- [ ] **Step 10: Clean up the baseline worktree**

```bash
git worktree remove /tmp/phase1-baseline
```

The built trees under `/tmp/phase1-*` can be left for the reviewer, or deleted.

---

## Phase 1 done — what phases 2–6 can now rely on

| Capability | How to use it |
|---|---|
| Shared fragments | Put the file in `includes/`, reference it as `--8<-- "path/relative/to/includes.md"` |
| Published raw Markdown stays correct | Automatic; `make check-raw-md` proves it |
| A build that fails on broken links and anchors | `python3 -m mkdocs build --strict` |
| A build that fails on unfilled templates | `make check-templates` |
| Page skeletons | `templates/*.md.tmpl`, marker reference in `templates/README.md` |
| Redirects | Add entries to `redirect_maps` in `mkdocs.yml` in the phase that moves the page |

**Not** delivered by phase 1, by design: any content change beyond the six anchor
fixes, and any of the four product questions in §11 of the spec. Those block phases 2
and 3 and need answering by the product side.
