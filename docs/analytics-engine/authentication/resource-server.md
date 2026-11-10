---
title: Resource-Server Mode
description: Accept access tokens issued by your own identity provider, so an application that has already signed the user in can call the Actian MCP Server for Analytics Engine without a second OAuth login.
---

# Resource-Server Mode

By default, the Actian MCP Server runs the OAuth login itself: it signs the user in through your identity provider (IdP), issues its own token, and accepts only that token. This suits general-purpose MCP clients, such as Claude Desktop and GitHub Copilot, which register with the server and run the login.

**Resource-server mode** is for an application that has **already signed the user in**. Instead of running a second login, the application calls the MCP Server with an access token from your IdP. The server does not run a login at all. It verifies each token against your IdP's published signing keys and runs the call as the user named in the token.

| | OAuth login (default) | Resource-server mode |
| :--- | :--- | :--- |
| Who signs the user in | The MCP Server | Your application or gateway |
| Tokens accepted | Only its own | Tokens from your IdP that carry the MCP Server's audience |
| Client registration | Each MCP client registers with the server | None |
| Suits | General-purpose MCP clients | Applications that already hold the user's token |

A deployment runs one mode. To serve both kinds of client, run two deployments against the same databases.

---

## Configuration

Set `auth_mode` at the **top level** of `conf.json`, not inside the `oauth` block:

```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "ssl_certfile": "/app/server.crt",
  "ssl_keyfile": "/app/server.key",
  "auth_mode": "resource-server",
  "oauth": {
    "FASTMCP_SERVER_AUTH_CONFIG_URL": "<oidc_discovery_url>",
    "FASTMCP_SERVER_AUTH_AUDIENCE": "<mcp_api_audience>",
    "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp_server_host>:8000",
    "user_impersonation": true
  }
}
```

Add your database settings, or a [`targets` block](../multi-target.md), as usual.

