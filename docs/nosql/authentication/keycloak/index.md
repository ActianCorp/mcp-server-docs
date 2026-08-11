---
title: Keycloak Setup Guide
description: Step-by-step guide to configure Keycloak as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Keycloak

This guide explains how to create and configure a Keycloak Realm and Client for OAuth 2.0 authentication with the Actian MCP Server for Actian NoSQL.

!!! note "Manual client registration"
    This guide focuses on manually created clients. Dynamic Client Registration (DCR) is not covered in this documentation.

By the completion of this guide, you will have obtained the issuer URL needed for `quarkus.oidc.auth-server-url`, as well as the Client ID and Client Secret (for Client Credentials flow) for the MCP client configuration.

!!! note "Keycloak version"
    This guide applies to **Keycloak 22 and later** (Quarkus-based). Versions older than version 17 (WildFly-based) use a different admin interface and URL structure.

## Quick Start

1. **Create a realm** (or use an existing one).
2. **Create a client per flow:** Enable **Standard flow** for Authorization Code. Enable **Client authentication** and **Service accounts roles** for Client Credentials.
3. **Add the write scope**, in write mode only: create an `mcp:write` client scope under **Client scopes** with **Include in token scope** on, then attach it to the client as **Optional**.
4. **Create users** for those logging in via the Authorization Code flow. (This is not required for Client Credentials.)
5. **Note the realm issuer URL**: `http://<keycloak-host>:8080/realms/<realm-name>`.
6. **Set `quarkus.oidc.auth-server-url`** and **`quarkus.oidc.resource-metadata.scopes`** in `application.properties`. In write mode the scopes list is `mcp:write`, which is what makes the client request it.
7. **Start the server:** Follow the standard server startup instructions as described in [Start the Server](../../index.md#start-the-server) documentation.


## Prerequisites

- A running Keycloak instance (version 22 or higher) is accessible from both the MCP server and the MCP client.
- Admin access to the Keycloak Admin Console.
- The Actian MCP Server installed and ready to run.

## Step 1: Create a Keycloak Realm

A realm is the primary container in Keycloak. It manages users, clients, roles, and configurations.

1. Log in to the Keycloak Admin Console (`http://<keycloak-host>:8080/admin`).
2. In the top-left drop-down menu (showing `master`), select **Create Realm**.
3. Enter the following information:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Realm name** | `actian-nosql-mcp` | Any descriptive name. Appears in all OIDC URLs. |
    | **Enabled** | `On` | |

4. Select **Create**.

### Output of Step 1

| Value | Where to find it |
|---|---|
| **Issuer URL** | `http://<keycloak-host>:8080/realms/actian-nosql-mcp` (Use this for `quarkus.oidc.auth-server-url`). |

## Step 2: Create Keycloak Clients

The Keycloak client represents the OAuth client used by your MCP client application to request tokens. The Actian MCP Server validates tokens but does not require its own Keycloak client.

Create one client for each required flow:

| Flow | Client to create |
|------|-----------------|
| Interactive login (Authorization Code) | A **public** client with **Standard flow** enabled |
| Automated / server-to-server (Client Credentials) | A **confidential** client with **Service accounts roles** enabled |

### Client A: Authorization Code Flow

1. In the Admin Console, select the realm and navigate to **Clients > Create client**.
2. Enter the following:

    | Field | Value |
    |-------|-------|
    | **Client type** | `OpenID Connect` |
    | **Client ID** | `nosql-mcp-client` |

3. Select **Next**.
4. On the **Capability config** screen:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Client authentication** | `Off` | Public client, no secret needed for Authorization Code flow. |
    | **Standard flow** | Checked | Required for browser-based login. |
    | **Direct access grants** | Unchecked (production) | Enable only for local `curl`-based testing. |

5. Select **Next**.
6. On the **Login settings** screen:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Valid redirect URIs** | MCP client's callback URL | Consult the [MCP client documentation](../../../mcp-clients/index.md) for the exact value. |
    | **Web origins** | MCP client's origin | For CORS. |

7. Select **Save**.

### Client B: Client Credentials Flow (M2M)

1. Navigate to **Clients > Create client**.
2. Enter the following:

    | Field | Value |
    |-------|-------|
    | **Client type** | `OpenID Connect` |
    | **Client ID** | `nosql-mcp-m2m` |

3. Select **Next**.
4. On the **Capability config** screen:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Client authentication** | `On` | Makes the client confidential and generates a client secret. |
    | **Service accounts roles** | Checked | Enables the `client_credentials` grant type, required for M2M token requests. |
    | **Direct access grants** | Unchecked (production) | Enable only for local `curl`-based testing. |

5. Select **Next**, then **Save** (no redirect URI needed).
6. Go to the **Credentials** tab and copy the **Client secret**.

### Output of Step 2

| Value | Where to find it in Keycloak                                                               |
|---|--------------------------------------------------------------------------------------------|
| **Client ID** | The **Client ID** entered for each client.                                             |
| **Client Secret** | Clients > [your client] > **Credentials** tab. Only needed for the Client Credentials client |


## Step 3: Add the Write Scope (Write Mode Only)

Skip this step when `nsql.writes.enabled` is `false`. A read-only server never inspects the scope.

In write mode, every write call is checked for the `mcp:write` scope, and a token without it is turned away. In Keycloak you create that scope once as a client scope, then attach it to the client your writers authenticate through. For what the server does with the scope, see [Write support](../../write-support.md#what-each-call-must-clear).

### Create the Client Scope

1. Navigate to **Client scopes** in the left sidebar and select **Create client scope**.
2. Complete the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `mcp:write` | Must match exactly — this is the string the server looks for. |
    | **Description** | `Write access to NoSQL objects` | A label for administrators. |
    | **Type** | `None` | You attach it to a client in the next section. |
    | **Protocol** | `openid-connect` | — |
    | **Include in token scope** | `On` | Puts the scope in the token's `scope` claim, which is the only place the server reads it from. |

3. Select **Save**.

### Attach It to the Client as Optional

1. Navigate to **Clients >** your client, for example `nosql-mcp-client`, and select the **Client scopes** tab.
2. Select **Add client scope**.
3. Select `mcp:write`, then select **Add > Optional**.

!!! warning "Optional, not Default"
    An optional scope is issued only to a caller that asks for it, which keeps a read-only client's tokens free of write access. Added as **Default** instead, every token this client issues carries `mcp:write` whether the caller wanted it or not, and the scope stops telling read-only callers apart from write-capable ones.

### Which Callers Can Obtain the Scope

A Keycloak client scope attaches to a **client**, not to a user, so any user who authenticates through that client and requests `scope=openid mcp:write` receives it. Roles make no difference here, because the server authorizes on the token's `scope` claim rather than on roles.

!!! important "To withhold writes from some people, use a second client"
    Keycloak cannot issue an optional client scope to some users of a client and not others, and Actian NoSQL Database offers no second line of defense: every statement the server runs uses the single database user from `nsql.connectionURL`, so there are no per-user table privileges to fall back on. See [How a write is authorized](../../write-support.md#how-a-write-is-authorized).

    Register two clients instead — one with `mcp:write` attached for writers, one without it for everyone else — and point read-only callers at the second. This is where Keycloak differs from Auth0, which grants the permission per user through a role and can therefore withhold it inside a single client.

Attaching the scope in Keycloak only makes it available. The client still has to ask for it, and it takes its cue from the server, so `quarkus.oidc.resource-metadata.scopes` becomes `mcp:write` in write mode — see [Step 5](#step-5-configure-and-start-the-server).

## Step 4: Create Keycloak Users

Create users in Keycloak who will sign in through your MCP client.

!!! note
    This step is only necessary for the Authorization Code flow. Client Credentials clients authenticate using their own credentials and do not require a user account.

1. Navigate to **Users** in the left sidebar.
2. Select **Add user**.
3. Enter the user details:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Username** | `jdoe` | The login name. |
    | **Email** | `jdoe@example.com` | Optional but recommended. |
    | **First Name** | `John` | Optional |
    | **Last Name** | `Doe` | Optional |

4. Select **Create**.
5. Navigate to the **Credentials** tab and select **Set password**.
6. Enter a password, set **Temporary** to **Off**, and select **Save**.

!!! note "If login fails with "Offline tokens not allowed""
    Some MCP clients add `offline_access` to their scope request to obtain a refresh token. Keycloak grants that scope only to a user who holds the `offline_access` **realm role** — having the client scope available is not enough, which makes the failure look like a client misconfiguration when it is a user one. Assign it under **Users >** the user **> Role mapping > Assign role > Realm roles**.


## Step 5: Configure and Start the Server

The Actian MCP Server requires the Keycloak realm issuer URL to validate tokens. It does not require the client ID or secret; those are used exclusively by the MCP client.

### Mapping Summary

| `application.properties` Property | Keycloak Source | Example Value |
|---|---|---|
| `quarkus.oidc.auth-server-url` | Realm issuer URL | `http://<keycloak-host>:8080/realms/actian-nosql-mcp` |
| `quarkus.oidc.resource-metadata.scopes` | — | `openid,profile,email` on a read-only server, `mcp:write` in write mode |

!!! caution "Set the scopes list, even on a read-only server"
    Keycloak refuses an authorization request that asks for any scope the client cannot obtain. A client with no advertised list to work from falls back to requesting every scope the realm advertises, and unless the client is entitled to all of them, login fails outright rather than degrading. Setting this property pins the request to a list you control, which is why it matters here more than it does on Auth0.

    Use `openid,profile,email` on a read-only server and `mcp:write` in write mode, as set up in [Step 3](#step-3-add-the-write-scope-write-mode-only). Whatever you list must exist as a client scope on the client the caller uses.

    Keeping the list short costs you nothing: Keycloak applies a client's **Default** client scopes whether or not they were requested, so their claims stay in the token either way. Only **Optional** scopes, `mcp:write` among them, depend on the client actually asking. For the mechanism, see [Advertising scopes to MCP clients](../index.md#advertising-scopes-to-mcp-clients).

### Example `application.properties`

Add the following to the `application.properties` and start the server as described in [Start the Server](../../index.md#start-the-server) documentation:

```properties
nsql.connectionURL=<connection-url>
mcp.auth.enabled=true
quarkus.oidc.auth-server-url=http://<keycloak-host>:8080/realms/actian-nosql-mcp
quarkus.oidc.resource-metadata.scopes=openid,profile,email
```


## Verify End-to-End

### Authorization Code Flow

After starting the Actian MCP Server with OAuth configured:

1. Connect to the server from your MCP client.
2. The MCP client fetches `/.well-known/oauth-protected-resource` and discovers the Keycloak realm issuer URL.
3. The MCP client redirects you to the Keycloak login page.
4. After logging in, Keycloak issues an access token to the MCP client.
5. The MCP client includes the Bearer token in all subsequent requests.
6. The server validates the token signature against Keycloak's JWKS endpoint and grants access.

### Client Credentials Flow

For automated clients using Service Accounts:

1. The client authenticates directly with Keycloak using its **Client ID** and **Client Secret**.
2. Keycloak issues an access token without any user interaction.
3. The client includes the Bearer token in all requests to the MCP server.
4. The server validates the token signature against Keycloak's JWKS endpoint and grants access.

## Staging versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Enable direct access grants for `curl`-based testing. `http://` is acceptable for local Keycloak. |
| **Staging / Production** | Deploy Keycloak behind HTTPS. Use `https://` for `quarkus.oidc.auth-server-url`. Disable direct access grants. Change default admin credentials. Enable TLS on the Actian MCP Server, see [NoSQL TLS configuration](../index.md#secure-remote-deployments-with-https-and-tls) for more information. |

