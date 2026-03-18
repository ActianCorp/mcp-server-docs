# Actian Data Intelligence Platform — Documentation Portal

> Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) · Dark/light theme · AI chatbot · Versioned with [mike](https://github.com/jimporter/mike)

**Live site:** https://testdocs.actian.com/zeenea_poc/site/index.html

---

## Using This Repo as a Template

This repository is a production-ready MkDocs Material template. You can clone it and replace the content under `docs/` with your own documentation.

### What's Included

| Feature | Description |
|---|---|
| **MkDocs Material 9.6+** | Modern Material Design theme with dark/light toggle |
| **Navigation** | Tabs, sections, breadcrumbs, instant loading, pruning |
| **Search** | Enhanced search with highlighting, suggestions, and sharing |
| **Diagrams** | Mermaid and PlantUML diagram support |
| **API docs** | Swagger UI tag plugin for OpenAPI specs |
| **Versioning** | Multi-version support via `mike` |
| **SEO** | Auto-generated meta descriptions, robots.txt, sitemap |
| **Code blocks** | Copy button, syntax highlighting, annotations |
| **AI chatbot** | Floating chat widget (custom JavaScript) |
| **Custom 404** | Branded 404 page with search and popular links |
| **CI/CD** | Jenkins pipeline for automated builds |

---

## Project Structure

```
mkdocs_poc/
├── mkdocs.yml                  # Main MkDocs configuration
├── requirements.txt            # Python dependencies
├── makefile                    # Docker shortcuts
├── docs/                       # All your documentation content goes here
│   ├── index.md                # Homepage content
│   ├── .pages                  # Navigation ordering (awesome-pages plugin)
│   ├── .meta.yml               # Default front matter for all pages
│   ├── tags.md                 # Auto-generated tags index
│   ├── robots.txt              # Search engine directives
│   ├── assets/                 # Images, logos, homepage assets
│   │   ├── homepage-images/    # Landing page images
│   │   └── stylesheets/        # Site-wide CSS (style.css)
│   ├── stylesheets/            # Component CSS (chatbot, search, etc.)
│   ├── javascripts/            # Custom JS (chatbot, search, mermaid)
│   ├── APIs/                   # API documentation & OpenAPI specs
│   ├── get_started/            # Getting started guides
│   ├── Zeenea/                 # Product overview section
│   ├── Zeenea_Administration/  # Admin guides
│   ├── Zeenea_Explorer/        # Explorer user guides
│   └── Zeenea_Studio/          # Studio user guides
├── theme_overrides/            # Custom theme templates
│   ├── main.html               # Base template (header, banner, scripts)
│   ├── home.html               # Landing page template
│   ├── home-blocks.html        # Landing page content blocks
│   ├── 404.html                # Custom 404 page
│   ├── assets/stylesheets/     # Landing page & dark mode CSS
│   └── partials/               # Partial templates (comments, etc.)
├── hooks/                      # MkDocs build hooks
│   ├── bitbucket_edit_url.py   # Edit URL for Bitbucket
│   └── custom_lexers.py        # Custom syntax highlighters
├── jenkins/                    # CI/CD pipeline
│   ├── Jenkinsfile             # Build pipeline
│   └── pr-checks.groovy        # PR validation
├── utils/                      # Utility scripts (audits, link checks)
└── site/                       # Built output (auto-generated, do not edit)
```

---

## Prerequisites

- **Python 3.9+** (recommended: 3.10 or later)
- **pip** (comes with Python)
- **Git**

Verify your setup:

```bash
python --version   # Should print 3.9+
pip --version
git --version
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://alm.actian.com/bitbucket/users/bpandey/repos/mkdocs_poc
cd mkdocs_poc
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

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

### Option A: Direct (recommended for development)

```bash
mkdocs serve
```

Opens a live-reload development server at **http://127.0.0.1:8000**. Changes to any file under `docs/` are reflected instantly.

### Option B: Dirty reload (faster for large sites)

```bash
mkdocs serve --dirtyreload
```

Only rebuilds changed pages — much faster on large documentation sites.

### Option C: Docker container

```bash
make run-in-faster-container
```

Runs MkDocs inside a Python Docker container — no local Python installation required.

---

## Building the Site

```bash
mkdocs build
```

Generates the static site in the `site/` directory. This is what gets deployed to production.

To preview the built site locally:

```bash
python -m http.server 8080 --directory site
```

Then open **http://127.0.0.1:8080** in your browser.

---

## Adding Your Own Content

### Step 1: Create a section folder and Markdown files

Add new `.md` files in the appropriate folder under `docs/`:

```
docs/
├── my_section/
│   ├── index.md            # Section landing page
│   ├── getting-started.md  # A guide page
│   └── images/             # Section-specific images
│       └── screenshot.png
```

### Step 2: Write your content

Each page can include optional front matter for SEO and categorization:

```markdown
---
title: My Page Title
description: A brief description for search engines.
tags:
  - guide
  - setup
---

# My Page Title

Your content here. This template supports:

- **Admonitions** — `!!! note`, `!!! warning`, `!!! tip`, etc.
- **Code blocks** — with syntax highlighting and a copy button
- **Mermaid diagrams** — inside ` ```mermaid ` fenced blocks
- **PlantUML diagrams** — via the `plantuml_markdown` extension
- **Tabbed content** — with `=== "Tab 1"` syntax
- **Tables, images, links** — standard Markdown
```

### Step 3: Control navigation order

Create a `.pages` file in your section folder to set the page ordering:

```yaml
# docs/my_section/.pages
nav:
  - index.md
  - getting-started.md
  - advanced-usage.md
```

Without a `.pages` file, navigation order is inferred alphabetically from file names.

### Step 4: Preview and commit

```bash
mkdocs serve              # Preview at http://127.0.0.1:8000
git add .
git commit -m "Add my_section documentation"
git push
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

The `mkdocs-swagger-ui-tag` plugin renders interactive API documentation automatically.

---

## Customizing the Theme

### Colors and branding

| File | What it controls |
|---|---|
| `theme_overrides/assets/stylesheets/actian-landing.css` | Landing page, dark mode overrides, CSS variables |
| `docs/assets/stylesheets/style.css` | Header, tabs, search bar, general overrides |
| `docs/stylesheets/minichat.css` | AI chatbot widget styles |
| `docs/stylesheets/dx_style.css` | Search enhancements, syntax highlighting |

### Logos and images

- **Site logo:** Replace `docs/assets/dx_logo.png`
- **Favicon:** Replace `docs/assets/favicon.png`
- **Landing page images:** Add to `docs/assets/homepage-images/`

### Templates

| File | Purpose |
|---|---|
| `theme_overrides/main.html` | Header banner, announcement bar, scripts |
| `theme_overrides/home.html` | Landing page layout |
| `theme_overrides/home-blocks.html` | Landing page content blocks |
| `theme_overrides/404.html` | Custom 404 error page |

### Configuration (`mkdocs.yml`)

Key sections you may want to modify:

- **`site_name`** — Your documentation title
- **`site_url`** — Production URL
- **`theme.palette`** — Dark/light mode colors (dark is default)
- **`theme.features`** — Navigation behavior toggles
- **`markdown_extensions`** — Enable/disable Markdown features
- **`plugins`** — Search, tags, versioning, minification, etc.
- **`extra_css` / `extra_javascript`** — Custom stylesheets and scripts
- **`repo_url`** — Link to your source repository

---

## Versioning with Mike

This project uses [mike](https://github.com/jimporter/mike) for multi-version documentation:

```bash
# Deploy current docs as version "1.0" and alias it as "latest"
mike deploy 1.0 latest --update-aliases

# List all deployed versions
mike list

# Set the default version redirect
mike set-default latest

# Serve versioned docs locally
mike serve
```

---

## Key MkDocs Commands

| Command | Description |
|---|---|
| `mkdocs serve` | Start live-reload dev server |
| `mkdocs serve --dirtyreload` | Faster dev server (rebuilds only changed pages) |
| `mkdocs build` | Build the static site to `site/` |
| `mkdocs build --strict` | Build with strict mode (fail on warnings) |
| `mike deploy <version>` | Deploy a versioned build |
| `mike serve` | Serve versioned docs locally |

---

## Useful Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Material Reference](https://squidfunk.github.io/mkdocs-material/reference/) — Admonitions, code blocks, tabs, diagrams, etc.
- [Awesome Pages Plugin](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin)
- [mike — Versioning](https://github.com/jimporter/mike)
- [MkDocs Plugins Catalog](https://github.com/mkdocs/catalog)

---

## Contributing

1. Clone the repository
2. Create a feature branch: `git checkout -b feature/my-update`
3. Make your changes in the `docs/` directory
4. Preview locally with `mkdocs serve`
5. Commit and push
6. Open a Pull Request

> **Note:** Only edit files in `docs/` unless you are intentionally modifying the theme, build hooks, or CI pipeline.

---

## License

Available as open source under the terms of the [Apache License 2.0](http://www.apache.org/licenses/).
