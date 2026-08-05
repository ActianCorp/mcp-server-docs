# Design: Restructure the documentation around "How do I use the MCP Server for my database?"

- **Date:** 2026-08-05
- **Status:** Phases 1 and 2 implemented. Phases 3-6 pending; 3 is blocked on §11.
- **Branch:** `feat/docs-by-product`

> This document lives outside `docs/` on purpose. Everything under `docs/` is built
> by MkDocs *and* published as raw Markdown by `hooks/copy_md_sources.py`, so an
> internal design document placed there would appear on docs.actian.com.

## 1. Problem

The Actian MCP Server ships one image per database backend. Four of them
(Ingres, HCL Informix, Zen, Analytics Engine) are SQL/ODBC based and behave
almost identically. NoSQL is a Quarkus/Java implementation with a different
configuration file, a different query language, a different port, and a
different extension API.

The current documentation is organised by product, but the cross-cutting topics
sit above the products and implicitly describe only the SQL family. This produces
two concrete failures.

### 1.1 Two competing axes

`get-started/`, `mcp-clients/`, `authentication/`, and `extensions/` are named
generically but document SQL/ODBC behaviour. A NoSQL reader enters them and is
then redirected back out by admonitions:

| Location | Admonition |
|---|---|
| `docs/get-started/index.md:63-64` | "Actian NoSQL users — uses a different startup command" |
| `docs/nosql/index.md:20-21` | "NoSQL supports extensions, but through a different interface … Documentation for it is not yet available" |
| `docs/nosql/index.md:109-110` | "For connecting AI clients … see the Connecting MCP Clients guide" |

The workaround for authentication was to duplicate the entire subtree:
`docs/nosql/authentication/` mirrors `docs/authentication/` with Auth0 (425 vs
190 lines) and Keycloak (463 vs 202 lines) maintained twice.

### 1.2 Duplication that has already caused a factual gap

The four SQL product pages are structurally identical. A diff of
`docs/ingres/index.md` against `docs/analytics-engine/index.md` differs only in
the image name, the connection fields, and a few engine-specific notes. The same
holds for the tools pages, where `execute_query`, `list_tables`,
`describe_table`, and `list_functions` are written out four times.

This duplication has already drifted. Write support is documented as if it were
an Ingres and Analytics Engine feature:

- `docs/intro/write-support.md:101-106` links only Ingres and Analytics Engine.
- Only `docs/ingres/tools/index.md` and `docs/analytics-engine/tools/index.md`
  contain "Example: Writing a Row" and "Write Errors" sections.
- `docs/zen/index.md` and `docs/hcl-informix/index.md` do not list write in
  their capabilities tables, and their optional-field tables omit `query_mode`
  and `write_confirmation`.

But `examples/extensions/conf.example.zen.json` sets `"query_mode": "read-write"`,
and `examples/extensions/README.md` states the examples run unmodified in
read-write mode on all four engines. Write support is therefore a
**documentation gap, not a product limitation** — exactly the failure mode that
copy-paste page authoring produces.

## 2. Goals

1. A reader who knows which database they have can follow one path end to end:
   orientation → set up my database → connect a client → understand the tools →
   secure it → enable writes → add my own tools.
2. NoSQL stops being an exception that other pages warn about, and becomes one of
   five equals.
3. Content that is genuinely identical is authored once, so a change to shared
   behaviour cannot land on three of four pages.
4. Pages that must exist per database are generated from a template, so they stay
   structurally identical and diffable.
5. The two topics that have exactly two variants (write support, extensions) get
   exactly two pages each: SQL family and NoSQL.

## 3. Non-goals

- No scalability provision for additional backends. The five are the current
  scope (decided 2026-08-05).
- No rewrite of prose that is already correct. Content moves and is deduplicated;
  it is not re-authored for its own sake.
- Filling the NoSQL write support and NoSQL extensions pages is **out of scope**.
  They ship as published stubs; the content requires product knowledge not
  present in this repository.

## 4. Decisions and constraints

