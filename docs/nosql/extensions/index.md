---
title: Extensions
description: Add your own tools, resources, and prompts to the Actian MCP Server for NoSQL with a Java extension JAR, and the allowlist, verification, and trust model an operator uses to deploy one.
---

# Extensions

An extension is a Java JAR that adds tools, resources, resource templates, and prompts to a running Actian MCP Server for Actian NoSQL. The server loads it at startup and registers what it finds; nothing in the core product changes, and no fork is involved.

The subsystem is off until an operator turns it on with `nsql.extensions.enabled`, and even then the server loads only the JARs the operator has explicitly declared. A server that never sets the property behaves exactly as it does today.

## Extension Contributions

An extension contributes four kinds of thing, each declared by annotating a plain Java method. The annotations come from the framework-neutral `org.mcpjava` library rather than from a server-specific package, so an extension never compiles against the server's own MCP internals.

| Contribution | Annotation | What the method returns |
|--------------|-----------|-------------------------|
| Tool | `@Tool`, with arguments marked `@ToolArg` | A `String`, a content block, an `org.mcpjava.server.tools.ToolResponse`, a list of these, or any record or POJO. What the client receives for each is described under [Tool Return Types](#tool-return-types). Setting `structuredContent = true` sends the return value as structured content, with an output schema derived from the method's return type. `outputSchemaFrom` names the schema class explicitly and also turns structured content on. If both are set, the schema comes from `outputSchemaFrom`. |
| Resource | `@Resource`, addressed purely by its fixed URI | A `String` (one text content), a `byte[]` (one binary blob), any other record, POJO or `Map` (one text content holding its JSON), a `List` of these (one content per element), or an `org.mcpjava.server.resources.ResourceResponse`, which is sent as built. What the client receives for each is described under [Resource Return Types](#resource-return-types). |
| Resource template | `@ResourceTemplate`, with `{placeholder}` segments in the URI bound to `@ResourceTemplateArg` parameters | The same shapes as a resource. A plain return is delivered at the concrete URI that was requested; a `ResourceResponse` keeps the URI of each content it carries. Returning `null` answers that the resource was not found. |
| Prompt | `@Prompt`, with arguments marked `@PromptArg` | A `String` (one message attributed to the user role), an `org.mcpjava.server.prompts.PromptMessage` (one message with its own role), or an `org.mcpjava.server.prompts.PromptResponse` (several messages, each with its own role, for example an assistant-primed message ahead of the user's question). What the client receives for each is described under [Prompt Return Types](#prompt-return-types). |

A tool argument does not have to be a scalar. A record, a POJO, a list or set of them, or a map all work, and the input schema is generated from the type's own fields.

!!! warning "An omitted `mimeType()` is blank, not JSON"
    On `@Resource` and `@ResourceTemplate`, leaving `mimeType()` unset registers an empty MIME type rather than defaulting to `application/json`. If your resource returns JSON and clients need that advertised, set it yourself.

For records, POJOs, maps and other plain types, a handler never serializes its own return value — the server does it, so an extension needs no JSON library of its own. A handler that returns text, content blocks, a `ToolResponse`, a `ResourceResponse`, a `PromptMessage` or a `PromptResponse` has already decided its own content, and the server usually sends what it built. Some declared types change this, and the return-type tables below spell each one out: a neutral `ResourceContents` (`TextResourceContents` or `BlobResourceContents`), on its own or in a list, and a `ResourceResponse` returned from a method declared `Object` are serialized as JSON text, and a `List<ToolResponse>` is not merged into one result. Declare `ResourceResponse` to send resource contents as built.

### Tool Return Types

The declared return type of a `@Tool` method decides what the client receives.

| Declared return type | What the client receives |
|----------------------|--------------------------|
| `String` | One text block holding the string as it is. |
| `List<String>` | One text block per string. |
| A content block: `TextContent`, `ImageContent`, `AudioContent`, `EmbeddedResource` or `ResourceLink`, all from `org.mcpjava.server.content` | That block. |
| `List<ContentBlock>` | One block per element. |
| `ToolResponse`, built with `ofText`, `ofError`, `ofStructured` or `builder()` | The response exactly as built, including its error flag and structured content. |
| A boxed primitive such as `Integer` or `Boolean`, or any other type: a record, a POJO, a `Map` | JSON text serialized by the server. An `Integer` 7 arrives as the text `7`. |
| A `List` of any other type | One JSON text block per element. |

A few rules apply across the table:

- Only a return type declared as `List` is split into one block per element. A `Set`, an array or another collection arrives as one JSON text block. To get plain text blocks from a list of strings, declare `List<String>`.
- A `List<ToolResponse>` is not merged into one result. Each response arrives as its own JSON text block and the call is not an error result, so return a single `ToolResponse` when you need to control the result.
- A method declared `Object` is matched by the value it returns only when that value is a `ToolResponse` or a content block, which arrive as in the table. Any other value arrives as one JSON text block, so a returned `String` arrives quoted and a returned list is not split. Declare `String` or `List<String>` to get plain text.
- Returning `null` produces an error result that names the handler.

#### Structured Output

| Setting | What the client receives |
|---------|--------------------------|
| `structuredContent = true` on a record or POJO | The return value as structured content, with an output schema generated from its own shape. |
| `structuredContent = true` on a `ToolResponse` or a content block | The whole value as structured content, with the output schema `{"type":"object"}`. A response built with `ofError` is therefore not an error result, because its error flag becomes part of the structured data. Leave `structuredContent` unset to send a `ToolResponse` as built. |
| `outputSchemaFrom` on a record or POJO | The return value as structured content, with the output schema generated from the named class. |
| `outputSchemaFrom` on a single content block | The block, serialized whole, as the structured content. |
| `outputSchemaFrom` alone on a `ToolResponse` | The response exactly as built. You set structured content that matches the schema yourself, for example with `ToolResponse.ofStructured(...)`. |
| Both attributes on a `ToolResponse` | The schema comes from `outputSchemaFrom`, and the whole response is sent as the structured content. |

As the server ships, structured content also arrives as a text block carrying the same JSON. An operator can switch this off with `quarkus.mcp.server.tools.structured-content.compatibility-mode=false`. The exception is a `ToolResponse` sent exactly as built, which carries only the content you set.

### Resource Return Types

The declared return type of a `@Resource` or `@ResourceTemplate` method decides what the client receives. A plain return is delivered under the resource's own URI — for a template, the concrete URI that was requested — and the annotation's `mimeType()`.

| Declared return type | What the client receives |
|----------------------|--------------------------|
| `String` | One text content holding the string as it is. |
| `byte[]` | One blob content. |
| Any other type: a record, a POJO, a `Map`, a boxed primitive | One text content holding the JSON serialized by the server. |
| `List<String>`, `List<byte[]>`, or a `List` of any other type | One content per element: a text content for a string, a blob for a `byte[]`, a JSON text content for anything else. |
| `org.mcpjava.server.resources.ResourceResponse` | The response exactly as built. Every content keeps its own URI and MIME type, a content built without a MIME type is sent without one, and the annotation's `mimeType()` is not filled in. |
| A single neutral `ResourceContents` (`TextResourceContents` or `BlobResourceContents`), or a `List<ResourceContents>` | JSON text, under the resource's URI and MIME type, not the contents as built. Declare `ResourceResponse` to send contents as built. |
| `Object` | Matched by the value returned, as in the rows above, except that a returned `ResourceResponse` is serialized as JSON text too. Declare `ResourceResponse` to send it as built. |

A few rules apply across the table:

- Only a return type declared as `List` is split into one content per element. A `Set`, another collection or an array arrives as one JSON text content.
- Only a return type declared as `ResourceResponse` itself is sent as built. A type of your own that extends or implements it is serialized as JSON text.
- Metadata set on a `ResourceResponse` goes to the `_meta` of the result, and metadata set on a content goes to the `_meta` of that content. A metadata key needs at least two characters: letters, digits, `_`, `.` and `-`, starting and ending with a letter or digit.
- A `@ResourceTemplate` method that returns `null`, whatever its declared type, answers the JSON-RPC error `-32002` with the message `Resource not found: <uri>`, naming the requested URI. A client on a stateless protocol version gets `-32602` instead, as it would from a built-in template. This is the way for a lookup template to say that nothing exists at that URI.
- A static `@Resource` that returns `null`, or any resource or template whose returned list holds a `null` element, fails the read with an error that names the handler.

### Prompt Return Types

The declared return type of a `@Prompt` method decides what the client receives.

| Declared return type | What the client receives |
|----------------------|--------------------------|
| `String` | One message with the user role, holding the string as it is. |
| `org.mcpjava.server.prompts.PromptMessage` | One message with the role it was built with. The neutral API has no `PromptMessage` factory, so obtain one with `PromptResponse.of(role, content).messages().get(0)`. |
| `org.mcpjava.server.prompts.PromptResponse` | Its messages and roles as built, with its description. The response metadata is not sent. |
| `Object` | A returned `PromptMessage` or `PromptResponse` is delivered as in the rows above. Any other value, including a returned `String`, gets an error reading `No encoder found for class <X>`; to send a string, declare the method `String`. |

A prompt that returns `null` gets an error that names the handler. Metadata keys on a `PromptResponse` follow the same two-character rule as for resources, and a response with an invalid key fails the call with an error that names the handler.

### Return Types That Stop Startup

The server refuses these when it loads the extension, and startup aborts with a message naming the method:

| Return type | What to do |
|-------------|------------|
| `void` or the boxed `Void`, on a tool, resource, resource template or prompt | Return a type from that feature's table above. |
| A primitive such as `int` or `boolean`, on a tool, resource or resource template | Return the boxed type, for example `Integer`. |
| Any type other than `String`, `PromptMessage`, `PromptResponse` or `Object`, on a prompt: a primitive, a record or POJO, a boxed number, or any `List` (including `List<PromptMessage>` and `List<String>`) | Return a `String`, a `PromptMessage` or a `PromptResponse`. |
| Structured output (`structuredContent = true` or `outputSchemaFrom`) on a declared return type, or an `outputSchemaFrom` class, that does not serialize to a JSON object with the server's JSON configuration. For example: a `String`, a number or boxed primitive, a boolean, a character, an enum, an array, any list or other collection (including `List<ContentBlock>` and `List<ToolResponse>`), a `UUID`, a date or time type such as `LocalDate` or `Date`, a `URI`, a `Path`, an `Optional` of a scalar, or a class the server writes as a scalar through `@JsonValue` | Return a record or POJO, or a `ToolResponse` built with structured content, for example `ToolResponse.ofStructured(...)`. |

Records, POJOs, `Map`, `ToolResponse` and content blocks are accepted for structured output. A single content block under `outputSchemaFrom` does not stop startup: it is sent whole as the structured content.

A declared return type whose shape cannot be told in advance, such as `Object`, loads. If such a call then returns structured content that is not a JSON object, the call gets an error result that names the handler instead of sending it.

## Authoring Overview

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

### Extension Access

`ExtensionContext` is the extension's entire view of the server, and it arrives in two places. Any handler method can declare it as a parameter, as `forecastRevenue` does above, and gets one scoped to that call. `initialize` is handed one as its argument, for startup work such as reading configuration.

The distinction matters, because not every member means something at startup: `confirm()` and `log()` need a live call to a client, and `currentUser()` and `currentScopes()` describe whoever made that call.

| Member | What it gives you |
|--------|-------------------|
| `config()` | This extension's own settings, from `nsql.extensions.jars.<id>.config.*`. Isolated by design: it exposes no other extension's keys and none of the server's global configuration. Treat it as a flat key/value lookup — profiles, `${...}` expansion, environment variables, and system properties are all deliberately inactive. |
| `newEntityManager()` | A new `EntityManager` on the same factory the server uses. You close it. Note the package is `javax.persistence`, not `jakarta.persistence` — the Versant JPA provider predates the Jakarta namespace change. |
| `currentUser()` | The authenticated principal, or empty when the caller is anonymous or authentication is off server-wide. |
| `currentScopes()`, `hasScope(scope)` | The caller's OAuth scopes, and a convenience check for one of them. |
| `confirm(message)` | Asks a person to approve an operation, with a message you compose. Behaves slightly differently for stateless clients; see [Write Gating for Extension Tools](#write-gating-for-extension-tools). |
| `log()` | Sends MCP log notifications to the connected client, at a level you choose. |

!!! note "`confirm()` and `log()` work only inside a tool handler"
    Both need a live per-call channel to the client. Calling either from `initialize` or from a resource or prompt handler throws `UnsupportedOperationException`.

### Signalling Errors

**From a tool.** A tool reports a failure in one of two ways: return `ToolResponse.ofError(message)`, or throw a `RuntimeException`. Either way the client gets an error result carrying your message. An exception thrown without a message carries its class name instead.

```java
import org.mcpjava.server.tools.ToolResponse;

@Tool(
    name = "region_lookup",
    description = "Look up one sales region by code.",
    annotations = @Tool.Annotations(readOnlyHint = true))
public ToolResponse regionLookup(
        @ToolArg(description = "Region code: NA, EMEA, APAC") String region) {
    if (!KNOWN_REGIONS.contains(region)) {
        return ToolResponse.ofError("Unknown region code: " + region);
    }
    return ToolResponse.ofText(model.describeRegion(region));
}
```

The neutral API has no `ToolCallException`. `org.mcpjava.server.McpException` carries no error code and gets no special treatment: the server handles it like any other `RuntimeException`.

**From a resource, resource template or prompt.** These handlers report a failure by throwing a `RuntimeException`. The client gets the JSON-RPC error `-32603` carrying the exception's message, or its class name when it has none. A resource template can also answer "resource not found" by returning `null`, which gives the error `-32002` (`-32602` on a stateless protocol version) with the message `Resource not found: <uri>`.

!!! warning "The message reaches the client"
    Whatever you put in an error message is shown to the caller, and so is an exception's class name when it has no message. This applies to tools, resources, resource templates and prompts alike. Keep secrets, and data the caller should not see, out of it.

`SchemaExplorerExtension`, in the SDK, shows the pattern in its `extension_get_object` tool: a blank, malformed or unknown LOID returns an error result instead of throwing.

### Getting the SDK

Everything needed to write an extension ships in the **Extension SDK**, a self-contained zip that asks only for Java 21 and Maven. It carries the API JAR, a project you can build immediately, and `SchemaExplorerExtension` — a working example that exercises every contribution kind described on this page, and the easiest starting point for a real extension.

It also carries the API Javadoc, which goes further than this page does: every annotation's full attribute list, each member of `ExtensionContext`, and the rules the server applies while loading your JAR.

<!-- TODO: confirm the exact ESD product and release path before publishing. ESD currently lists
     Actian NoSQL Database and Actian NoSQL JPA; the SDK is filed under neither today. -->
The SDK is available from [esd.actian.com](https://esd.actian.com/) under Actian NoSQL Database.

## Write Gating for Extension Tools

An extension tool that changes data passes the same checks as a built-in one. There is no separate extension permission model and no way for an extension to opt out.

The server decides which is which from one signal: a tool is a **write** unless it declares `readOnlyHint = true`.

```java
annotations = @Tool.Annotations(readOnlyHint = true)   // read tool
annotations = @Tool.Annotations(readOnlyHint = false)  // write tool
// annotations omitted entirely                        // also a write tool
```

That default is deliberate. Omitting the annotation gives you gating rather than a bypass, so forgetting to think about it fails safe. Once classified as a write, the tool is subject to `nsql.writes.enabled` and, when authentication is on, the caller's `mcp:write` scope — both enforced at the tool boundary, before your handler runs. [Write support](../write-support.md) describes both checks, and the same page explains why the tool may not appear in the client's tool list at all.

Confirmation works differently from the built-in tools. It is opt-in: nothing prompts the user unless your handler calls `context.confirm(...)`, and you write the message. What you cannot do is influence the answer — the server enforces it, throwing if the user declines, cancels, leaves it unconfirmed, does not respond in time, or is on a client that cannot show prompts at all. An operator who sets `nsql.writes.confirmation-required=false` silences your prompt along with the built-in ones, since both use the same mechanism.

A client on the stateless 2026-07-28 protocol cannot be asked while your handler is running. It answers by repeating the tool call, so your handler runs again from the start once the person approves. Write your handler with that in mind:

- Keep side effects after `confirm()`. Anything done before it happens once for the question and again for the approved call.
- Do not catch exceptions around `confirm()`. On a stateless client the question reaches the client as an exception, and a handler that swallows it carries on without approval.
- Call `confirm()` at most once per tool call. A second `confirm()` in one stateless call is refused and the handler does not continue.

The approval covers only that exact call: the same tool, the same arguments, and the same user when authentication is on. It lasts `nsql.writes.confirmation-timeout-seconds`. The same code works on both protocols. For how the two differ, see [Protocol Versions](../protocol-versions.md#write-confirmation-on-each-protocol).

## Enabling and Declaring Extensions

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

### The Ordering Rule

`order` is optional, but it is all or nothing: **number every declared JAR, or number none of them.** Numbers must be unique. Declaring `order` on some JARs and not others, or reusing a value, aborts startup with an error naming the problem.

With no `order` anywhere, JARs load sorted by their declared id. The order matters only for `initialize` at startup and `destroy` at shutdown, so most deployments never need it — use it when one extension's `initialize` must run before another's.

### Deploying an Extension JAR

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

Mounting read-only is recommended: the server only ever reads from this directory. See [Security and Trust Model](#security-and-trust-model) for why write access to it matters.

!!! note "Bundle your dependencies into the extension JAR"
    Each extension is loaded by a classloader holding one JAR — its own — plus the server's own classpath. A second JAR sitting in the directory is not on that classpath, whether or not you declare it, so a third-party library your extension needs must be shaded into the extension JAR itself. Build an uber-JAR, and pin the digest of that.

    The two API JARs are the exception, and must stay unshaded. See [Never Shade the API JARs](#security-and-trust-model) below.

## Startup Behavior and Failure Modes

Extension loading is all or nothing. Anything that goes wrong stops the server rather than starting it in a reduced state, so a server that comes up is a server whose extensions all loaded.

| What you see at startup | Cause | What to do |
|-------------------------|-------|------------|
| Startup aborts, reporting a digest mismatch | The JAR's bytes are not the ones pinned in `sha256`. | Recompute the digest from the JAR you actually deployed and update the declaration — or work out why the file changed. |
| Startup aborts, reporting a missing file | `nsql.extensions.jars.<id>.file` names something that is not in the directory. | Check the filename and the mount. |
| Startup aborts, reporting no `ServiceLoader` provider | The JAR has no `META-INF/services/com.actian.mcp.extension.McpExtension` file. | Add the provider file naming your `McpExtension` implementation. |
| Startup aborts, reporting a duplicate name or URI | A tool, resource, resource template, or prompt collides with a built-in or with an extension loaded earlier. | Rename it. Prefixing every name and URI with something specific to your extension avoids this. |
| Startup aborts, naming an extension method's return type | The method is a `@Tool`, `@Resource`, `@ResourceTemplate` or `@Prompt` whose declared return type is refused, for example `void`, a primitive, a prompt returning a record or a list, or a tool asking for structured output (`structuredContent` or `outputSchemaFrom`) from a type that does not serialize to a JSON object. | Change the return type or the attribute as the message suggests. See [Return Types That Stop Startup](#return-types-that-stop-startup). |
| Startup aborts with an exception from your own code | `initialize` threw a `RuntimeException`. | Fix the underlying condition. Throwing from `initialize` is a legitimate way to refuse to start on bad configuration. |

Shutdown is more forgiving: an exception from `destroy` is logged, and the remaining extensions are still torn down.

## Security and Trust Model

An extension is not sandboxed. It runs inside the server's JVM with the full access that implies — the database, the configuration, the network, the filesystem. Deploying one is closer to adding a library to your application than to running third-party code in a container.

The guardrails on this page protect the `@Tool` surface an extension *declares*, and nothing more. An extension holds a live `EntityManager` and can read or write anything through it, at any time, without passing write gating, the `mcp:write` scope, or a confirmation prompt. Those checks constrain how a *client* reaches an extension's tools. They are not a boundary around the extension's own code, and were never intended as one.

SHA-256 verification is provenance, not containment. It proves the bytes the server loaded are the bytes you reviewed and pinned; it says nothing about what those bytes do, and it does not vet the extension's transitive dependencies.

That makes the extensions directory the real boundary. Keep it operator-owned and not world-writable, prefer a read-only mount or an image that bakes the JARs in, and review an extension before you pin its digest — the digest records your decision; it does not make it.

!!! warning "Never shade the API JARs into your extension"
    Keep both `nsql-mcp-extension-api` and `org.mcpjava:mcp-server-api` as `provided`-scope, unshaded dependencies. The server loads both from its own classpath, and a bundled copy is a second, different class of the same name.

    For `nsql-mcp-extension-api` this breaks `ServiceLoader` outright: your `McpExtension` and the server's are no longer the same type, so your extension may never be discovered. For `org.mcpjava:mcp-server-api`, a bundled copy can shadow the annotation types the server's reflectors read.

    Shading your *other* runtime dependencies into an uber-JAR is acceptable, and it helps — an operator can then run composition analysis against a single artifact before pinning its digest.

## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write support](../write-support.md)**  
  The checks an extension's write tools inherit, and how to turn writes on.

- :material-tools: **[Tools](../tools/index.md)**  
  The built-in tools, and the response shapes an extension's own tools sit alongside.

- :material-lock: **[Authentication](../authentication/index.md)**  
  Enable OAuth 2.0, so `currentUser()`, `currentScopes()`, and `mcp:write` carry real values.

</div>
