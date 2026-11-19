---
name: Search
description: Use when changing Elasticsearch full-text product search, the product index mapping, semantic search, or search backfills.
---

# Search

## When to use

- `GET /api/v1/search/products`.
- Elasticsearch index mapping or indexing jobs.
- Semantic/vector search.
- Search relevance, filters, or pagination.

## Files

| Concern | File |
|---|---|
| Route | `src/app/api/v1/search/controller.py` |
| Logic | `src/app/api/v1/search/service.py` |
| Schemas | `src/app/api/v1/search/schema.py` |
| ES client | `src/app/core/elasticsearch.py` |
| Index mapping | `src/app/core/search_index.py` |
| Indexing jobs | `src/app/jobs/tasks.py` |
| Backfill | `src/app/jobs/backfill_search_index.py` |

## Endpoint

`GET /search/products?q=<term>&limit=<1..50>` (public) →
`{query, total, results: [{id, name, description, category_name, price, stock_quantity, score}]}`.

Query is an Elasticsearch `multi_match` over `name^3` and `description` with
`fuzziness: AUTO`.

## Index

Index name: `ELASTICSEARCH_PRODUCTS_INDEX` (default `products`).
Fields: `id` keyword, `name` text (+ `name.raw` keyword), `description` text,
`category_id` keyword, `category_name` keyword, `price` scaled_float×100,
`stock_quantity` integer, `created_at` date.

`ensure_product_index_exists()` runs in the app lifespan and creates the index
if missing. It logs a warning if Elasticsearch is unreachable.

## Indexing pipeline

- Product create → `index_product_task` + `generate_product_embedding_task`.
- Product delete → `delete_product_from_index_task`.
- Product update currently does **not** re-index or regenerate the embedding.
- Backfills: `python -m app.jobs.backfill_search_index` and
  `python -m app.jobs.backfill_embeddings`.

## Semantic search

`SearchService.semantic_search_products(query)` embeds the query with
`text-embedding-3-small` and orders products by pgvector cosine distance
(`Product.embedding`, `VECTOR(1536)`, ivfflat index). It is only reachable
through the chat tool `semantic_search_products`; there is no HTTP endpoint.

## Rules

1. Keep the ES document shape in sync with `PRODUCT_INDEX_MAPPING`.
2. Index writes only through arq jobs, never inline in request handlers.
3. Always pass `limit` bounds.
4. Treat Elasticsearch as eventually consistent; the DB is the source of truth.
5. If you add a filter to the API, implement it in the ES query, not in Python
   over the page of results.

## Gotchas

- Product **updates** do not re-index; search shows stale names/prices/stock.
- Search API has no price/category filters even though the chat tool schema
  advertises `min_price`/`max_price` (and executor only applies `min_price`).
- `SearchService.__init__` accepts a repository, but the controller creates it
  with none; semantic search would fail if exposed without wiring the repo.
- Elasticsearch being down makes search return a 500, not a degraded response.
- `ensure_product_index_exists` catches errors and continues, so the app can
  boot without search.

## Verify

```bash
uv run pytest tests/integration/test_routes.py -q
uv run python -m app.jobs.backfill_search_index   # needs services running
```

## Related

- `docs/11-search.md`
- `docs/13-background-jobs.md`
