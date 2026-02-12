# Advanced Features Best Practices

These features are high leverage when used with the right workload shape.

## 1) Use native full-text search for linguistic queries
For document search, prefer `tsvector` + GIN over wildcard `LIKE` scans.

```sql
alter table articles
add column search_vector tsvector
generated always as (
  to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
) stored;

create index articles_search_idx on articles using gin (search_vector);
```

## 2) Use JSONB with the right index strategy
Use GIN for containment/existence, and expression indexes for scalar path filters.

```sql
create index products_attrs_gin_idx on products using gin (attributes);
create index products_brand_expr_idx on products ((attributes ->> 'brand'));
```

## 3) Use trigram indexes for fuzzy/wildcard text search
`pg_trgm` can accelerate `ILIKE '%term%'` and similarity search.

```sql
create extension if not exists pg_trgm;
create index users_email_trgm_idx on users using gin (email gin_trgm_ops);
```

## 4) Use range types + exclusion constraints for overlap rules
For scheduling and booking, enforce non-overlap at the database level.

```sql
create table room_bookings (
  room_id bigint not null,
  during tstzrange not null,
  exclude using gist (room_id with =, during with &&)
);
```

## 5) Use generated columns or expression indexes for computed predicates
Persist or index deterministic expressions used often in filters.

```sql
create index users_lower_email_idx on users (lower(email));
```

## Verification References
- https://www.postgresql.org/docs/current/textsearch-intro.html
- https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING
- https://www.postgresql.org/docs/current/pgtrgm.html
- https://www.postgresql.org/docs/current/rangetypes.html
- https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION
- https://www.postgresql.org/docs/current/ddl-generated-columns.html
- https://www.postgresql.org/docs/current/indexes-expressional.html
