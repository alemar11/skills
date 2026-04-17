# Connection Management Best Practices

These rules are generic for PostgreSQL deployments and avoid provider-specific assumptions.

## 1) Keep connection counts bounded
Each backend is a server process with memory/CPU cost. Set `max_connections` intentionally for your host resources.

## 2) Use a pooler when client concurrency is high
A pooler lets many clients share fewer database backends, improving resilience under burst traffic.

## 3) Match pool mode to session features
If your workload depends on session state (for example named prepared statements or temp tables), use a compatible pooling mode.

## 4) Set timeouts at the narrowest practical scope
Use timeouts to protect the cluster from runaway or abandoned sessions, but prefer role-, database-, or session-scoped defaults for application traffic. Cluster-wide defaults for `statement_timeout`, `transaction_timeout`, and `lock_timeout` can break maintenance or administrative work. If your PostgreSQL version does not support `transaction_timeout`, omit that setting rather than forcing a version-specific workaround into the general pattern.

```sql
alter role app_user in database appdb set statement_timeout = '30s';
alter role app_user in database appdb set lock_timeout = '5s';
alter role app_user in database appdb set idle_in_transaction_session_timeout = '30s';
alter role app_user in database appdb set idle_session_timeout = '10min';
alter role app_user in database appdb set transaction_timeout = '2min';
```

## 5) Monitor connection pressure continuously
Track active sessions, waiting states, and long-lived idle-in-transaction sessions.

```sql
select state, count(*)
from pg_stat_activity
group by state
order by count(*) desc;
```

## Verification References
- https://www.postgresql.org/docs/current/runtime-config-connection.html
- https://www.postgresql.org/docs/current/runtime-config-client.html
- https://www.postgresql.org/docs/current/sql-alterrole.html
- https://www.postgresql.org/docs/current/monitoring-stats.html
- https://www.pgbouncer.org/features.html
