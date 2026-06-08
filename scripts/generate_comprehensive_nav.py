#!/usr/bin/env python3
"""
Generate comprehensive-nav-sections.js from docs/.pages navigation trees.

Labels: optional navTitle in .pages, else index.md title, else .pages title.
Tab labels: optional tabLabel in .pages, else .pages title, else section label.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
OUTPUT_FILE = DOCS_DIR / "javascripts" / "comprehensive-nav-sections.js"


def _read_front_matter_title(md_path: Path) -> str | None:
    if not md_path.is_file():
        return None
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    meta = yaml.safe_load(text[3:end]) or {}
    title = meta.get("title")
    return str(title).strip() if title else None


def _read_pages(pages_path: Path) -> dict:
    if not pages_path.is_file():
        return {}
    data = yaml.safe_load(pages_path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _humanize_slug(slug: str) -> str:
    return re.sub(r"\b\w", lambda m: m.group(0).upper(), slug.replace("-", " "))


def _page_label(docs_dir: Path, rel_dir: Path, slug: str | None = None) -> str:
    if slug:
        pages_child = _read_pages(docs_dir / rel_dir / slug / ".pages")
        if pages_child.get("navTitle"):
            return str(pages_child["navTitle"])
        index_md = docs_dir / rel_dir / slug / "index.md"
        return (
            _read_front_matter_title(index_md)
            or pages_child.get("title")
            or _humanize_slug(slug)
        )
    pages_meta = _read_pages(docs_dir / rel_dir / ".pages")
    index_md = docs_dir / rel_dir / "index.md"
    return (
        _read_front_matter_title(index_md)
        or pages_meta.get("title")
        or _humanize_slug(rel_dir.name)
    )


def _tab_label(docs_dir: Path, rel_dir: Path, label: str) -> str:
    pages_meta = _read_pages(docs_dir / rel_dir / ".pages")
    return str(pages_meta.get("tabLabel") or pages_meta.get("title") or label)


def _href_for(rel_path: str) -> str:
    if not rel_path:
        return "index.html"
    return f"{rel_path}/index.html"


def _nav_entry_name(entry: str | dict) -> tuple[str | None, str | None]:
    if isinstance(entry, dict):
        title = entry.get("title") or entry.get("name")
        for key in ("path", "glob", "file", "page"):
            if key in entry:
                value = str(entry[key])
                if value.endswith(".md"):
                    stem = Path(value).stem
                    return (None if stem == "index" else stem), title
                return value, title
        return None, title
    if isinstance(entry, str):
        if entry == "..." or entry.startswith("..."):
            return None, None
        if entry.endswith(".md"):
            stem = Path(entry).stem
            return (None if stem == "index" else stem), None
        return entry, None
    return None, None


def _build_child_pages(docs_dir: Path, rel_dir: Path, nav_items: list) -> list[dict]:
    pages: list[dict] = []
    for entry in nav_items:
        slug, explicit_title = _nav_entry_name(entry)
        if slug is None:
            continue

        child_rel = rel_dir / slug
        child_path = str(child_rel).replace("\\", "/")
        href = _href_for(child_path)
        name = explicit_title or _page_label(docs_dir, rel_dir, slug)

        child_pages_meta = _read_pages(docs_dir / child_rel / ".pages")
        child_nav = child_pages_meta.get("nav") or []
        nested = _build_child_pages(docs_dir, child_rel, child_nav)

        node: dict = {"name": name, "href": href}
        if nested:
            node["pages"] = nested
        pages.append(node)

    return pages


def _build_sections(docs_dir: Path) -> list[dict]:
    root_pages = _read_pages(docs_dir / ".pages")
    nav_items = root_pages.get("nav") or []
    sections: list[dict] = []

    for entry in nav_items:
        if isinstance(entry, str) and entry in ("index.md", "index"):
            sections.append(
                {
                    "key": "",
                    "label": _page_label(docs_dir, Path(".")),
                    "tabLabel": "Home",
                    "href": "index.html",
                    "pages": [],
                }
            )
            continue

        slug, explicit_title = _nav_entry_name(entry)
        if slug is None:
            continue

        rel_dir = Path(slug)
        section_path = str(rel_dir).replace("\\", "/")
        label = explicit_title or _page_label(docs_dir, rel_dir)
        section_pages_meta = _read_pages(docs_dir / rel_dir / ".pages")
        child_nav = section_pages_meta.get("nav") or []

        sections.append(
            {
                "key": section_path,
                "label": label,
                "tabLabel": _tab_label(docs_dir, rel_dir, label),
                "href": _href_for(section_path),
                "pages": _build_child_pages(docs_dir, rel_dir, child_nav),
            }
        )

    return sections


def generate_sections_js(docs_dir: Path | None = None) -> str:
    docs_dir = docs_dir or DOCS_DIR
    sections = _build_sections(docs_dir)
    body = json.dumps(sections, indent=2, ensure_ascii=True)
    return (
        "/* AUTO-GENERATED from docs .pages files - do not edit by hand. */\n"
        "(function () {\n"
        "  window.CN_SECTIONS = "
        f"{body};\n"
        "})();\n"
    )


def write_sections_file(docs_dir: Path | None = None, output: Path | None = None) -> Path:
    docs_dir = docs_dir or DOCS_DIR
    output = output or OUTPUT_FILE
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_sections_js(docs_dir), encoding="utf-8")
    return output


def main() -> None:
    path = write_sections_file()
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
