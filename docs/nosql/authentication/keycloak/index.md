---
title: Keycloak Setup Guide
description: Step-by-step guide to configure Keycloak as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Keycloak

This guide explains how to create and configure a Keycloak Realm and Client for OAuth 2.0 authentication with the Actian MCP Server for Actian NoSQL.

!!! note "Manual client registration"
    This guide focuses on manually created clients. Dynamic Client Registration (DCR) is not covered in this documentation.

By the completion of this guide, you will have obtained the issuer URL needed for `quarkus.oidc.auth-server-url`, as well as the audience value for `quarkus.oidc.token.audience` and the Client ID and Client Secret (for Client Credentials flow) for the MCP client configuration.

!!! note "Keycloak version"
    This guide applies to **Keycloak 22 and later** (Quarkus-based). Versions older than version 17 (WildFly-based) use a different admin interface and URL structure. Token exchange for a calling application (see [Token Exchange for a Calling Application](#token-exchange-for-a-calling-application)) requires Keycloak 26.2 or later.

## Quick Start

1. **Create a realm** (or use an existing one).
2. **Create a client per flow:** Enable **Standard flow** for Authorization Code. Enable **Client authentication** and **Service accounts roles** for Client Credentials.
3. **Add the token audience:** create a client scope with an **Audience** mapper whose **Included Custom Audience** is the audience value (for example `nsql-mcp`), and attach it to those clients as **Default**.
4. **Add the write scope**, in write mode only: create an `mcp:write` client scope under **Client scopes** with **Include in token scope** on, then attach it to the client as **Optional**.
5. **Create users** for those logging in via the Authorization Code flow. (This is not required for Client Credentials.)
6. **Note the realm issuer URL**: `http://<keycloak-host>:8080/realms/<realm-name>`.
7. **Set `quarkus.oidc.auth-server-url`**, **`quarkus.oidc.token.audience`** (the Included Custom Audience value) and **`quarkus.oidc.resource-metadata.scopes`** in `application.properties`. In write mode the scopes list is `mcp:write`, which is what makes the client request it.
8. **Start the server:** Follow the standard server startup instructions as described in [Start the Server](../../index.md#start-the-server) documentation.


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

### Step 2.1: Add the Token Audience

A 1.2 server rejects any token whose `aud` claim does not contain the value of `quarkus.oidc.token.audience`. Keycloak does not add such an audience on its own, so tokens carry no audience for this server until you add one. For what a rejected token looks like, see [Rejected Tokens](../index.md#rejected-tokens).

#### Create the Client Scope

1. Navigate to **Client scopes** in the left sidebar and select **Create client scope**.
2. Complete the following fields:

    | Field | Value |
    |-------|-------|
    | **Name** | `nsql-mcp-audience` |
    | **Type** | `None` |
    | **Protocol** | `openid-connect` |
    | **Include in token scope** | `On` |

3. Select **Save**.

#### Add the Audience Mapper

1. Open the new scope and select the **Mappers** tab.
2. Select **Configure a new mapper**, then choose **Audience**. Do not choose **Audience Resolve**: that is a different mapper, which derives audiences from client roles. This guide uses the plain **Audience** mapper.
3. Complete the following fields:

    | Field | Value |
    |-------|-------|
    | **Name** | Any label, for example `nsql-mcp-audience` |
    | **Included Client Audience** | Leave empty |
    | **Included Custom Audience** | `nsql-mcp` |
    | **Add to access token** | `On` |
    | **Add to ID token** | `Off` |

4. Select **Save**.

!!! note "The mapper Name is only a label"
    The **Name** field does not affect the token. The audience is the value of **Included Custom Audience**, and that is the value you set in `quarkus.oidc.token.audience`.

!!! warning "Never use the MCP client's own ID as the audience"
    Do not select the MCP client's own ID (for example `nosql-mcp-client`) under **Included Client Audience**. The `aud` claim must name this server, not the application that requests the token.

#### Attach It to the Clients

1. Navigate to **Clients >** your client, and select the **Client scopes** tab.
2. Select **Add client scope**, select `nsql-mcp-audience`, then select **Add > Default**.
3. Repeat for each client that MCP clients use, for example Client A and Client B in [Step 2](#step-2-create-keycloak-clients).

Attached as **Default**, the scope puts the audience in every token the client issues, without the client having to request it.

#### Check the Audience Before You Start the Server

1. Navigate to **Clients >** your client **> Client scopes > Evaluate**.
2. Select a user, then open **Generated access token**.
3. Confirm that the `aud` claim contains `nsql-mcp`.

!!! tip "Planning to use token exchange?"
    If a calling application will use token exchange, the audience value must also be the Client ID of a Keycloak client, because the `audience` parameter of a Keycloak token exchange takes a client ID. Using `nsql-mcp` here keeps the two aligned. See [Token Exchange for a Calling Application](#token-exchange-for-a-calling-application).


## Step 3: Add the Write Scope (Write Mode Only)

Skip this step when `nsql.writes.enabled` is `false`. A read-only server never inspects the scope.

In write mode, the server checks every write call for the `mcp:write` scope and rejects a token that lacks it. In Keycloak, you create that scope once as a client scope, then attach it to the client that your writers authenticate through. For what the server does with the scope, see [Write support](../../write-support.md#what-each-call-must-clear).

### Create the Client Scope

1. Navigate to **Client scopes** in the left sidebar and select **Create client scope**.
2. Complete the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `mcp:write` | Must match exactly — this is the string the server looks for. |
    | **Description** | `Write access to NoSQL objects` | A label for administrators. |
    | **Type** | `None` | You attach it to a client in the next section. |
    | **Protocol** | `openid-connect` | — |
    | **Include in token scope** | `On` | Keycloak puts the scope in the token's `scope` claim, which the server reads. |

3. Select **Save**.

### Attach It to the Client as Optional

1. Navigate to **Clients >** your client, for example `nosql-mcp-client`, and select the **Client scopes** tab.
2. Select **Add client scope**.
3. Select `mcp:write`, then select **Add > Optional**.

!!! warning "Optional, not Default"
    Keycloak issues an optional scope only to a caller that requests it, which keeps a read-only client's tokens free of write access. If you add it as **Default** instead, every token this client issues carries `mcp:write` whether the caller requested it or not, and the scope can no longer distinguish read-only callers from write-capable ones.

### Caller Eligibility

A Keycloak client scope attaches to a **client**, not to a user, so any user who authenticates through that client and requests `scope=openid mcp:write` receives it. Roles make no difference here, because the server authorizes on the token's `scope` claim rather than on roles.

!!! important "To withhold writes from some people, use a second client"
    Keycloak cannot issue an optional client scope to some users of a client and not others, and Actian NoSQL Database offers no second line of defense: every statement the server runs uses the single database user from `nsql.connectionURL`, so there are no per-user table privileges to fall back on. See [How a write is authorized](../../write-support.md#authorizing-a-write).

    Register two clients instead — one with `mcp:write` attached for writers, one without it for everyone else — and point read-only callers at the second. This is where Keycloak differs from Auth0, which grants the permission per user through a role and can therefore withhold it inside a single client.

Attaching the scope in Keycloak only makes it available. The client must still request it, and the client follows the server's advertised list, so `quarkus.oidc.resource-metadata.scopes` becomes `mcp:write` in write mode. See [Step 5](#step-5-configure-and-start-the-server).

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
    Some MCP clients add `offline_access` to their scope request to obtain a refresh token. Keycloak grants that scope only to a user who holds the `offline_access` **realm role**; making the client scope available is not enough. The failure looks like a client misconfiguration when it is really a user configuration problem. Assign the role under **Users >** the user **> Role mapping > Assign role > Realm roles**.


## Step 5: Configure and Start the Server

The Actian MCP Server requires the Keycloak realm issuer URL and the audience value from [Step 2.1](#step-21-add-the-token-audience) to validate tokens. It does not require the client ID or secret; those are used exclusively by the MCP client.

### Mapping Summary

| `application.properties` Property | Keycloak Source | Example Value |
|---|---|---|
| `quarkus.oidc.auth-server-url` | Realm issuer URL | `http://<keycloak-host>:8080/realms/actian-nosql-mcp` |
| `quarkus.oidc.token.audience` | Included Custom Audience from Step 2.1 | `nsql-mcp` |
| `quarkus.oidc.resource-metadata.scopes` | — | `openid,profile,email` on a read-only server, `mcp:write` in write mode |

!!! caution "Set the scopes list, even on a read-only server"
    Keycloak refuses an authorization request that asks for any scope the client cannot obtain. A client with no advertised list requests every scope the realm advertises, and unless the client is entitled to all of them, login fails outright rather than degrading. Setting this property restricts the request to a list you control, which is why it matters more here than on Auth0.

    Use `openid,profile,email` on a read-only server and `mcp:write` in write mode, as set up in [Step 3](#step-3-add-the-write-scope-write-mode-only). Whatever you list must exist as a client scope on the client the caller uses.

    Keeping the list short has no cost: Keycloak applies a client's **Default** client scopes whether or not they were requested, so their claims stay in the token either way. Only **Optional** scopes, `mcp:write` among them, depend on the client requesting them. For the mechanism, see [Advertising scopes to MCP clients](../index.md#advertising-scopes-to-mcp-clients).

### Example `application.properties`

Add the following to the `application.properties` and start the server as described in [Start the Server](../../index.md#start-the-server) documentation:

```properties
nsql.connectionURL=<connection-url>
mcp.auth.enabled=true
quarkus.oidc.auth-server-url=http://<keycloak-host>:8080/realms/actian-nosql-mcp
quarkus.oidc.token.audience=nsql-mcp
quarkus.oidc.resource-metadata.scopes=openid,profile,email
```


## Token Exchange for a Calling Application

Use this section for an application that has already signed the user in and calls this server for that user. For the concept, see [Token Exchange for Calling Applications](../index.md#token-exchange-for-calling-applications). The recipe uses Keycloak 26.2 standard token exchange (RFC 8693).

1. **Create a client for the audience.** Create a client whose Client ID equals the audience value, `nsql-mcp`, with every flow off: **Client authentication** `Off`, and **Standard flow**, **Direct access grants** and **Service accounts roles** unchecked. The client exists only so that the `audience` parameter of the exchange request can name it.
2. **Configure the calling application's client.** For the calling application's client (example Client ID `actian-agentic`), set **Client authentication** to `On`, because only confidential clients may exchange tokens, and check **Standard Token Exchange**.
3. **Attach the scopes as Optional.** On the calling client's **Client scopes** tab, add `nsql-mcp-audience` and `mcp:write` as **Optional**.

    !!! warning "Optional, not Default"
        If the audience scope is **Default** on the calling client, the application's own login token already carries this server's audience and the server accepts it without any exchange. If the scopes are not attached at all, the exchange fails with this error:

        ```text
        invalid_scope: Invalid scopes: nsql-mcp-audience mcp:write
        ```

4. **Send the exchange request.** The calling application posts the user's existing access token to the realm's token endpoint:

    ```bash
    curl -X POST "http://<keycloak-host>:8080/realms/actian-nosql-mcp/protocol/openid-connect/token" \
      -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
      -d "client_id=actian-agentic" \
      -d "client_secret=<client-secret>" \
      -d "subject_token=<user-access-token>" \
      -d "subject_token_type=urn:ietf:params:oauth:token-type:access_token" \
      -d "audience=nsql-mcp" \
      --data-urlencode "scope=nsql-mcp-audience mcp:write"
    ```

5. **Check the result.** In the returned token, `aud` is exactly `nsql-mcp` (the original audience, for example `account`, is dropped), `azp` is the calling client, and the user is the same (`preferred_username`). Omit `mcp:write` from `scope` to get a read-only token.

The server validates the audience, not how the token was obtained.


## Verify End-to-End

### Authorization Code Flow

After starting the Actian MCP Server with OAuth configured:

1. Connect to the server from your MCP client.
2. The MCP client fetches `/.well-known/oauth-protected-resource` and discovers the Keycloak realm issuer URL.
3. The MCP client redirects you to the Keycloak login page.
4. After logging in, Keycloak issues an access token to the MCP client.
5. The MCP client includes the Bearer token in all subsequent requests.
6. The server validates the token signature against Keycloak's JWKS endpoint and checks the audience, then grants access.

### Client Credentials Flow

For automated clients using Service Accounts:

1. The client authenticates directly with Keycloak using its **Client ID** and **Client Secret**.
2. Keycloak issues an access token without any user interaction.
3. The client includes the Bearer token in all requests to the MCP server.
4. The server validates the token signature against Keycloak's JWKS endpoint and checks the audience, then grants access.

### Token Exchange Flow

For a calling application that has already signed the user in:

1. The application exchanges the user's token at the Keycloak token endpoint, as described in [Token Exchange for a Calling Application](#token-exchange-for-a-calling-application).
2. The application includes the exchanged Bearer token in all requests to the MCP server.
3. The server validates the token signature against Keycloak's JWKS endpoint and checks the audience, then grants access.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| The server exits at startup with a message beginning `Authentication is enabled (mcp.auth.enabled=true) but quarkus.oidc.token.audience is not set.` | The audience is not set. | Set `quarkus.oidc.token.audience`. See [If the Audience Is Missing](../index.md#if-the-audience-is-missing). |
| Requests get 401 and the server log shows `Token verification has failed: No Audience (aud) claim present.` | The client has no Audience mapper, or the audience scope is not **Default** on the client. | Follow [Step 2.1](#step-21-add-the-token-audience). |
| Requests get 401 and the server log shows `Token verification has failed: Audience (aud) claim [account] doesn't contain an acceptable identifier. Expected nsql-mcp as an aud value.` | The calling application sent its own login token instead of an exchanged one. | Exchange the token first. See [Token Exchange for a Calling Application](#token-exchange-for-a-calling-application). |
| The exchange fails with `invalid_scope: Invalid scopes: nsql-mcp-audience mcp:write`. | The scopes are not attached to the calling client. | Attach both as **Optional**, as in step 3 of [Token Exchange for a Calling Application](#token-exchange-for-a-calling-application). |
| Keycloak uses a self-signed or internal-CA certificate. | The server does not trust that certificate. | See [Trusting a Self-Signed or Internal-CA Identity Provider Certificate](../index.md#trusting-a-self-signed-or-internal-ca-identity-provider-certificate). |

!!! caution "Logs can contain tokens"
    Replace tokens with `<redacted>` before you share a server log. See [Rejected Tokens](../index.md#rejected-tokens).


## Staging Versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Enable direct access grants for `curl`-based testing. `http://` is acceptable for local Keycloak. |
| **Staging / Production** | Deploy Keycloak behind HTTPS. Use `https://` for `quarkus.oidc.auth-server-url`. Disable direct access grants. Change default admin credentials. Enable TLS on the Actian MCP Server, see [NoSQL TLS configuration](../index.md#secure-remote-deployments-with-https-and-tls) for more information. |

