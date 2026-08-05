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
