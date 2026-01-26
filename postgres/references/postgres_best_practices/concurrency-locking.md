# Concurrency & Locking Best Practices

Reduce contention, avoid deadlocks, and keep queues moving.

## Use advisory locks for application-level coordination
Avoid creating lock rows when you only need a logical mutex.

```sql
select pg_advisory_lock(hashtext('report_generator'));
-- do exclusive work
select pg_advisory_unlock(hashtext('report_generator'));
```

## Prevent deadlocks with consistent lock ordering
Acquire locks in a stable order across all code paths.

```sql
begin;
select * from accounts where id in (1, 2) order by id for update;
update accounts set balance = balance - 100 where id = 1;
update accounts set balance = balance + 100 where id = 2;
commit;
```

## Keep transactions short
Hold locks only for the minimal critical section.

```sql
begin;
update orders set status = 'paid'
where id = $1 and status = 'pending'
returning *;
commit;
```

## Use SKIP LOCKED for queue workers
Let workers claim different jobs without blocking each other.

```sql
update jobs
set status = 'processing', worker_id = $1, started_at = now()
where id = (
  select id from jobs
  where status = 'pending'
  order by created_at
  limit 1
  for update skip locked
)
returning *;
```
