import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ChevronRight,
  RotateCcw,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Truck,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getProductImageUrl, ProductCard } from "../components/catalog/ProductCard";
import {
  Button,
  ErrorState,
  Price,
  QuantityStepper,
  Skeleton,
  StockBadge,
} from "../components/ui/Primitives";
import { api, ApiError } from "../lib/api/client";
import { multiplyMoney } from "../lib/money";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [quantity, setQuantity] = useState(1);

  const authStatus = useAuthStore((s) => s.status);
  const demoMode = useAuthStore((s) => s.demoMode);
  const addToast = useUiStore((s) => s.addToast);
  const setCartDrawerOpen = useUiStore((s) => s.setCartDrawerOpen);
  const openChatWithPrompt = useUiStore((s) => s.openChatWithPrompt);

  const productQuery = useQuery({
    queryKey: [...qk.product(productId ?? ""), demoMode],
    queryFn: () => api.products.get(productId!),
    enabled: Boolean(productId),
  });

  const relatedQuery = useQuery({
    queryKey: [...qk.products({ limit: 8, offset: 0 }), demoMode],
    queryFn: () => api.products.list({ limit: 8, offset: 0 }),
  });

  const addMutation = useMutation({
    mutationFn: (qty: number) =>
      api.cart.addItem({ product_id: productId!, quantity: qty }),
    onSuccess: (updatedCart) => {
      queryClient.setQueryData(qk.cart(), updatedCart);
      addToast({
        title: "Added to shopping bag",
        description: `${quantity} × ${productQuery.data?.name ?? "Item"} added.`,
        tone: "success",
      });
      setCartDrawerOpen(true);
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        addToast({
          title: "Stock limit reached",
          description: err.detail,
          tone: "error",
        });
        queryClient.invalidateQueries({ queryKey: qk.product(productId!) });
        return;
      }
      addToast({
        title: "Could not add item",
        description: err instanceof ApiError ? err.detail : "Please try again.",
        tone: "error",
      });
    },
  });

  if (productQuery.isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <Skeleton className="h-5 w-48" />
        <div className="mt-8 grid gap-10 lg:grid-cols-12">
          <Skeleton className="aspect-square w-full rounded-3xl lg:col-span-6" />
          <div className="space-y-4 lg:col-span-6">
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (productQuery.isError || !productQuery.data) {
    const is404 =
      productQuery.error instanceof ApiError && productQuery.error.status === 404;
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <ErrorState
          title={is404 ? "Product Not Found" : "Unable to load product"}
          message={
            is404
              ? "This product may have been removed or is no longer available in the catalog."
              : "An unexpected error occurred while fetching product details."
          }
          onRetry={() => (is404 ? navigate("/products") : productQuery.refetch())}
        />
      </div>
    );
  }

  const product = productQuery.data;
  const outOfStock = product.stock_quantity <= 0;
  const clampedQuantity = Math.min(
    Math.max(1, quantity),
    Math.max(1, product.stock_quantity)
  );
  const relatedProducts =
    relatedQuery.data?.filter((item) => item.id !== product.id).slice(0, 4) ?? [];

  const handleAddToBag = () => {
    if (authStatus !== "authenticated" && !demoMode) {
      addToast({
        title: "Sign in to shop",
        description: "Please sign in or enable Demo Mode to add items to your bag.",
        tone: "info",
      });
      navigate(`/login?next=${encodeURIComponent(`/products/${product.id}`)}`);
      return;
    }
    addMutation.mutate(clampedQuantity);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-xs text-[var(--muted-fg)]">
        <Link to="/" className="hover:text-[var(--fg)]">
          Home
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <Link to="/products" className="hover:text-[var(--fg)]">
          Catalog
        </Link>
        {product.category && (
          <>
            <ChevronRight className="h-3.5 w-3.5" />
            <Link
              to={`/products?category=${encodeURIComponent(product.category.slug)}`}
              className="hover:text-[var(--fg)]"
            >
              {product.category.name}
            </Link>
          </>
        )}
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="font-medium text-[var(--fg)]">{product.name}</span>
      </nav>

      {/* Main Product Section */}
      <div className="mt-8 grid gap-10 lg:grid-cols-12">
        {/* Product Image */}
        <div className="lg:col-span-6">
          <div className="relative aspect-square overflow-hidden rounded-3xl border border-[var(--border)] bg-[var(--muted)] shadow-sm">
            <img
              src={getProductImageUrl(product)}
              alt={product.name}
              className="h-full w-full object-cover"
            />
            {product.category && (
              <span className="absolute left-4 top-4 rounded-full bg-[var(--card)]/90 px-3.5 py-1 text-xs font-semibold text-[var(--fg)] shadow-xs backdrop-blur-md">
                {product.category.name}
              </span>
            )}
          </div>
        </div>

        {/* Product Info & Purchase Controls */}
        <div className="flex flex-col justify-between lg:col-span-6">
          <div>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <StockBadge stock={product.stock_quantity} />
              <span className="font-mono text-xs text-[var(--muted-fg)]">
                SKU: {product.id.slice(0, 8).toUpperCase()}
              </span>
            </div>

            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--fg)] sm:text-4xl">
              {product.name}
            </h1>

            <div className="mt-4 flex items-baseline gap-3">
              <Price amount={product.price} className="text-3xl font-extrabold text-[var(--fg)]" />
              <span className="text-xs text-[var(--muted-fg)]">
                Tax calculated at checkout · Free express shipping
              </span>
            </div>

            <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-fg)]">
                Overview &amp; Specifications
              </h2>
              <p className="mt-2.5 whitespace-pre-line text-sm leading-relaxed text-[var(--fg)]">
                {product.description ||
                  "Precision engineered with durable materials and designed for daily performance."}
              </p>
            </div>

            {/* Quantity & Add to Cart */}
            <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--muted-fg)]">
                    Quantity
                  </label>
                  <p className="mt-0.5 text-xs text-[var(--muted-fg)]">
                    {outOfStock
                      ? "Currently unavailable"
                      : `Up to ${product.stock_quantity} available for immediate dispatch`}
                  </p>
                </div>
                <QuantityStepper
                  value={clampedQuantity}
                  min={1}
                  max={Math.max(1, product.stock_quantity)}
                  disabled={outOfStock || addMutation.isPending}
                  onChange={setQuantity}
                />
              </div>

              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <Button
                  size="lg"
                  className="flex-1"
                  disabled={outOfStock}
                  loading={addMutation.isPending}
                  onClick={handleAddToBag}
                >
                  <ShoppingBag className="h-4 w-4" />
                  {outOfStock ? (
                    "Out of Stock"
                  ) : (
                    <>
                      Add to Bag · <Price amount={multiplyMoney(product.price, clampedQuantity)} />
                    </>
                  )}
                </Button>

                <Button
                  variant="secondary"
                  size="lg"
                  onClick={() =>
                    openChatWithPrompt(
                      `Tell me more about the "${product.name}" (NRs ${product.price}) and whether it's in stock or has complementary items.`
                    )
                  }
                >
                  <Sparkles className="h-4 w-4 text-[var(--primary)]" />
                  Ask AI Concierge
                </Button>
              </div>
            </div>
          </div>

          {/* Perks */}
          <div className="mt-6 grid grid-cols-1 gap-3 border-t border-[var(--border)] pt-6 sm:grid-cols-3">
            <div className="flex items-center gap-2.5 text-xs text-[var(--muted-fg)]">
              <Truck className="h-4 w-4 shrink-0 text-[var(--primary)]" />
              <span>Ships within 24 hours</span>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-[var(--muted-fg)]">
              <RotateCcw className="h-4 w-4 shrink-0 text-[var(--primary)]" />
              <span>Instant order cancellation</span>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-[var(--muted-fg)]">
              <ShieldCheck className="h-4 w-4 shrink-0 text-[var(--primary)]" />
              <span>2-Year hardware warranty</span>
            </div>
          </div>
        </div>
      </div>

      {/* Related Products */}
      {relatedProducts.length > 0 && (
        <section className="mt-20 border-t border-[var(--border)] pt-12">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-[var(--fg)]">You Might Also Like</h2>
            <Link
              to="/products"
              className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--primary)] hover:underline"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to catalog
            </Link>
          </div>
          <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {relatedProducts.map((item) => (
              <ProductCard key={item.id} product={item} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
