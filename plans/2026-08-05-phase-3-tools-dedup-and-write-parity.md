# Phase 3: Deduplicate the Tools Pages and Close the Write Gap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal plan placed there would appear on docs.actian.com.

**Goal:** Author each shared tool description once, and make the documentation say what
the product actually does: write support exists on all four SQL engines, not just Ingres
and Analytics Engine.

**Architecture:** Measurement (below) shows the four SQL engines split two ways, not
four: Ingres, Informix and Analytics Engine return structurally identical responses for
every tool, while Zen returns a different, richer shape and has no `list_functions`. So
the tool includes have three consumers, and Zen keeps its own descriptions — the same
pattern `conf/tls-fields.md` already follows. Separately, the §11.1 answer makes write
support a documented feature of all four engines, which touches capabilities tables,
config tables, the tools pages and `write-support.md`.

**Tech Stack:** MkDocs 1.6.1, mkdocs-material 9.6+, pymdown-extensions 10.21.2
(`pymdownx.snippets`), GNU make

## Global Constraints

- Phases 1 and 2 are prerequisites and are complete as of commit `177299e`.
- **This phase changes rendered output** and adds statements that were previously
  missing. Every added statement is derived from an answered question in spec §11 or
  from a structurally identical sibling page — never invented.
- Verification after every task, all three must pass:
  ```bash
  python3 -m mkdocs build --strict     # no -q: it suppresses the warnings
  make check-templates
  python3 -m mkdocs build -q && make check-raw-md
  ```
- Row-fragment includes (those continuing a table the page opened) must have **no
  trailing newline**. Section-level includes keep theirs. Phase 2 learned this the hard
  way: a trailing newline renders as a blank line, ends the table, and every later
  include becomes literal pipes in a paragraph — while the table *count* stays correct,
  so check for `^<p>| ` in the rendered HTML, not table counts.
- Include paths are relative to `includes/`. Relative links inside an include resolve
  from the **including page's** location. The tool includes are consumed only from
  `docs/<db>/tools/index.md` — depth 2 — so links in them need `../../`, not `../`.
  This is the first phase with depth-2 consumers; every existing include is depth 1.
- Answered questions this phase acts on (spec §11):
  - §11.1 — Zen and Informix use **identical** write semantics (`query_mode`,
    `mcp:write`, `write_confirmation`) to Ingres and Analytics Engine.
  - §11.2 — Zen genuinely has **no** `list_functions`.
  - §11.5 — image tag is `1.1.0` everywhere (already applied in `177299e`).

## Measured: the engines split two ways, not four

The spec (§7.1) assumed `execute_query`, `list_tables`, `describe_table` and
`list_functions` were shareable across all four SQL pages. They are not, and the
grouping is not what the spec implied. Parsing every `Output Schema` JSON block and
comparing key structures:

| Tool | Ingres | Informix | Analytics Engine | Zen |
|---|---|---|---|---|
| `execute_query` | `success` `columns` `rows` `row_count` `truncated` `warning` `error` | identical | identical | `method` `original_sql` `translated` `translation_note` `results[].column` `row_count` `truncated` `truncation_note` |
| `list_tables` | `success` `columns` `rows` `row_count` `error` | identical | identical | `tables` `count` |
| `describe_table` | `success` `columns` `rows` `row_count` `error` | identical | identical | `table_name` `columns[].name/type/nullable/default/precision/scale/primary_key` `primary_keys` `foreign_keys` |
| `list_functions` | `success` `columns` `rows` `row_count` `error` | identical | identical | **absent** |

So:

- **Ingres, Informix, Analytics Engine are structurally identical for all four tools.**
  Their textual differences are wording, indentation (tabs versus spaces) and
  placeholder convention (`"row_count": 1` versus `"row_count": "<num_rows>"`). Those
  are editorial and get harmonized here.
- **Zen differs structurally for all three tools it has**, consistent with the dialect
  translation and ORM tooling its own page describes. Zen keeps its tool descriptions
  written out and consumes no tool include.

Two further measurements that shape the includes:

- The `Example` subsections of `execute_query` (all three use a `customers` table) and
  `list_tables` (no table name at all) are shareable as-is.