| Decision | Rationale |
|---|---|
| Restructure IA **and** deduplicate content | Nav-only reorg leaves the maintenance problem — and §1.2 shows it has already produced a factual error. |
| Product directories keep their paths | `ingres/`, `zen/`, `authentication/`, `mcp-clients/` etc. are unchanged, so only four redirects are needed. |
| Redirects are added where paths do move | `mkdocs-redirects` is a new dependency. `versions.json` contains only `latest`, so no historical mike versions need serving. |
| Hybrid single-sourcing: `pymdownx.snippets` for identical blocks, authoring templates for page structure | Snippets remove duplication; templates enforce consistency where content genuinely differs per engine. |
| Includes live in `includes/` at the repo root, **not** in `docs/_includes/` | Anything under `docs/` is built as a page *and* published as raw Markdown. Inside `docs/` this would need `exclude_docs`, and the fragments would still be reachable as raw URLs — context-free half-sentences at a public address. |
| Unwritten pages ship as published stubs | Readers should see that the feature exists and documentation is coming. |

## 5. Target structure

```
Home                     index.md
Introduction             intro/            MCP concepts, architecture, request flow
Get started              get-started/      backend-agnostic arc + "Which database do you have?"
                                           → chooser table + capability matrix

  ── Your database ──                      setup end to end + reference, per backend
Ingres                   ingres/           index · tools · resources · prompts
HCL Informix             hcl-informix/     index · tools · resources · prompts
Zen                      zen/              index · tools · resources · prompts
Analytics Engine         analytics-engine/ index · tools · resources · prompts
NoSQL                    nosql/            index · tools · resources · prompts

  ── Cross-cutting ──
Connect a client         mcp-clients/      index · python
Secure the server        authentication/   index · keycloak · auth0   (NoSQL as tabs)
Write support            write-support/    index (SQL) · nosql            ← new
Extensions               extensions/       index (SQL) · examples · api-reference · nosql
```

The tree shape is close to today's. The substance of the change is **which page
answers which question**:

- `get-started/` stops being a SQL walkthrough with NoSQL warnings. It becomes
  the orientation point: this is the arc, this is your database, continue here.
  Both NoSQL admonitions disappear.
- `<db>/index.md` becomes the actual answer to the driving question:
  prerequisites → configuration → start → verify → continue to a client.
  Complete, with no jumping back out.
- Write support and Extensions get one SQL page and one NoSQL page each.

The five database sections stay at the top level rather than nesting under a
`databases/` parent, which keeps their URLs. If the visual grouping turns out to
matter, a parent directory can be introduced later at the cost of five redirects.

## 6. Content mapping

| Today | Target | Action |
|---|---|---|
| `get-started/index.md` | unchanged path | Becomes chooser + arc, consuming **no** includes. Its `conf.json` field table is dropped rather than shared: a chooser must not carry a configuration reference, which is the duplication being removed. The four setup pages already hold that content. |
| `{ingres,hcl-informix,zen,analytics-engine}/index.md` | unchanged paths | Re-authored from `setup-sql-database.md.tmpl`, structurally identical. Engine-specific: image, connection fields, engine quirks. Shared content included. |
| `nosql/index.md` | unchanged path | The Python client section (lines 107–241) moves to `mcp-clients/python.md`; it does not belong on a setup page and the SQL family needs it equally. |
| `{ingres,hcl-informix,zen,analytics-engine}/tools/index.md` | unchanged paths | `execute_query`, `list_tables`, `describe_table`, `list_functions` come from `includes/tools/`. Zen keeps its three extras written out. **Write examples are added everywhere**, closing the gap from §1.2. |
| `nosql/tools/index.md` | unchanged path | Stays standalone; no include sharing (JPQL, LOIDs, pagination). |
| `nosql/authentication/**` (4 files) | **removed** | Merged into `authentication/**` with tabs at the diverging steps. Redirects required. |
| `intro/write-support.md` | `write-support/index.md` | **Done (phase 4).** Promoted; 18 references rewritten and one redirect added. All 15 depth-1 and depth-2 Markdown references took one substitution — see §7.4. |
| — | `write-support/nosql.md` | New, published stub. |
| — | `extensions/nosql.md` | New, published stub. Replaces the admonition at `nosql/index.md:20-21`. |
| — | `mcp-clients/python.md` | New, extracted from `nosql/index.md`, with a SQL and a NoSQL variant. |

