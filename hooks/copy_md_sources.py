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