- The `Example` of `describe_table` is **not**: Ingres and Analytics Engine describe
  `ii_tables`, an Ingres system catalog, while Informix describes `table`. Task 2
  harmonizes this to `customers`, matching the demo table the rest of the page already
  uses, which makes the example engine-neutral and internally consistent.

## Deferred: what this phase deliberately does not do

| Deferred | Why | Unblocks when |
|---|---|---|
| **Zen's write example** | Zen's `execute_query` returns a different response shape, so the write response cannot be copied from Ingres. Writing one would mean inventing the payload. | Someone supplies Zen's actual `execute_query` response for an `INSERT`/`UPDATE`/`DELETE` |
| Moving `max_rows` into `conf/common-optional-fields.md` | Spec §11.6: Ingres documents `1000` as a hard cap, the other three as a default. Unresolved. | §11.6 is answered |
| `conf/tls-fields.md` reaching a fourth consumer | Whether Zen supports `ssl_certfile` / `ssl_keyfile` is unestablished | That question is answered |
| `includes/write/authorization-flow.md` | It would have exactly one consumer today (`intro/write-support.md`). Extracting a fragment for a single caller is premature. | Phase 4 gives it a second consumer (`write-support/nosql.md`) |

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `includes/tools/execute-query-sql.md` | Parameters, output schema and read example, for the three structurally identical engines | 1 |
| `includes/tools/list-tables.md` | Same, for `list_tables` | 1 |
| `includes/tools/describe-table.md` | Same, for `describe_table`, with the harmonized `customers` example | 2 |
| `includes/tools/list-functions.md` | Same, for `list_functions` | 1 |
| `includes/tools/write-example-sql.md` | The write example and write-error table, for the three engines | 3 |
| `docs/ingres/tools/index.md` | Reference tools page — the include content is taken from here | 1, 2, 3 |
| `docs/hcl-informix/tools/index.md` | Consumer; gains the write example and the owner example | 1, 2, 3 |
| `docs/analytics-engine/tools/index.md` | Consumer | 1, 2, 3 |
| `docs/zen/tools/index.md` | Consumes no tool include; gets the wording fix only | 4 |
| `docs/hcl-informix/index.md` | Capabilities table gains write; config table gains `conf/write-fields.md` | 4 |
| `docs/zen/index.md` | Same | 4 |
| `docs/intro/write-support.md` | Stops presenting write as an Ingres and Analytics Engine feature | 5 |

---

## Task 0: Capture the baseline

**Files:** none

**Interfaces:**
- Produces: `/tmp/phase3-baseline-site`, the rendered site before any phase 3 change.

- [ ] **Step 1: Confirm phases 1–2 are in place and the tree is clean**

```bash
git status --short
ls includes/conf/write-fields.md includes/verify-connection.md
grep -c '1.1.0' docs/ingres/index.md
```

Expected: no output from `git status`, both files listed, `1` from the grep. If any
fails, stop — an earlier phase is incomplete.

- [ ] **Step 2: Build the baseline**

```bash
python3 -m mkdocs build -q -d /tmp/phase3-baseline-site
```

Expected: a Material for MkDocs banner on stderr, nothing else.

- [ ] **Step 3: Record the current write-support footprint**

This is the gap the phase closes; capture it so the change is demonstrable.

```bash
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s capabilities-write=%s query_mode=%s write-example=%s\n" "$p" \
    "$(grep -ci 'write' docs/$p/index.md | head -1)" \
    "$(grep -c 'write-fields' docs/$p/index.md)" \
    "$(grep -c 'Writing a Row' docs/$p/tools/index.md)"
done
```

Expected today: Ingres and Analytics Engine show `write-fields=1` and
`write-example=1`; Informix and Zen show `0` and `0`.

---

## Task 1: Share the three tools that need no example change

`execute_query`, `list_tables` and `list_functions` have shareable examples as they
stand. `describe_table` needs its example harmonized first and is handled in Task 2.