### 6.1 The authentication merge is the one risky step

The NoSQL Keycloak guide is not merely worded differently; it has a different
flow — two clients (authorization code + client credentials), no audience mapper,
no sub-override mapper, and `application.properties` instead of `conf.json`. Only
realm creation, prerequisites, and end-to-end verification are shared. With tabs
at the four diverging steps the page grows to roughly 500 lines.

**Fallback if that page becomes unwieldy:** keep NoSQL authentication as a
separate `authentication/nosql.md`. Duplication remains, but at least in one
place. This is a decision to make while implementing phase 6, not before.

## 7. Single-sourcing layer

`pymdownx.snippets` ships with `pymdown-extensions`, a dependency of
`mkdocs-material`. No new requirement is needed for snippets.

```yaml
markdown_extensions:
  - pymdownx.snippets:
      base_path: ['includes']
      check_paths: true
```

`check_paths: true` matters: without it a mistyped include renders as literal
text and nobody notices.

### 7.1 Include inventory

Only content that is *identical*, not merely *similar*. Similar content stays
written out — otherwise the source becomes unreadable and changes get inherited
where they do not belong.

| Include | Consumed by | Why shareable |
|---|---|---|
| `conf/common-optional-fields.md` | 4 SQL setup pages | `log_level`, `oauth`, `extensions` — the only rows common to all four. See §7.3 |
| `conf/tls-fields.md` | 3 SQL setup pages | `ssl_certfile`, `ssl_keyfile` — Zen documents neither |
| `conf/write-fields.md` | 2 SQL setup pages | `query_mode`, `write_confirmation` — Ingres and Analytics Engine only, pending §11.1 |
| `conf/protection-note.md` | 4 SQL setup pages | The `chmod 600` admonition |
| `docker/run-sql.md` | 4 SQL setup pages, `get-started/` | The `docker run` pattern; image name is a placeholder the surrounding page names |
| `docker/mount-path-note.md` | 5 setup pages | "The container reads from `/app/conf.json`; do not change the path" |
| `verify-connection.md` | 4 SQL setup pages | The three verification steps from `get-started/` step 5 |
| `tools/execute-query-sql.md` | 3 SQL tools pages | Identical parameters, output schema, example. Not Zen — see §7.5 |
| `tools/list-tables.md` | 3 SQL tools pages | as above |
| `tools/describe-table.md` | 3 SQL tools pages | as above, with an engine-neutral example — see §7.5 |
| `tools/list-functions.md` | 3 SQL tools pages (Zen has none, confirmed §11.2) | as above |
| `tools/write-example-sql.md` | 3 SQL tools pages | **Closes the Informix gap.** Zen's response shape differs, so its example cannot be derived — see §11.8 |
| `write/authorization-flow.md` | deferred to phase 4 | Would have one consumer today; extracting a fragment for a single caller is premature |
| `stub-notice.md` | all stub pages | So "in progress" looks identical everywhere |

Deliberately **not** shared, despite the temptation: prerequisites lists (they
should stay engine-specific — Informix mentions Podman, Zen needs `--add-host`)
and the capabilities tables (genuinely different per engine).

### 7.3 Measured: the SQL family is less uniform than assumed

An earlier draft of §7.1 claimed a single eight-field `conf/common-fields.md` was
"already verbatim identical 4×". Measuring the four pages disproved it:

| Field | Ingres | Informix | Zen | Analytics Engine |
|---|---|---|---|---|
| `extensions` | ✅ | ✅ | ✅ | ✅ (verbatim identical) |
| `log_level`, `oauth` | ✅ | ✅ | ✅ | ✅ (phrasing differs only) |
| `max_rows` | "Maximum value: 1000" | "Default is 1000" | "Default is 1000" | "Default is 1000" |
| `ssl_certfile`, `ssl_keyfile` | ✅ | ✅ | ❌ absent | ✅ |
| `query_mode`, `write_confirmation` | ✅ | ❌ absent | ❌ absent | ✅ |

