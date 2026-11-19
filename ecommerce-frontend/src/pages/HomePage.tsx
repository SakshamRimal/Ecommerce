import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  Compass,
  Layers,
  ShieldCheck,
  Sparkles,
  Truck,
  Zap,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import {
  AiConciergeBanner,
  ProductCard,
  ProductGridSkeleton,
} from "../components/catalog/ProductCard";
import { Button, EmptyState, ErrorState, Skeleton } from "../components/ui/Primitives";
import { api } from "../lib/api/client";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

export function HomePage() {
  const navigate = useNavigate();
  const demoMode = useAuthStore((s) => s.demoMode);
  const openChatWithPrompt = useUiStore((s) => s.openChatWithPrompt);

  const categoriesQuery = useQuery({
    queryKey: [...qk.categories(), demoMode],
    queryFn: () => api.categories.list(),
  });

  const featuredProductsQuery = useQuery({
    queryKey: [...qk.products({ limit: 8, offset: 0 }), demoMode],
    queryFn: () => api.products.list({ limit: 8, offset: 0 }),
  });

  const categories = categoriesQuery.data ?? [];
  const featuredProducts = featuredProductsQuery.data ?? [];

  return (
    <div className="space-y-16 pb-20">
      {/* Hero Banner */}
      <section className="relative overflow-hidden border-b border-[var(--border)] bg-gradient-to-b from-indigo-50/70 via-[var(--bg)] to-[var(--bg)] dark:from-indigo-950/30 dark:via-[var(--bg)] dark:to-[var(--bg)]">
        <div className="pointer-events-none absolute -top-24 left-1/2 h-96 w-[48rem] -translate-x-1/2 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3.5 py-1.5 text-xs font-semibold text-[var(--primary)]">
                <Sparkles className="h-3.5 w-3.5" />
                Next-Gen AI Commerce Experience
              </div>
              <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-[var(--fg)] sm:text-5xl lg:text-6xl">
                Curated essentials for{" "}
                <span className="bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 bg-clip-text text-transparent dark:from-indigo-400 dark:via-violet-400 dark:to-purple-400">
                  modern craft &amp; living
                </span>
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-relaxed text-[var(--muted-fg)] sm:text-lg">
                Discover precision audio, tactile mechanical hardware, architectural desk lighting,
                and everyday carry designed to endure. Powered by hybrid semantic search and a
                real-time AI shopping concierge.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3.5">
                <Button
                  size="lg"
                  onClick={() => navigate("/products")}
                  className="shadow-md shadow-indigo-500/15"
                >
                  Explore Collection
                  <ArrowRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="secondary"
                  size="lg"
                  onClick={() =>
                    openChatWithPrompt(
                      "Help me build a clean, productive home office setup under $750."
                    )
                  }
                >
                  <Sparkles className="h-4 w-4 text-[var(--primary)]" />
                  Ask AI Concierge
                </Button>
                <Link
                  to="/search?mode=semantic"
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-[var(--muted-fg)] transition hover:text-[var(--fg)]"
                >
                  Try Semantic Search →
                </Link>
              </div>

              {/* Trust Badges */}
              <div className="mt-10 grid grid-cols-3 gap-4 border-t border-[var(--border)] pt-6 sm:max-w-lg">
                <div>
                  <p className="tabular-nums text-xl font-bold text-[var(--fg)]">100%</p>
                  <p className="text-xs text-[var(--muted-fg)]">Verified Inventory</p>
                </div>
                <div>
                  <p className="tabular-nums text-xl font-bold text-[var(--fg)]">AI + Vector</p>
                  <p className="text-xs text-[var(--muted-fg)]">Semantic Product Discovery</p>
                </div>
                <div>
                  <p className="tabular-nums text-xl font-bold text-[var(--fg)]">Instant</p>
                  <p className="text-xs text-[var(--muted-fg)]">Idempotent Safe Checkout</p>
                </div>
              </div>
            </div>

            {/* Right Interactive Showcase Card */}
            <div className="lg:col-span-5">
              <div className="relative rounded-3xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-xl">
                <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-[var(--muted)]">
                  <img
                    src="https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=1000&q=80"
                    alt="Workspace setup"
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-slate-950/20 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between text-white">
                    <div>
                      <span className="inline-block rounded-full bg-white/20 px-2.5 py-0.5 text-[11px] font-semibold backdrop-blur-md">
                        Editor&apos;s Pick
                      </span>
                      <p className="mt-1 text-lg font-bold">Tactile Studio Series</p>
                      <p className="text-xs text-slate-200">
                        Precision CNC Aluminum &amp; Studio Acoustics
                      </p>
                    </div>
                    <Link
                      to="/products"
                      className="rounded-xl bg-white px-3.5 py-2 text-xs font-semibold text-slate-900 shadow transition hover:bg-indigo-50"
                    >
                      Shop Now
                    </Link>
                  </div>
                </div>

                {/* Quick AI Prompt Pills inside Hero */}
                <div className="mt-4 space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[var(--fg)]">
                      Try asking our AI Concierge:
                    </span>
                    <span className="text-[var(--muted-fg)]">Live Tool-Calling</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      "Headphones for deep focus",
                      "Gifts for a remote engineer under $200",
                      "Compare mechanical keyboard & ergonomic mouse",
                    ].map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => openChatWithPrompt(prompt)}
                        className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/60 px-3 py-1.5 text-left text-xs font-medium text-[var(--fg)] transition hover:border-[var(--primary)] hover:bg-indigo-500/10 hover:text-[var(--primary)]"
                      >
                        &ldquo;{prompt}&rdquo;
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Value Props Strip */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              icon: Zap,
              title: "Semantic AI Discovery",
              desc: "Search by vibe, use-case, or problem using pgvector embeddings.",
            },
            {
              icon: ShieldCheck,
              title: "Idempotent Checkout",
              desc: "Zero double-charges and atomic row-locked stock reservation.",
            },
            {
              icon: Truck,
              title: "Fast Express Dispatch",
              desc: "Real-time stock tracking with instant restock on order cancellation.",
            },
            {
              icon: CheckCircle2,
              title: "Precision Pricing",
              desc: "Exact decimal currency arithmetic from database to checkout receipt.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="flex items-start gap-3.5 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-xs"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 text-[var(--primary)]">
                <item.icon className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-[var(--fg)]">{item.title}</h2>
                <p className="mt-1 text-xs leading-relaxed text-[var(--muted-fg)]">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Browse by Category */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
              Departments
            </span>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-[var(--fg)]">
              Shop by Category
            </h2>
          </div>
          <Link
            to="/products"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--primary)] hover:underline"
          >
            View full catalog
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="mt-6">
          {categoriesQuery.isLoading ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-28 rounded-2xl" />
              ))}
            </div>
          ) : categoriesQuery.isError ? (
            <ErrorState
              message="Could not load categories from the server."
              onRetry={() => categoriesQuery.refetch()}
            />
          ) : categories.length === 0 ? (
            <EmptyState
              icon={<Layers className="h-6 w-6" />}
              title="No categories available yet"
              description="Categories created by administrators will appear here."
            />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  to={`/products?category=${encodeURIComponent(cat.slug)}`}
                  className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 transition duration-200 hover:-translate-y-0.5 hover:border-[var(--primary)] hover:shadow-md"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--muted)] text-[var(--fg)] transition group-hover:bg-[var(--primary)] group-hover:text-white">
                    <Compass className="h-5 w-5" />
                  </div>
                  <div className="mt-5">
                    <h3 className="font-semibold text-[var(--fg)] group-hover:text-[var(--primary)]">
                      {cat.name}
                    </h3>
                    <p className="mt-0.5 text-xs text-[var(--muted-fg)]">#{cat.slug}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Featured Products */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
              Featured Drop
            </span>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-[var(--fg)]">
              Trending Essentials
            </h2>
          </div>
          <Link
            to="/products"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--primary)] hover:underline"
          >
            Browse all products
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="mt-6">
          {featuredProductsQuery.isLoading ? (
            <ProductGridSkeleton count={8} />
          ) : featuredProductsQuery.isError ? (
            <ErrorState
              message="Unable to load featured products right now."
              onRetry={() => featuredProductsQuery.refetch()}
            />
          ) : featuredProducts.length === 0 ? (
            <EmptyState
              title="No products in catalog"
              description="Seed the backend database or switch to Demo Mode in the top bar to explore products."
            />
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {featuredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* AI Concierge Banner */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <AiConciergeBanner />
      </section>
    </div>
  );
}
