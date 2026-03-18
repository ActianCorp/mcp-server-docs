---
title: Home
template: home-blocks.html
hide:
  - navigation
  - toc
  - feedback
---

<!-- Hero Section -->
<div class="actian-hero">
  <blockquote class="hero-quote">
    Connect AI agents to your Actian data sources with the Model Context Protocol.
  </blockquote>

  <div class="hero-cta">
    <a href="./get_started/index.html" class="primary-link">Get started →</a>
  </div>
</div>

<!-- Value Propositions -->
<div class="value-props-section">
  <div class="value-props-grid">
    <div class="value-prop-item">
      <h3 class="jumbo-heading">Connect</h3>
      <p class="value-prop-text">Bridge any MCP-compatible AI client — Claude, Cursor, or your own agent — directly to Actian Zen and Analytics Engine.</p>
    </div>
    <div class="value-prop-item">
      <h3 class="jumbo-heading">Extend</h3>
      <p class="value-prop-text">Build custom tools, resources, and prompts using the plugin architecture. Add new Actian data sources in minutes.</p>
    </div>
    <div class="value-prop-item">
      <h3 class="jumbo-heading">Trust</h3>
      <p class="value-prop-text">Secure every connection with OAuth 2.0, read-only mode, and multi-tenant isolation built into the core.</p>
    </div>
  </div>
</div>

<!-- Get Started Section -->
<div class="get-started-section">
  <div class="side-by-side">
    <div class="content-side">
      <h2 class="jumbo-heading">Up and running in minutes</h2>
      <p class="section-description">
        Install the server, drop in a config file, and your AI agent can query Actian databases, explore schemas, and run analytics — all through natural language.
      </p>
      <div class="section-cta">
        <a href="./get_started/index.html" class="primary-link">Read the quickstart →</a>
      </div>
    </div>
    <div class="code-side">
      <div class="code-block">
        <pre><code>pip install actian-mcp-server</code></pre>
      </div>
      <div class="code-block">
        <pre><code>actian-mcp-server \
  --config conf.json \
  --transport stdio</code></pre>
      </div>
    </div>
  </div>
</div>

<!-- Features Section -->
<div class="features-section">
  <div class="features-header">
    <h3 class="jumbo-heading">Everything you need to build with MCP</h3>
    <p class="features-subtitle">
      From schema introspection to query execution to custom plugins, the Actian MCP Server gives AI agents full, governed access to your data.
    </p>
  </div>

  <div class="features-grid">
    <div class="feature-item">
      <h4 class="feature-title">Tools & Resources</h4>
      <p class="feature-description">Expose SQL execution, schema discovery, and data operations as MCP-native tools and resources.</p>
      <a href="./develop_with_mcp/index.html" class="primary-link">Develop with MCP →</a>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Plugin Architecture</h4>
      <p class="feature-description">Extend the server with custom plugins for any Actian product or third-party data source.</p>
      <a href="./develop_with_mcp/plugins/index.html" class="primary-link">Build a plugin →</a>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Secure by Default</h4>
      <p class="feature-description">OAuth 2.0 authentication, read-only mode, and multi-tenancy support out of the box.</p>
      <a href="./configuration/index.html" class="primary-link">Configure security →</a>
    </div>
  </div>
</div>
