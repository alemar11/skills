# Security and RLS Best Practices

These rules focus on built-in PostgreSQL authorization and row-level controls.

## 1) Enforce least privilege with explicit roles
Use role separation (`read`, `write`, `admin`) and grant only required privileges.

```sql
create role app_readonly nologin;
grant usage on schema public to app_readonly;
grant select on table public.products to app_readonly;
```

## 2) Remove broad default access where possible
Review and tighten default grants (especially `PUBLIC`) for shared schemas.

```sql
revoke all on schema public from public;
```

## 3) Enable RLS for tenant-scoped tables
Apply `ENABLE ROW LEVEL SECURITY` and policies to make tenant filtering database-enforced.

```sql
alter table orders enable row level security;

create policy orders_tenant_policy on orders
for all
using (tenant_id = current_setting('app.tenant_id')::bigint);
```

## 4) Use `FORCE ROW LEVEL SECURITY` when needed
`FORCE` ensures table owners do not bypass policies unintentionally.

```sql
alter table orders force row level security;
```

## 5) Index columns referenced by policies
RLS predicates run with user queries; index policy columns to avoid full scans.

```sql
create index orders_tenant_id_idx on orders (tenant_id);
```

## Verification References
- https://www.postgresql.org/docs/current/user-manag.html
- https://www.postgresql.org/docs/current/sql-grant.html
- https://www.postgresql.org/docs/current/sql-revoke.html
- https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- https://www.postgresql.org/docs/current/sql-createpolicy.html
