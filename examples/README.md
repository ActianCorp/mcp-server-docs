# Actian MCP Server Examples

Runnable examples that accompany the [Actian MCP Server documentation](https://docs.actian.com/mcp-server/).

| Directory | Contents |
|---|---|
| [`extensions/`](extensions/) | Five example extensions that add your own tools to the server, plus a configuration template and a schema file for each supported database. |
| [`clients/`](clients/) | A console client that answers the server's write-approval prompt, for testing writes from a client that cannot display the prompt itself, and a client for multi-target deployments. |
| [`targets.d/`](targets.d/) | Target files for a multi-target deployment, added to a running Ingres or Analytics Engine server without a restart. |
| `conf.example.multi-target*.json` | `conf.json` examples for a multi-target Ingres or Analytics Engine deployment: two installations with per-database credentials, targets taken from `targets.d/`, and extensions offered on specific targets. |

Each directory has its own README with setup and usage details. For the
authoring contract and the full API, see the
[Extensions guide](https://docs.actian.com/mcp-server/extensions/index.html).
