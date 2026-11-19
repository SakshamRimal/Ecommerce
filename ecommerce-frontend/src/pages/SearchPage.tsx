import { useQuery } from "@tanstack/react-query";
import { Filter, Search, Sparkles, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ProductCard, ProductGridSkeleton } from "../components/catalog/ProductCard";
import { Button, EmptyState, ErrorState } from "../components/ui/Primitives";
import { api } from "../lib/api/client";
import type { ProductListItem } from "../lib/api/types";
import { isValidMoneyInput } from "../lib/money";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const initialMode = searchParams.get("mode") === "semantic" ? "semantic" : "keyword";
  const initialCategory = searchParams.get("category_id") ?? "";
  const initialMinPrice = searchParams.get("min_price") ?? "";
  const initialMaxPrice = searchParams.get("max_price") ?? "";

  const [queryText, setQueryText] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);
  const [mode, setMode] = useState<"keyword" | "semantic">(initialMode);
  const [categoryId, setCategoryId] = useState(initialCategory);
  const [minPrice, setMinPrice] = useState(initialMinPrice);
  const [maxPrice, setMaxPrice] = useState(initialMaxPrice);

  const demoMode = useAuthStore((s) => s.demoMode);
  const openChatWithPrompt = useUiStore((s) => s.openChatWithPrompt);

  useEffect(() => {
    const urlQ = searchParams.get("q") ?? "";
    const urlMode = searchParams.get("mode") === "semantic" ? "semantic" : "keyword";
    setQueryText(urlQ);
    setDebouncedQuery(urlQ);
    setMode(urlMode);
  }, [searchParams]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(queryText.trim());
    }, 250);
    return () => clearTimeout(timer);
  }, [queryText]);

  const categoriesQuery = useQuery({
    queryKey: [...qk.categories(), demoMode],
    queryFn: () => api.categories.list(),
  });

  const validMin = minPrice && isValidMoneyInput(minPrice) ? minPrice : undefined;
  const validMax = maxPrice && isValidMoneyInput(maxPrice) ? maxPrice : undefined;

  const keywordSearchQuery = useQuery({
    queryKey: [
      ...qk.search({
        q: debouncedQuery,
        mode: "keyword",
        categoryId: categoryId || undefined,
        minPrice: validMin,
        maxPrice: validMax,
      }),
      demoMode,
    ],
    queryFn: ({ signal }) =>
      api.search.products(
        {
          q: debouncedQuery,
          category_id: categoryId || undefined,
          min_price: validMin,
          max_price: validMax,
          limit: 24,
          offset: 0,
        },
        signal
      ),
    enabled: mode === "keyword" && debouncedQuery.length > 0,
  });

  const semanticSearchQuery = useQuery({
    queryKey: [
      ...qk.search({
        q: debouncedQuery,
        mode: "semantic",
        categoryId: categoryId || undefined,
        minPrice: validMin,
        maxPrice: validMax,
      }),
      demoMode,
    ],
    queryFn: ({ signal }) =>
      api.search.semantic(
        {
          q: debouncedQuery,
          category_id: categoryId || undefined,
          min_price: validMin,
          max_price: validMax,
          limit: 12,
        },
        signal
      ),
    enabled: mode === "semantic" && debouncedQuery.length > 0,
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = queryText.trim();
    setDebouncedQuery(trimmed);
    const next = new URLSearchParams();
    if (trimmed) next.set("q", trimmed);
    if (mode === "semantic") next.set("mode", "semantic");
    if (categoryId) next.set("category_id", categoryId);
    if (validMin) next.set("min_price", validMin);
    if (validMax) next.set("max_price", validMax);
    setSearchParams(next);
  };

  const handleModeSwitch = (nextMode: "keyword" | "semantic") => {
    setMode(nextMode);
    const next = new URLSearchParams(searchParams);
    if (nextMode === "semantic") {
      next.set("mode", "semantic");
    } else {
      next.delete("mode");
    }
    setSearchParams(next);
  };

  const clearFilters = () => {
    setCategoryId("");
    setMinPrice("");
    setMaxPrice("");
  };

  const activeQuery = mode === "keyword" ? keywordSearchQuery : semanticSearchQuery;

  const results: ProductListItem[] = useMemo(() => {
    if (mode === "semantic") {
      return semanticSearchQuery.data ?? [];
    }
    const raw = keywordSearchQuery.data?.results ?? [];
    return raw.map((r) => ({
      id: r.id,
      name: r.name,
      description: r.description,
      price: r.price,
      stock_quantity: r.stock_quantity,
      category: r.category_name
        ? { id: r.category_name, name: r.category_name, slug: r.category_name.toLowerCase() }
        : undefined,
    }));
  }, [mode, keywordSearchQuery.data, semanticSearchQuery.data]);

  const totalMatches =
    mode === "keyword" ? (keywordSearchQuery.data?.total ?? 0) : results.length;

  const sampleSearches =
    mode === "semantic"
      ? [
          "quiet headphones for deep work and travel",
          "ergonomic setup to prevent wrist fatigue",
          "minimalist desk lighting for late nights",
          "waterproof bag for daily laptop commute",
        ]
      : ["headphones", "coffee", "chair", "backpack", "keyboard"];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Header & Search Box */}
      <div className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xs sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
              Hybrid Discovery Engine
            </span>
            <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-[var(--fg)] sm:text-3xl">
              Search Catalog
            </h1>
          </div>

          {/* Mode Switcher */}
          <div className="inline-flex rounded-xl border border-[var(--border)] bg-[var(--muted)] p-1">
            <button
              type="button"
              onClick={() => handleModeSwitch("keyword")}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                mode === "keyword"
                  ? "bg-[var(--card)] text-[var(--fg)] shadow-xs"
                  : "text-[var(--muted-fg)] hover:text-[var(--fg)]"
              }`}
            >
              <Search className="h-3.5 w-3.5" />
              Keyword + Filters
            </button>
            <button
              type="button"
              onClick={() => handleModeSwitch("semantic")}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                mode === "semantic"
                  ? "bg-[var(--primary)] text-[var(--primary-fg)] shadow-xs"
                  : "text-[var(--muted-fg)] hover:text-[var(--fg)]"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Semantic AI Search
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="relative flex items-center">
            <Search className="pointer-events-none absolute left-4 h-5 w-5 text-[var(--muted-fg)]" />
            <input
              type="search"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder={
                mode === "semantic"
                  ? "Describe what you need in natural language (e.g. 'gear for comfortable coding all day')..."
                  : "Search by product name, material, or keyword..."
              }
              className="h-13 w-full rounded-2xl border border-[var(--border)] bg-[var(--bg)] pl-12 pr-28 text-sm text-[var(--fg)] placeholder:text-[var(--muted-fg)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]/20"
            />
            {queryText && (
              <button
                type="button"
                onClick={() => {
                  setQueryText("");
                  setDebouncedQuery("");
                }}
                aria-label="Clear search query"
                className="absolute right-24 rounded-lg p-1.5 text-[var(--muted-fg)] hover:text-[var(--fg)]"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <Button type="submit" size="sm" className="absolute right-2">
              Search
            </Button>
          </div>

          {/* Price & Category Filters */}
          <div className="grid grid-cols-1 gap-3 pt-1 sm:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--muted-fg)]">
                Category
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 text-xs font-medium text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
              >
                <option value="">All Categories</option>
                {(categoriesQuery.data ?? []).map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--muted-fg)]">
                Min Price (USD)
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                placeholder="0.00"
                className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 text-xs text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--muted-fg)]">
                Max Price (USD)
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="1000.00"
                className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 text-xs text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
              />
            </div>

            <div className="flex items-end">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="h-10 w-full border border-[var(--border)]"
              >
                <Filter className="h-3.5 w-3.5" />
                Reset Filters
              </Button>
            </div>
          </div>
        </form>

        {/* Sample Prompts */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs text-[var(--muted-fg)]">Try:</span>
          {sampleSearches.map((sample) => (
            <button
              key={sample}
              type="button"
              onClick={() => {
                setQueryText(sample);
                setDebouncedQuery(sample);
              }}
              className="rounded-full border border-[var(--border)] bg-[var(--muted)]/60 px-3 py-1 text-xs font-medium text-[var(--fg)] transition hover:border-[var(--primary)] hover:text-[var(--primary)]"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>

      {/* Results Area */}
      <div className="mt-8">
        {!debouncedQuery ? (
          <EmptyState
            icon={mode === "semantic" ? <Sparkles className="h-6 w-6" /> : <Search className="h-6 w-6" />}
            title={
              mode === "semantic"
                ? "Semantic Vector Search Ready"
                : "Enter a keyword to search the catalog"
            }
            description={
              mode === "semantic"
                ? "Type a natural-language description above to match products using vector similarity."
                : "Search across product names and descriptions with instant category and price filtering."
            }
          />
        ) : activeQuery.isLoading ? (
          <ProductGridSkeleton count={8} />
        ) : activeQuery.isError ? (
          <ErrorState
            message="Search request failed. Please check your connection and try again."
            onRetry={() => activeQuery.refetch()}
          />
        ) : results.length === 0 ? (
          <EmptyState
            icon={<Search className="h-6 w-6" />}
            title={`No matches for "${debouncedQuery}"`}
            description="Try broadening your search terms, clearing price filters, or asking our AI Concierge for personalized recommendations."
            action={
              <Button
                variant="secondary"
                onClick={() =>
                  openChatWithPrompt(`Can you help me find products related to "${debouncedQuery}"?`)
                }
              >
                <Sparkles className="h-4 w-4 text-[var(--primary)]" />
                Ask AI Concierge Instead
              </Button>
            }
          />
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-sm text-[var(--muted-fg)]">
                Found <span className="font-bold text-[var(--fg)]">{totalMatches}</span> result
                {totalMatches === 1 ? "" : "s"} for{" "}
                <span className="font-semibold text-[var(--fg)]">&ldquo;{debouncedQuery}&rdquo;</span>
                {mode === "semantic" && (
                  <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-[var(--primary)]">
                    <Sparkles className="h-3 w-3" />
                    Ranked by Vector Similarity
                  </span>
                )}
              </p>
            </div>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {results.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
