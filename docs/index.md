---
title: Home
template: home-blocks.html
hide:
  - navigation
  - toc
  - feedback
---

<!-- What is MCP? -->
<div class="databases-section">
  <div class="features-header">
    <h3 class="jumbo-heading">What is MCP?</h3>
    <p class="databases-subtitle">
      The Model Context Protocol (MCP) is an open standard that enables Large Language Models (LLMs) to securely access and interact with external data sources and tools. Think of MCP as a <strong>"USB-C port for AI."</strong> Instead of building fragile, custom integrations for every database, MCP provides a standardized way for an AI model to "plug in" to your infrastructure. This allows the model to understand schemas, execute queries, and retrieve real-time context without the data ever leaving your secure environment.
    </p>
    <div class="hero-cta">
      <a href="https://hub.docker.com/u/actian" class="primary-link">Browse the Actian MCP Hub →</a>
      <a href="./get_started/index.html" class="primary-link" style="margin-left:1.5rem;">View Documentation →</a>
    </div>
  </div>
</div>

<!-- Why MCP for Agentic AI? -->
<div class="features-section">
  <div class="features-header">
    <h3 class="jumbo-heading">Why MCP for Agentic AI?</h3>
    <p class="features-subtitle">
      We are moving beyond simple chatbots to <strong>Agentic AI</strong> — systems that can reason, plan, and execute tasks autonomously. To be effective, these agents require more than just a training set; they need "eyes and hands" inside your data estate.
    </p>
  </div>

  <div class="features-grid">
    <div class="feature-item">
      <h4 class="feature-title">Autonomous Exploration</h4>
      <p class="feature-description">MCP allows agents to explore your database schemas to find the right data to answer a complex prompt, reducing the need for hard-coded prompts.</p>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Grounding and Truth</h4>
      <p class="feature-description">By querying Actian Ingres or HCL Informix in real-time, agents provide answers grounded in your latest business facts, eliminating "hallucinations."</p>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Tool-Use Capabilities</h4>
      <p class="feature-description">MCP transforms database functions (like a complex Join in the Analytics Engine or a search in NoSQL) into "Tools" the agent can choose to use when appropriate.</p>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Contextual Memory</h4>
      <p class="feature-description">Agents can use databases like Actian Zen at the edge to store and retrieve long-term state across different user sessions.</p>
    </div>
  </div>
</div>

<!-- The Actian MCP Hub: Specialized Connectors -->
<div class="databases-section" style="text-align: center;">
  <div class="databases-header" style="text-align: center;">
    <h3 class="jumbo-heading">The Actian MCP Hub: Specialized Connectors</h3>
    <p class="databases-subtitle" style="max-width: 700px; margin: 0 auto;">
      While MCP is a universal protocol, the performance must be native. We provide a centralized repository on Docker Hub containing optimized, dedicated images for our entire portfolio.
    </p>
  </div>

  <table style="margin: 0 auto;">
    <thead>
      <tr>
        <th>Database</th>
        <th>MCP Image Name</th>
        <th>Suited For</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="./analytics_engine/index.html">Actian Analytics Engine</a></td>
        <td><code>actian/mcp-server-ae</code></td>
        <td>Large-scale RAG and high-performance vector analysis.</td>
      </tr>
      <tr>
        <td><a href="./ingres/index.html">Actian Ingres</a></td>
        <td><code>actian/mcp-server-ingres</code></td>
        <td>Mission-critical relational data and enterprise logic.</td>
      </tr>
      <tr>
        <td><a href="./nosql/index.html">Actian NoSQL</a></td>
        <td><code>actian/mcp-server-nosql</code></td>
        <td>High-fidelity context from complex object structures.</td>
      </tr>
      <tr>
        <td><a href="./zen/index.html">Actian Zen</a></td>
        <td><code>actian/mcp-server-zen</code></td>
        <td>Edge-based AI and zero-admin mobile applications.</td>
      </tr>
      <tr>
        <td><a href="./informix/index.html">HCL Informix</a></td>
        <td><code>actian/mcp-server-informix</code></td>
        <td>Time-series, IoT, and high-availability spatial data.</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Enterprise Architecture -->
<div class="features-section">
  <div class="features-header">
    <h3 class="jumbo-heading">Enterprise Architecture</h3>
    <p class="features-subtitle">
      The Actian MCP Server acts as a stateless security proxy between your Agent and your Database.
    </p>
  </div>

  <div class="features-grid">
    <div class="feature-item">
      <h4 class="feature-title">1. Agent Request</h4>
      <p class="feature-description">The Agent (for example, Claude, GPT-4o) requests a specific tool or data point.</p>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">2. Native Translation</h4>
      <p class="feature-description">The MCP Server (running in your Docker environment) translates that request into native DB syntax.</p>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">3. Secure Execution</h4>
      <p class="feature-description">The Database executes the request and returns only the necessary context.</p>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">4. Agentic Action</h4>
      <p class="feature-description">The Agent uses that context to complete its task or plan its next move.</p>
    </div>
  </div>
</div>

<!-- Get Started in Minutes -->
<div class="get-started-section">
  <div class="side-by-side">
    <div class="content-side">
      <h2 class="jumbo-heading">Get Started in Minutes</h2>
      <p class="section-description">
        All MCP server images are available at <strong>hub.docker.com/u/actian</strong>. You can spin up a specific server using standard container orchestration.
      </p>
      <div class="section-cta">
        <a href="./get_started/index.html" class="primary-link">Read the quickstart →</a>
      </div>
    </div>
    <div class="code-side">
      <div class="code-block">
        <pre><code># Example: Launch the HCL Informix MCP Server
docker pull actian/mcp-server-informix:latest

# Run with your secure environment variables
docker run -e INFORMIXSERVER=myserver \
  -e DB_NAME=finance \
  actian/mcp-server-informix</code></pre>
      </div>
    </div>
  </div>
</div>

<!-- Security & Governance -->
<div class="features-section" style="border-top: none;">
  <div class="features-header">
    <h3 class="jumbo-heading">Security and Governance</h3>
  </div>

  <div class="features-grid" style="grid-template-columns: repeat(3, 1fr);">
    <div class="feature-item">
      <h4 class="feature-title">Identity-Aware</h4>
      <p class="feature-description">Supports modern authentication to ensure agents only see the data they are authorized to access.</p>
      <a href="./authentication/index.html" class="primary-link">Set up authentication →</a>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Read-Only Enforced</h4>
      <p class="feature-description">Configuration toggles allow you to ensure agents can read data but never modify it.</p>
      <a href="./intro/index.html" class="primary-link">Learn about read-only mode →</a>
    </div>

    <div class="feature-item">
      <h4 class="feature-title">Audit Trails</h4>
      <p class="feature-description">Every tool call and query generated by the AI is logged for compliance and monitoring.</p>
      <a href="./intro/index.html" class="primary-link">Explore the architecture →</a>
    </div>
  </div>
</div>

<!-- Footer CTA -->
<div class="cta-section">
  <h2>Empower your agents with the world's most reliable data.</h2>
  <div class="cta-buttons">
    <a href="https://hub.docker.com/u/actian" class="primary-link">Visit the Actian Docker Hub →</a>
    <a href="https://www.actian.com/contact/" class="primary-link" style="margin-left:1.5rem;">Contact an AI Architect →</a>
  </div>
</div>
