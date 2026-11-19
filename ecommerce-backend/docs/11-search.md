# 11 — Search

## Two search backends

| Type | Storage | Entry point |
|---|---|---|
| Keyword/full-text | Elasticsearch | `GET /api/v1/search/products` |
| Semantic/vector | PostgreSQL + pgvector | `SearchService.semantic_search_products` (chat tool only) |

## Full-text search

### Endpoint

```
GET /api/v1/search/products?q=trail&limit=20
```

```json
{
  "query": "trail",
  "total": 3,
  "results": [
    {
      "id": "uuid",
      "name": "Trail Runner",
      "description": "Lightweight trail shoe",
      "category_name": "Footwear",
      "price": "89.90",
      "stock_quantity": 12,
      "score": 4.21
    }
  ]
}
```

### Query

```python
{
  "query": {
    "multi_match": {
      "query": query,
      "fields": ["name^3", "description"],
      "fuzziness": "AUTO"
    }
  },
  "size": limit
}
```

- `name` is weighted 3×.
- `AUTO` fuzziness gives typo tolerance.
- No filters, no sorting options, no `from`/offset, no highlighting.
- `total` is the ES hit total, but only `limit` hits are returned.
- If a product is missing from the index, it will not appear (even if it exists
  in PostgreSQL).

### Index

Defined in `src/app/core/search_index.py`:

| Field | Type | Notes |
|---|---|---|
| `id` | keyword | product UUID |
| `name` | text | standard analyzer; `name.raw` keyword subfield |
| `description` | text | standard analyzer |
| `category_id` | keyword | |
| `category_name` | keyword | |
| `price` | scaled_float | `scaling_factor: 100` |
| `stock_quantity` | integer | |
| `created_at` | date | ISO string |

Creation is idempotent via `ensure_product_index_exists()` at app startup. If ES
is down, the app logs `elasticsearch_unavailable` and continues.

### Indexing

| Event | Job |
|---|---|
| Product create | `index_product_task` |
| Product delete | `delete_product_from_index_task` |
| Product update | **none** (stale index) |
| Manual backfill | `python -m app.jobs.backfill_search_index` |

`index_product_task` reloads the product with its category, builds the document,
and calls `es_client.index(index=..., id=..., document=...)` (upsert).

### Failure behaviour

- ES unreachable during a search → exception → HTTP 500.
- ES unreachable during startup → warning only.
- ES unreachable in a job → exception propagates to arq (retry/log).
- Delete job catches exceptions and logs a warning.

## Semantic search

`src/app/ai/embeddings.py`:

```python
response = await client.embeddings.create(
    model="text-embedding-3-small",
    input=text,
)
return response.data[0].embedding  # 1536 dims
```

Product text = `name-category_name-description` (joined with `-`).

Query:

```python
products = await repo.semantic_search(embedding, limit=10)
```

```python
stmt = (
    select(Product)
    .options(joinedload(Product.category))
    .where(Product.embedding.is_not(None))
    .order_by(Product.embedding.cosine_distance(embedding))
    .limit(limit)
)
```

- Uses the `ix_products_embedding` ivfflat cosine index.
- Only products with a non-null embedding are considered.
- Embeddings are generated on product create and by
  `python -m app.jobs.backfill_embeddings`.
- Product updates do not regenerate embeddings.

### Why semantic search is not exposed

`SearchService.semantic_search_products` exists, but:

- No HTTP route calls it.
- The chat tool `semantic_search_products` does call it.
- `ToolExecutor` is built by the chat controller with
  `ToolExecutor(SearchService(), ProductRepository(session))`, so the chat path
  passes a `SearchService` with `product_repository=None`, then calls
  `semantic_search_products`, which would fail on `None.semantic_search`.
  This is a real bug in the AI path.

## Recommended improvements

1. Re-index and regenerate embeddings on product update.
2. Wire a `ProductRepository` into `SearchService` for the chat path.
3. Add `min_price` / `max_price` / `category_id` filters to the ES query.
4. Add `from`/`offset` and sorting.
5. Add a `GET /search/products/semantic` endpoint.
6. Return a degraded response (DB `ILIKE` fallback) when ES is down.
7. Add bulk indexing for backfills.
8. Add `ANALYZE products;` after embedding backfills.
