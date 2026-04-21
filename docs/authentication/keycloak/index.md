---
title: Keycloak Setup Guide
description: Step-by-step guide to configure Keycloak as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Keycloak 

This guide describes the creation and configuration of a Keycloak Realm, Client, and Audience Mapper. It enables the Actian MCP Server to authenticate users through OAuth 2.0 and OpenID Connect (OIDC). 

By the end of this guide, you will have the values that are required to populate the `oauth` block in the `conf.json` file. For the full configuration reference and shared concepts such as TLS, user impersonation, and security practices, see  [Authentication Overview](../index.md).

!!! info "Generic OIDC provider"
    FastMCP uses a generic OIDC provider. While there is no dedicated Keycloak class, the server uses the `OIDCProxy` provider, which is compatible with any OIDC-compliant identity provider.


## Quick Start - Existing Keycloak User

If you are an experienced Keycloak user, use the following checklist to set up the environment:

1. **Create a realm** (or use an existing one).
2. **Create a client** with _Client authentication_ enabled and record the **Client ID** and **Client Secret**.
3. **Add an audience mapper** using the **Included Custom Audience** field to show the audience string in the token's `aud` claim. 

    !!! warning
        If you skip this step, the MCP Server rejects tokens with `audience mismatch`.

4. **(Optional)** Add a **sub override mapper** to the `sub` claim containing the username instead of a UUID.
5. **Create users** in the realm, if using `user_impersonation: true`.
6. **Fill `conf.json`** file with the values from [Step 1](#step-1-create-a-keycloak-realm) to [Step 3](#step-3-add-the-audience-mapper-required).
7. **Start the server** with `--transport sse`or `http` / `streamable-http`.


## Prerequisites - New Keycloak User

- A running Keycloak instance (version 22 or higher) is accessible by the MCP server.
- Admin access is granted to the Keycloak Admin Console.
- The Actian MCP Server is installed and ready for deployment.

!!! note "Keycloak version"
    This guide is optimized for Quarkus-based Keycloak (v22+). If you are using a WildFly-based version (v17 or older), the UI and URL structures will differ significantly.

!!! warning "Default admin credentials"
    If your Keycloak instance uses the default `admin` / `admin` credentials, change it through **Users** > **admin** > **Credentials** in the `master` realm.


## Step 1: Create a Keycloak Realm

A Realm is an isolated container for managing users, credentials, and roles.

1. Log in to the Keycloak Admin Console `http://<keycloak-host>:8080/admin`.
2. In the top-left drop-down (displaying `master`), select **Create Realm**.
3. Fill the form as follows:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Realm name** | `actian-mcp` | Any descriptive name; it appears in all OIDC URLs |
    | **Enabled** | `On` | NA |

4. Select **Create**.

### Output of Step 1

| Config Field | Where to find it |
|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `http://<keycloak-host>:8080/realms/actian-mcp/.well-known/openid-configuration` |


## Step 2: Create a Keycloak Client

The client represents the MCP server’s OAuth credentials and holds `client_id` and `client_secret`.

1. In the Admin Console, select your realm from the drop-down.
2. Select **Clients** in the left panel.
3. Select **Create client**.
4. Fill the form as follows:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Client type** | `OpenID Connect` | Default |
    | **Client ID** | `actian-mcp` | Becomes both `FASTMCP_SERVER_AUTH_CLIENT_ID` and `FASTMCP_SERVER_AUTH_AUDIENCE` (after audience mapper) |

5. Select **Next**.
6. On the **Capability config** screen, configure the following values:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Client authentication** | `On` | Makes the client _confidential_ and generates a client secret |
    | **Authorization** | `Off` | Not needed for basic OAuth |
    | **Standard flow** | Checked | Required for browser login |
    | **Direct access grants** | Checked | Required for testing only |

    !!! warning "Disable direct access grants in production"
        The `password` grant (direct access grants) is insecure for production use and only intended for local debugging with `curl`.

7. Select **Next**.
8. On the **Login settings** screen, configure the following values:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Root URL** | `https://<mcp-server-host>:8000` | MCP server's external URL |
    | **Valid redirect URIs** | `https://<mcp-server-host>:8000/*` | Must match the server's external URL |
    | **Web origins** | `https://<mcp-server-host>:8000` | For CORS |

9. Select **Save**.

### Get the Client Secret

1. After creating the client, select the **Credentials** tab.
2. Copy the **Client secret** value.

### Output of Step 2

| Config Field | Where to find it in Keycloak |
|---|---|
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | **Client ID**, for example, `actian-mcp` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Clients > your client > **Credentials** tab |
| `FASTMCP_SERVER_AUTH_BASE_URL` | MCP server's external URL, for example, `https://<mcp-server-host>:8000` |


## Step 3: Add the Audience Mapper (Required)

!!! danger "This step is critical"
    Without the Audience Mapper, Keycloak does not include the Client ID in the token's `aud` (audience) claim, and the MCP server rejects tokens with an `audience mismatch` error.

By default, Keycloak tokens only include internal audiences like `account`. The MCP server validates that the token's `aud` claim matches the configured `FASTMCP_SERVER_AUTH_AUDIENCE` value. You must inform Keycloak to include the audience string in the token.

!!! warning "Included Client Audience versus Included Custom Audience"
    The Audience mapper uses two audience fields:

    - **Included Client Audience** - Resolves the selected client name to its **internal UUID**, for example, `16f502e4-483e-4b0d-adbd-4d20e6e33e73`. It does not match the audience string that MCP server expects and causes `audience mismatch` errors.
    - **Included Custom Audience** - Inserts the literal string, for example, `actian-mcp`. This is required by the MCP server and the recommended option.

1. Navigate to **Clients** and select your client, for example, `actian-mcp`.
2. Select the **Client scopes** tab.
3. Select the **`actian-mcp-dedicated`** link (listed as "Dedicated"). If you don't see the dedicated scope, check the **Mappers** tab directly.
4. Select **Configure a new mapper** or **Add Mapper**.
5. Select **Audience** (not **Audience Resolve**) from the list.

    !!! note "Audience versus Audience Resolve"
         "Audience Resolve" is a different mapper that resolves audiences dynamically. It does not hardcode your audience into `aud`. Therefore, you are required to select **Audience** mapper.

6. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `audience-mapping` | Provide a descriptive name. |
    | **Included Client Audience** | _(leave empty)_ | Do not use this field. It resolves to an internal UUID. |
    | **Included Custom Audience** | `actian-mcp` | The literal string that must match `FASTMCP_SERVER_AUTH_AUDIENCE` in the `conf.json` file. |
    | **Add to ID token** | `Off` | This field is not required. |
    | **Add to access token** | `On` | **Required** - the MCP server checks the access token. |

7. Select **Save**.

### Verification

After adding the mapper, request a new token and decode it. The `aud` claim includes the audience string:

```bash
# Request a token
TOKEN=$(curl -s -X POST \
  "http://<keycloak-host>:8080/realms/actian-mcp/protocol/openid-connect/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=actian-mcp" \
  -d "client_secret=<your-secret>" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Decode and inspect the aud claim
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool | grep aud
```

Expected output:
```json
"aud": ["actian-mcp", "account"]
```

!!! note "Token caching"
    If you still see a UUID instead of `actian-mcp` in the `aud` claim, the old token may be cached. Wait for it to expire (default 5 minutes) or go to **Sessions** in the Keycloak Admin Console and sign out of all sessions for the service account to force a fresh token.


## Step 4 (Optional): Add the Sub Override Mapper

By default, Keycloak sets the `sub` claim to a UUID. You can override it to contain the login name for easier `user_impersonation` mapping.

1. Navigate to **Clients** > your client > **Client scopes** tab.
2. Select the **`actian-mcp-dedicated`** link.
3. Select **Configure a new mapper** > **User Property**.
4. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `sub-override` | Acts as a label |
    | **Property** | `username` | Maps the login name |
    | **Token Claim Name** | `sub` | Overwrites the standard `sub` field |
    | **Claim JSON Type** | `String` | NA |
    | **Add to ID token** | `On` | NA |
    | **Add to access token** | `On` | NA |

5. Select **Save**.

### Verification

After adding the mapper, the token contains the following:

```json
{
  "sub": "jdoe",
  "iss": "http://<keycloak-host>:8080/realms/actian-mcp",
  "aud": ["realm-management", "account", "actian-mcp"],
  "preferred_username": "jdoe",
  "scope": "openid email profile"
}
```

!!! warning "OIDC spec trade-off"
    The OIDC spec expects `sub` to be a stable, unique identifier (like a UUID). It is acceptable to override it with a username for internal tools like the MCP Server, but if a user renames their account, database permissions tied to the old name will break.

!!! tip "Alternative: use preferred_username"
    Instead of overriding `sub`, you can rely on the `preferred_username` claim (included by default when the `profile` scope is present). The MCP server's username extraction priority uses `preferred_username` before `sub`, so it works automatically without any mapper changes.


## Step 5: Create Keycloak Users (If Using User Impersonation)

If `user_impersonation` is `true`, each Keycloak user contains a matching database account. For more information, see [User Impersonation](../index.md#user-impersonation).

1. Navigate to **Users** in the left panel.
2. Select **Add user**.
3. Fill the form as follows:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Username** | `jdoe` | Must match with the database account name |
    | **Email** | `jdoe@example.com` | Optional but recommended |
    | **First Name** | `John` | Optional |
    | **Last Name** | `Doe` | Optional |
    | **Enabled** | `On` | NA |

4. Select **Create**.
5. Navigate to the **Credentials** tab > **Set password** > enter a password > toggle **Temporary** to `Off` > **Save**.

### Creating Matching Database User

```sql
-- Create the user account (no DB password needed — Keycloak handles authentication)
CREATE USER jdoe;

-- Grant access to the database
GRANT ACCESS ON DATABASE mydb TO jdoe;

-- Grant the necessary table permissions (adjust per your schema)
GRANT SELECT ON TABLE orders TO jdoe;
GRANT SELECT ON TABLE products TO jdoe;
```

!!! note "`profile` scope is required"
    Keycloak's userinfo endpoint only returns `preferred_username` when the token includes the `profile` scope. Without it, the endpoint returns only the `sub` claim (a UUID by default).

!!! important "Keycloak does not produce a `username` claim automatically"
    The MCP server's username extraction priority is - `username` > `preferred_username` > email prefix > sanitized `sub`. Keycloak **does not** produce a `username` claim by default. It only appears if you explicitly configure a User Attribute mapper. In practice, `preferred_username` (second in the priority) is the reliable choice for Keycloak, and it works automatically when the `profile` scope is present.

!!! note "Federated identity (LDAP / Social login)"
    If Keycloak federates users from an external LDAP or social provider, the `sub` claim may be a UUID that does not match a database account. Ensure that the federated users have `preferred_username` set, or add the sub-override mapper ([Step 4](#step-4-optional-add-the-sub-override-mapper)), or set `user_impersonation: false`.


## Step 6: Assemble the Final Configuration

### Mapping Summary

| `conf.json` Field | Keycloak Source | Example Value |
|---|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `http://<keycloak-host>:8080/realms/<realm>/.well-known/openid-configuration` | `http://10.100.11.187:8080/realms/actian-mcp/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | Clients > your client > **Client ID**| `actian-mcp` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Clients > your client > **Credentials**| (your secret) |
| `FASTMCP_SERVER_AUTH_BASE_URL` | MCP server's external URL | `https://<mcp-server-host>:8000` |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | Value from **Included Custom Audience** in the audience mapper | `actian-mcp` |
| `user_impersonation` | As per your choice | `true` or `false` |

!!! info "Audience in Keycloak versus Auth0"
    In Auth0, the audience is a separate API Identifier (often a URL). In Keycloak, you define the audience string through the **Included Custom Audience** field in the audience mapper ([Step 3](#step-3-add-the-audience-mapper-required)). A common convention is to set it to the Client ID, for example, `actian-mcp`. If `FASTMCP_SERVER_AUTH_AUDIENCE` is omitted from the configuration, the server falls back to `CLIENT_ID`.

### Example `conf.json`

```json
{
    "driver": "{Ingres}",
    "server": "@<db-host>,tcp_ip,<port>",
    "database": "mydb",
    "database_user": "<database_user>",
    "database_password": "<database_password>",
    "max_connections": 10,
    "host": "0.0.0.0",
    "port": 8000,
    "ssl_certfile": "/app/server.crt",
    "ssl_keyfile":  "/app/server.key",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "http://<keycloak-host>:8080/realms/actian-mcp/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "actian-mcp",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<your-client-secret>",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp-server-host>:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "actian-mcp",
        "user_impersonation": true
    }
}
```

!!! note
    Replace `<db-host>` with the database server address. In the Docker container, use the host's IP address or `host.docker.internal`(not `localhost` or `127.0.0.1`, which refer to the container itself).

For TLS setup details (certificate generation, Docker deployment, trusting self-signed certifications), see [HTTPS / TLS for Remote Deployments](../index.md#secure-remote-deployments-with-https-and-tls).

For security best practices (file permissions, `.gitignore`, secrets management), see [Security Best Practices](../index.md#security-best-practices).


## Verify End-to-End

After starting the MCP server container with OAuth configured:

1. Open a browser and navigate to the server's `/mcp` endpoint, for example, `https://<mcp-server-host>:8000/mcp`.
2. You are **redirected to the Keycloak login page**.
3. Log in with a Keycloak user, for example, `jdoe`.
4. After logging in, Keycloak redirects you back to the MCP server with a valid token.
5. Check server logs for `Stored database username: jdoe` to confirm user impersonation is active.


## Troubleshooting

### Verify OIDC Discovery Endpoint

```bash
curl http://<keycloak-host>:8080/realms/actian-mcp/.well-known/openid-configuration \
  | python3 -m json.tool
```

### Verify Token Contents (Development Only)

```bash
curl -s -X POST \
  http://<keycloak-host>:8080/realms/actian-mcp/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=actian-mcp" \
  -d "client_secret=your-secret" \
  -d "username=jdoe" \
  -d "password=secret" \
  -d "scope=openid email profile" \
  | python3 -m json.tool
```

Decode the `access_token` at [jwt.io](https://jwt.io) and verify the following:

- `aud` contains Client ID, for example, `actian-mcp`.
- `sub` contains the username (if you added the sub override mapper) or a UUID.
- `preferred_username` contains the login name.

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `audience mismatch` | Audience string not in the token's `aud` claim. | [Step 3](#step-3-add-the-audience-mapper-required) - add the audience mapper using **Included Custom Audience** (not Included Client Audience, which resolves to a UUID). |
| `invalid_client` | Wrong `client_id` or `client_secret`. | Re-copy from Clients > Credentials tab. |
| `invalid_grant` | Wrong username/password, or user disabled. | Check user exists and is enabled. |
| `KeyError` on startup (for example, `CLIENT_SECRET`) | Some OAuth fields are present but others missing. | Provide **all** required fields or remove `oauth` entirely. |
| `Could not extract username` | No usable username claim in token. | Add sub-override mapper ([Step 4](#step-4-optional-add-the-sub-override-mapper)). Ensure `preferred_username` is present or set `user_impersonation: false`. |
| `unauthorized` / 401 on every request | OAuth misconfigured or token expired. | Check server logs and verify the OIDC discovery URL is reachable. |
| `Client not enabled` / `Realm not found` | Realm or client is disabled. | Ensure both  Realm and client are enabled in the Admin console. |
| `ValueError: Issuer URL must be HTTPS` | OAuth without TLS configured. | Add `ssl_certfile`/`ssl_keyfile` and use `https://` for `BASE_URL`. |
| `ValueError: BASE_URL must start with https://` | SSL configured but `BASE_URL` still uses `http://`. | Update `BASE_URL` to `https://`. |
| `ssl.SSLError: PEM lib` | Missing certificate/key environment variables before Docker starts. | Mount certificate/key as volumes when starting the container (see [Docker deployment](../index.md#step-3-deploy-the-docker)). |
| `ERR_TLS_CERT_ALTNAME_INVALID` | Certificate missing SAN. | Regenerate with `-addext "subjectAltName=IP:<ip>"`. |
| `TypeError: fetch failed` (VS Code) | Self-signed certificate not trusted by `Node.js`. | Trust certificate and set `NODE_EXTRA_CA_CERTS`. |
| Token validation behaves unexpectedly | OIDC endpoint is unreachable at startup. | The server falls back to default verification without `TokenCapturingJWTVerifier` - `user_impersonation` does not work even though the server appears to be running. Restart after the endpoint is accessible. |

### Token Expiration

Keycloak tokens have a configurable lifetime:

1. Navigate to **Realm Settings** > **Tokens** tab.
2. Do the following key settings:

    | Setting | Default | Notes |
    |---------|---------|-------|
    | **Access Token Lifespan** | 5 minutes | Increase for long-running MCP sessions, for example, 1 hour |
    | **SSO Session Idle** | 30 minutes | How long before an idle session expires |
    | **SSO Session Max** | 10 hours | Maximum session duration |

3. Adjust as needed and select **Save**.


## Keycloak versus Auth0 - Key Differences

| Aspect | Auth0 | Keycloak |
|--------|-------|----------|
| **Provider class** | Dedicated Auth0 support in FastMCP | Generic `OIDCProxy` (standard OIDC) |
| **Audience** | Separate API Identifier (often a URL) | Configured through **Included Custom Audience** in the audience mapper (typically set to the Client ID) |
| **`sub` claim** | `auth0\|<id>` or `google-oauth2\|<id>` | UUID by default (can override to username) |
| **`preferred_username`** | Not always present | Always present by default |
| **Discovery URL format** | `https://<domain>/.well-known/openid-configuration` | `http://<host>/realms/<realm>/.well-known/openid-configuration` |
| **Self-hosted** | No (SaaS only) | Yes (self-hosted or cloud) |
| **Token lifetime config** | API Settings > Token Expiration | Realm Settings > Tokens|


## Staging versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Enable direct access grants for `curl`-based testing. |
| **Staging / Production** | Deploy Keycloak behind HTTPS. Always use HTTPS for `CONFIG_URL`, `BASE_URL`, and callback URLs. Use a strong `CLIENT_SECRET`. **Disable direct access grants**. Change default admin credentials. |



