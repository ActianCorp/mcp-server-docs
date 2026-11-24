# `targets.d/` example files

Target files for a multi-target Ingres or Analytics Engine deployment. Mount a
directory of these files at `/app/targets.d` in the container, and the server
applies new, changed, and removed files within about 10 seconds, without a restart.
For the full description, see
[Multi-Target Deployments](https://docs.actian.com/mcp-server/latest/ingres/multi-target.html).

Both files assume `conf.json` has a `targets` block with shared defaults:

```json
{"targets": {"defaults": {"driver": "{Ingres}", "max_connections": 10}}}
```

so each file holds only the fields that vary per target.

| File | Shows |
|---|---|
| [`db07-sales.json`](db07-sales.json) | One file, one installation, with a database that uses its own credentials. |
| [`team-hr.json`](team-hr.json) | One file, several installations, as a JSON list. |

Both shapes can be mixed in the same directory.

An installation (`host` and `instance`) must appear only once across `conf.json`
and all files in `targets.d/`. A duplicate stops the server from starting, or, when
added while the server runs, is rejected while the server keeps serving its
previous targets. To add a database to an installation that is already listed,
add it to that entry's `databases` list.

## Trying it

```bash
mkdir targets.d
cp db07-sales.json targets.d/
docker run -d -p 8000:8000 \
  -v "$PWD/conf.json:/app/conf.json:ro" \
  -v "$PWD/targets.d:/app/targets.d:ro" \
  actian/ingres-mcp-server:1.2.0
# later, while the server runs:
cp team-hr.json targets.d/
# within about 10 seconds, list_accessible_targets shows the new databases
```

The passwords in these files are placeholders. These files carry database
passwords just like `conf.json`: keep the directory read-only, and in Kubernetes
mount it from a Secret, not a ConfigMap.