**Files:**
- Create: `includes/tools/execute-query-sql.md`
- Create: `includes/tools/list-tables.md`
- Create: `includes/tools/list-functions.md`
- Modify: `docs/ingres/tools/index.md`
- Modify: `docs/hcl-informix/tools/index.md`
- Modify: `docs/analytics-engine/tools/index.md`

**Interfaces:**
- Produces three section-body includes. Each contains the `### Parameters`,
  `### Output Schema` and `### Example` subsections for one tool — but **not** the
  `## <tool_name>` heading, which the consuming page supplies, and **not** the write
  subsections, which Task 3 handles separately so Zen-less engines can opt in.
- Each keeps its trailing newline: these are section bodies, not row fragments.

- [ ] **Step 1: Extract the Ingres version as the canonical text**

Ingres is the reference because its page is the one the other two drifted from. Copy the
body of `## execute_query` from `docs/ingres/tools/index.md` — the `### Parameters`,
`### Output Schema` and `### Example` subsections only, stopping before
`### Example: Writing a Row` — into `includes/tools/execute-query-sql.md`.

Apply three harmonizations while copying:

1. Indent JSON with **two spaces**, not tabs. Ingres uses tabs; Informix and Analytics
   Engine use spaces, so spaces win two to one and match every other code block in the
   docs.
2. Use `"<placeholder>"` style for values that vary, so `"row_count": 1` becomes
   `"row_count": "<num_rows>"`. Analytics Engine already does this; it reads as a schema
   rather than as one particular response.
3. Any link must use `../../`, not `../` — the consumers are at depth 2
   (`docs/<db>/tools/index.md`). Check the copied text for `](../` and fix.

- [ ] **Step 2: Extract `list_tables` the same way**

Copy the body of `## list_tables` from `docs/ingres/tools/index.md` into
`includes/tools/list-tables.md`, applying the same three harmonizations. The
`### Parameters` text becomes the wording used by two of the three pages:

```markdown
### Parameters

This tool takes no input parameters.
```

Ingres says "This tool does not require input parameters" and Informix says "This
**resource** does not require any input parameters" — the latter calls a tool a
resource, which is simply wrong. Both are replaced.

- [ ] **Step 3: Extract `list_functions` the same way**

Copy the body of `## list_functions` from `docs/ingres/tools/index.md` into
`includes/tools/list-functions.md`, same harmonizations, same `### Parameters` wording
as Step 2.

- [ ] **Step 4: Rewire the Ingres page**

In `docs/ingres/tools/index.md`, replace the body of each of the three tool sections
with its include, keeping the `## <tool>` heading. For `execute_query`, keep
`### Example: Writing a Row` and `### Write Errors` in place after the include — Task 3
extracts those:

```markdown
## execute_query

--8<-- "tools/execute-query-sql.md"

### Example: Writing a Row
```

- [ ] **Step 5: Rewire the Informix page**

Same three replacements in `docs/hcl-informix/tools/index.md`. Informix has no write
subsections yet, so `## execute_query` becomes exactly:

```markdown
## execute_query

--8<-- "tools/execute-query-sql.md"
```

- [ ] **Step 6: Rewire the Analytics Engine page**

Same three replacements in `docs/analytics-engine/tools/index.md`, keeping its
`### Example: Writing a Row` and `### Write Errors` after the `execute_query` include,
as on Ingres.

- [ ] **Step 7: Verify the three pages render the same schema**

The point of the include is that these three now agree by construction. Prove it by
comparing the parsed key sets, not the text:

```bash
python3 -m mkdocs build -q -d /tmp/phase3-t1
for p in ingres hcl-informix analytics-engine; do
  printf "%-18s " "$p"
  grep -o '"row_count"\|"truncated"\|"warning"\|"columns"\|"rows"\|"success"\|"error"' \
    /tmp/phase3-t1/$p/tools/index.html | sort -u | tr '\n' ' '; echo
done
```

Expected: the same seven quoted keys on all three lines.

- [ ] **Step 8: Verify Zen was not touched**

Zen must keep its own descriptions — it is structurally different.

