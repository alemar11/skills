# Advanced Features Best Practices

Use Postgres-native features to avoid slow pattern matching and unindexed JSON access.

## Use tsvector for full-text search
Avoid leading-wildcard LIKE queries; use full-text search with a GIN index.

```sql
alter table articles add column search_vector tsvector
  generated always as (
    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(content,''))
  ) stored;

create index articles_search_idx on articles using gin (search_vector);

select * from articles
where search_vector @@ to_tsquery('english', 'postgresql & performance');
```

## Index JSONB columns
Use GIN or expression indexes for JSONB containment and key lookups.

```sql
create index products_attrs_gin on products using gin (attributes);
create index products_brand_idx on products ((attributes->>'brand'));

select * from products where attributes @> '{"color": "red"}';
select * from products where attributes->>'brand' = 'Nike';
```

Choose the right operator class:
- `jsonb_ops` (default, supports all operators)
- `jsonb_path_ops` (smaller, faster for @> only)
