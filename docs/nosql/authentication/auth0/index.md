---
title: Auth0 Setup Guide
description: Step-by-step guide to configure Auth0 as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Auth0

This guide describes how to create and configure an Auth0 API and Application for OAuth 2.0 authentication with the Actian MCP Server for Actian NoSQL.

!!! note "Manual client registration"
    This guide focuses on manually created clients. Dynamic Client Registration (DCR) is not covered in this documentation.

By the completion of this guide, you will have obtained the issuer URL needed for `quarkus.oidc.auth-server-url`, the audience value for `quarkus.oidc.token.audience`, as well as the Client ID and Client Secret (for Client Credentials flow) for the MCP client configuration.

!!! info "Reference"
    [Auth0 OpenID Connect documentation](https://auth0.com/docs/authenticate/protocols/openid-connect-protocol)


## Quick Start

1. **Create a Database Connection:** Navigate to **Authentication > Database > + Create DB Connection** if one does not exist.
2. **Create users:** Navigate to **User Management > Users > + Create User** for individuals who will log in via the Authorization Code flow.
3. **Create an API:** Navigate to **Applications > APIs > + Create API**. The "Identifier" becomes the audience for which MCP clients request tokens. It is also the value of `quarkus.oidc.token.audience`, character for character. Auth0 automatically creates a **Machine to Machine** application with access to this API and uses it directly for Client Credentials flow.
4. **Add the write scope**, in write mode only: add an `mcp:write` permission on the API's **Permissions** tab, turn on **Enable RBAC** under **Settings > RBAC Settings**, then grant it through a role under **User Management > Roles**. Each application also selects it on its own **API Access** tab. With targets, follow [Permissions with Targets](#permissions-with-targets) instead, and leave `quarkus.oidc.resource-metadata.scopes` without target scopes.
5. **Create an Application:** Navigate to **Applications > Applications > + Create Application**. Choose **Native**, **Regular Web Application**, or **Single Page Application**. Copy the Client ID for the configuration.
6. **Configure Allowed Callback URLs:** Set the **Allowed Callback URLs** in the application settings to match the MCP client’s redirect URI.
7. **Grant API access:** Under the **APIs** tab of the application, authorize the API created in step 3.
8. **Enable compatibility profile:** Under **Settings > Advanced**, enable the **Resource Parameter Compatibility Profile**.
9. **Update properties:** Set `quarkus.oidc.auth-server-url` in `application.properties` to `https://<your-tenant>.auth0.com/` and `quarkus.oidc.token.audience` to the API Identifier. In write mode without targets, also set `quarkus.oidc.resource-metadata.scopes=mcp:write`. With targets, never list a target scope there; see [Permissions with Targets](#permissions-with-targets).
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

!!! important "The Identifier is the audience the server checks"
    Set `quarkus.oidc.token.audience` to the Identifier exactly, with a trailing `/` included or excluded in the same way.

Then add the permissions your mode needs:

- **Without targets**, the `mcp:write` permission, in write mode only. A read-only server never inspects it. See [Write Permission Without Targets](#write-permission-without-targets-write-mode-only).
- **With targets**, the permissions of each target, whether writes are on or off, because every target needs its read permission. See [Permissions with Targets](#permissions-with-targets).

### Enable RBAC

Both modes need role-based access control (RBAC) on the API. Only a read-only server without targets can skip this section.

On the API's **Settings** tab, scroll to **RBAC Settings**, turn on **Enable RBAC**, and select **Save**. With RBAC on, Auth0 checks what the caller holds before it fills the token's `scope` claim, which is the claim the server reads. Without RBAC, Auth0 grants any defined API scope that the application is authorized for and requests, so any user of an authorized application can obtain any permission of the API. RBAC is what makes access per user.

!!! note "**Add Permissions in the Access Token** Depends on Targets"
    That neighboring toggle adds the user's granted permissions to a separate `permissions` claim. The server reads its scopes from that claim as well as from `scope`. With the toggle on, a permission that a user's role grants counts even when the client did not request it, so a client cannot limit itself below the user's role. With the toggle off, only `scope` counts and a client can ask for less.

    Without targets, this guide keeps the toggle off and relies on the scope request. With targets, turn the toggle on: the target permissions reach the token through `permissions` without being requested, as [Permissions with Targets](#permissions-with-targets) describes.

### Write Permission Without Targets (Write Mode Only)

In write mode, the server offers the write tools only to a token that carries `mcp:write`, and checks every write call for it. Auth0 models the `mcp:write` scope as a **permission** on the API, so this section defines the permission and grants it through a role. You choose which applications receive it later, in [Grant API Access](#grant-api-access). For what the server does with the scope, see [Write support](../../write-support.md#what-each-call-must-clear).

#### Define the Permission

1. Open the API you just created, for example `Actian MCP Server`, and select the **Permissions** tab.
2. Under **Add a Permission**, enter the following and select **+ Add**:

     | Field | Value |
     |-------|-------|
     | **Permission** | `mcp:write` |
     | **Description** | `Write access to NoSQL objects` |

#### Grant It Through a Role

A role is how an interactive user receives the permission. Skip this section if you use only the Client Credentials flow, which has no user.

1. Navigate to **User Management > Roles** and select **+ Create Role**. Name it, for example `NoSQL MCP Writer`, and select **Create**.
2. On the role's **Permissions** tab, select **Add Permissions**, choose your API, select `mcp:write`, and add it.
3. On the role's **Users** tab, select **Add Users** and assign everyone who is allowed to write.

Users outside that role read normally, and the write tools are not offered to them. Because the grant is per user, nobody obtains write access by asking for it.

!!! note "Creating the permission gives it to nobody"
    Defining `mcp:write` on the API only makes it available to grant. Two separate things put it in a token: the application must be allowed to request it, which you set per application in [Grant API Access](#grant-api-access), and an interactive user must hold it through the role above.

Auth0 can now issue the scope, but no client requests it until the server advertises it. That is a server setting, covered in [Step 6](#step-6-configure-and-start-the-server).

### Permissions with Targets

With targets (see [Targets](../../targets/index.md)), `mcp:write` grants nothing: a caller reads a target with the permission `actian:<target>:read` and writes there with `actian:<target>:write`. For the scope rules, see [Scopes per Target](../scopes.md#scopes-per-target). The audience stays the API Identifier from [Step 3](#step-3-create-an-auth0-api).

#### Define the Target Permissions

1. Open the API and select the **Permissions** tab.
2. For each target, add two permissions with **+ Add**: `actian:<target>:read` and `actian:<target>:write`. For targets named `sales` and `hr`, that is `actian:sales:read`, `actian:sales:write`, `actian:hr:read` and `actian:hr:write`.

#### Grant Them Through Roles

Roles bundle the target permissions, and users receive roles.

1. On the API's **Settings** tab, turn on **Add Permissions in the Access Token**, next to the **Enable RBAC** toggle from [Enable RBAC](#enable-rbac). With both on, the permissions of a user's roles arrive in the token's `permissions` claim without being requested.
2. Navigate to **User Management > Roles** and create a role for each group of users, for example `Sales Team`. On the role's **Permissions** tab, select **Add Permissions**, choose your API, and add the target permissions the group needs. One role can hold permissions of several targets, for example read on `sales` and `hr` and write on `sales` only.
3. On the role's **Users** tab, select **Add Users** and assign the members of the group.

The write permission of a target is never requested through the `403` the server answers with, because the write tools are not offered without it. It must therefore reach the token without being requested, which is why **Add Permissions in the Access Token** has to be on here. With it on, a client cannot ask for less than its user's roles grant.

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

It applies as written when the API's **Application Access Policy**, on the API's **Settings** tab, sets **User-delegated Access** to **Per-app authorization**. With **All apps allowed**, every application may act for a signed-in user without being authorized here, and the **User-Delegated Access** tab needs no selection. **Client Access** offers no such option, so a Client Credentials application is always authorized here.

1. Go to the **API Access** tab of the application.
2. Select the **Actian MCP Server** API created in [Step 3](#step-3-create-an-auth0-api). A panel opens with two tabs, each covering a different kind of access:

    | Tab | Covers |
    |-----|--------|
    | **User-Delegated Access** | Tokens the application requests on behalf of a signed-in user — the Authorization Code flow. |
    | **Client Access** | Tokens the application requests for itself, with no user involved — the Client Credentials flow. |

3. Open the tab that matches the flow this application uses.
4. Without targets, in write mode, select `mcp:write` from the permission list, then select **Save**. With targets, select no permission for the Authorization Code flow: the permissions of the user's roles reach the token through **Add Permissions in the Access Token**, so authorizing the API is enough. For the Client Credentials flow with targets, select on the **Client Access** tab the target permissions the application needs, for example `actian:sales:read` and `actian:sales:write`. They arrive in the token's `scope` claim.

!!! note "Both flows need this, and the interactive one needs a role as well"
    The permission list controls what the application is *allowed to request*. For Client Credentials that is the entire grant, because there is no user whose role could carry it. For the Authorization Code flow it is only half: the signed-in user must also hold `mcp:write` through the role created in [Write Permission Without Targets](#write-permission-without-targets-write-mode-only), or the token is issued without the scope. A scope the client requests, such as `mcp:write` without targets, must be selected here, or the request does not yield it. Permissions that Auth0 adds on its own through **Add Permissions in the Access Token** need no selection.

### Calling Applications

An application that has already signed the user in and calls this server for that user (see [Calling Applications](../index.md#calling-applications)) requests the API Identifier as its `audience` when the user signs in. Auth0 offers no equivalent of the Keycloak standard token exchange for this case, so there is no exchange step.

Authorize that application for the API as described in [Grant API Access](#grant-api-access). Without targets, in write mode, have it include `mcp:write` in its scope request.

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

MCP clients name the server they want a token for in the standard `resource` parameter, not in the Auth0-specific `audience` parameter. With this profile on, Auth0 treats `resource` as the audience, so the API Identifier must match the server URL that clients send, for example `https://<mcp-server-host>:8443/mcp`.

## Step 6: Configure and Start the Server

The Actian MCP Server requires the Auth0 issuer URL to validate incoming tokens.

### Mapping Summary

| `application.properties` Property | Auth0 Source | Example Value |
|---|---|---|
| `quarkus.oidc.auth-server-url` | Your Auth0 tenant domain | `https://dev-abc123.us.auth0.com/` |
| `quarkus.oidc.token.audience` | API Identifier from Step 3 | `https://<mcp-server-host>:8443/mcp` |
| `quarkus.oidc.resource-metadata.scopes` | The permission from [Write Permission Without Targets](#write-permission-without-targets-write-mode-only) | `mcp:write`, in write mode only; with targets never a target scope, and `mcp:write` has no effect (see [Advertising Scopes](../scopes.md#advertising-scopes-to-mcp-clients)) |

!!! tip "Finding the Issuer URL"
    The issuer URL format is `https://<your-domain>/`. You can find the `<your-domain>` domain at the top of the **Settings** tab for any application. For example, `dev-abc123.us.auth0.com`.

!!! caution "Set the scopes list in write mode"
    Auth0 does not list custom API permissions in its OIDC discovery document, so a client that discovers its scopes never learns from Auth0 that `mcp:write` exists. Advertising the scope here is what makes the client request it. Without it, the whole Auth0 configuration from [Write Permission Without Targets](#write-permission-without-targets-write-mode-only) stays invisible: the client authenticates cleanly and still cannot write.

    A read-only server can leave the property unset. Auth0 issues a token without the scopes it will not grant, rather than refusing the request, so a client that requests more than it can obtain still authenticates. This is therefore a write-mode concern on Auth0, unlike Keycloak, where you should set it either way. For the mechanism, see [Advertising scopes to MCP clients](../scopes.md#advertising-scopes-to-mcp-clients).

    With targets, `mcp:write` in this list has no effect, and target scopes never go in it: the list is public and every client would request every target. A client learns the read scope it needs from the `403`, and the write permissions arrive in `permissions` as [Permissions with Targets](#permissions-with-targets) sets up. See [Advertising Scopes](../scopes.md#advertising-scopes-to-mcp-clients).

### Example `application.properties`

Add the following to the `application.properties` and start the server as described in [Start the Server](../../index.md#start-the-server):

```properties
nsql.connectionURL=<connection-url>
mcp.auth.enabled=true
quarkus.oidc.auth-server-url=https://dev-abc123.us.auth0.com/
quarkus.oidc.token.audience=https://<mcp-server-host>:8443/mcp
# Write mode only
quarkus.oidc.resource-metadata.scopes=mcp:write
```


## Verify End-to-End

### Authorization Code Flow

After starting the Actian MCP Server with OAuth configured:

1. Connect to the server from your MCP client.
2. The MCP client fetches `/.well-known/oauth-protected-resource` and discovers the Auth0 issuer URL.
3. The MCP client redirects you to the Auth0 login page.
4. After logging in, Auth0 issues an access token to the MCP client.
5. The MCP client includes the Bearer token in all subsequent requests.
6. The server validates the token signature against Auth0's JWKS endpoint and checks the audience, then grants access.

### Client Credentials Flow

For automated clients using the Machine to Machine application:

1. The client authenticates directly with Auth0 using its **Client ID** and **Client Secret**.
2. Auth0 issues an access token without any user interaction.
3. The client includes the Bearer token in all requests to the MCP server.
4. The server validates the token signature against Auth0's JWKS endpoint and checks the audience, then grants access.

## Staging Versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Use a free Auth0 tenant. HTTP is acceptable for local testing (without TLS). |
| **Staging / Production** | Use a dedicated Auth0 tenant. Always enable TLS, see [NoSQL TLS configuration](../index.md#secure-remote-deployments-with-https-and-tls) for more information. |

