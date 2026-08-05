# Phase 4: Promote Write Support and Add the NoSQL Stubs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal plan placed there would appear on docs.actian.com.

**Goal:** Give write support and extensions their NoSQL sibling pages, so the two topics
that have exactly two variants stop looking like SQL-only features with a warning
attached.

**Architecture:** Move `docs/intro/write-support.md` to `docs/write-support/index.md`,
which is a top-level section rather than a subpage of the introduction, and add
`docs/write-support/nosql.md` beside it. Add `docs/extensions/nosql.md` the same way.
Both new pages ship as published stubs carrying a shared "in progress" notice, because
their content needs product knowledge this repository does not hold (spec §11.7). One
redirect covers the moved page.

**Tech Stack:** MkDocs 1.6.1, mkdocs-material 9.6+, mkdocs-redirects 1.2+,
pymdown-extensions 10.21.2 (`pymdownx.snippets`), GNU make

## Global Constraints

- Phases 1–3 are prerequisites and are complete as of commit `07f6205`.
- Verification after every task, all three must pass:
  ```bash
  python3 -m mkdocs build --strict     # no -q: it suppresses the warnings
  make check-templates
  python3 -m mkdocs build -q && make check-raw-md
  ```
- **The stubs must pass `make check-templates`.** That guard rejects `{{...}}` and
  `TODO(fill)` but permits `<!-- STUB: pending product input -->`. So a stub is **not**
  a filled-in template — the templates in `templates/` are for when content arrives.
  A stub is a minimal published page carrying the shared notice.
- **A stub must not claim what is not established.** Spec §11.7 is open: the NoSQL write
  semantics and extension API are unknown here. The stubs say documentation is being
  written and point at what does exist. They do not describe behaviour, and they do not
  include `includes/write/authorization-flow.md`, which describes the SQL flow.
- Row-fragment includes have **no trailing newline**; section and block includes keep
  theirs. `stub-notice.md` is a block include and keeps its newline.
- Relative links inside an include resolve from the **including page's** location, so the
  two includes referencing write support sit at different depths:
  `includes/conf/write-fields.md` at depth 1 (`../`) and
  `includes/tools/execute-query-sql.md` at depth 2 (`../../`). Both are correct today and
  both are handled by the single substitution in Task 1 Step 4 — substitute the tail of
  the path, never prepend to it.
- `mkdocs-redirects` generates a redirect at the **source** path, so
  `docs/intro/write-support.md` must be deleted, not left in place, or the real page and
  the redirect collide.
- Accepted limitation, already recorded in spec §9.1: the raw Markdown at the old address
  (`…/intro/write-support.md`) will 404 after the move, while
  `…/intro/write-support.html` redirects correctly. `copy_md_sources.py` walks
  `docs_dir`, so it cannot publish a file that no longer exists there.

## Correction to the phase 3 plan

Phase 3 deferred `includes/write/authorization-flow.md` with the reason "phase 4 gives it
a second consumer (`write-support/nosql.md`)". That reason is wrong.
`write-support/nosql.md` is a stub, and NoSQL's authorization behaviour is unknown
(§11.7) — a stub must not include a description of the SQL flow. The extraction stays
deferred until NoSQL write content is actually written. Until then the flow has one
consumer and stays inline, per the same no-premature-abstraction reasoning.

## The 17 references that must move

Measured, so no step has to rediscover them:

| Location | Current | Becomes |
|---|---|---|
| `docs/get-started/index.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/ingres/index.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/hcl-informix/index.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/zen/index.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/analytics-engine/index.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/authentication/index.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/authentication/keycloak/index.md` | `../../intro/write-support.md` — already correct for depth 2 | `../../write-support/index.md` |
| `docs/authentication/auth0/index.md` | `../../intro/write-support.md` — already correct for depth 2 | `../../write-support/index.md` |
| `docs/extensions/index.md` ×2 | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/extensions/examples.md` | `../intro/write-support.md` | `../write-support/index.md` |
| `docs/mcp-clients/index.md` | `../intro/write-support.md#skipping-the-approval-prompt` | `../write-support/index.md#skipping-the-approval-prompt` |
| `docs/index.md` ×2 | `./intro/write-support.html` | `./write-support/index.html` — raw HTML, not Markdown |
| `includes/conf/write-fields.md` ×2 | `../intro/write-support.md` | `../write-support/index.md` |
| `includes/tools/execute-query-sql.md` | `../../intro/write-support.md` | `../../write-support/index.md` |

