---
title: Scopes
description: The scopes that decide what a caller of the Actian MCP Server for NoSQL may do, with targets and without, the token claims they are read from, what a caller gets when one is missing, and how MCP clients learn which scopes to request.
---

# Scopes

With authentication on, the scopes of the access token decide what a caller may do. The token itself, its issuer, signature, and audience, is set up as [Authentication](index.md) describes. With authentication off (`mcp.auth.enabled` is `false`), no scope is checked, and with targets every target is open.

A scope never turns writes on by itself: the write tools also need `nsql.writes.enabled` to be `true` and the confirmation described in [What Each Call Must Clear](../write-support.md#what-each-call-must-clear).

## The Write Scope Without Targets

Without targets, a valid token is enough for the read tools, the schema resources, and the prompts. A write needs the `mcp:write` scope, and `actian:` scopes grant nothing.

## Scopes per Target

With targets, a request to `/mcp/{target}` needs a token that grants access to that target.

| Scope | Grants |
|-------|--------|
| `actian:{target}:read` | The read tools, the schema resources, and the prompts at `/mcp/{target}`. |
| `actian:{target}:write` | The write tools at `/mcp/{target}`, and everything the read scope grants. |
| `actian:*:read` | What the read scope grants, at every target. |
| `actian:*:write` | What the write scope grants, at every target. |

The rules for a scope:

- It is matched exactly, case included, so `actian:Sales:read` does not grant the target `sales`.
- `*` stands for a whole target name and nothing else. A scope such as `actian:sa*:read` grants nothing, and a target name is never matched as a prefix.
- A scope of any other shape grants nothing and is skipped, and it does not affect a valid scope beside it.
- There is no deny scope and there are no group scopes. Build groups of targets in the identity provider (see [Advertising with Targets](#advertising-with-targets)).
- With authentication on, no property turns the read check off. To give a caller read access to every target, grant `actian:*:read`.

`mcp:write` grants nothing with targets: the write scope of the target replaces it.

A request that only a `*` scope admits is logged as a warning every time, and so is a write that only a `*` scope admits. A request that a scope naming the target also covers is not logged. Keep wildcard scopes for exceptions such as administrators, and grant per-target scopes for routine access.

## Claims the Server Reads

The server reads grants from three claims of the access token and treats them as one set:

- `scope`, a space-delimited string.
- `scp`, a space-delimited string or an array.
- `permissions`, an array.

A grant in any one of the three counts. The `roles` claim is not read, so a role named like a scope grants nothing until the identity provider also delivers it in one of the three claims. Auth0 emits the `permissions` claim only when a specific setting is on; see [Enable RBAC](auth0/index.md#enable-rbac).

The token must be a JSON Web Token (JWT) whose claims the server can read, and its audience must be one of the values in `quarkus.oidc.token.audience`, as [Token Audience](index.md#token-audience) describes.

## What a Caller Gets

With authentication on, a refused request gets one of the answers below.

| What you see | Cause | What to do |
|--------------|-------|------------|
| `401` | The request carries no valid access token. | The client signs in again. An MCP client starts its OAuth flow from the resource metadata that the `401` points to. |
| Reads work and no write tools are listed | The token lacks the write scope (`mcp:write` without targets, the target's write scope with targets), writes are disabled, or the client cannot show the confirmation form. With targets, `mcp:write` does not help. A direct call of a hidden write tool is answered as an unknown tool. | See [Missing Write Tools](../write-support.md#missing-write-tools). |

### Refusals with Targets

With targets, a request can also get these answers:

| What you see | Cause | What to do |
|--------------|-------|------------|
| `403` with a `WWW-Authenticate` header whose error is `insufficient_scope`, and an empty body | The token is valid but does not grant read access to the target, or the target does not exist. The two replies are identical. | Have the identity provider issue the scope named in the header, then connect again. If the target name in the client's URL is mistyped, correct it. |
| `500` with an empty body | The server cannot read the scopes of the token, because the token is not a JWT whose claims the server can read. | Have the identity provider issue JWT access tokens. |

The `scope` value of the `403` header is the token's own `scope` claim followed by `actian:<target>:read`, with the name from the request path. A client that replaces its scopes at step-up therefore keeps what it had. Only the `scope` claim is repeated: a grant that arrives in `scp` or `permissions` is read for the decision but is not listed. The `resource_metadata` value of the header is the same address that the `401` gives.

The `403` is the same for a target that does not exist and for one the caller may not read, so a caller cannot use it to find out which target names exist. At a target the token cannot read, the `403` also comes before the `404` for a session id from another target.

After a `403`, the client signs in again and asks for the scope named in the header. Some clients do this on their own, and others need the person to connect again. A mistyped target name gets the same `403`, so the client is sent to the identity provider with a scope that does not exist. Keycloak refuses that login. Auth0 signs the user in without the scope, so the `403` repeats. Either way, correct the name in the client's URL.

To see which targets a token reaches, call `list_accessible_targets` at plain `/mcp`. See [What an Agent Sees](../targets/index.md#what-an-agent-sees).

## Advertising Scopes to MCP Clients

The server never requests scopes of its own. It publishes the list in `quarkus.oidc.resource-metadata.scopes` at `/.well-known/oauth-protected-resource`, and each MCP client decides what to request from there. Set this property carefully: if you leave it out, clients have no sensible default to fall back on:

| `quarkus.oidc.resource-metadata.scopes` | What the client requests |
|---|---|
| Set | Each client requests exactly the scopes you listed. A client that offers a manual scope field ignores it and uses the advertised list. |
| Unset | `scopes_supported` is absent, so each client chooses on its own. Some request nothing and receive no write access. Others request every scope the identity provider advertises, which usually includes scopes the client cannot obtain. |

Without targets, the only scope in that list that matters to the server is `mcp:write`, in write mode. The server never consumes an ID token, so `openid` is present only for clients that need one. The same applies to `profile` and `email`, which populate user claims that the server does not use.

### Provider-Specific Settings

The behavior described above applies to every provider. What differs is how a provider reacts when a client requests a scope it cannot obtain:

| Provider | A requested scope the client cannot obtain | So the property is |
|----------|--------------------------------------------|--------------------|
| Keycloak | Keycloak rejects the whole authorization request with an invalid-scope error, and login stops working. | Effectively required on every server, because a client that chooses on its own can break login. |
| Auth0 | Auth0 issues the token without that scope, and login succeeds. | Needed only in write mode without targets. A client that chooses on its own still authenticates; it just never receives `mcp:write`. |

The value to use, and how much it matters, depends on your provider:

- **Keycloak**: [Step 6: Configure and Start the Server](keycloak/index.md#step-6-configure-and-start-the-server)
- **Auth0**: [Step 6: Configure and Start the Server](auth0/index.md#step-6-configure-and-start-the-server)

!!! note "Without targets, write mode needs this on both sides"
    Without targets, a server in write mode rejects a write unless the caller's token carries `mcp:write`. Two separate things must be true: the identity provider must issue the scope, and this server must advertise it. Configuring only the provider is the usual reason a client authenticates cleanly and still cannot write. For the provider half, see [Auth0](auth0/index.md#write-permission-without-targets-write-mode-only) or [Keycloak](keycloak/index.md#write-scope-without-targets-write-mode-only); for what the check does, see [Write support](../write-support.md#what-each-call-must-clear).

### Advertising with Targets

`quarkus.oidc.resource-metadata.scopes` is one public list for the whole server, and a client requests all of it at its first login. The scope in the `403` is different: it is built per request for one target, and only a caller with a valid token sees it.

- Never put target scopes in `quarkus.oidc.resource-metadata.scopes`. The list is public, so it would publish every target name, and it would ask every client for every target. On Keycloak, one scope that the client cannot obtain makes the login fail for every target, as [Provider-Specific Settings](#provider-specific-settings) explains.
- Keep the base scopes of the identity provider in the list. Listing `mcp:write` has no effect with targets.
- A read scope needs no advertising: the `403` names the scope the client has to ask for.
- A write scope is never requested through this path. The write tools are not listed without the write scope, so no `403` names `actian:{target}:write`. The grant must therefore reach the token without being requested, through the identity provider's own assignment, for example a role that holds the permissions of several targets. See [Permissions with Targets](auth0/index.md#permissions-with-targets) for Auth0 and [Scopes with Targets](keycloak/index.md#scopes-with-targets) for Keycloak.

## Next Steps

<div class="grid cards" markdown>

- :material-key: **[Keycloak](keycloak/index.md)**  
  Set up Keycloak as the identity provider, step by step.

- :material-cloud: **[Auth0](auth0/index.md)**  
  Set up Auth0 as the identity provider, step by step.

- :material-pencil: **[Write Support](../write-support.md)**  
  When the write tools appear and how a write is confirmed.

- :material-database: **[Targets](../targets/index.md)**  
  Targets, names, and what an agent sees.

</div>
