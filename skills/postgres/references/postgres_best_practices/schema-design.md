# Schema Design Best Practices

These rules prioritize correctness first, then predictable performance.

## 1) Encode business invariants in constraints
Use `NOT NULL`, `CHECK`, `UNIQUE`, foreign keys, and exclusion constraints where applicable. Remember that `CHECK` evaluates to true for `NULL`, so pair it with `NOT NULL` when the value must be present.

```sql
create table products (
  id bigint generated always as identity primary key,
  sku text not null unique,
  price numeric(10,2) not null check (price >= 0)
);
```

If a nullable column still needs true uniqueness, use `NULLS NOT DISTINCT`.

```sql
create table external_accounts (
  id bigint generated always as identity primary key,
  external_ref text unique nulls not distinct
);
```

## 2) Choose primary keys deliberately
- Use identity keys for simple single-cluster write paths.
- Prefer identity columns over `serial`.
- Use UUIDs when externally visible/global uniqueness is required.

```sql
create table users (
  id bigint generated always as identity primary key
);
```

## 3) Use semantically correct data types
- `timestamptz` for real-world timestamps; avoid `timestamp without time zone` unless the value is intentionally timezone-free.
- `numeric` for exact currency/financial math.
- `text` by default for strings; add an explicit length check when the limit is part of the domain.
- `jsonb` for semi-structured payloads you query.

```sql
create table customer_profiles (
  id bigint generated always as identity primary key,
  display_name text not null check (length(display_name) <= 120),
  created_at timestamptz not null default now(),
  settings jsonb not null default '{}'
);
```

## 4) Index foreign key columns explicitly
PostgreSQL enforces the FK but does not auto-create the referencing index.

```sql
create table orders (
  id bigint generated always as identity primary key,
  customer_id bigint not null references customers(id)
);

create index orders_customer_id_idx on orders (customer_id);
```

## 5) Use generated columns or expression indexes for repeated computed predicates
Persist or index deterministic computed values that appear frequently in filters or joins.

```sql
alter table users
add column email_domain text
generated always as (split_part(lower(email), '@', 2)) stored;

create index users_email_domain_idx on users (email_domain);
```

## 6) Use partitioning only when justified
Partition for large tables with clear partition-key filters and lifecycle operations (retention, archival, fast drops).

```sql
create table events (
  id bigint generated always as identity,
  created_at timestamptz not null,
  payload jsonb not null
) partition by range (created_at);
```

## 7) Keep naming conventions stable
Unquoted lowercase identifiers avoid case-sensitivity surprises across tools and SQL clients.

## Verification References
- https://www.postgresql.org/docs/current/ddl-constraints.html
- https://www.postgresql.org/docs/current/sql-createtable.html
- https://www.postgresql.org/docs/current/datatype.html
- https://www.postgresql.org/docs/current/ddl-partitioning.html
