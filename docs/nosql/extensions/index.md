---
title: Extensions
description: Add your own tools, resources, and prompts to the Actian MCP Server for NoSQL with a Java extension JAR, and the allowlist, verification, and trust model an operator uses to deploy one.
---

# Extensions

An extension is a Java JAR that adds tools, resources, resource templates, and prompts to a running Actian MCP Server for Actian NoSQL. The server loads it at startup and registers what it finds; nothing in the core product changes, and no fork is involved.

The subsystem is off until an operator turns it on with `nsql.extensions.enabled`, and even then the server loads only the JARs the operator has explicitly declared. A server that never sets the property behaves exactly as it does today.

## What an extension can contribute

Four kinds of thing, each declared by annotating a plain Java method. The annotations come from the framework-neutral `org.mcpjava` library rather than from a server-specific package, so an extension never compiles against the server's own MCP internals.

| Contribution | Annotation | What the method returns |
|--------------|-----------|-------------------------|
| Tool | `@Tool`, with arguments marked `@ToolArg` | Any record or POJO. By default the result is serialized as JSON text. To also emit structured content with a generated output schema, either set `structuredContent = true` to derive the schema from the method's return type, or name the class explicitly with `outputSchemaFrom`. If both are set, `outputSchemaFrom` wins. |
| Resource | `@Resource`, addressed purely by its fixed URI | A record or POJO (serialized to JSON), a `byte[]` for binary content, or a `String` passed through as raw text. |
| Resource template | `@ResourceTemplate`, with `{placeholder}` segments in the URI bound to `@ResourceTemplateArg` parameters | The same three shapes as a resource. |
| Prompt | `@Prompt`, with arguments marked `@PromptArg` | A `String`. It reaches the client as a single message attributed to the user role; per-message roles are not available in this release. |

A tool argument does not have to be a scalar. A record, a POJO, a list or set of them, or a map all work, and the input schema is generated from the type's own fields.

!!! warning "An omitted `mimeType()` is blank, not JSON"
    On `@Resource` and `@ResourceTemplate`, leaving `mimeType()` unset registers an empty MIME type rather than defaulting to `application/json`. If your resource returns JSON and clients need that advertised, set it yourself.

Handlers never serialize their own return values — the loader does it from the method's declared return type, so an extension needs no JSON library of its own.

## Authoring at a glance

Every extension implements `McpExtension` and names its implementation in a `META-INF/services` file. That interface is how the server finds the extension at all: discovery runs through `ServiceLoader`, not through a class name in configuration.

```java
package com.example.forecasting;

import com.actian.mcp.extension.ExtensionContext;
import com.actian.mcp.extension.McpExtension;
import org.mcpjava.server.tools.Tool;
import org.mcpjava.server.tools.ToolArg;

public final class RevenueForecastExtension implements McpExtension {

    private ForecastModel model;

    @Tool(
        name = "forecast_revenue",
        title = "Forecast Revenue",
        description = "Run the revenue forecast model for one region and quarter.",
        annotations = @Tool.Annotations(readOnlyHint = true),
        structuredContent = true)
    public ForecastResult forecastRevenue(
            @ToolArg(description = "Fiscal quarter, e.g. 2026-Q1") String quarter,
            @ToolArg(description = "Region code: NA, EMEA, APAC") String region,
            ExtensionContext context) {
        context.log().info("Forecasting %s for %s", quarter, region);
        return model.predict(quarter, region);
    }

    @Override
    public void initialize(ExtensionContext context) {
        int horizonMonths = context.config()
            .getOptionalValue("horizonMonths", Integer.class)
            .orElse(12);
        model = ForecastModel.load(horizonMonths);
    }

    @Override
    public void destroy() {
        model.close();
    }
}
```

The provider file, `META-INF/services/com.actian.mcp.extension.McpExtension`, holds one line:

```text
com.example.forecasting.RevenueForecastExtension
```

`initialize` and `destroy` both have no-op defaults, so override them only when you have startup or shutdown work — an extension whose handlers are self-contained can leave both alone. `initialize` runs once per extension after every extension has registered its methods, in JAR load order; `destroy` runs at shutdown in the reverse order, which is why anything acquired in the first is released in the second.

### What an extension can reach

`ExtensionContext` is the extension's entire view of the server, and it arrives in two places. Any handler method can declare it as a parameter, as `forecastRevenue` does above, and gets one scoped to that call. `initialize` is handed one as its argument, for startup work such as reading configuration.

The distinction matters, because not every member means something at startup: `confirm()` and `log()` need a live call to a client, and `currentUser()` and `currentScopes()` describe whoever made that call.