Hence three includes with three different consumer sets, each matching the evidence,
rather than one include asserting uniformity that does not exist. Each grows a consumer
as the §11 questions get answered — no rewrite needed.

Two further consequences:

- **`docker/run-sql.md` is impossible.** `pymdownx.snippets` has no variable
  substitution, and the `docker run` block names the engine's image. Consistency there
  comes from the template plus review, not from single-sourcing. The include is removed
  from §7.1.
- **Zen's startup genuinely differs.** It needs
  `--add-host=host.docker.internal:host-gateway` to reach the Zen engine on the host;
  the other three do not.

### 7.4 Row-fragment includes must have no trailing newline

An include that continues a table the page has already opened must not end with a
newline. A file ending in `\n` contributes one blank line when inlined, which terminates
the table; every include after it renders as literal pipes in a paragraph. Measured
during phase 2: the first include joined the table, the next two broke out of it, while
the table *count* stayed correct — so a table-count check alone does not catch this.
Check for `^<p>| ` in the rendered HTML instead.

Standalone includes (admonitions, whole sections) are unaffected.

When a page moves between two locations at the same depth, one substitution handles
referring pages at **every** depth: `../intro/x.md` is a substring of `../../intro/x.md`,
so replacing it leaves the extra `../` in place. Phase 4 moved write support with a single
sed across 15 references at two depths. The counterexample is phase 3, which over-applied
a `../` to `../../` transformation to a file already at depth 2 and produced `../../../`.
Substitute the *tail* of the path, never prepend to it.

Grepping for the old path does not find every reference. Phase 4's inventory searched for
`intro/write-support` and counted 17, missing an 18th in `docs/intro/index.md` that wrote
the sibling-relative `write-support.md` with no directory part at all. `mkdocs build
--strict` caught it. Trust the build, not the grep.

### 7.5 Measured: the tools split three-plus-Zen, not four

Parsing every `Output Schema` JSON block and comparing key structures shows Ingres,
Informix and Analytics Engine are structurally identical for all four tools, while Zen
returns a different shape for each of the three it has and lacks `list_functions`
entirely:

| Tool | Ingres / Informix / Analytics Engine | Zen |
|---|---|---|
| `execute_query` | `success` `columns` `rows` `row_count` `truncated` `warning` `error` | `method` `original_sql` `translated` `translation_note` `results[].column` `row_count` `truncated` `truncation_note` |
| `list_tables` | `success` `columns` `rows` `row_count` `error` | `tables` `count` |
| `describe_table` | `success` `columns` `rows` `row_count` `error` | `table_name` `columns[].name/type/nullable/default/precision/scale/primary_key` `primary_keys` `foreign_keys` |
| `list_functions` | `success` `columns` `rows` `row_count` `error` | **absent** |

So `includes/tools/*` has three consumers and Zen keeps its own descriptions — the same
pattern `conf/tls-fields.md` follows. The remaining textual differences among the three
were wording, tabs versus spaces, and placeholder convention, all harmonized.

One content change was needed to make `describe_table` shareable: Ingres and Analytics
Engine described `ii_tables`, an Ingres system catalog, which is wrong for Informix. It
is now `customers`, the demo table the rest of the page already uses.

`row_count` is written as `"<num_rows>"` in the read includes but stays the literal `1`
in the write include: there it means one row was written, not "some number of rows".

### 7.2 Hook change

`hooks/copy_md_sources.py` must resolve includes before copying, otherwise the
raw `.md` files published at `docs.actian.com/mcp-server/*.md` contain unresolved
`--8<--` directives.

This must **not** be a hand-rolled regex. Reuse the `pymdownx.snippets`
preprocessor itself — the same implementation that runs during the build, with
the same configuration read from `mkdocs.yml`:

