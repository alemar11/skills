# Connection Management Best Practices

Reduce connection overhead and prevent resource exhaustion.

## Set appropriate connection limits
Too many connections consume memory and degrade performance.

```sql
-- Example guidance; tune for your hardware
alter system set max_connections = 100;
alter system set work_mem = '8MB';
```

## Use connection pooling
Poolers (e.g., PgBouncer) let many clients share a small set of server connections.

```ini
# pgbouncer.ini (example)
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 10
```

## Configure idle connection timeouts
Automatically reclaim idle and idle-in-transaction sessions.

```sql
alter system set idle_in_transaction_session_timeout = '30s';
alter system set idle_session_timeout = '10min';
select pg_reload_conf();
```

## Use prepared statements correctly with pooling
Named prepared statements are connection-bound; in transaction pooling they can disappear.

```sql
-- Safer: unnamed statements (driver-managed) or deallocate in txn mode
prepare get_user as select * from users where id = $1;
execute get_user(123);
deallocate get_user;
```

If you require named prepared statements, use session pooling or disable prepares at the driver level.
