# Schema Design Best Practices

Design schemas for performance, clarity, and operational safety.

## Choose appropriate data types
Use types that match semantics and size.

```sql
create table users (
  id bigint generated always as identity primary key,
  email text,
  created_at timestamptz,
  is_active boolean default true,
  price numeric(10,2)
);
```

## Index foreign key columns
Postgres does not automatically index foreign keys.

```sql
create table orders (
  id bigint generated always as identity primary key,
  customer_id bigint references customers(id),
  total numeric(10,2)
);

create index orders_customer_id_idx on orders (customer_id);
```

## Use lowercase identifiers
Avoid quoted mixed-case identifiers to reduce tooling friction.

```sql
create table users (
  user_id bigint primary key,
  first_name text
);
```

## Partition large tables
Partition by time or key when tables reach very large sizes or hot partitions.

```sql
create table events (
  id bigint generated always as identity,
  created_at timestamptz not null,
  data jsonb
) partition by range (created_at);
```

## Choose an optimal primary key strategy
Prefer sequential keys unless you need distributed, time-ordered IDs.

```sql
-- Sequential identity
create table users (
  id bigint generated always as identity primary key
);

-- Time-ordered UUIDs (if needed)
create table orders (
  id uuid default uuid_generate_v7() primary key
);
```