All 15 Markdown references take **one** substitution, whatever their depth. The pattern
`../intro/write-support.md` is a substring of `../../intro/write-support.md`, so replacing
it with `../write-support/index.md` leaves the extra `../` in place and yields
`../../write-support/index.md` — correct for depth 2. Verified against all three depth-2
references (`authentication/auth0`, `authentication/keycloak`,
`includes/tools/execute-query-sql.md`), which are already correct today; none of them is
broken. Only the two landing-page links need their own substitution, because they are raw
HTML with `.html` targets.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `docs/write-support/index.md` | Write support for the SQL engines — the moved page | 1 |
| `docs/write-support/.pages` | Section title and page order | 1 |
| `docs/intro/.pages` | Loses `write-support.md`, keeps only `index.md` | 1 |
| `docs/.pages` | Gains `write-support` between `authentication` and `extensions` | 1 |
| `mkdocs.yml` | One `redirect_maps` entry for the moved page | 1 |
| `includes/stub-notice.md` | The shared "documentation in progress" admonition | 2 |
| `docs/write-support/nosql.md` | Published stub | 2 |
| `docs/extensions/nosql.md` | Published stub; replaces the admonition in `nosql/index.md` | 2 |
| `docs/extensions/.pages` | Gains `nosql.md` | 2 |
| `docs/nosql/index.md` | Its "documentation not yet available" admonition becomes a link | 2 |
| `specs/2026-08-05-docs-by-database-design.md` | Records the phase-3 correction and the state | 3 |

---

## Task 0: Capture the baseline

**Files:** none

**Interfaces:**
- Produces `/tmp/phase4-baseline-site` and a recorded reference count, so Task 1 can
  prove no link was missed.

- [ ] **Step 1: Confirm phase 3 is in place and the tree is clean**

```bash
git status --short
ls includes/tools/write-example-sql.md includes/conf/max-rows-capped.md
```

Expected: `git status` shows nothing except possibly `theme_overrides/.DS_Store`, which
is a macOS Finder artefact and not part of this work — leave it alone. Both files listed.

- [ ] **Step 2: Build the baseline**

```bash
python3 -m mkdocs build -q -d /tmp/phase4-baseline-site
```

- [ ] **Step 3: Record the reference count**

```bash
grep -rc 'intro/write-support' docs/ includes/ 2>/dev/null | grep -v ':0$' | sort
grep -rn 'intro/write-support' docs/ includes/ | wc -l
```

Expected: `17` from the second command. Task 1 must end with `0`.

---

## Task 1: Move write support into its own section

**Files:**
- Create: `docs/write-support/index.md` (moved from `docs/intro/write-support.md`)
- Create: `docs/write-support/.pages`
- Delete: `docs/intro/write-support.md`
- Modify: `docs/intro/.pages`
- Modify: `docs/.pages`
- Modify: `mkdocs.yml` (`redirect_maps`)
- Modify: the 14 files listed in the reference table above

**Interfaces:**
- Produces `docs/write-support/index.md`, whose anchors other pages depend on. Two are
  linked from elsewhere and must survive the move: `#skipping-the-approval-prompt`
  (from `mcp-clients/index.md` and `includes/conf/write-fields.md`) and the page root.
- Both old and new locations sit one level below `docs/`, so the moved page's **own**
  outbound links (`../ingres/tools/index.md` and friends) stay correct unchanged.

- [ ] **Step 1: Move the file with git, so history follows**

```bash
mkdir -p docs/write-support
git mv docs/intro/write-support.md docs/write-support/index.md
```

- [ ] **Step 2: Verify the moved page's own links still resolve**

The move keeps the page at depth 1, so its `../` links are unchanged. Confirm nothing
needs editing inside the file:

```bash
grep -on '](\.\.[^)]*' docs/write-support/index.md
```

Expected: links like `](../ingres/tools/index.md`, `](../authentication/index.md`,
`](../get-started/index.md#which-database-do-you-have`. All still correct from
`docs/write-support/`. Do not edit them.

- [ ] **Step 3: Record the three reference classes**

One substitution covers both Markdown depths; only the landing page differs. Confirm the
counts before changing anything, so Step 7 has something to compare against:

```bash
grep -rEc '\.\./\.\./intro/write-support\.md' docs/ includes/ | grep -v ':0$'
grep -rEno '\./intro/write-support\.html' docs/ | wc -l
grep -rn 'intro/write-support' docs/ includes/ | wc -l
```

Expected: three files matching the depth-2 pattern
(`docs/authentication/auth0/index.md`, `docs/authentication/keycloak/index.md`,
`includes/tools/execute-query-sql.md`), `2` landing-page HTML links, and `17` in total.
All three depth-2 references are already correct — none is broken.

