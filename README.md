# Actian MCP Server — Documentation Portal

> Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) · Light/dark theme · Versioned with [mike](https://github.com/jimporter/mike)

**Repository:** https://alm.actian.com/bitbucket/users/alokaj/repos/actian_mcp_server  
**Branch:** `mcpdocs`

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
| **Edit on Bitbucket** | Per-page edit button linking to `mcpdocs` branch |

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
│   ├── bitbucket_edit_url.py   # Generates edit URLs for mcpdocs branch
│   └── custom_lexers.py        # Custom syntax highlighters
├── utils/                      # Utility scripts (audits, link checks)
└── site/                       # Built output (auto-generated, do not edit)
```

---


## Installation

### 1. Clone the repository

```bash
git clone https://alm.actian.com/bitbucket/users/alokaj/repos/actian_mcp_server
cd actian_mcp_server
git checkout mcpdocs
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
git push origin mcpdocs
```

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
- **`repo_url`** — Bitbucket repo link
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

## Using the Edit Button on the Documentation Portal

Every page on the published documentation site has a **pencil (✏️) edit icon** in the top-right corner (next to the page title). Use it to suggest corrections, report errors, or improve content directly.

### How it works

1. **Click the edit icon** on any documentation page.  
   You will be taken directly to the source `.md` file for that page in Bitbucket, on the `mcpdocs` branch.

2. **Edit the file** in Bitbucket's web editor:
   - Click **Edit** (pencil icon) in Bitbucket's file toolbar.
   - Make your changes to the Markdown content.

3. **Commit your changes:**
   - Scroll down to the **Commit changes** section.
   - Add a short commit message describing what you changed.
   - Choose **"Create a new branch"** if you do not have write access to `mcpdocs`, then open a Pull Request.
   - If you have write access, you can commit directly to `mcpdocs`.

4. **Open a Pull Request** (if on a feature branch):
   - Target branch: `mcpdocs`
   - Add a description of your change and assign a reviewer.

### Edit URL format

The edit button points to:

```
https://alm.actian.com/bitbucket/users/alokaj/repos/actian_mcp_server/browse/docs/{page-path}?at=refs%2Fheads%2Fmcpdocs&mode=edit
```

> **Tip:** If the edit icon is not visible, ensure you are viewing the published HTML portal (served via mike or the deployed site), not a local `mkdocs serve` preview.

---

## Contributing

1. Clone the repository and check out the `mcpdocs` branch
2. Create a feature branch: `git checkout -b feature/my-update`
3. Make your changes in the `docs/` directory
4. Preview locally with `mkdocs serve`
5. Commit and push to Bitbucket
6. Open a Pull Request targeting `mcpdocs`

> **Note:** Only edit files in `docs/` unless you are intentionally modifying the theme, build hooks, or CI pipeline.

---