| Member | What it gives you |
|--------|-------------------|
| `config()` | This extension's own settings, from `nsql.extensions.jars.<id>.config.*`. Isolated by design: it exposes no other extension's keys and none of the server's global configuration. Treat it as a flat key/value lookup — profiles, `${...}` expansion, environment variables, and system properties are all deliberately inactive. |
| `newEntityManager()` | A new `EntityManager` on the same factory the server uses. You close it. Note the package is `javax.persistence`, not `jakarta.persistence` — the Versant JPA provider predates the Jakarta namespace change. |
| `currentUser()` | The authenticated principal, or empty when the caller is anonymous or authentication is off server-wide. |
| `currentScopes()`, `hasScope(scope)` | The caller's OAuth scopes, and a convenience check for one of them. |
| `confirm(message)` | Asks a person to approve an operation, with a message you compose. See [Write gating for extension tools](#write-gating-for-extension-tools). |
| `log()` | Sends MCP log notifications to the connected client, at a level you choose. |

!!! note "`confirm()` and `log()` work only inside a tool handler"
    Both need a live per-call channel to the client. Calling either from `initialize` or from a resource or prompt handler throws `UnsupportedOperationException`.

### Getting the SDK

Everything needed to write an extension ships in the **Extension SDK**, a self-contained zip that asks only for Java 21 and Maven. It carries the API JAR, a project you can build straight away, and `SchemaExplorerExtension` — a working example that exercises every contribution kind described on this page, and the easiest starting point for a real extension.

It also carries the API Javadoc, which goes further than this page does: every annotation's full attribute list, each member of `ExtensionContext`, and the rules the server applies while loading your JAR.

<!-- TODO: confirm the exact ESD product and release path before publishing. ESD currently lists
     Actian NoSQL Database and Actian NoSQL JPA; the SDK is filed under neither today. -->
The SDK is available from [esd.actian.com](https://esd.actian.com/) under Actian NoSQL Database.

## Write gating for extension tools

An extension tool that changes data passes the same checks as a built-in one. There is no separate extension permission model and no way for an extension to opt out.

The server decides which is which from one signal: a tool is a **write** unless it declares `readOnlyHint = true`.

```java
annotations = @Tool.Annotations(readOnlyHint = true)   // read tool
annotations = @Tool.Annotations(readOnlyHint = false)  // write tool
// annotations omitted entirely                        // also a write tool
```

That default is deliberate. Omitting the annotation gives you gating rather than a bypass, so forgetting to think about it fails safe. Once classified as a write, the tool is subject to `nsql.writes.enabled` and, when authentication is on, the caller's `mcp:write` scope — both enforced at the tool boundary, before your handler runs. [Write support](../write-support.md) describes both checks, and the same page explains why the tool may not appear in the client's tool list at all.

Confirmation works differently from the built-in tools. It is opt-in: nothing prompts the user unless your handler calls `context.confirm(...)`, and you write the message. What you cannot do is influence the answer — the server enforces it, throwing if the user declines, cancels, leaves it unconfirmed, does not respond in time, or is on a client that cannot show prompts at all. An operator who sets `nsql.writes.confirmation-required=false` silences your prompt along with the built-in ones, since both use the same mechanism.

## Enabling and declaring extensions

`nsql.extensions.enabled` turns the subsystem on, and `nsql.extensions.directory` says where to look. Putting a JAR in that directory is not enough to load it, though: the server loads exactly the JARs declared in an allowlist, each under a stable id you choose, and ignores anything else it finds there.

| Property | Default | Description |
|----------|---------|-------------|
| `nsql.extensions.enabled` | `false` | Master switch. While `false`, no JAR is scanned or loaded. |
| `nsql.extensions.directory` | `/extensions` | Where declared JARs are read from. There is no hot reload — restart to pick up a change. |
| `nsql.extensions.verification.mode` | `sha256` | Which provenance checks a declared JAR must pass, as a comma-separated list; all listed checks must pass. `sha256` requires each JAR's bytes to match its pinned digest. `none` skips the check and must be the only value. This never changes *which* JARs load — that is always the allowlist. |
| `nsql.extensions.jars.<id>.file` | — | The JAR's filename, relative to the extensions directory. |
| `nsql.extensions.jars.<id>.sha256` | — | The pinned digest, lowercase hex. Required while `verification.mode` includes `sha256`. |
| `nsql.extensions.jars.<id>.order` | — | Optional load order. See the rule below. |
| `nsql.extensions.jars.<id>.config.*` | — | Free-form settings for this JAR alone, readable through `ExtensionContext.config()`. |

### The ordering rule

`order` is optional, but it is all or nothing: **number every declared JAR, or number none of them.** Numbers must be unique. Declaring `order` on some JARs and not others, or reusing a value, aborts startup with an error naming the problem.

With no `order` anywhere, JARs load sorted by their declared id. The order matters only for `initialize` at startup and `destroy` at shutdown, so most deployments never need it — reach for it when one extension's `initialize` has to run before another's.

### Deploying an extension JAR

**1. Compute the JAR's digest** with whatever your platform provides:

```bash
shasum -a 256 revenue-forecast-1.0.0.jar               # macOS, BSD
sha256sum revenue-forecast-1.0.0.jar                   # Linux
CertUtil -hashfile revenue-forecast-1.0.0.jar SHA256   # Windows
```

**2. Declare the JAR** in `application.properties`, pasting in the digest you just computed:

```properties
nsql.extensions.enabled=true
nsql.extensions.directory=/opt/nsql-mcp/extensions

nsql.extensions.jars.forecasting.file=revenue-forecast-1.0.0.jar
nsql.extensions.jars.forecasting.sha256=9f2b8c1d4e...
nsql.extensions.jars.forecasting.config.horizonMonths=18
```

**3. Put the JAR in the directory and restart.** Mount it into the container alongside your configuration:

```bash
docker run \
  -v $(pwd)/application.properties:/home/jboss/config/application.properties:ro \
  -v $(pwd)/extensions:/opt/nsql-mcp/extensions:ro \
  -p 8080:8080 \
  actian/nsql-mcp-server:1.1.0
```

Mounting read-only is worth doing: the server only ever reads from this directory, and see [Security and trust model](#security-and-trust-model) for why write access to it matters.

!!! note "Bundle your dependencies into the extension JAR"
    Each extension is loaded by a classloader holding one JAR — its own — plus the server's own classpath. A second JAR sitting in the directory is not on that classpath, whether or not you declare it, so a third-party library your extension needs must be shaded into the extension JAR itself. Build an uber-JAR, and pin the digest of that.

    The two API JARs are the exception, and must stay unshaded. See [Never shade the API JARs](#security-and-trust-model) below.

## Startup behavior and failure modes

Extension loading is all or nothing. Anything that goes wrong stops the server rather than starting it in a reduced state, so a server that comes up is a server whose extensions all loaded.

| What you see at startup | Cause | What to do |
|-------------------------|-------|------------|
| Startup aborts, reporting a digest mismatch | The JAR's bytes are not the ones pinned in `sha256`. | Recompute the digest from the JAR you actually deployed and update the declaration — or work out why the file changed. |
| Startup aborts, reporting a missing file | `nsql.extensions.jars.<id>.file` names something that is not in the directory. | Check the filename and the mount. |
| Startup aborts, reporting no `ServiceLoader` provider | The JAR has no `META-INF/services/com.actian.mcp.extension.McpExtension` file. | Add the provider file naming your `McpExtension` implementation. |
| Startup aborts, reporting a duplicate name or URI | A tool, resource, resource template, or prompt collides with a built-in or with an extension loaded earlier. | Rename it. Prefixing every name and URI with something specific to your extension avoids this. |
| Startup aborts with an exception from your own code | `initialize` threw a `RuntimeException`. | Fix the underlying condition. Throwing from `initialize` is a legitimate way to refuse to start on bad configuration. |

Shutdown is more forgiving: an exception from `destroy` is logged, and the remaining extensions are still torn down.

## Security and trust model

An extension is not sandboxed. It runs inside the server's JVM with the full access that implies — the database, the configuration, the network, the filesystem. Deploying one is closer to adding a library to your own application than to running third-party code in a container.

The point that catches people out: the guardrails on this page protect the `@Tool` surface an extension *declares*, and nothing more. An extension holds a live `EntityManager` and can read or write anything through it, at any time, without passing write gating, the `mcp:write` scope, or a confirmation prompt. Those checks constrain how a *client* reaches an extension's tools. They are not a boundary around the extension's own code, and were never intended as one.

SHA-256 verification is provenance, not containment. It proves the bytes the server loaded are the bytes you reviewed and pinned; it says nothing about what those bytes do, and it does not vet the extension's transitive dependencies.

That makes the extensions directory the real boundary. Keep it operator-owned and not world-writable, prefer a read-only mount or an image that bakes the JARs in, and review an extension before you pin its digest — the digest records your decision, it does not make it for you.

!!! warning "Never shade the API JARs into your extension"
    Keep both `nsql-mcp-extension-api` and `org.mcpjava:mcp-server-api` as `provided`-scope, unshaded dependencies. The server loads both from its own classpath, and a bundled copy is a second, different class of the same name.

    For `nsql-mcp-extension-api` this breaks `ServiceLoader` outright: your `McpExtension` and the server's are no longer the same type, so your extension may never be discovered. For `org.mcpjava:mcp-server-api`, a bundled copy can shadow the annotation types the server's reflectors read.

    Shading your *other* runtime dependencies into an uber-JAR is fine, and it helps — an operator can then run composition analysis against a single artifact before pinning its digest.

## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write support](../write-support.md)**  
  The checks an extension's write tools inherit, and how to turn writes on.

- :material-tools: **[Tools](../tools/index.md)**  
  The built-in tools, and the response shapes an extension's own tools sit alongside.

- :material-lock: **[Authentication](../authentication/index.md)**  
  Enable OAuth 2.0, so `currentUser()`, `currentScopes()`, and `mcp:write` carry real values.

</div>
