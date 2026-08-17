---
title: Auth0 Setup Guide
description: Step-by-step guide to configure Auth0 as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Auth0

This guide describes how to create and configure an Auth0 API and Application for OAuth 2.0 authentication with the Actian MCP Server for Actian NoSQL.

!!! note "Manual client registration"
    This guide focuses on manually created clients. Dynamic Client Registration (DCR) is not covered in this documentation.

By the completion of this guide, you will have obtained the issuer URL needed for `quarkus.oidc.auth-server-url`, as well as the Client ID and Client Secret (for Client Credentials flow) for the MCP client configuration.

!!! info "Reference"
    [Auth0 OpenID Connect documentation](https://auth0.com/docs/authenticate/protocols/openid-connect-protocol)


## Quick Start

1. **Create a Database Connection:** Navigate to **Authentication > Database > + Create DB Connection** if one does not exist.
2. **Create users:** Navigate to **User Management > Users > + Create User** for individuals who will log in via the Authorization Code flow.
3. **Create an API:** Navigate to **Applications > APIs > + Create API**. The "Identifier" becomes the audience for which MCP clients request tokens. Auth0 automatically creates a **Machine to Machine** application with access to this API and uses it directly for Client Credentials flow.
4. **Add the write scope**, in write mode only: add an `mcp:write` permission on the API's **Permissions** tab, turn on **Enable RBAC** under **Settings > RBAC Settings**, then grant it through a role under **User Management > Roles**. Each application also selects it on its own **API Access** tab.
5. **Create an Application:** Navigate to **Applications > Applications > + Create Application**. Choose **Native**, **Regular Web Application**, or **Single Page Application**. Copy the Client ID for the configuration.
6. **Configure Allowed Callback URLs:** Set the **Allowed Callback URLs** in the application settings to match the MCP client’s redirect URI.
7. **Grant API access:** Under the **APIs** tab of the application, authorize the API created in step 3.
8. **Enable compatibility profile:** Under **Settings > Advanced**, enable the **Resource Parameter Compatibility Profile**.
9. **Update properties:** Set `quarkus.oidc.auth-server-url` in `application.properties` to `https://<your-tenant>.auth0.com/`.
10. **Start the server:** Follow the standard server startup instructions as described in [Start the Server](../../index.md#start-the-server) documentation.


## Prerequisites

- An Auth0 account ([sign up free](https://auth0.com/signup))
- An Auth0 **Tenant** (created automatically on signup, for example, `dev-abc123`)
- The Actian MCP Server installed and ready to run

## Step 1: Create a Database Connection

Create a database connection to authenticate users:

1. In the Auth0 Dashboard, navigate to **Authentication > Database**.
2. If no connection exists, select **+ Create DB Connection**.
3. In the **Name** box, enter a name (for example, `Username-Password-Authentication`), and then select **Create**.

## Step 2: Create Auth0 Users

Users represent the individuals who log in via the Authorization Code flow:

!!! note
    This step is required only for the Authorization Code flow. Machine-to-machine (M2M) clients authenticate using their own credentials. No user account is required.

1. In the Auth0 Dashboard, navigate to **User Management > Users**.
2. Select **+ Create User**.
3. Complete the following fields:

     | Field | Value |
     |-------|-------|
     | **Email** | `jdoe@example.com` |
     | **Password** | A strong password |
     | **Connection** | `Username-Password-Authentication` (default) |

4. Select **Create**.

## Step 3: Create an Auth0 API

The API represents the Actian MCP Server as a protected resource in Auth0. Tokens issued by Auth0 include the API identifier as the audience claim.

1. In the Auth0 Dashboard, go to **Applications > APIs**.
2. Select **+ Create API**.
3. Configure the following settings:

     | Field | Value | Notes |
     |-------|-------|-------|
     | **Name** | `Actian MCP Server` | Display name (any descriptive string)|
     | **Identifier (Audience)** | `https://<mcp-server-host>:8443/mcp` | A logical identifier, it does not need to be a reachable URL. |
     | **Signing Algorithm** | `RS256` | Default; leave as-is. |

4. Select **Create**.

### Step 3.1: Add the Write Scope (Write Mode Only)

Skip this step when `nsql.writes.enabled` is `false`. A read-only server never inspects the scope.

In write mode, the server checks every write call for the `mcp:write` scope and rejects a token that lacks it. Auth0 models that scope as a **permission** on the API, so this step defines the permission and turns on the setting that lets Auth0 issue it. You choose which applications receive it later, in [Grant API Access](#grant-api-access). For what the server does with the scope, see [Write support](../../write-support.md#what-each-call-must-clear).

#### Define the Permission

1. Open the API you just created, for example `Actian MCP Server`, and select the **Permissions** tab.
2. Under **Add a Permission**, enter the following and select **+ Add**:

     | Field | Value |
     |-------|-------|
     | **Permission** | `mcp:write` |
     | **Description** | `Write access to NoSQL objects` |

#### Enable RBAC

On the API's **Settings** tab, scroll to **RBAC Settings**, turn on **Enable RBAC**, and select **Save**. With RBAC on, Auth0 checks what the caller holds before it fills the token's `scope` claim, which is the claim the server reads. If you leave RBAC off, Auth0 ignores the grant, and `mcp:write` never reaches the token.

!!! note "**Add Permissions in the Access Token** is not needed"
    That neighboring toggle adds the same grants to a separate `permissions` claim. This server never reads that claim; the only claim it inspects is `scope`. Turning the toggle on causes no harm if another system in your environment needs it.

#### Grant It Through a Role

A role is how an interactive user receives the permission. Skip this section if you use only the Client Credentials flow, which has no user.

1. Navigate to **User Management > Roles** and select **+ Create Role**. Name it, for example `NoSQL MCP Writer`, and select **Create**.
2. On the role's **Permissions** tab, select **Add Permissions**, choose your API, select `mcp:write`, and add it.
3. On the role's **Users** tab, select **Add Users** and assign everyone who is allowed to write.

Users outside that role continue to work as before: they read normally, and the server rejects a write attempt, naming the missing scope. Because the grant is per user, nobody obtains write access by asking for it.

!!! note "Creating the permission gives it to nobody"
    Defining `mcp:write` on the API only makes it available to grant. Two separate things put it in a token: the application must be allowed to request it, which you set per application in [Grant API Access](#grant-api-access), and an interactive user must hold it through the role above.

Auth0 can now issue the scope, but no client requests it until the server advertises it. That is a server setting, covered in [Step 6](#step-6-configure-and-start-the-server).

## Step 4: Create an Auth0 Application

The application represents the OAuth client, the MCP client (such as Claude Desktop or Cursor) that requests tokens on behalf of the user.

!!! note "Machine-to-machine applications"
    When you created the API in [Step 3](#step-3-create-an-auth0-api), Auth0 automatically created an Machine-to-Machine application with client access granted to that API. You can use that application for the Client Credentials flow.

The following steps describe how to create an application for the interactive Authorization Code flow:

1. In the Auth0 Dashboard, navigate to **Applications > Applications**.
2. Select **+ Create Application**.
3. Complete the following fields:

     | Field | Value |
     |-------|-------|
     | **Name** | `MCP Client` (or the name of your MCP client tool) |
     | **Application Type** | **Native**, **Regular Web Application**, or **Single Page Application** — depending on your MCP client. |

4. Select **Create**. The **Settings** tab opens automatically.

### Configure Application Settings

On the **Settings** tab, configure the redirect URI to match the MCP client's OAuth callback:

| Setting | Value | Notes |
|---------|-------|-------|
| **Allowed Callback URLs** | MCP client's callback URL | Consult the [MCP client documentation](../../../mcp-clients/index.md) for the exact value. |
| **Allowed Logout URLs** | MCP client's logout URL | Optional. |
| **Allowed Web Origins** | MCP client's origin | Optional, for CORS. |

Select **Save**.

### Grant API Access

This step allows the application to request tokens for the API and to choose which permissions it may request.

1. Go to the **API Access** tab of the application.
2. Select the **Actian MCP Server** API created in [Step 3](#step-3-create-an-auth0-api). A panel opens with two tabs, each covering a different kind of access:

    | Tab | Covers |
    |-----|--------|
    | **User-Delegated Access** | Tokens the application requests on behalf of a signed-in user — the Authorization Code flow. |
    | **Client Access** | Tokens the application requests for itself, with no user involved — the Client Credentials flow. |

3. Open the tab that matches the flow this application uses.
4. In write mode, select `mcp:write` from the permission list, then select **Save**.

!!! note "Both flows need this, and the interactive one needs a role as well"
    The permission list controls what the application is *allowed to request*. For Client Credentials that is the entire grant, because there is no user whose role could carry it. For the Authorization Code flow it is only half: the signed-in user must also hold `mcp:write` through the role created in [Step 3.1](#step-31-add-the-write-scope-write-mode-only), or the token is issued without the scope.

### Output of Step 4

Retain the following values for your MCP client configuration:

| Value | Where to find it in Auth0 |
|---|---|
| **Client ID** | **Client ID** on the Settings tab. |
| **Client Secret** | **Client Secret** on the Settings tab (only for the **Machine to Machine** client). |


## Step 5: Enable Resource Parameter Compatibility Profile

This is a **tenant-level** setting required for MCP clients to pass the audience parameter during the authorization flow:

1. In the Auth0 Dashboard, navigate to **Settings**.
2. Select the **Advanced** tab.
3. Enable **Resource Parameter Compatibility Profile**.
4. Select **Save**.

## Step 6: Configure and Start the Server

The Actian MCP Server requires the Auth0 issuer URL to validate incoming tokens.

### Mapping Summary

| `application.properties` Property | Auth0 Source | Example Value |
|---|---|---|
| `quarkus.oidc.auth-server-url` | Your Auth0 tenant domain | `https://dev-abc123.us.auth0.com/` |
| `quarkus.oidc.resource-metadata.scopes` | — | `mcp:write`, in write mode only |

!!! tip "Finding the Issuer URL"
    The issuer URL format is `https://<your-domain>/`. You can find the `<your-domain>` domain at the top of the **Settings** tab for any application. For example, `dev-abc123.us.auth0.com`.

!!! caution "Set the scopes list in write mode"
    Auth0 does not list custom API permissions in its OIDC discovery document, so a client that discovers its scopes never learns from Auth0 that `mcp:write` exists. Advertising the scope here is what makes the client request it. Without it, the whole Auth0 configuration from [Step 3.1](#step-31-add-the-write-scope-write-mode-only) stays invisible: the client authenticates cleanly and still cannot write.

    A read-only server can leave the property unset. Auth0 issues a token without the scopes it will not grant, rather than refusing the request, so a client that requests more than it can obtain still authenticates. This is therefore a write-mode concern on Auth0, unlike Keycloak, where you should set it either way. For the mechanism, see [Advertising scopes to MCP clients](../index.md#advertising-scopes-to-mcp-clients).

### Example `application.properties`

Add the following to the `application.properties` and start the server as described in [Start the Server](../../index.md#start-the-server):

```properties
nsql.connectionURL=<connection-url>
mcp.auth.enabled=true
quarkus.oidc.auth-server-url=https://dev-abc123.us.auth0.com/
```

In write mode, add `quarkus.oidc.resource-metadata.scopes=mcp:write` to the same file.


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

## Staging Versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Use a free Auth0 tenant. HTTP is acceptable for local testing (without TLS). |
| **Staging / Production** | Use a dedicated Auth0 tenant. Always enable TLS, see [NoSQL TLS configuration](../index.md#secure-remote-deployments-with-https-and-tls) for more information. |