- [ ] **Step 4: Rewrite all 15 Markdown references with one substitution**

```bash
grep -rl 'intro/write-support\.md' docs/ includes/ | while read -r f; do
  sed -i.bak 's|\.\./intro/write-support\.md|../write-support/index.md|g' "$f"
done
find docs includes -name '*.bak' -delete
```

The depth-2 references keep their leading `../` and become `../../write-support/index.md`
automatically, because the replaced text is a substring. Confirm that happened rather than
assuming it:

```bash
grep -rn 'write-support/index.md' docs/authentication/auth0/index.md \
  docs/authentication/keycloak/index.md includes/tools/execute-query-sql.md
```

Expected: `../../write-support/index.md` in all three, not `../write-support/index.md`.

- [ ] **Step 5: Confirm no Markdown reference was missed**

```bash
grep -rn 'intro/write-support\.md' docs/ includes/; echo "(empty above = good)"
```

Expected: no output. The two landing-page `.html` links remain and are handled next.

- [ ] **Step 6: Rewrite the two landing-page HTML links**

`docs/index.md` uses raw HTML with `.html` targets, not Markdown links, so the sed above
did not touch them:

```bash
sed -i.bak 's|\./intro/write-support\.html|./write-support/index.html|g' docs/index.md
rm -f docs/index.md.bak
grep -c 'write-support/index.html' docs/index.md
```

Expected: `2`.

- [ ] **Step 7: Verify every reference moved**

```bash
grep -rn 'intro/write-support' docs/ includes/; echo "(empty above = good)"
grep -rn 'write-support/index' docs/ includes/ | wc -l
```

Expected: no output from the first, and `17` from the second — the same count Task 0
recorded.

- [ ] **Step 8: Create the section's `.pages`**

`docs/write-support/.pages`:

```yaml
title: Write Support
nav:
  - index.md
  - nosql.md
```

`nosql.md` does not exist yet; Task 2 creates it. `awesome-pages` warns about a missing
nav entry, and `--strict` turns warnings into failures, so **add the `nosql.md` line in
Task 2, not here**. For now:

```yaml
title: Write Support
nav:
  - index.md
```

- [ ] **Step 9: Remove the page from the introduction's nav**

`docs/intro/.pages` becomes:

```yaml
title: Introduction
nav:
  - index.md
```

- [ ] **Step 10: Add the section to the top-level nav**

In `docs/.pages`, insert `write-support` between `authentication` and `extensions`,
matching the relative order in the spec's target structure. Phase 5 does the full
reorder; this is only the insertion:

```yaml
title: Actian MCP Server
nav:
  - index.md
  - intro
  - get-started
  - mcp-clients
  - authentication
  - write-support
  - extensions
  - ingres
  - hcl-informix
  - zen
  - nosql
  - analytics-engine
```

- [ ] **Step 11: Add the redirect**

In `mkdocs.yml`, the `redirects` plugin currently has an empty map. Fill it:

```yaml
  - redirects:
      redirect_maps:
        'intro/write-support.md': 'write-support/index.md'
```

- [ ] **Step 12: Verify the redirect is generated and points at the right place**

```bash
python3 -m mkdocs build -q -d /tmp/phase4-t1
ls /tmp/phase4-t1/intro/write-support.html
grep -o 'url=[^"]*' /tmp/phase4-t1/intro/write-support.html
```

Expected: the file exists and the meta-refresh URL points at the new page. This is the
first redirect in the project, so also confirm the real page is there:

```bash
ls /tmp/phase4-t1/write-support/index.html /tmp/phase4-t1/write-support/index.md
```

- [ ] **Step 13: Confirm the accepted raw-Markdown limitation**

```bash
ls /tmp/phase4-t1/intro/write-support.md 2>&1 | tail -1
```

Expected: "No such file or directory". This is the limitation recorded in spec §9.1, not
a defect: `copy_md_sources.py` walks `docs_dir` and the source no longer lives there. The
`.html` redirect covers browser and search-engine traffic.

- [ ] **Step 14: Run the gates**

`--strict` is the real test here — it validates all 17 rewritten links plus the two
anchors that had to survive the move.

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
```

Expected: no warnings. If one names `#skipping-the-approval-prompt`, the heading did not
survive the move — check `docs/write-support/index.md`.

- [ ] **Step 15: Commit**

```bash
git add -A docs/ includes/ mkdocs.yml
git commit -m "docs: promote write support to its own top-level section"
```