```bash
diff -q /tmp/phase3-baseline-site/zen/tools/index.html /tmp/phase3-t1/zen/tools/index.html \
  && echo "Zen unchanged"
grep -c 'original_sql\|translation_note' /tmp/phase3-t1/zen/tools/index.html
```

Expected: `Zen unchanged`, and a non-zero count proving Zen's own schema survived.

- [ ] **Step 9: Verify no include leaked a depth-1 link**

```bash
grep -n '](\.\./[a-z]' includes/tools/*.md; echo "(empty above = good)"
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
```

Expected: no output from either. `--strict` is what actually catches a wrong relative
depth, because the link resolves against the consuming page.

- [ ] **Step 10: Run the remaining gates and commit**

```bash
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add includes/tools/ docs/ingres/tools/index.md \
  docs/hcl-informix/tools/index.md docs/analytics-engine/tools/index.md
git commit -m "docs: author the shared SQL tool descriptions once"
```

---

## Task 2: Share `describe_table` with a neutral example

Held back from Task 1 because its example is engine-specific in a way the others are
not: Ingres and Analytics Engine describe `ii_tables`, an **Ingres system catalog**,
while Informix describes `table`. Sharing the section as-is would tell Informix readers
to describe an Ingres catalog.

**Files:**
- Create: `includes/tools/describe-table.md`
- Modify: `docs/ingres/tools/index.md`
- Modify: `docs/hcl-informix/tools/index.md`
- Modify: `docs/analytics-engine/tools/index.md`

**Interfaces:**
- Produces `includes/tools/describe-table.md`, containing `### Parameters`,
  `### Output Schema`, `### Example` and `### Example: Naming the Owner`. The owner
  example is included rather than left per-page because the three engines are
  structurally identical and Informix simply lacks it today.

- [ ] **Step 1: Build the include from the Ingres version**

Copy the body of `## describe_table` from `docs/ingres/tools/index.md` — all four
subsections — into `includes/tools/describe-table.md`, with the same three
harmonizations as Task 1 Step 1 (two-space JSON, `"<placeholder>"` values, `../../`
links).

- [ ] **Step 2: Make the example engine-neutral**

In the new include, change every occurrence of `ii_tables` to `customers`, the demo
table `execute_query`'s example already uses on all three pages. Check what you changed:

```bash
grep -c 'customers' includes/tools/describe-table.md
grep -c 'ii_tables' includes/tools/describe-table.md
```

Expected: a non-zero count for `customers` and `0` for `ii_tables`.

This is a deliberate content change, not a harmonization: it replaces an Ingres-specific
catalog name with the page's own demo table. Ingres and Analytics Engine readers lose an
example that pointed at a system catalog; all three gain one that is correct for their
engine and consistent with the rest of the page.

- [ ] **Step 3: Rewire all three pages**

In each of `docs/ingres/tools/index.md`, `docs/hcl-informix/tools/index.md` and
`docs/analytics-engine/tools/index.md`, replace the body of `## describe_table` with:

```markdown
## describe_table

--8<-- "tools/describe-table.md"
```

For Ingres and Analytics Engine this removes their existing
`### Example: Naming the Owner`, which the include now supplies. For Informix it adds
that subsection for the first time.

- [ ] **Step 4: Verify all three now have the owner example**

```bash
python3 -m mkdocs build -q -d /tmp/phase3-t2
for p in ingres hcl-informix analytics-engine; do
  printf "%-18s owner-example=%s ii_tables=%s customers=%s\n" "$p" \
    "$(grep -c 'id="example-naming-the-owner"' /tmp/phase3-t2/$p/tools/index.html)" \
    "$(grep -c 'ii_tables' /tmp/phase3-t2/$p/tools/index.html)" \
    "$(grep -c 'customers' /tmp/phase3-t2/$p/tools/index.html)"
done
```

Expected: `owner-example=1`, `ii_tables=0`, and a non-zero `customers` on all three.

- [ ] **Step 5: Verify the table did not break and Zen is still untouched**

```bash
for p in ingres hcl-informix analytics-engine zen; do
  printf "%-18s stray-pipes=%s\n" "$p" "$(grep -c '^<p>| ' /tmp/phase3-t2/$p/tools/index.html)"
done
diff -q /tmp/phase3-baseline-site/zen/tools/index.html /tmp/phase3-t2/zen/tools/index.html \
  && echo "Zen unchanged"
```

