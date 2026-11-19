---
name: Search UI
description: Use when building the search bar, search results page, query state, or search empty/loading/error states.
---

# Search UI

## When to use

- Header search input.
- `/search?q=…` results page.
- Debouncing, suggestions, no-results handling.

## Endpoint

`GET /search/products?q=<term>&limit=<1..50>`

```ts
{
  query: string;
  total: number;
  results: {
    id: string;
    name: string;
    description: string | null;
    category_name: string;
    price: string;
    stock_quantity: number;
    score: number;
  }[];
}
```

- Elasticsearch `multi_match` over name (3× weight) + description, fuzzy.
- No pagination beyond `limit`; no offset.
- No price/category filters or sorting.
- `total` may exceed the returned `results.length`.

## UX rules

1. Debounce input ~300 ms; only search after 2+ characters.
2. Keep the query in the URL (`?q=`), so results are shareable/back-button safe.
3. Use `AbortController` to cancel stale requests.
4. Show the result count and the query in the heading.
5. Empty query → show suggestions or a recent-searches list (client-side only).
6. No results → "No matches for '<q>'" + link to catalog.
7. ES failure (500) → friendly error with retry; do not crash the page.
8. Results are eventually consistent; note that very new/edited products may lag.

## Missing capabilities

| Feature | Status |
|---|---|
| Filters (price/category) | ❌ |
| Sort | ❌ |
| Pagination | ❌ (`limit` only) |
| Autocomplete | ❌ (build client-side from results) |
| Semantic search | ❌ no HTTP endpoint |
| Product images | ❌ not in the model |

Do not fake these against the API. Plan them as backend work in
`../../../docs/11-build-plan.md`.

## Accessibility

- `<input type="search">` with a label/`aria-label`.
- Announce result count changes with `aria-live="polite"`.
- Keyboard: `/` focuses search; `Esc` clears.
- Result links have descriptive names.

## Related

- `../../../docs/05-pages-and-routes.md`
- `../../../../ecommerce-backend/docs/11-search.md`
