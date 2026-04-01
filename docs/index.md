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
    Connect AI agents to your Actian databases with the Model Context Protocol.
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
      <p class="value-prop-text">Bridge any MCP-compatible AI client directly to Ingres, Analytics Engine, Informix, NoSQL, and Zen.</p>
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

<!-- Supported Databases Section -->
<div class="databases-section">
  <div class="databases-header">
    <h3 class="jumbo-heading">One server, every Actian database</h3>
    <p class="databases-subtitle">
      The Actian MCP Server provides a unified MCP interface across the full Actian database portfolio. Each database has its own tools, resources, and prompts tailored to its capabilities.
    </p>
  </div>

  <div class="databases-grid">
    <a class="database-card" href="./analytics_engine/index.html">
      <h4 class="database-name">Analytics Engine</h4>
      <p class="database-description">Column-store analytics database optimized for complex queries, large-scale aggregations, and data warehousing workloads.</p>
    </a>

    <a class="database-card" href="./ingres/index.html">
      <h4 class="database-name">Ingres</h4>
      <p class="database-description">Enterprise relational database with full ACID compliance, robust SQL support, and proven scalability for mission-critical applications.</p>
    </a>

    <a class="database-card" href="./informix/index.html">
      <h4 class="database-name">Informix&reg;</h4>
      <p class="database-description">High-performance relational database designed for OLTP workloads, time-series data, and IoT applications.</p>
    </a>

    <a class="database-card" href="./nosql/index.html">
      <h4 class="database-name">NoSQL</h4>
      <p class="database-description">Flexible document and key-value store for schema-free data models, JSON documents, and rapid application development.</p>
    </a>

    <a class="database-card" href="./zen/index.html">
      <h4 class="database-name">Zen</h4>
      <p class="database-description">Edge-to-cloud embedded database with zero-administration deployment, local and remote data access, and minimal resource requirements.</p>
    </a>
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
      <h4 class="feature-title">Tools & resources</h4>
      <p class="feature-description">Expose SQL execution, schema discovery, and data operations as MCP-native tools and resources.</p>
      <a href="./analytics_engine/tools/index.html" class="primary-link">Explore tools →</a>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Authentication & security</h4>
      <p class="feature-description">OAuth 2.0 with Keycloak or Auth0, TLS encryption, read-only mode, and user impersonation out of the box.</p>
      <a href="./authentication/index.html" class="primary-link">Set up authentication →</a>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Flexible deployment</h4>
      <p class="feature-description">Run locally with stdio, expose over HTTP/SSE for remote clients, or deploy as a Docker container.</p>
      <a href="./get_started/deployment.html" class="primary-link">Deploy the server →</a>
    </div>
  </div>
</div>