Expected: `stray-pipes=0` everywhere and `Zen unchanged`.

- [ ] **Step 6: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add includes/tools/describe-table.md docs/ingres/tools/index.md \
  docs/hcl-informix/tools/index.md docs/analytics-engine/tools/index.md
git commit -m "docs: share describe_table with an engine-neutral example"
```

---

## Task 3: Give Informix the write example it should always have had

Spec §11.1 is answered: write semantics are identical across all four SQL engines.
Informix is structurally identical to Ingres, so its write example can be derived rather
than invented. Zen cannot — see the deferred table.

**Files:**
- Create: `includes/tools/write-example-sql.md`
- Modify: `docs/ingres/tools/index.md`
- Modify: `docs/hcl-informix/tools/index.md`
- Modify: `docs/analytics-engine/tools/index.md`

**Interfaces:**
- Produces `includes/tools/write-example-sql.md`, containing `### Example: Writing a Row`
  and `### Write Errors`. Consumed by the three structurally identical engines, appended
  after `--8<-- "tools/execute-query-sql.md"` inside `## execute_query`.

- [ ] **Step 1: Confirm Ingres and Analytics Engine agree before extracting**

Never extract from two sources without checking they say the same thing:

```bash
python3 - <<'PY'
import pathlib, re
def owner(p):
    t = pathlib.Path(f"docs/{p}/tools/index.md").read_text()
    m = re.search(r"### Example: Writing a Row(.*?)(?=\n## |\Z)", t, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None
a, b = owner("ingres"), owner("analytics-engine")
print("identical:", a == b)
if a != b:
    print("INGRES:", a[:400]); print("AE    :", b[:400])
PY
```

If they differ, read both and use the Ingres text, noting the difference in the commit
message. Do not merge two variants silently.

- [ ] **Step 2: Create the include**

Copy `### Example: Writing a Row` and `### Write Errors` from
`docs/ingres/tools/index.md` into `includes/tools/write-example-sql.md`, with the same
three harmonizations as Task 1 Step 1. Links to write support must be `../../` from a
depth-2 page, so `](../../intro/write-support.md)`.

- [ ] **Step 3: Rewire Ingres and Analytics Engine to the include**

In both pages, replace the inline `### Example: Writing a Row` and `### Write Errors`
subsections with the include, so `## execute_query` reads:

```markdown
## execute_query

--8<-- "tools/execute-query-sql.md"

--8<-- "tools/write-example-sql.md"
```

- [ ] **Step 4: Add the include to Informix**

In `docs/hcl-informix/tools/index.md`, `## execute_query` becomes the same two lines.
This is the new content: Informix documents write for the first time.

- [ ] **Step 5: Verify all three now document write, and Zen still does not**

```bash
python3 -m mkdocs build -q -d /tmp/phase3-t3
for p in ingres hcl-informix analytics-engine zen; do
  printf "%-18s write-example=%s write-errors=%s\n" "$p" \
    "$(grep -c 'id="example-writing-a-row"' /tmp/phase3-t3/$p/tools/index.html)" \
    "$(grep -c 'id="write-errors"' /tmp/phase3-t3/$p/tools/index.html)"
done
```

Expected: `1 1` for Ingres, Informix and Analytics Engine, and `0 0` for Zen. Zen's zero
is the deferred item, not an oversight — record it in the commit message.

- [ ] **Step 6: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add includes/tools/write-example-sql.md docs/ingres/tools/index.md \
  docs/hcl-informix/tools/index.md docs/analytics-engine/tools/index.md
git commit -m "docs: document write support on the Informix tools page"
```

---

## Task 4: Make the setup pages agree that all four engines support write

The tools pages now say Informix supports write, but its setup page still omits
`query_mode` and `write_confirmation` and its capabilities table does not mention write
at all. Zen has the same omissions. Spec §11.1 says both are wrong.

**Files:**
- Modify: `docs/hcl-informix/index.md` (capabilities table, optional-fields table)
- Modify: `docs/zen/index.md` (capabilities table, optional-fields table)
- Modify: `docs/zen/tools/index.md` (`### Parameters` wording only)

