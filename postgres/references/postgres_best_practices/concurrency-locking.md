# Concurrency and Locking Best Practices

Use these rules to reduce contention and avoid avoidable blocking/deadlocks.

## 1) Keep transactions short
Acquire locks as late as possible, commit/rollback as soon as possible.

## 2) Lock rows in a consistent order
When two transactions touch the same entities, a stable ordering reduces deadlock risk.

```sql
begin;
select * from accounts where id in (1,2) order by id for update;
update accounts set balance = balance - 100 where id = 1;
update accounts set balance = balance + 100 where id = 2;
commit;
```

## 3) Use `SKIP LOCKED` for queue workers
Multiple workers can claim different jobs without waiting on each other.

```sql
update jobs
set status = 'processing', worker_id = $1
where id = (
  select id
  from jobs
  where status = 'pending'
  order by created_at
  limit 1
  for update skip locked
)
returning *;
```

## 4) Use advisory locks for logical mutexes
For app-level mutual exclusion without dedicated lock rows, advisory locks are often cleaner.

```sql
select pg_advisory_lock(hashtext('nightly-closeout'));
-- critical section
select pg_advisory_unlock(hashtext('nightly-closeout'));
```

## 5) Set practical lock/statement timeouts
Fail fast under lock contention instead of accumulating stuck workers.

```sql
set lock_timeout = '5s';
set statement_timeout = '30s';
```

## Verification References
- https://www.postgresql.org/docs/current/mvcc.html
- https://www.postgresql.org/docs/current/explicit-locking.html
- https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE
- https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS
- https://www.postgresql.org/docs/current/runtime-config-client.html
