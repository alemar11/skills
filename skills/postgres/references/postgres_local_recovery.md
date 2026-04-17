# Postgres Local Recovery

Use this reference when a local Postgres instance will not start, or when a client is reaching the wrong local server. This guide is for local/dev recovery only, especially Docker-backed setups.

## Important warnings
- Prefer restore-from-backup or vendor-supported recovery procedures for production systems.
- Do not run repair commands until you know the actual cluster root and have copied the data directory.
- Treat `pg_resetwal` as an emergency last-resort tool for local recovery, not a routine fix.

## 1) Classify the failure
Decide which of these you have before changing anything:
- Connection-path problem: the client reaches the wrong server, the wrong port, or a different local Postgres than expected.
- Startup problem: Postgres cannot start its data directory and exits during bootstrap or recovery.

Start with logs and port ownership, not with schema or auth changes.

## 2) Check for local port collisions first
If Docker and a host-local Postgres both try to use `5432`, the client may hit the wrong server even if Docker starts successfully.

Examples:
```sh
lsof -nP -iTCP:5432 -sTCP:LISTEN
docker compose ps
docker port <pg_container_name>
```

Typical local fixes:
- Stop the host-local Postgres process if Docker should own `5432`.
- Or move Docker to a different host port if both must run at the same time.

## 3) Verify the actual cluster root
Do not assume the cluster root is the top-level bind mount. Confirm it by finding `PG_VERSION`.

Examples:
```sh
find pgdata -maxdepth 3 -name PG_VERSION -print
find /path/to/data -maxdepth 3 -name PG_VERSION -print
```

Important: some Docker layouts use nested paths such as `pgdata/18/docker`. In that case:
- the cluster root is the directory that contains `PG_VERSION`
- the bind mount and `PGDATA` must agree with that layout

If Postgres says the data directory is non-empty but not a cluster, you likely mounted the wrong parent directory or set `PGDATA` to the wrong path.

## 4) Inspect startup logs before repair
Look for the exact startup failure:

```sh
docker compose logs --no-color --tail=200 pg
```

Common meanings:
- `role "<name>" does not exist`: often a connection-path problem, not a broken cluster.
- `directory ".../data" exists but is not empty`: the path is not the real cluster root.
- `invalid checkpoint record` or `could not locate a valid checkpoint record`: control file / WAL state is inconsistent and may require physical recovery steps.

## 5) Inspect control-file and WAL state
Use `pg_controldata` first to read the cluster metadata:

```sh
pg_controldata /path/to/cluster_root
```

If the control file points to a checkpoint/WAL location that looks suspicious, inspect WAL directly:

```sh
pg_waldump -p /path/to/cluster_root/pg_wal <wal_segment> | tail -n 40
```

This is the key distinction:
- If logs and `pg_waldump` show the control file points beyond the last valid record, `pg_resetwal` may be appropriate.
- If WAL segments are missing entirely, or the data directory has broader corruption, stop and treat it as a deeper recovery case.

## 6) Copy the data directory before any repair
Make a full filesystem copy before running repair commands.

Example:
```sh
ts="$(date +%Y%m%d-%H%M%S)"
backup="pgdata.broken-${ts}-pre-reset"
rsync -a pgdata/ "${backup}/"
echo "${backup}"
```

Do not repair the only copy.

## 7) Use `pg_resetwal` only as an emergency local repair step
Run a dry run first:

```sh
pg_resetwal -n /path/to/cluster_root
```

Only if the evidence points to a bad checkpoint pointer or broken WAL control state, run the actual reset:

```sh
pg_resetwal -f /path/to/cluster_root
```

Use it only after:
- logs confirm checkpoint/WAL startup failure
- `pg_controldata` identifies the relevant checkpoint/WAL position
- `pg_waldump` supports the diagnosis when possible
- you have a full copy of the original data directory

## 8) Restart and verify immediately
After any repair step:

```sh
docker compose up -d pg
docker compose ps
docker compose logs --no-color --tail=200 pg
```

Then verify both local socket/container access and TCP access:

```sh
docker compose exec pg psql -U postgres -d postgres -c "select current_user, current_database();"
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "select current_user, current_database();"
```

If the second command hits the wrong server, re-check port ownership.

## 9) Dump the cluster after recovery
If the server comes back after `pg_resetwal`, take a logical dump as soon as possible.

Examples:
```sh
docker compose exec pg pg_dumpall -U postgres > "pg_dumpall-$(date +%Y%m%d-%H%M%S).sql"
```

Or dump only the important databases if the cluster is large. Plan a clean rebuild/reinit if the recovered data matters.