**Interfaces:**
- Consumes: `includes/conf/write-fields.md` from phase 2, which currently has two
  consumers. This task takes it to four — the state the phase-2 deferred table predicted.

- [ ] **Step 1: Add `conf/write-fields.md` to the Informix config table**

In `docs/hcl-informix/index.md`, the optional-fields table currently ends with
`--8<-- "conf/tls-fields.md"`. Append the write include after it:

```markdown
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
--8<-- "conf/write-fields.md"
```

- [ ] **Step 2: Add it to the Zen config table**

In `docs/zen/index.md`, the table ends with `--8<-- "conf/common-optional-fields.md"`.
Append:

```markdown
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/write-fields.md"
```

Zen gets no `conf/tls-fields.md` — whether it supports TLS is still unestablished.

- [ ] **Step 3: Add write to the Informix capabilities table**

`docs/hcl-informix/index.md` lists five read operations. Add a sixth row, worded as
Ingres words it:

```markdown
| **Execute write queries** | Run `INSERT`, `UPDATE`, and `DELETE` statements. Off by default. Requires `query_mode` set to `read-write` |
```

Then add the opt-in admonition Ingres carries, directly after the table:

```markdown
!!! note "Write support is opt-in"
    The server permits only read queries unless you set `query_mode` to `read-write`. Each write then requires the `mcp:write` scope and human approval. For more information, see [Write support](../intro/write-support.md).
```

- [ ] **Step 4: Add the same to the Zen capabilities table**

Add the identical row and admonition to `docs/zen/index.md`. Zen's tools page does not
yet show a write *example* — that is the deferred item — but the capability and its
configuration are documented, which is what §11.1 established.

- [ ] **Step 5: Fix the tool-parameter wording on the Zen tools page**

Zen consumes no tool include, so its `### Parameters` one-liners were not harmonized by
Tasks 1–2. Bring them to the same wording:

```bash
grep -n 'input parameters' docs/zen/tools/index.md
```

Replace each with `This tool takes no input parameters.` — Zen already uses that wording
in some places, so expect few or no changes; this step exists so the four pages agree.

- [ ] **Step 6: Verify all four engines now document write configuration**

```bash
python3 -m mkdocs build -q -d /tmp/phase3-t4
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s query_mode=%s write_confirmation=%s opt-in-note=%s\n" "$p" \
    "$(grep -c 'query_mode' /tmp/phase3-t4/$p/index.html)" \
    "$(grep -c 'write_confirmation' /tmp/phase3-t4/$p/index.html)" \
    "$(grep -c 'Write support is opt-in' /tmp/phase3-t4/$p/index.html)"
done
```

Expected: non-zero in all three columns on all four lines. Before this task, Informix
and Zen were zero in all three.

- [ ] **Step 7: Verify the config tables did not break**

```bash
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s stray-pipes=%s tables=%s\n" "$p" \
    "$(grep -c '^<p>| ' /tmp/phase3-t4/$p/index.html)" \
    "$(grep -c '<table>' /tmp/phase3-t4/$p/index.html)"
done
```

Expected: `stray-pipes=0` on all four. `tables` must equal the baseline count — a higher
number means a table split:

```bash
for p in ingres hcl-informix zen analytics-engine; do
  printf "%-18s before=%s after=%s\n" "$p" \
    "$(grep -c '<table>' /tmp/phase3-baseline-site/$p/index.html)" \
    "$(grep -c '<table>' /tmp/phase3-t4/$p/index.html)"
done
```

