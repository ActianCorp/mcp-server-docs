"""
MkDocs hook: after each build, copy every source .md file from docs/ into
site/ at the same relative path.

This makes raw Markdown available at predictable public URLs on the deployed
site (e.g. https://docs.actian.com/mcp-server/getting-started.md),
so they can be used by:
  - in-app docs browsers that need Markdown endpoints
  - users who want to copy-paste page content into Claude / ChatGPT
"""
import os
import shutil


def on_post_build(config):
    docs_dir = config["docs_dir"]
    site_dir = config["site_dir"]

    for root, _dirs, files in os.walk(docs_dir):
        for filename in files:
            if not filename.endswith(".md"):
                continue

            src_path = os.path.join(root, filename)
            rel_path = os.path.relpath(src_path, docs_dir)
            dst_path = os.path.join(site_dir, rel_path)

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
