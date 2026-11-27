---
title: Scopes
description: The scopes that decide what a caller of the Actian MCP Server for NoSQL may do, with targets and without, the token claims they are read from, what a caller gets when one is missing, and how MCP clients learn which scopes to request.
---

# Scopes

With authentication on, the scopes of the access token decide what a caller may do. Which identity provider issues the token and which audience it must carry are set up as [Authentication](index.md) describes. With authentication off (`mcp.auth.enabled` is `false`), no scope is checked, and with targets every target is open.

A scope never turns writes on by itself: the write tools also need `nsql.writes.enabled` to be `true` and the confirmation described in [What Each Call Must Clear](../write-support.md#what-each-call-must-clear).

## Write Scope Without Targets {#the-write-scope-without-targets}

Without targets, a valid token is enough for the read tools, the schema resources, and the prompts. A write needs the `mcp:write` scope.

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
- There is no deny scope and there are no group scopes. Build groups of targets in the identity provider (see [How a Scope Reaches the Token](#how-a-scope-reaches-the-token)).
- With authentication on, no property turns the read check off. To give a caller read access to every target, grant `actian:*:read`.

`mcp:write` grants nothing with targets: the write scope of the target replaces it. Without targets, the `actian:` scopes grant nothing.

A request that only a `*` scope admits is logged as a warning every time, and so is a write that only a `*` scope admits. A request that a scope naming the target also covers is not logged. Keep wildcard scopes for exceptions such as administrators, and grant per-target scopes for routine access.

## Claims the Server Reads

The server reads grants from three claims of the access token and treats them as one set:

- `scope`, a space-delimited string.
- `scp`, a space-delimited string or an array.
- `permissions`, an array.

A grant in any one of the three counts. The `roles` claim is not read, so a role named like a scope grants nothing until the identity provider also delivers it in one of the three claims. Auth0 adds the `permissions` claim only when a specific setting is on; see [Enable RBAC](auth0/index.md#enable-rbac).

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
| `403` with a `WWW-Authenticate` header whose error is `insufficient_scope`, and an empty body | The token is valid but does not grant read access to the target, or the target does not exist. The two replies are identical. | Have the identity provider issue the scope named in the header, then sign in again. If the target name in the client's URL is mistyped, correct it. |
| `500` with an empty body | The server cannot read the scopes of the token, because the token is not a JWT whose claims the server can read. | Have the identity provider issue JWT access tokens. |

The `scope` value of the `403` header is the token's own `scope` claim followed by `actian:<target>:read`, with the name from the request path. A client that replaces its scopes at step-up therefore keeps what it had. Only the `scope` claim is repeated: a grant that arrives in `scp` or `permissions` is read for the decision but is not listed. The `resource_metadata` value of the header is the same address that the `401` gives.

The `403` is the same for a target that does not exist and for one the caller may not read, so a caller cannot use it to find out which target names exist. At a target the token cannot read, the `403` also comes before the `404` for a session id from another target.

After a `403`, the client signs in again and asks for the scope named in the header. Some clients do this on their own, and others need the person to sign in again. A mistyped target name gets the same `403`, so the client is sent to the identity provider with a scope that does not exist. Keycloak refuses that login. Auth0 signs the user in without the scope, so the `403` repeats. Either way, correct the name in the client's URL.

The `401` names no scope, also with targets, so a client learns a target's read scope from the `403` or from its own configuration. A client that does not open the new sign-in by itself can be configured to request the target's read scope at sign-in, so the `403` never occurs; otherwise the person signs in again after the `403`. With Auth0 set up as in [Permissions with Targets](auth0/index.md#permissions-with-targets), the permissions of the user's roles arrive without being requested, so no client setting is needed.

To see which targets a token reaches, call `list_accessible_targets` at plain `/mcp`. See [What an Agent Sees](../targets/index.md#what-an-agent-sees). Plain `/mcp` needs no target scope and never answers `403`, so a client is never sent to ask for one there, and the list holds only the targets whose scopes the token already carries. A target whose read scope the identity provider issues only on request is therefore not listed until the token carries that scope, and it stays reachable at `/mcp/{target}` through the `403` described above.

## How a Scope Reaches the Token

The server never requests a scope. It only reads what the presented token carries, and a scope reaches the token in one of three ways:

- **The client requests it from its own configuration.** This works for any scope, with a client that lets you set the scopes it requests.
- **The identity provider assigns it without a request**, for example, a Keycloak **Default** client scope, or an Auth0 role with **Add Permissions in the Access Token** on. This works for any scope.
- **The server names it in a `403`, and the client signs in again with it.** This works only for a target's read scope, `actian:{target}:read`.

A write scope, `mcp:write` or `actian:{target}:write`, is never named in a response, because the write tools are not listed without it. A client that takes its scopes only from the server therefore never requests one, so for such a client the identity provider must assign it. One role can hold the permissions of several targets, which is how groups of targets are built. For the setup, see [Keycloak](keycloak/index.md#step-4-add-the-scopes) and [Auth0](auth0/index.md#step-3-create-an-auth0-api).

### Scopes the Server Publishes

!!! note "On Keycloak, set `quarkus.oidc.resource-metadata.scopes=openid`"
    The server publishes this list as `scopes_supported` at `/.well-known/oauth-protected-resource/mcp`. A client that finds no list there chooses on its own: some request nothing, and others, such as FastMCP, request every scope the realm advertises, and Keycloak refuses the whole sign-in when the client lacks any of them. With `openid`, which Keycloak always accepts, such a client requests only that, and Keycloak still adds the client's **Default** client scopes. A client's own scope setting takes precedence over the list. Auth0 does not need the property, because it leaves out a scope it cannot grant instead of refusing the sign-in.

    Never list `mcp:write` or target scopes. The list is public, so target scopes would publish every target name, and every client that follows the list would request them. On Keycloak, a client that lacks one of them could no longer sign in.

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
