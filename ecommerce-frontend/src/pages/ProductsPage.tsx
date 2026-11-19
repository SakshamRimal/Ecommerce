import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Filter, PackageSearch, Sparkles } from "lucide-react";
import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ProductCard, ProductGridSkeleton } from "../components/catalog/ProductCard";
import { Button, EmptyState, ErrorState } from "../components/ui/Primitives";
import { api } from "../lib/api/client";
import { parseCents } from "../lib/money";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";

const PAGE_LIMIT = 12;

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedCategorySlug = searchParams.get("category") ?? "";
  const sortOrder = searchParams.get("sort") ?? "featured";
  const demoMode = useAuthStore((s) => s.demoMode);

  const categoriesQuery = useQuery({
    queryKey: [...qk.categories(), demoMode],
    queryFn: () => api.categories.list(),
  });

  const productsInfiniteQuery = useInfiniteQuery({
    queryKey: [...qk.products({ limit: PAGE_LIMIT, offset: 0 }), "infinite", demoMode],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api.products.list({
        limit: PAGE_LIMIT,
        offset: pageParam,
      }),
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < PAGE_LIMIT) return undefined;
      return allPages.reduce((sum, page) => sum + page.length, 0);
    },
  });

  const allItems = useMemo(
    () => productsInfiniteQuery.data?.pages.flatMap((page) => page) ?? [],
    [productsInfiniteQuery.data]
  );

  const filteredItems = useMemo(() => {
    let list = [...allItems];
    if (selectedCategorySlug) {
      list = list.filter((item) => item.category?.slug === selectedCategorySlug);
    }
    if (sortOrder === "price-asc") {
      list.sort((a, b) => parseCents(a.price) - parseCents(b.price));
    } else if (sortOrder === "price-desc") {
      list.sort((a, b) => parseCents(b.price) - parseCents(a.price));
    } else if (sortOrder === "stock") {
      list.sort((a, b) => b.stock_quantity - a.stock_quantity);
    }
    return list;
  }, [allItems, selectedCategorySlug, sortOrder]);

  const categories = categoriesQuery.data ?? [];

  const handleCategoryChange = (slug: string) => {
    const next = new URLSearchParams(searchParams);
    if (slug) {
      next.set("category", slug);
    } else {
      next.delete("category");
    }
    setSearchParams(next);
  };

  const handleSortChange = (nextSort: string) => {
    const next = new URLSearchParams(searchParams);
    if (nextSort && nextSort !== "featured") {
      next.set("sort", nextSort);
    } else {
      next.delete("sort");
    }
    setSearchParams(next);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-[var(--border)] pb-8 md:flex-row md:items-end">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
            Storefront Catalog
          </span>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-[var(--fg)] sm:text-4xl">
            All Products
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted-fg)]">
            Every item is backed by real-time inventory tracking and exact decimal pricing. Looking
            for something specific? Try our{" "}
            <Link to="/search?mode=semantic" className="font-semibold text-[var(--primary)] hover:underline">
              AI Semantic Search
            </Link>
            .
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="catalog-sort" className="text-xs font-medium text-[var(--muted-fg)]">
            Sort by
          </label>
          <select
            id="catalog-sort"
            value={sortOrder}
            onChange={(e) => handleSortChange(e.target.value)}
            className="h-10 rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 text-sm font-medium text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
          >
            <option value="featured">Featured</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="stock">Availability</option>
          </select>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--muted-fg)]">
            <Filter className="h-3.5 w-3.5" />
            Category:
          </span>
          <button
            type="button"
            onClick={() => handleCategoryChange("")}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              selectedCategorySlug === ""
                ? "bg-[var(--primary)] text-[var(--primary-fg)] shadow-xs"
                : "border border-[var(--border)] bg-[var(--card)] text-[var(--muted-fg)] hover:text-[var(--fg)]"
            }`}
          >
            All ({allItems.length})
          </button>
          {categories.map((cat) => {
            const active = selectedCategorySlug === cat.slug;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => handleCategoryChange(active ? "" : cat.slug)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
                  active
                    ? "bg-[var(--primary)] text-[var(--primary-fg)] shadow-xs"
                    : "border border-[var(--border)] bg-[var(--card)] text-[var(--muted-fg)] hover:text-[var(--fg)]"
                }`}
              >
                {cat.name}
              </button>
            );
          })}
        </div>

        <p className="tabular-nums text-xs text-[var(--muted-fg)]">
          Showing <span className="font-semibold text-[var(--fg)]">{filteredItems.length}</span>{" "}
          product{filteredItems.length === 1 ? "" : "s"}
        </p>
      </div>

      {/* Product Grid */}
      <div className="mt-8">
        {productsInfiniteQuery.isLoading ? (
          <ProductGridSkeleton count={8} />
        ) : productsInfiniteQuery.isError ? (
          <ErrorState
            message="Failed to load catalog products."
            onRetry={() => productsInfiniteQuery.refetch()}
          />
        ) : filteredItems.length === 0 ? (
          <EmptyState
            icon={<PackageSearch className="h-6 w-6" />}
            title="No matching products found"
            description={
              selectedCategorySlug
                ? `No products are currently listed under "${selectedCategorySlug}". Try clearing the category filter or loading more products.`
                : "The product catalog is currently empty."
            }
            action={
              selectedCategorySlug ? (
                <Button variant="secondary" onClick={() => handleCategoryChange("")}>
                  Clear Category Filter
                </Button>
              ) : undefined
            }
          />
        ) : (
          <>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filteredItems.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            {/* Load More Pagination */}
            {productsInfiniteQuery.hasNextPage && (
              <div className="mt-12 flex flex-col items-center justify-center gap-3">
                <Button
                  variant="secondary"
                  size="lg"
                  loading={productsInfiniteQuery.isFetchingNextPage}
                  onClick={() => productsInfiniteQuery.fetchNextPage()}
                >
                  Load More Products
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Bottom Search Callout */}
      <div className="mt-16 flex flex-col items-center justify-between gap-4 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 sm:flex-row">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 text-[var(--primary)]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--fg)]">
              Need help narrowing down your options?
            </h3>
            <p className="text-xs text-[var(--muted-fg)]">
              Filter by price range or search with natural language on our dedicated search page.
            </p>
          </div>
        </div>
        <Link to="/search">
          <Button variant="secondary" size="sm">
            Open Advanced &amp; Semantic Search
          </Button>
        </Link>
      </div>
    </div>
  );
}