```python
def on_post_build(config):
    snippet_cfg = config["mdx_configs"].get("pymdownx.snippets", {})
    md = markdown.Markdown(
        extensions=["pymdownx.snippets"],
        extension_configs={"pymdownx.snippets": snippet_cfg},
    )
    preprocessor = md.preprocessors["snippet"]
    # for each .md under docs_dir: preprocessor.run(text.splitlines()), then write
```

There is then no second snippet-syntax implementation that can drift, and
`base_path` stays configured in exactly one place.

## 8. Templates

`templates/` at the repo root, never built, never published:

```
templates/
  README.md                    Authoring guide: what each placeholder means
  setup-sql-database.md.tmpl   A new or reworked SQL setup page
  tools-sql-database.md.tmpl   A new or reworked SQL tools page
  write-support.md.tmpl        For the NoSQL variant and future variants
  extensions.md.tmpl           as above
```

Two placeholder conventions, deliberately separate:

| Marker | Meaning | May ship? |
|---|---|---|
| `{{DB_NAME}}`, `{{IMAGE}}`, `{{PORT}}` | Substitute a value, mechanical | **No** |
| `<!-- TODO(fill): … -->` | Write prose, needs product knowledge | **No** |
| `<!-- STUB: pending product input -->` | Deliberately unfinished, published page | **Yes** |

Separating `TODO(fill)` from `STUB` is the point: published stubs are wanted, so
"unfinished" cannot be banned outright — but *accidentally* unfinished must be.
Guard in the `makefile`:

```make
check-templates:
	@! grep -rn -e '{{' -e 'TODO(fill)' docs/ --include='*.md' \
	  || (echo "Unfilled template placeholder in docs/" && exit 1)
```

## 9. Configuration changes

Each change is annotated with the phase (§10) it lands in. Two of them
deliberately do **not** land in phase 1, so that phase 1's byte-identical claim
holds: `content.tabs.link` changes rendered output, and a `redirect_maps` entry is
only valid once its target page exists.

| File | Change | Phase |
|---|---|---|
| `requirements.txt` | `mkdocs-redirects>=1.2` | 1 |
| `mkdocs.yml` | `pymdownx.snippets` (base_path `includes`, `check_paths: true`); `redirects` plugin with an empty `redirect_maps` | 1 |
| `hooks/copy_md_sources.py` | Snippet resolution before copying (§7.2) | 1 |
| `makefile` | `check-templates` target | 1 |
| `docs/write-support/.pages` | New | 4 |
| `docs/extensions/.pages` | `nosql.md` added | 4 |
| `mkdocs.yml` | `redirect_maps`: `intro/write-support.md` | 4 |
| `mkdocs.yml` | `content.tabs.link` in `theme.features` | 5 |
| `docs/mcp-clients/.pages` | `python.md` added | 5 |
| `docs/.pages` | New order; `write-support` added | 5 |
| `docs/nosql/.pages` | `authentication` removed | 6 |
| `mkdocs.yml` | `redirect_maps`: the three `nosql/authentication/**` entries | 6 |

### 9.1 Redirects

The final map, assembled across phases 4 and 6 as the pages actually move:

```yaml
plugins:
  - redirects:
      redirect_maps:
        'intro/write-support.md': 'write-support/index.md'
        'nosql/authentication/index.md': 'authentication/index.md'
        'nosql/authentication/auth0/index.md': 'authentication/auth0/index.md'
        'nosql/authentication/keycloak/index.md': 'authentication/keycloak/index.md'
```

**Accepted limitation:** `mkdocs-redirects` generates HTML redirect stubs, but
`copy_md_sources.py` walks `docs_dir`, so moved pages have no raw `.md` at the old
address. `…/intro/write-support.md` will 404 while `…/intro/write-support.html`
redirects correctly. The raw path is a copy-paste convenience feature, not an
indexed URL. If this needs fixing, the hook can emit a one-line pointer file for
those four paths.

### 9.2 Why `content.tabs.link`

Material synchronises tabs with identical labels across the whole site and across
page navigations. A reader who selects "NoSQL" on the authentication page sees
NoSQL on every other tabbed page. That turns the tabs into a de facto database
switcher — and it is why the labels must be **word-for-word identical** everywhere.

