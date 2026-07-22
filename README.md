# Actian MCP Server — Documentation Portal

> Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) · Light/dark theme · Versioned with [mike](https://github.com/jimporter/mike)

**Repository:** https://github.com/ActianCorp/mcp-server-docs  
**Branch:** `main`

---

## About This Repository

This repository contains the MkDocs-based documentation portal for the **Actian MCP Server**

---

## What's Included

| Feature | Description |
|---|---|
| **MkDocs Material 9.6+** | Modern Material Design theme with light/dark toggle |
| **Navigation** | Tabs, sections, breadcrumbs, instant loading, pruning |
| **Search** | Enhanced search with highlighting, suggestions, and sharing |
| **Diagrams** | Mermaid and PlantUML diagram support |
| **API docs** | Swagger UI tag plugin for OpenAPI specs |
| **Versioning** | Multi-version support via `mike` |
| **SEO** | Auto-generated meta descriptions, robots.txt, sitemap |
| **Code blocks** | Copy button, syntax highlighting, annotations |
| **Custom 404** | Branded 404 page |
| **Edit on GitHub** | Per-page edit button linking to `main` branch |

---

## Project Structure

```
actian_mcp_server/
├── mkdocs.yml                  # Main MkDocs configuration
├── requirements.txt            # Python dependencies
├── makefile                    # Docker shortcuts
├── docs/                       # All documentation content
│   ├── index.md                # Homepage (landing page)
│   ├── .pages                  # Top-level navigation order
│   ├── robots.txt              # Search engine directives
│   ├── assets/                 # Logos, homepage images, site-wide CSS
│   ├── stylesheets/            # Component CSS (search, DX styles)
│   ├── javascripts/            # Custom JS (search, mermaid)
│   ├── intro/                  # What is MCP? Architecture overview
│   ├── get_started/            # Installation & quickstart
│   ├── develop_with_mcp/       # Tools, Resources, Prompts, Plugins
│   │   ├── tools/              # Defining MCP tools
│   │   ├── resources/          # Defining MCP resources
│   │   ├── prompts/            # Defining MCP prompt templates
│   │   └── plugins/            # Building & registering plugins
│   ├── configuration/          # Server configuration reference
│   ├── deployment/             # Local, Docker, and production deployment
│   └── APIs/                   # API reference documentation
├── theme_overrides/            # Custom theme templates
│   ├── main.html               # Base template (header, scripts)
│   ├── home.html               # Landing page template
│   ├── home-blocks.html        # Landing page hero & content blocks
│   ├── 404.html                # Custom 404 page
│   ├── assets/stylesheets/     # Landing page & theme CSS
│   └── partials/               # Partial templates
├── hooks/                      # MkDocs build hooks
│   └── copy_md_sources.py      # Publishes raw Markdown alongside built HTML
├── utils/                      # Utility scripts (audits, link checks)
└── site/                       # Built output (auto-generated, do not edit)
```

---


## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ActianCorp/mcp-server-docs.git
cd mcp-server-docs
git checkout main
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---|---|
| `mkdocs-material` | Material Design theme |
| `mike` | Documentation versioning |
| `mkdocs-awesome-pages-plugin` | Custom navigation ordering |
| `mkdocs-git-revision-date-localized-plugin` | "Last updated" dates on pages |
| `mkdocs-minify-plugin` | HTML minification for production |
| `mkdocs-swagger-ui-tag` | Swagger/OpenAPI rendering |
| `mkdocs-meta-descriptions-plugin` | Auto SEO meta descriptions |
| `plantuml-markdown` | PlantUML diagram support |

---

## Running Locally

### Option A: mkdocs serve (recommended for authoring)

```bash
mkdocs serve
```

Opens a live-reload development server at **http://127.0.0.1:8000**. Changes to any file under `docs/` are reflected instantly.

### Option B: Dirty reload (faster for large sites)

```bash
mkdocs serve --dirtyreload
```

Only rebuilds changed pages — faster during active writing.


## Building the Site

```bash
mkdocs build
```

Generates the static site in the `site/` directory.

To preview the built output locally:

```bash
python -m http.server 8080 --directory site
```

Then open **http://127.0.0.1:8080**.

---

## Adding Documentation

### Step 1: Create a section folder and Markdown files

```
docs/
├── my_section/
│   ├── index.md            # Section landing page
│   ├── my-guide.md         # A guide page
│   └── images/             # Section-specific images
```

### Step 2: Write your content

Each page can include optional front matter:

```markdown
---
title: My Page Title
description: A brief description for search engines.
---

# My Page Title

Content supports:
- **Admonitions** — `!!! note`, `!!! warning`, `!!! tip`
- **Code blocks** — syntax highlighting + copy button
- **Mermaid diagrams** — inside ```mermaid``` fenced blocks
- **PlantUML diagrams** — via the `plantuml_markdown` extension
- **Tabbed content** — `=== "Tab 1"` syntax
```

### Step 3: Control navigation order

Create a `.pages` file in your section folder:

```yaml
# docs/my_section/.pages
nav:
  - index.md
  - my-guide.md
```

### Step 4: Preview and commit

```bash
mkdocs serve              # Preview at http://127.0.0.1:8000
git add .
git commit -m "docs: add my_section"
git push origin <your-branch>
```

See [Contributing](#contributing) below for the full contribution workflow,
including how to open a pull request against `main`.

---

## Adding API Documentation

Place your OpenAPI/Swagger JSON spec in `docs/APIs/` and create a Markdown file:

```markdown
---
title: My API
---

# My API

<swagger-ui src="my-api-spec.json"/>
```

---

## Customizing the Theme

### Colors and branding

| File | What it controls |
|---|---|
| `theme_overrides/assets/stylesheets/actian-landing.css` | Landing page, CSS variables, dark mode |
| `docs/assets/stylesheets/style.css` | Header, tabs, search bar, general overrides |
| `docs/stylesheets/dx_style.css` | Search enhancements, syntax highlighting |

### Logos and images

- **Site logo:** Replace `docs/assets/dx_logo.png`
- **Favicon:** Replace `docs/assets/favicon.png`
- **Landing page images:** Add to `docs/assets/homepage-images/`

### Templates

| File | Purpose |
|---|---|
| `theme_overrides/main.html` | Header, scripts |
| `theme_overrides/home.html` | Landing page layout |
| `theme_overrides/home-blocks.html` | Hero banner and content blocks |
| `theme_overrides/404.html` | Custom 404 error page |

### Configuration (`mkdocs.yml`)

Key sections:

- **`site_name`** — Documentation title
- **`site_url`** — Production URL
-- **`repo_url`** — GitHub repo link
- **`theme.palette`** — Light/dark mode (light is default)
- **`theme.features`** — Navigation behaviour toggles
- **`plugins`** — Search, versioning, minification, etc.
- **`extra_css` / `extra_javascript`** — Custom stylesheets and scripts

---

## Versioning with Mike

```bash
# Deploy current docs as version "1.0" aliased as "latest"
mike deploy --push --update-aliases 1.0 latest

# List all deployed versions
mike list

# Set the default version redirect
mike set-default latest

# Serve versioned docs locally
mike serve
```

---

## Key Commands

| Command | Description |
|---|---|
| `mkdocs serve` | Start live-reload dev server |
| `mkdocs serve --dirtyreload` | Faster dev server (rebuilds only changed pages) |
| `mkdocs build` | Build the static site to `site/` |
| `mkdocs build --strict` | Build with strict mode (fail on warnings) |
| `mike deploy <version>` | Deploy a versioned build to gh-pages |
| `mike serve` | Serve versioned docs locally |

---

## Useful Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Material Reference](https://squidfunk.github.io/mkdocs-material/reference/)
- [Awesome Pages Plugin](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin)
- [mike — Versioning](https://github.com/jimporter/mike)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

## Contributing

Thank you for helping improve the Actian MCP Server documentation portal.
`main` is the single source of truth for this repository. All contributions
are made against `main`; there is no separate long-lived branch for a given
release.

### Before you start

- Contributors never run `mike`. Version deployment (`mike deploy`, `mike
  set-default`, and similar) is handled separately by the documentation
  maintainers.
- Contributors never edit the `site/` directory. It is generated output and is
  overwritten on every build.
- All content changes belong under `docs/`. Only touch `mkdocs.yml`,
  `theme_overrides/`, or `hooks/` if you are intentionally changing the site's
  build or theme, and mention that clearly in your pull request.

### Local setup

Fork the repository, then follow [Installation](#installation) and
[Running Locally](#running-locally) above to clone your fork, install
dependencies, and start the live-reload development server.

### Making changes

1. Create a feature branch from `main`:

   ```bash
   git checkout -b docs/my-update
   ```

2. Edit or add Markdown files under `docs/`. See [Adding
   Documentation](#adding-documentation) above for page structure, front
   matter, and navigation ordering.

3. Preview your changes with `mkdocs serve` and confirm the page renders and
   navigates as expected.

4. Validate the build in strict mode before committing. Strict mode fails on
   warnings (broken links, missing nav entries, and so on), which is the same
   check applied before a release build:

   ```bash
   mkdocs build --strict
   ```

5. Commit your changes with a `docs:` prefix:

   ```bash
   git add docs/
   git commit -m "docs: describe your change here"
   ```

6. Push your branch and open a pull request targeting `main`. Describe the
   change and, if relevant, why it was needed.

### Style checklist

Before submitting, check your writing against these rules:

- [ ] Use Global English (avoid idioms, culturally specific references, and
      regional spelling; prefer terms understood by a worldwide audience).
- [ ] Follow the Chicago Manual of Style for punctuation, capitalization, and
      numbers.
- [ ] Expand acronyms on first use on a page, followed by the acronym in
      parentheses, for example: Model Context Protocol (MCP).
- [ ] Do not use em dashes or en dashes. Rewrite the sentence, or use a comma,
      parentheses, or a period instead.
- [ ] Use sentence case for headings (capitalize only the first word and
      proper nouns), not title case.

---

