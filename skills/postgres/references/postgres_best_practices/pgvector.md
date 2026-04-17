# pgvector Runtime Guidance

Use this reference when the task involves embeddings, semantic search,
similarity search, vector indexes, or retrieval/RAG patterns in Postgres.

## 1) Enable the extension and lock the dimension
Create the extension in the target database and choose one fixed embedding
dimension per column.

```sql
create extension if not exists vector;

create table documents (
  id bigint generated always as identity primary key,
  content text not null,
  embedding vector(1536) not null
);
```

Use `vector(N)` or `halfvec(N)` deliberately. Prefer `halfvec` when smaller
storage and indexes are worth the precision tradeoff and your deployment
supports it.

## 2) Keep storage and query types consistent
- Use the same embedding model family for stored rows and query vectors.
- Keep the same dimension everywhere.
- Do not mix `vector`, `halfvec`, and query operators casually; pick one shape
  for the table and query it explicitly.

## 3) Default to HNSW for approximate nearest-neighbor search
Use HNSW as the default ANN index unless the workload has a proven reason to
prefer something else. It usually has a better speed-recall tradeoff than
IVFFlat, but it builds more slowly and uses more memory.

```sql
create index documents_embedding_hnsw_idx
on documents using hnsw (embedding vector_cosine_ops);
```

IVFFlat can still be the better fit when build time or memory pressure matters
more than peak query performance.

## 4) Default to cosine distance unless the workload needs something else
For typical text-embedding workloads, cosine is a practical default.
The query operator and index operator class must match.

- Cosine: `<=>` with `vector_cosine_ops` or `halfvec_cosine_ops`
- L2 distance: `<->` with `vector_l2_ops` or `halfvec_l2_ops`

If vectors are normalized to length 1, consider inner product for better
performance.

## 5) Cast query vectors explicitly
Prepared statements and reusable application queries should cast the input
vector explicitly to the table's exact type and dimension.

```sql
select id, content
from documents
order by embedding <=> $1::vector(1536)
limit 10;
```

For approximate-index usage, keep the query in the form `ORDER BY
distance_operator ... LIMIT ...`. Wrapping the distance expression can prevent
index usage.

## 6) Bulk load first, then index when practical
For initial backfills or large imports, insert the rows first and create the
vector index afterward when the workflow allows it.

## 7) Pair vector search with ordinary indexes for selective filters
If the query filters heavily by tenant, category, or visibility, keep ordinary
indexes on those filter columns too.

```sql
create index documents_tenant_id_idx on documents (tenant_id);
```

Use the vector index for nearest-neighbor ranking and the ordinary index to
avoid scanning irrelevant slices of the table.

With approximate indexes, filtering is applied after the index scan. If a very
selective filter returns too few rows, increase `hnsw.ef_search` and use
iterative scans when the installed version supports them. Partial indexes or
partitioning can also help for repeated filtered workloads.

## 8) Keep the first version simple
Start with one embedding column, one distance metric, and one HNSW index.
Only add more complex indexing or multiple embedding spaces after the first
query pattern is working and measured.

## Official References
- Main README: https://github.com/pgvector/pgvector
- HNSW: https://github.com/pgvector/pgvector#hnsw
- Filtering: https://github.com/pgvector/pgvector#filtering
- Iterative index scans: https://github.com/pgvector/pgvector#iterative-index-scans
- Half-precision vectors: https://github.com/pgvector/pgvector#half-precision-vectors
