---
title: Keycloak Setup Guide
description: Step-by-step guide to configure Keycloak as the OAuth identity provider for the Actian MCP Server.
---

# Keycloak Setup Guide

This guide describes how to create and configure a Keycloak **Realm** and **Client** for OAuth 2.0 authentication with the Actian MCP Server for **Actian NoSQL Database**.

!!! note "Manual client registration"
    This guide uses **manually created clients**. Dynamic Client Registration (DCR) is not covered here.

By the end, you will have the issuer URL needed for `quarkus.oidc.auth-server-url` in your `application.properties`. For the full configuration reference and TLS setup, see the [NoSQL Authentication overview](../index.md).

!!! note "Keycloak version"
    This guide was written for **Keycloak 22+** (Quarkus-based). Older WildFly-based versions (< 17) have a different admin UI and URL structure.

## Quick-Start Checklist

1. **Create a realm** (or use an existing one).
2. **Create a client** with _Client authentication_ enabled. Enable **Standard flow** for Authorization Code, **Service accounts roles** for Client Credentials, or both.
3. **Create users** for people who will log in via Authorization Code flow. Not needed for Client Credentials.
4. **Note the realm issuer URL**: `http://<keycloak-host>:8080/realms/<realm-name>`.
5. **Set `quarkus.oidc.auth-server-url`** and **`quarkus.oidc.resource-metadata.scopes`** in `application.properties`.
6. **Start the server** as described in [Start the Server](../../index.md#start-the-server).


## Prerequisites

- A running Keycloak instance accessible from both the MCP server and the MCP client.
- Admin access to the Keycloak Admin Console.
- The Actian MCP Server installed and ready to run.

## Part 1: Create a Keycloak Realm

A **Realm** is the top-level container in Keycloak that holds users, clients, roles, and configuration.

### Steps

1. Log in to the Keycloak Admin Console (`http://<keycloak-host>:8080/admin`).
2. In the top-left dropdown (showing `master`), select **Create Realm**.
3. Fill in:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Realm name** | `actian-nosql-mcp` | Any descriptive name. Appears in all OIDC URLs. |
    | **Enabled** | `On` | |

4. Select **Create**.

### What You Get from This Step

| Value | Where to find it |
|---|---|
| **Issuer URL** | `http://<keycloak-host>:8080/realms/actian-nosql-mcp` — use this for `quarkus.oidc.auth-server-url`. |

## Part 2: Create Keycloak Clients

The **Client** in Keycloak represents the OAuth client used by your **MCP client application** to request tokens. The Actian MCP Server itself does not need a Keycloak client — it only validates tokens.

Create one client per flow:

| Flow | Client to create |
|------|-----------------|
| Interactive login (Authorization Code) | A client with **Standard flow** enabled |
| Automated / server-to-server (Client Credentials) | A client with **Service accounts roles** enabled |

### Client A: Authorization Code Flow

1. In the Admin Console, select your realm and go to **Clients → Create client**.
2. Fill in:

    | Field | Value |
    |-------|-------|
    | **Client type** | `OpenID Connect` |
    | **Client ID** | `nosql-mcp-client` |

3. Select **Next**.
4. On the **Capability config** screen:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Client authentication** | `On` | Generates a client secret. |
    | **Standard flow** | Checked | Required for browser-based login. |
    | **Direct access grants** | Unchecked (production) | Enable only for local `curl`-based testing. |

    !!! warning "Disable direct access grants in production"
        The `password` grant is insecure for production use and is only intended for local debugging.

5. Select **Next**.
6. On the **Login settings** screen:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Valid redirect URIs** | Your MCP client's callback URL | Consult your MCP client's documentation for the exact value. |
    | **Web origins** | Your MCP client's origin | For CORS. |

7. Select **Save**.
8. Go to the **Credentials** tab and copy the **Client secret** — this is used in your MCP client configuration.

### Client B: Client Credentials Flow (M2M)

1. Go to **Clients → Create client**.
2. Fill in:

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

5. Select **Next**, then **Save** (no redirect URI needed).
6. Go to the **Credentials** tab and copy the **Client secret**.

### What You Get from This Step

| Value | Where to find it in Keycloak |
|---|---|
| **Client ID** | The **Client ID** you entered for each client. |
| **Client Secret** | Clients → your client → **Credentials** tab. |


## Part 3: Create Keycloak Users

Create users in Keycloak that your MCP client users will log in as.

!!! note
    This step is only needed for the Authorization Code flow. Client Credentials clients authenticate using their own credentials — no user account is required.

### Steps

1. Go to **Users** in the left sidebar.
2. Select **Add user**.
3. Fill in:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Username** | `jdoe` | The login name. |
    | **Email** | `jdoe@example.com` | Optional but recommended. |
    | **First Name** | `John` | Optional |
    | **Last Name** | `Doe` | Optional |

4. Select **Create**.
5. Go to the **Credentials** tab → **Set password** → enter a password, toggle **Temporary** to `Off` → **Save**.


## Part 4: Assemble the Server Configuration

The Actian MCP Server only needs the Keycloak **realm issuer URL** to validate incoming tokens. It does not need the client ID or secret — those belong to the MCP client.

### Mapping Summary

| `application.properties` Property | Keycloak Source | Example Value |
|---|---|---|
| `quarkus.oidc.auth-server-url` | Realm issuer URL | `http://<keycloak-host>:8080/realms/actian-nosql-mcp` |
| `quarkus.oidc.resource-metadata.scopes` | — | `openid,profile,email` |

!!! note "Why set scopes on the server?"
    The MCP server advertises which scopes to request via its resource metadata endpoint. If this is not set, some MCP clients (such as VS Code) may request scopes that are not enabled for the client in Keycloak (for example, `service_account`), causing the token request to fail. Set this to the scopes actually configured for your client.

### Example `application.properties`

Add the following to your `application.properties` and start the server as described in [Start the Server](../../index.md#start-the-server):

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
4. Log in with a Keycloak user (for example, `jdoe`).
5. Keycloak issues an access token to the MCP client.
6. The MCP client includes the Bearer token in all subsequent requests.
7. The server validates the token signature against Keycloak's JWKS endpoint and grants access.

### Client Credentials Flow

For automated clients using Service Accounts:

1. The client authenticates directly with Keycloak using its **Client ID** and **Client Secret**.
2. Keycloak issues an access token without any user interaction.
3. The client includes the Bearer token in all requests to the MCP server.
4. The server validates the token signature against Keycloak's JWKS endpoint and grants access.

## Staging vs. Production

| Environment | Recommendation |
|---|---|
| **Development** | Enable direct access grants for `curl`-based testing. `http://` is acceptable for local Keycloak. |
| **Staging / Production** | Deploy Keycloak behind HTTPS. Use `https://` for `quarkus.oidc.auth-server-url`. Disable direct access grants. Change default admin credentials. Enable TLS on the Actian MCP Server — see [NoSQL TLS configuration](../index.md#secure-remote-deployments-with-https-and-tls). |

