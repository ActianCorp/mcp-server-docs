---
title: Auth0 Setup Guide
description: Step-by-step guide to configure Auth0 as the OAuth identity provider for the Actian MCP Server.
---

# Auth0 Setup Guide

This guide describes how to create and configure an Auth0 **API** and **Application** for OAuth 2.0 authentication with the Actian MCP Server for Actian NoSQL.

!!! note "Manual client registration"
    This guide uses **manually created applications**. Dynamic Client Registration (DCR) is not covered here.

By the end, you will have the **issuer URL** needed for `quarkus.oidc.auth-server-url`, as well as the **Client ID** (and **Client Secret** for Client Credentials flow) for your MCP client configuration.

!!! info "Reference"
    [Auth0 OpenID Connect documentation](https://auth0.com/docs/authenticate/protocols/openid-connect-protocol)


## Quick-Start Checklist

1. **Create a Database Connection** (Authentication → Database → + Create DB Connection) if none exists.
2. **Create users** (User Management → Users → + Create User) for people who will log in via the Authorization Code flow.
3. **Create an API** (Applications → APIs → + Create API). The **Identifier** becomes the audience that MCP clients request tokens for. Auth0 automatically creates a **Machine to Machine** application with access to this API — use it directly for Client Credentials flow.
4. **Create an Application** for Authorization Code flow (Applications → Applications → + Create Application → **Native**, **Regular Web Application**, or **Single Page Application**). Copy the **Client ID** for use in the MCP client configuration.
5. **Configure Allowed Callback URLs** in the Application settings to match your MCP client's redirect URI.
6. **Grant API access** by going to the APIs tab of the application and authorizing the API created in step 3.
7. **Enable Resource Parameter Compatibility Profile** under **Settings → Advanced** (tenant-level setting).
8. **Set `quarkus.oidc.auth-server-url`** in `application.properties` to `https://<your-tenant>.auth0.com/`.
9. **Start the server** as described in [Start the Server](../../index.md#start-the-server).


## Prerequisites

- An Auth0 account ([sign up free](https://auth0.com/signup)).
- An Auth0 **Tenant** (created automatically on signup, for example, `dev-abc123`).
- The Actian MCP Server installed and ready to run.

## Step 1: Create a Database Connection

Create a database connection to authenticate users against it.

1. In the Auth0 Dashboard, go to **Authentication → Database**.
2. If no connection exists, select **+ Create DB Connection**.
3. Give it a name (for example, `Username-Password-Authentication`) and select **Create**.

## Step 2: Create Auth0 Users

Users in Auth0 represent the people who will log in via the Authorization Code flow.

!!! note
    This step is only needed for the Authorization Code flow. Machine to Machine clients authenticate using their own credentials — no user account is required.

1. In the Auth0 Dashboard, go to **User Management → Users**.
2. Select **+ Create User**.
3. Fill in:

     | Field | Value |
     |-------|-------|
     | **Email** | `jdoe@example.com` |
     | **Password** | A strong password. |
     | **Connection** | `Username-Password-Authentication` (default). |

4. Select **Create**.

## Step 3: Create an Auth0 API

The API represents the Actian MCP Server as a protected resource in Auth0. Tokens issued by Auth0 include the API's identifier as the audience claim.

1. In the Auth0 Dashboard, go to **Applications → APIs**.
2. Select **+ Create API**.
3. Fill in the form:

     | Field | Value | Notes |
     |-------|-------|-------|
     | **Name** | `Actian MCP Server` | Display name (any descriptive string). |
     | **Identifier (Audience)** | `https://<mcp-server-host>:8443/mcp` | A logical identifier — it does not need to be a reachable URL. |
     | **Signing Algorithm** | `RS256` | Default; leave as-is. |

4. Select **Create**.

## Step 4: Create an Auth0 Application

The **Application** represents the OAuth client — the **MCP client** (such as Claude Desktop or Cursor) that requests tokens on behalf of the user.

!!! note "Machine to Machine application"
    When you created the API in Step 3, Auth0 automatically created a **Machine to Machine** application with Client Access already granted to that API. You can use that application directly for Client Credentials flow.

The steps below cover creating an application for the **Authorization Code flow** (interactive login).

1. In the Auth0 Dashboard, go to **Applications → Applications**.
2. Select **+ Create Application**.
3. Fill in:

     | Field | Value |
     |-------|-------|
     | **Name** | `MCP Client` (or the name of your MCP client tool) |
     | **Application Type** | **Native**, **Regular Web Application**, or **Single Page Application** — depending on your MCP client. |

4. Select **Create**. The application's **Settings** tab opens.

### Configure Application Settings

On the **Settings** tab, configure the redirect URI to match your MCP client's OAuth callback:

| Setting | Value | Notes |
|---------|-------|-------|
| **Allowed Callback URLs** | Your MCP client's callback URL | Consult your MCP client's documentation for the exact value. |
| **Allowed Logout URLs** | Your MCP client's logout URL | Optional. |
| **Allowed Web Origins** | Your MCP client's origin | Optional, for CORS. |

Select **Save**.

### Grant API Access

1. Go to the **APIs** tab of your application.
2. Find the API you created in Step 3 (`Actian MCP Server`).
3. Click edit and toggle it to **Authorized**.

### Output of Step 4

These values are used in your **MCP client configuration**:

| Value | Where to find it in Auth0 |
|---|---|
| **Client ID** | **Client ID** on the Settings tab. |
| **Client Secret** | **Client Secret** on the Settings tab (only for the **Machine to Machine** client). |


## Step 5: Enable Resource Parameter Compatibility Profile

This is a **tenant-level** setting required for MCP clients to pass the audience parameter during the authorization flow:

1. In the Auth0 Dashboard, go to **Settings**.
2. Select the **Advanced** tab.
3. Enable **Resource Parameter Compatibility Profile**.
4. Select **Save**.

## Step 6: Configure and Start the Server

The Actian MCP Server only needs the Auth0 **issuer URL** to validate incoming tokens.

### Mapping Summary

| `application.properties` Property | Auth0 Source | Example Value |
|---|---|---|
| `quarkus.oidc.auth-server-url` | Your Auth0 tenant domain | `https://dev-abc123.us.auth0.com/` |

!!! tip "Finding the Issuer URL"
    The issuer URL is `https://<your-domain>/`, where `<your-domain>` is shown at the top of any Application's Settings tab (for example, `dev-abc123.us.auth0.com`).

### Example `application.properties`

Add the following to the `application.properties` and start the server as described in [Start the Server](../../index.md#start-the-server):

```properties
nsql.connectionURL=<connection-url>
mcp.auth.enabled=true
quarkus.oidc.auth-server-url=https://dev-abc123.us.auth0.com/
```


## Verify End-to-End

### Authorization Code Flow

After starting the Actian MCP Server with OAuth configured:

1. Connect to the server from your MCP client.
2. The MCP client fetches `/.well-known/oauth-protected-resource` and discovers the Auth0 issuer URL.
3. The MCP client redirects you to the Auth0 login page.
4. After logging in, Auth0 issues an access token to the MCP client.
5. The MCP client includes the Bearer token in all subsequent requests.
6. The server validates the token signature against Auth0's JWKS endpoint and grants access.

### Client Credentials Flow

For automated clients using the Machine to Machine application:

1. The client authenticates directly with Auth0 using its **Client ID** and **Client Secret**.
2. Auth0 issues an access token without any user interaction.
3. The client includes the Bearer token in all requests to the MCP server.
4. The server validates the token signature against Auth0's JWKS endpoint and grants access.

## Staging vs. Production

| Environment | Recommendation |
|---|---|
| **Development** | Use a free Auth0 tenant. HTTP is acceptable for local testing (without TLS). |
| **Staging / Production** | Use a dedicated Auth0 tenant. Always enable TLS — see [NoSQL TLS configuration](../index.md#secure-remote-deployments-with-https-and-tls). |

