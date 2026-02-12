# Schema Design Best Practices

These rules prioritize correctness first, then predictable performance.

## 1) Encode business invariants in constraints
Use `NOT NULL`, `CHECK`, `UNIQUE`, foreign keys, and exclusion constraints where applicable.

```sql
create table products (
  id bigint generated always as identity primary key,
  sku text not null unique,
  price numeric(10,2) not null check (price >= 0)
);
```

## 2) Choose primary keys deliberately
- Use identity keys for simple single-cluster write paths.
- Use UUIDs when externally visible/global uniqueness is required.

```sql
create table users (
  id bigint generated always as identity primary key
);
```

## 3) Use semantically correct data types
- `timestamptz` for real-world timestamps.
- `numeric` for exact currency/financial math.
- `jsonb` for semi-structured payloads you query.

## 4) Index foreign key columns explicitly
PostgreSQL enforces the FK but does not auto-create the referencing index.

```sql
create table orders (
  id bigint generated always as identity primary key,
  customer_id bigint not null references customers(id)
);

create index orders_customer_id_idx on orders (customer_id);
```

## 5) Use partitioning only when justified
Partition for large tables with clear partition-key filters and lifecycle operations (retention, archival, fast drops).

```sql
create table events (
  id bigint generated always as identity,
  created_at timestamptz not null,
  payload jsonb not null
) partition by range (created_at);
```

## 6) Keep naming conventions stable
Unquoted lowercase identifiers avoid case-sensitivity surprises across tools and SQL clients.

## Verification References
- https://www.postgresql.org/docs/current/ddl-constraints.html
- https://www.postgresql.org/docs/current/sql-createtable.html
- https://www.postgresql.org/docs/current/datatype.html
- https://www.postgresql.org/docs/current/ddl-partitioning.html