## 10. Implementation phases

Six separate pull requests. They have different risk profiles and the riskiest
comes last. Every phase leaves the site buildable and publishable.

| # | Content | Risk | Verification |
|---|---|---|---|
| 1 | **Infrastructure.** Snippets, redirects plugin, hook change, `templates/` + authoring README, `check-templates`. Then `validation.anchors: warn` plus the six anchor fixes it exposes (§10.1). | Very low | Rendered site **byte-identical** to before through the scaffolding tasks; then exactly twelve changed files for the six anchor fixes |
| 2 | **SQL setup pages deduplicated.** `includes/conf/*`, `includes/docker/*`, `verify-connection.md`; four setup pages from the template; `get-started/` becomes chooser + arc; NoSQL admonitions removed. | Low | `mkdocs build --strict`; rendered pages materially equivalent to before |
| 3 | **Tools pages deduplicated, write gap closed.** `includes/tools/*`, `includes/write/*`; write examples added for Zen and Informix. | **Factual** — this is where a new claim is made | Requires product verification, see §11 |
| 4 | **Write support promoted, stubs added.** `intro/write-support.md` → `write-support/index.md`; `write-support/nosql.md` and `extensions/nosql.md` as published stubs; admonition at `nosql/index.md:20-21` replaced. | Low | Redirect stub present in build; `STUB` marker rendered, no `TODO(fill)` |
| 5 | **Python client extracted, nav reordered.** `mcp-clients/python.md` from `nosql/index.md` with SQL and NoSQL variants as tabs; `content.tabs.link` enabled; setup page shortened; `docs/.pages` reordered. | Low | Link check — inbound anchors may point at `nosql/index.md#connect-using-a-python-client` |
| 6 | **Authentication merge.** `authentication/` with tabs at diverging steps; `nosql/authentication/**` removed; redirects live. | **Highest** | Read both guides step by step against the previous state; separately revertible |

### 10.1 `--strict` is not a gate until anchor validation is enabled

MkDocs 1.6 reports broken internal anchors at `INFO` level, so `mkdocs build --strict`
currently passes while six links are broken. Adding

```yaml
validation:
  anchors: warn
```

promotes them to warnings, at which point `--strict` aborts. Verified: it fails with
`Aborted with 6 warnings in strict mode!` The six, with the correct targets read from
the built HTML rather than inferred from heading text:

| File:line | Broken anchor | Correct anchor |
|---|---|---|
| `docs/analytics-engine/index.md:94` | `#the-oauth-configuration-block` | `#configuring-oauth-block` |
| `docs/hcl-informix/index.md:94` | `#the-oauth-configuration-block` | `#configuring-oauth-block` |
| `docs/ingres/index.md:94` | `#the-oauth-configuration-block` | `#configuring-oauth-block` |
| `docs/authentication/index.md:154` | `#tls` | `#secure-remote-deployments-with-https-and-tls` |
| `docs/authentication/auth0/index.md:322` | `#https-tls-for-remote-deployments` | `#secure-remote-deployments-with-https-and-tls` |
| `docs/mcp-clients/index.md:279` | `#https-tls-for-remote-deployments` | `#secure-remote-deployments-with-https-and-tls` |

This lands at the end of phase 1, after the byte-identical gate, because it is the only
part of phase 1 that changes rendered output. Without it the `--strict` verification
promised in §12 would not actually catch anything.

## 11. Open questions requiring product verification

Phase 3 is the only phase that produces new factual claims rather than
rearranging existing ones. These cannot be answered from this repository:

1. ~~**Write support on Zen and Informix.**~~ **Resolved 2026-08-05: yes, identical
   semantics.** `query_mode`, the `mcp:write` scope and `write_confirmation` behave the
   same on all four SQL engines. Consequences: `conf/write-fields.md` goes from two
   consumers to four; the Zen and Informix capabilities tables must list write; their
   tools pages need the write examples; and `write-support.md` must stop presenting this
   as an Ingres and Analytics Engine feature. Phase 3 is unblocked.