- [ ] **Step 8: Run the gates and commit**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/hcl-informix/index.md docs/zen/index.md docs/zen/tools/index.md
git commit -m "docs: document write support on the Informix and Zen setup pages"
```

---

## Task 5: Stop presenting write support as an Ingres and Analytics Engine feature

`docs/intro/write-support.md` is now the last place claiming otherwise. Its "Next Steps"
cards link only Ingres and Analytics Engine configuration, and its body points readers
at "the Tools page for your database, for example Ingres tools or Analytics Engine
tools" — an example list that silently excluded half the engines.

**Files:**
- Modify: `docs/intro/write-support.md`

**Interfaces:**
- Consumes: nothing. This page keeps its own text; phase 4 moves it to
  `write-support/index.md` and gives it a NoSQL sibling.

- [ ] **Step 1: See exactly what claims which engines**

```bash
grep -n -e 'ingres' -e 'analytics-engine' -e 'hcl-informix' -e 'zen' docs/intro/write-support.md
```

Expected: several hits for `ingres` and `analytics-engine`, none for `hcl-informix` or
`zen`. That asymmetry is the defect.

- [ ] **Step 2: Generalize the tools-page pointer**

Line 14 reads, in full:

```markdown
Which tools accept a write, and how, depends on the database. See the Tools page for your database, for example [Ingres tools](../ingres/tools/index.md) or [Analytics Engine tools](../analytics-engine/tools/index.md). The `query_mode` setting and the authorization checks described below apply the same way regardless of which tool performs the write.
```

Replace only the example pair with the full set. **Keep the second sentence** — it is the
statement that the authorization behaviour is engine-independent, which §11.1 makes more
important, not less:

```markdown
Which tools accept a write, and how, depends on the database. See the Tools page for your database: [Ingres](../ingres/tools/index.md), [HCL Informix®](../hcl-informix/tools/index.md), [Zen](../zen/tools/index.md), or [Analytics Engine](../analytics-engine/tools/index.md). The `query_mode` setting and the authorization checks described below apply the same way regardless of which tool performs the write.
```

Verify nothing was lost:

```bash
grep -c 'apply the same way regardless' docs/intro/write-support.md
```

Expected: `1`.

- [ ] **Step 3: Replace the two engine-specific Next Steps cards with one**

The page ends with four cards, two of which are "Ingres configuration" and "Analytics
Engine configuration". Replace both with a single card covering all four:

```markdown
- :material-database-cog: **[Configure your database](../get-started/index.md#which-database-do-you-have)**  
  The `query_mode` and `write_confirmation` fields, on the setup page for your engine.
```

Keep the existing Authentication and MCP clients cards unchanged. The anchor
`#which-database-do-you-have` was created by phase 2 — `--strict` verifies it in Step 5.

- [ ] **Step 4: Add the Zen caveat**

Zen's tools page has no write example yet, and a reader who enables write mode on Zen
should not be left guessing. Add after the `## Enabling write mode` table:

```markdown
!!! note "Zen write examples"
    Write support works the same way on Actian Zen, but the Zen tools page does not yet show a worked write example. The `query_mode`, scope and approval behaviour described here applies unchanged.
```

Remove this admonition in the phase that adds Zen's example.

- [ ] **Step 5: Verify no engine is excluded any more**

```bash
python3 -m mkdocs build --strict 2>&1 | grep -E "WARNING|ERROR|Aborted"; echo "(empty above = good)"
for e in ingres hcl-informix zen analytics-engine; do
  printf "  %-18s %s\n" "$e" "$(grep -c "$e" docs/intro/write-support.md)"
done
```

Expected: no build warnings — which also proves the
`get-started/index.md#which-database-do-you-have` anchor resolves — and a non-zero count
for all four engines.

- [ ] **Step 6: Run the gates and commit**

```bash
make check-templates
python3 -m mkdocs build -q && make check-raw-md
git add docs/intro/write-support.md
git commit -m "docs: present write support as a feature of all four SQL engines"
```

---

## Task 6: Update the tools template and the spec

The tools template from phase 1 references includes with the wrong consumer set, and the
spec's §7.1 inventory says four consumers where the measurement says three.

**Files:**
- Modify: `templates/tools-sql-database.md.tmpl`
- Modify: `specs/2026-08-05-docs-by-database-design.md`

**Interfaces:**
- Produces a template whose include list matches what exists, so a future engine page
  can be generated from it without editing.

- [ ] **Step 1: Correct the template**

`templates/tools-sql-database.md.tmpl` lists the includes in a header comment and uses
them in the body. Update the header comment to name the files that now exist and to state
the consumer restriction:

```markdown
<!-- Template: SQL/ODBC tools page. Target: docs/{{DB_SLUG}}/tools/index.md
     Expects includes: tools/execute-query-sql.md, tools/write-example-sql.md,
     tools/list-tables.md, tools/describe-table.md, tools/list-functions.md
     These describe the response shape shared by Ingres, HCL Informix and Analytics
     Engine. Zen returns a different shape and must not use them - write its
     descriptions out. Links inside these includes use ../../ because consumers sit at
     depth 2. -->
```

Then make the body match Task 1–3's structure, with the includes nested under their tool
headings rather than listed flat:

```markdown
## execute_query

--8<-- "tools/execute-query-sql.md"

--8<-- "tools/write-example-sql.md"

## list_tables

--8<-- "tools/list-tables.md"

## describe_table

--8<-- "tools/describe-table.md"

## list_functions

--8<-- "tools/list-functions.md"
```

- [ ] **Step 2: Verify every include the template names exists**

```bash
for i in $(grep -ohE '\-\-8<\-\- "[^"]+"' templates/tools-sql-database.md.tmpl | sed 's/.*"\(.*\)"/\1/'); do
  printf "  %-34s %s\n" "$i" "$([ -f "includes/$i" ] && echo OK || echo MISSING)"
done
make check-templates
```

Expected: `OK` on every line, and `check-templates` silent — the template lives outside
`docs/`, so its markers are ignored.

- [ ] **Step 3: Correct the spec's include inventory**

In `specs/2026-08-05-docs-by-database-design.md` §7.1, the `tools/*` rows claim four
consumers. Change them to three and add a §7.5 recording the measurement, in the same
style as §7.3 and §7.4:

```markdown
### 7.5 Measured: the tools split three-plus-Zen, not four

Parsing every `Output Schema` JSON block and comparing key structures shows Ingres,
Informix and Analytics Engine are structurally identical for all four tools, while Zen
returns a different shape for each of the three it has and lacks `list_functions`
entirely. So `includes/tools/*` has three consumers, and Zen keeps its own descriptions —
the same pattern `conf/tls-fields.md` follows.

The `describe_table` example needed one content change to become shareable: Ingres and
Analytics Engine described `ii_tables`, an Ingres system catalog, which is wrong for
Informix. It is now `customers`, the demo table the rest of the page uses.
```

- [ ] **Step 4: Record what is still deferred**

Add to §11 as a new entry, so Zen's missing write example is tracked rather than
forgotten:

```markdown
8. **Zen's `execute_query` response for a write.** Write support is confirmed identical
   on Zen (§11.1), and its capabilities and configuration are now documented, but its
   tools page has no worked write example: Zen's response shape differs from the other
   three, so the example cannot be derived and would have to be invented. Blocks nothing
   else; `docs/intro/write-support.md` carries a note until it is supplied.
```

- [ ] **Step 5: Commit**

```bash
git add templates/tools-sql-database.md.tmpl specs/2026-08-05-docs-by-database-design.md
git commit -m "docs: correct the tools template and record the measurement in the spec"
```

---

## Phase 3 done — state afterwards

| Include | Consumers | Grows when |
|---|---|---|
| `tools/execute-query-sql.md` | 3 | never — Zen is structurally different |
| `tools/list-tables.md` | 3 | never |
| `tools/describe-table.md` | 3 | never |
| `tools/list-functions.md` | 3 | never — Zen has no such tool (§11.2) |
| `tools/write-example-sql.md` | 3 | never |
| `conf/write-fields.md` | **4** | complete |
| `conf/common-optional-fields.md` | 4 | complete |
| `conf/tls-fields.md` | 3 | Zen TLS support is confirmed |

Write support is documented as a feature of all four SQL engines: capabilities tables,
configuration tables, the opt-in admonition, and worked examples on three of four pages.

Still open after this phase: Zen's worked write example (§11.8), the `max_rows`
cap-versus-default contradiction (§11.6), Zen TLS support, and the NoSQL write and
extension content needed for phase 4's stubs (§11.7).