| Key | Required | Description |
| :--- | :--- | :--- |
| `auth_mode` | Yes | `resource-server`. When omitted, the server runs the default OAuth login if the `oauth` block sets a client ID, and otherwise runs without authentication. |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | Yes | Your IdP's OpenID Connect discovery document. The server reads the token issuer and the signing keys from it. |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | Yes | The audience every token must carry, normally the identifier of the API that represents the MCP Server in your IdP. |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Yes | The server's public address. It must use `https://` unless `host` is `localhost`, `127.0.0.1`, or `::1`. |
| `user_impersonation` | No | Default `true`: every query runs as the database user named in the token. See [The Username Must Be in the Token](#the-username-must-be-in-the-token). |
| `FASTMCP_SERVER_AUTH_SCOPE` | No | Space-separated scopes that every token must carry. |

- No client ID or client secret is used. If `FASTMCP_SERVER_AUTH_CLIENT_ID` is set, it is ignored and the server logs a warning.
- When `host` is not `localhost`, `127.0.0.1`, or `::1`, set `ssl_certfile` and `ssl_keyfile`; the server does not start without them. See [Secure Remote Deployments with HTTPS and TLS](index.md#secure-remote-deployments-with-https-and-tls).
- Every configuration error in this mode stops the server from starting. A missing key, or a discovery document that cannot be fetched, never results in a server that runs without authentication.
- `auth_mode` is read **only at the top level**. If you place it inside the `oauth` block, the server ignores it. When the `oauth` block has no client ID, the server then starts **without authentication** instead of stopping. Always run the [verification](#verify-the-deployment) checks after a configuration change.

---

## The Token Flow

1. The user signs in to your application, which receives an access token.
2. The application obtains an access token for the MCP Server's audience, for the same user. It can request that audience when the user signs in, or, if your IdP supports it, exchange its own token for one (RFC 8693 token exchange).
3. The application calls the MCP Server with that token in the `Authorization: Bearer` header.
4. The server checks the token's issuer, signature, audience, and scopes, and runs the call as the user named in the token.

The server verifies the token it receives and does not depend on how the application obtained it. Whichever way you choose, the token must carry the MCP Server's audience, the scopes the call needs, and, with `user_impersonation` on, a username claim.

The server publishes the standard protected-resource metadata (RFC 9728) at `/.well-known/oauth-protected-resource/mcp`. It names your IdP, so a client can find out where to get a token.

The server has no login endpoints in this mode. `/mcp/authorize` and `/mcp/oauth/token` return `404`.

---

## Required Scopes

The default OAuth login requires `openid`, `email`, and `profile` on every token. **Resource-server mode does not**, because an access token issued for an API normally carries none of them.

A token needs:

- Any scopes listed in `FASTMCP_SERVER_AUTH_SCOPE`.
- In a [multi-target deployment](../multi-target.md), the per-target scope for each database it uses: `actian:{host}:{instance}:{database}:{read|write}`.
- For writes, the write scope described in [Write Support](../write-support.md#authorizing-a-write).

The server reads scopes from the token's `scope`, `scp`, and `permissions` claims, combined.

The calling application requests these scopes, at sign-in or in a token exchange, and your IdP issues only the scopes that the application's client is allowed to request. If a grant is missing from the token, check first that the scope is available to the application's client.

!!! warning "The application decides which grants a user receives"
    The server trusts the grants in the token. If one application client serves many users, any of those users can receive any scope that client is allowed to request. Request only the grants the signed-in user is entitled to, or use a separate client for each group of users with different access.

---

## The Username Must Be in the Token

With `user_impersonation` set to `true`, every query runs as the authenticated user (`SET SESSION AUTHORIZATION`), so the server needs that user's **database user name** from the token. The service account in `conf.json` must also be allowed to run that statement; see [Service Account Privileges](index.md#service-account-privileges). The server reads the first of these claims that is present:

1. `username`
2. `preferred_username`
3. `email`, using the part before `@`

In this mode the server does **not** call the IdP's userinfo endpoint and does **not** fall back to the `sub` claim, because `sub` is an IdP identifier, not a database user. A token with none of the three claims is rejected with `401`. The server log records which claims were missing; the caller gets no detail.

The value must match a database user. Configure your IdP to add the claim to the access token:

- **Auth0:** add a Post-Login Action. See [Auth0: Resource-Server Mode](auth0.md#resource-server-mode).
- **Keycloak:** see [Keycloak: Resource-Server Mode](keycloak.md#resource-server-mode).

### Service and Machine-to-Machine Callers

When the caller is a service rather than a user, set `user_impersonation` to `false`. Queries then run as the configured database account, and a token without a user claim is accepted. Per-target scopes are still checked.

!!! warning "Keycloak service accounts"
    A Keycloak service-account token carries `preferred_username: service-account-<client-id>`. With `user_impersonation` set to `true`, the server tries to run queries as that user, which normally does not exist in the database, so queries fail at the database. Use `user_impersonation: false` for a deployment that serves service accounts.

---

## Verify the Deployment

```bash
BASE=https://<mcp_server_host>:8000

# 1. The metadata names your IdP
curl -s "$BASE/.well-known/oauth-protected-resource/mcp"

# 2. No login endpoints exist (both return 404)
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp/authorize"
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp/oauth/token"

# 3. A request without a token is refused (401)
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp"
```

If check 3 returns anything other than `401`, authentication is not active. See the last row of [Troubleshooting](#troubleshooting).

Then call a tool with a real token from your application; see [Call the Server from a Client](#call-the-server-from-a-client). On success, the server log contains `Stored database username (strict claim mode): <name>`.

---

## Call the Server from a Client

A client in this mode sends the access token it already holds in the `Authorization: Bearer` header. It does not run a login.

### From an Application (Python)

The `fastmcp` Python client sends a token passed as `auth` as a bearer token:

```python
import asyncio
from fastmcp import Client

async def main(token: str):
    async with Client("https://<mcp_server_host>:8000/mcp", auth=token) as client:
        result = await client.call_tool("list_tables", {})
        print(result)

asyncio.run(main("<access_token>"))
```

Pass the token your application obtained in [The Token Flow](#the-token-flow), and obtain a new one before it expires. In a [multi-target deployment](../multi-target.md), use the target URL, `https://<mcp_server_host>:8000/mcp/{host}/{instance}/{database}`.

### From GitHub Copilot (Testing)

To try the deployment from GitHub Copilot in Visual Studio Code, add the token as a header in `.vscode/mcp.json`. The `inputs` entry makes Visual Studio Code ask for the token and hide what you type, instead of storing it in the file:

```json
{
    "inputs": [
        {
            "type": "promptString",
            "id": "actian-mcp-token",
            "description": "Access token for the Actian MCP Server",
            "password": true
        }
    ],
    "servers": {
        "actian-mcp-server": {
            "type": "http",
            "url": "https://<mcp_server_host>:8000/mcp",
            "headers": {
                "Authorization": "Bearer ${input:actian-mcp-token}"
            }
        }
    }
}
```

Use this for testing only. The token is a fixed value: when it expires, every request returns `401` until you supply a new token. To get a token for testing, see [Auth0: Resource-Server Mode](auth0.md#resource-server-mode) or [Keycloak: Resource-Server Mode](keycloak.md#resource-server-mode).

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| Server does not start; the error names an `oauth` key | A required key is missing or empty. | Set `FASTMCP_SERVER_AUTH_CONFIG_URL`, `FASTMCP_SERVER_AUTH_AUDIENCE`, and `FASTMCP_SERVER_AUTH_BASE_URL`. |
| Server does not start while fetching the discovery document | The URL is wrong, or the IdP cannot be reached from the container. | Check the URL from inside the container. |
| `401`; log shows `issuer mismatch` | The signature is valid, but the token's `iss` differs from the issuer in the discovery document. This happens when the IdP is reached under a different address or custom domain. | Point `FASTMCP_SERVER_AUTH_CONFIG_URL` at the address that matches the `iss` in your tokens. |
| `401`; log shows only `invalid_token` | The signature could not be verified. The token came from a different tenant or realm than the discovery document, or it was altered. | Point `FASTMCP_SERVER_AUTH_CONFIG_URL` at the IdP that issues the tokens. |
| `401`; log shows `audience mismatch` | The token's `aud` does not contain `FASTMCP_SERVER_AUTH_AUDIENCE`. | Request a token for the MCP Server's audience. |
| `401`; log names the missing username claims | The token has none of `username`, `preferred_username`, or `email`, and `user_impersonation` is `true`. | Add the claim at the IdP, or set `user_impersonation: false` for service callers. |
| `403` `insufficient_scope` on a target URL | The token has no read scope for that target, or the target does not exist. The two are answered identically. | Grant the scope named in the `WWW-Authenticate` header, or correct the URL. |
| Queries fail with `no GRANT` | The user named in the token has no privilege on the table (`no GRANT or GRANT compatible permit exists`), often because the name is not a database user. | Make the claim value match a database user, and grant that user the privileges it needs. |
| Every query fails with `You lack the privileges` | The service account in `conf.json` is not allowed to run `SET SESSION AUTHORIZATION`. | See [Service Account Privileges](index.md#service-account-privileges). |
| Writes fail; `mcp:write` is named | The token was issued without `mcp:write` (`write operations require the 'mcp:write' scope`). In this mode the server does not request it; the calling application must. | Request `mcp:write` at sign-in or in the exchange. See [Write Support](../write-support.md#authorizing-a-write). |
| Target writes fail with `no scope grants 'write'` | The token has only a `:read` grant for that target. `mcp:write` does not authorize writes on a target URL. | Request the target's `actian:{host}:{instance}:{database}:write` scope. |
| Brief `401`s after a signing-key change | The server fetches the IdP's key set again as soon as it sees an unknown key, but at most once every 30 seconds. | Nothing; the server recovers on its own within 30 seconds. |
| A request without a token does not get `401` | `auth_mode` is not at the top level of `conf.json`, for example because it is inside the `oauth` block. The server runs the default OAuth login, so `/mcp/authorize` returns a login page, or, when the `oauth` block has no client ID, runs without authentication and logs `server will run without authentication`. | Move `auth_mode` to the top level, restart, and confirm that a request without a token returns `401`. |

---

## Known Limits

- **Token exchange is optional and depends on your IdP.** Keycloak supports it, and also lets the application request the MCP Server's audience at sign-in. Auth0 has no token exchange for this purpose, so the application requests the audience directly.
- **Revoking access takes effect when the token expires.** Tokens are verified locally against the IdP's published keys.
- **A withdrawn signing key stays trusted for up to an hour.** The server caches the IdP's keys for one hour, so a token signed with a key the IdP has removed is still accepted until the cache expires.
- **Write approval still uses the MCP approval prompt.** A calling application that cannot display it has its writes declined. See [Write Support](../write-support.md).

---

## Next Steps

<div class="grid cards" markdown>

- :material-shield-key: **[Auth0](auth0.md#resource-server-mode)**  
  Configure Auth0 for resource-server mode, including the username Action.

- :material-shield-key: **[Keycloak](keycloak.md#resource-server-mode)**  
  Configure Keycloak for resource-server mode, requesting the MCP audience at sign-in or through token exchange.

- :material-server-network: **[Multi-Target Deployments](../multi-target.md)**  
  Serve many databases from one server with per-target scopes.

</div>