---

## Task 2: Add the two NoSQL stubs

**Files:**
- Create: `includes/stub-notice.md`
- Create: `docs/write-support/nosql.md`
- Create: `docs/extensions/nosql.md`
- Modify: `docs/write-support/.pages`
- Modify: `docs/extensions/.pages`
- Modify: `docs/nosql/index.md` (the extensions admonition at roughly line 20)

**Interfaces:**
- Produces `includes/stub-notice.md`, a block include with two consumers, so both stubs
  present "in progress" identically. It keeps its trailing newline — it is a block, not a
  table row.
- Produces `docs/extensions/nosql.md`, which `docs/nosql/index.md` links to instead of
  saying documentation does not exist.

- [ ] **Step 1: Create the shared notice**

`includes/stub-notice.md`:

```markdown
!!! info "Documentation in progress"
    This page is a placeholder. The feature exists, but its documentation is still being written. For details in the meantime, contact [Actian support](https://www.actian.com/contact/).
```

The wording is deliberately narrow: it states the feature exists and the documentation
does not, which is all that is established (spec §11.7). It does not describe behaviour.

- [ ] **Step 2: Create the write-support stub**

`docs/write-support/nosql.md`:

```markdown
---
title: Actian NoSQL
description: Write support on the Actian MCP Server for Actian NoSQL.
---

# Write support for Actian NoSQL

<!-- STUB: pending product input -->

--8<-- "stub-notice.md"

Actian NoSQL is a separate implementation from the four SQL engines: it is configured
through `application.properties` rather than `conf.json`, and it queries with JPQL rather
than SQL. Its write behaviour is therefore documented here rather than on the
[write support](index.md) page, which covers the SQL engines only.

For the capabilities documented today, see [NoSQL tools](../nosql/tools/index.md).
```

Note what this does **not** say: nothing about `query_mode`, the `mcp:write` scope, or
approval prompts. Those are the SQL semantics; whether NoSQL matches them is §11.7.

- [ ] **Step 3: Create the extensions stub**

`docs/extensions/nosql.md`:

```markdown
---
title: Actian NoSQL
description: Extensions for the Actian MCP Server for Actian NoSQL.
---

# Extensions for Actian NoSQL

<!-- STUB: pending product input -->

--8<-- "stub-notice.md"

Actian NoSQL supports extensions through a different interface from the SQL engines, with
its own API and its own examples. The [extensions guide](index.md) and its
[API reference](api-reference.md) describe the Python interface used by Ingres, HCL
Informix®, Zen and Analytics Engine, and do not apply to NoSQL.

For the capabilities documented today, see [NoSQL tools](../nosql/tools/index.md).
```

- [ ] **Step 4: Add both pages to their sections' nav**

`docs/write-support/.pages`:

```yaml
title: Write Support
nav:
  - index.md
  - nosql.md
```

`docs/extensions/.pages`:

```yaml
title: Extensions
nav:
  - index.md
  - examples.md
  - api-reference.md
  - nosql.md
```

- [ ] **Step 5: Turn the NoSQL admonition into a link**

`docs/nosql/index.md` currently says, at roughly line 20:

```markdown
!!! note "Extensions for NoSQL"
    NoSQL supports extensions, but through a different interface with its own API and examples. Documentation for it is not yet available. The [Extensions](../extensions/index.md) guide covers the other databases and does not apply here.
```

This is one of the three admonitions the whole restructure exists to remove — it tells a
reader what they cannot have. Replace it with a pointer to the page that now holds the
topic:

```markdown
!!! note "Extensions for NoSQL"
    NoSQL supports extensions through a different interface from the SQL engines. See [Extensions for Actian NoSQL](../extensions/nosql.md).
```

- [ ] **Step 6: Verify both stubs are published and carry the notice**

```bash
python3 -m mkdocs build -q -d /tmp/phase4-t2
for p in write-support/nosql extensions/nosql; do
  printf "%-24s html=%s notice=%s\n" "$p" \
    "$(ls /tmp/phase4-t2/$p.html >/dev/null 2>&1 && echo yes || echo NO)" \
    "$(grep -c 'Documentation in progress' /tmp/phase4-t2/$p.html)"
done
```

Expected: `html=yes notice=1` on both lines.

- [ ] **Step 7: Verify the stubs pass the placeholder guard**

This is the distinction the guard exists for: `STUB` is allowed, `{{` and `TODO(fill)`
are not.