2. ~~**Does Zen really have no `list_functions`?**~~ **Resolved 2026-08-05: correct,
   Zen has none.** Verified consistent: `list_functions` appears nowhere under
   `docs/zen/`, and its capabilities table omits it. No documentation change needed —
   `tools/list-functions.md` simply has three consumers, not four.
3. ~~**`user_impersonation` on NoSQL**~~ **Resolved 2026-08-05: not supported.**
   Nothing in the docs currently claims otherwise — `user_impersonation` appears nowhere
   under `docs/nosql/`, so no statement is wrong today. Open follow-up, small: whether the
   NoSQL authentication page should say so explicitly, the way `docs/zen/index.md` does
   for `SET SESSION AUTHORIZATION`. That depends on whether `user_impersonation` is even
   a valid `application.properties` key, which is not established here.
4. ~~**The Informix image contradiction.**~~ **Resolved 2026-08-05: Docker Hub.**
   `actian/informix-mcp-server` from Docker Hub is correct, as stated in
   `docs/index.md:80` and `docs/get-started/index.md:25`. The instructions at
   `docs/hcl-informix/index.md:106-115` are therefore wrong on two counts: the
   `docker load -i ifx_mcp_image.tar` step does not apply, and the image name
   `actian/informix-mcp-server-linux:1.0.0` is not the published one. Phase 2
   re-authors that page from the template and must drop both. Phase 2 is unblocked.
5. ~~**Inconsistent version tags**~~ **Resolved 2026-08-05: `1.1.0` everywhere.** Eight
   tagged references need changing, in seven files: `docs/index.md:144` (`:latest`),
   `docs/zen/index.md:100` (`:latest`), `docs/nosql/index.md:100` and
   `docs/nosql/authentication/index.md:120` (`:1.0.1`), and `:1.0.0` in
   `docs/ingres/index.md:104`, `docs/hcl-informix/index.md:106`,
   `docs/analytics-engine/index.md:106` and `docs/authentication/index.md:182`. The five
   untagged references in tables and Docker Hub links need no change.
6. ~~**Is `max_rows` = 1000 a hard cap or a default?**~~ **Resolved 2026-08-05: both,
   depending on the engine.** `1000` is the default on all four, and *additionally* a hard
   ceiling on Ingres and Analytics Engine. Two things were wrong before: the Analytics
   Engine page called `1000` a default a reader could raise, and Zen repeated "Default is
   `1000`" in the description where the Default column already says it.

   The two facts cannot share one table row, so there are two variants:
   `conf/max-rows-capped.md` ("Cannot be set above `1000`") for Ingres and Analytics
   Engine, and `conf/max-rows-default.md` for Informix and Zen. Two consumers each — the
   same evidence-matched pattern as `conf/tls-fields.md`. A future author sees two include
   names and has to choose, which is the point.
8. **Zen's `execute_query` response for a write.** Write support is confirmed identical
   on Zen (§11.1), and its capability and configuration are documented, but its tools page
   has no worked write example: Zen's response shape differs from the other three, so the
   example cannot be derived and would have to be invented. Blocks nothing else;
   `docs/intro/write-support.md` carries a note until it is supplied.
7. **NoSQL write semantics and NoSQL extension API** — needed to fill the two
   stub pages. Out of scope for this design; the stubs exist to hold the slot.

   The two stub pages exist as of phase 4 (`docs/write-support/nosql.md` and
   `docs/extensions/nosql.md`), each carrying `includes/stub-notice.md`. They state that
   the feature exists and the documentation does not, and describe no behaviour. Answering
   this question fills them; it no longer blocks any structural work.

## 12. Verification

```bash
mkdocs build --strict                          # fails on broken internal links and missing includes
make check-templates                           # no {{…}} and no TODO(fill) under docs/
grep -rn '\-\-8<\-\-' site/ --include='*.md'    # must be empty: includes were resolved
```

Plus one manual pass that cannot be automated and is the actual success
criterion: **follow one database's path end to end** — Get started → Zen setup →
connect a client → tools → secure the server — and check whether "How do I use
the MCP Server for my database?" is answered without jumping back out.