```bash
grep -c 'STUB: pending product input' docs/write-support/nosql.md docs/extensions/nosql.md
make check-templates && echo "guard passes with STUB markers present"
```

Expected: `1` for each file, then the confirmation line.

- [ ] **Step 8: Verify the "not available" admonition is gone**

```bash
grep -n 'not yet available' docs/nosql/index.md; echo "(empty above = good)"
grep -c 'extensions/nosql.md' docs/nosql/index.md
```

Expected: no output from the first, `1` from the second.

- [ ] **Step 9: Verify both stubs appear in the navigation**

A published stub that is not reachable from the nav is not published in any useful sense.

```bash
grep -c 'write-support/nosql.html' /tmp/phase4-t2/write-support/index.html
grep -c 'extensions/nosql.html' /tmp/phase4-t2/extensions/index.html
```

Expected: non-zero on both — Material renders the section's sibling pages in the sidebar
of every page in that section.

- [ ] **Step 10: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add includes/stub-notice.md docs/write-support/ docs/extensions/ docs/nosql/index.md
git commit -m "docs: add published NoSQL stubs for write support and extensions"
```

---

## Task 3: Record the state and the phase 3 correction

**Files:**
- Modify: `specs/2026-08-05-docs-by-database-design.md`
- Modify: `plans/2026-08-05-phase-3-tools-dedup-and-write-parity.md`

**Interfaces:**
- Produces a spec whose §6 content mapping, §7.1 include inventory and §11 open
  questions match what now exists.

- [ ] **Step 1: Correct the phase 3 plan's deferral reason**

In `plans/2026-08-05-phase-3-tools-dedup-and-write-parity.md`, the deferred table says
`includes/write/authorization-flow.md` unblocks when "Phase 4 gives it a second consumer
(`write-support/nosql.md`)". Replace that cell with:

```markdown
| `includes/write/authorization-flow.md` | It would have exactly one consumer today (`intro/write-support.md`). Extracting a fragment for a single caller is premature. | NoSQL write content is written. Phase 4 does **not** unblock it: `write-support/nosql.md` ships as a stub, and NoSQL's authorization behaviour is unknown (§11.7), so a stub must not include the SQL flow. |
```

- [ ] **Step 2: Update the spec's content mapping**

In §6, the `intro/write-support.md` row says "Promoted, because it needs a NoSQL
sibling. Redirect needed." Mark it done and record the side effect:

```markdown
| `intro/write-support.md` | `write-support/index.md` | **Done (phase 4).** Promoted; 17 references rewritten and one redirect added. All 15 Markdown references took one substitution regardless of depth — see §7.4. |
```

- [ ] **Step 3: Record that the stubs exist**

Add to §11.7, so it is clear the question now blocks content rather than structure:

```markdown
   The two stub pages exist as of phase 4 (`docs/write-support/nosql.md` and
   `docs/extensions/nosql.md`), each carrying `includes/stub-notice.md`. They state that
   the feature exists and the documentation does not, and describe no behaviour. Answering
   this question fills them; it no longer blocks any structural work.
```

- [ ] **Step 4: Note the substring property in §7.4**

Relative depth has been the recurring hazard in this restructure, and this phase found a
useful property worth recording rather than rediscovering. Add to §7.4:

```markdown
When a page moves between two locations at the same depth, one substitution handles
referring pages at **every** depth: `../intro/x.md` is a substring of `../../intro/x.md`,
so replacing it leaves the extra `../` in place. Phase 4 moved write support with a single
sed across 15 references at two depths. The counterexample is phase 3, which
over-applied a `../` to `../../` transformation to a file that was already at depth 2 and
produced `../../../`. Substitute the *tail* of the path, never prepend to it.
```

- [ ] **Step 5: Commit**

```bash
git add specs/ plans/
git commit -m "docs: record phase 4 state and correct the phase 3 deferral reason"
```

---

## Phase 4 done — state afterwards

| Topic | SQL page | NoSQL page |
|---|---|---|
| Write support | `write-support/index.md` | `write-support/nosql.md` — stub |
| Extensions | `extensions/index.md` | `extensions/nosql.md` — stub |

Both topics now have exactly the two variants the spec's goal 5 calls for. All three
NoSQL admonitions the restructure set out to remove are gone: the two in `get-started/`
went in phase 2, and the extensions one becomes a link here.

Still open: NoSQL write and extension content (§11.7 — now content-only, no longer
structural), Zen's worked write example (§11.8), and Zen TLS support. Phase 5 remains
(extract the Python client, reorder the nav) and phase 6 (merge the authentication
subtree), which is the riskiest step and still last.
