import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ShoppingBag, Sparkles } from "lucide-react";
import { api } from "../../lib/api/client";
import type { ProductListItem } from "../../lib/api/types";
import { qk } from "../../lib/query-keys";
import { useAuthStore } from "../../stores/auth-store";
import { useUiStore } from "../../stores/ui-store";
import { Button, Price, Skeleton, StockBadge } from "../ui/Primitives";

const FALLBACK_VISUALS = [
  "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=800&q=80",
];

export function getProductImageUrl(
  idOrProduct: string | { id: string; image_url?: string | null },
  imageUrl?: string | null
): string {
  const id = typeof idOrProduct === "string" ? idOrProduct : idOrProduct.id;
  const resolvedUrl =
    typeof idOrProduct === "string" ? imageUrl : idOrProduct.image_url;
  if (resolvedUrl && resolvedUrl.trim()) return resolvedUrl;
  const charSum = id
    .split("")
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return FALLBACK_VISUALS[charSum % FALLBACK_VISUALS.length];
}

export function ProductCard({
  product,
  categoryLabel,
}: {
  product: ProductListItem;
  categoryLabel?: string;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { status } = useAuthStore();
  const { addToast, setCartDrawerOpen } = useUiStore();

  const addMutation = useMutation({
    mutationFn: () =>
      api.cart.addItem({ product_id: product.id, quantity: 1 }),
    onSuccess: (cart) => {
      queryClient.setQueryData(qk.cart(), cart);
      queryClient.invalidateQueries({ queryKey: qk.cart() });
      addToast({
        tone: "success",
        title: "Added to cart",
        description: `${product.name} is ready in your bag.`,
      });
      setCartDrawerOpen(true);
    },
    onError: (err: Error) => {
      queryClient.invalidateQueries({ queryKey: qk.products({}) });
      addToast({
        tone: "error",
        title: "Could not add item",
        description: err.message,
      });
    },
  });

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (status !== "authenticated") {
      addToast({
        tone: "info",
        title: "Sign in to shop",
        description: "Please sign in or enable Demo Mode to add items to your cart.",
      });
      navigate(`/login?next=/products/${product.id}`);
      return;
    }
    addMutation.mutate();
  };

  const outOfStock = product.stock_quantity <= 0;
  const resolvedCategory = categoryLabel ?? product.category?.name;

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:border-indigo-200 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-900">
      <Link
        to={`/products/${product.id}`}
        className="relative aspect-[4/3] w-full overflow-hidden bg-slate-100 dark:bg-slate-800"
      >
        <img
          src={getProductImageUrl(product.id, product.image_url)}
          alt={product.name}
          loading="lazy"
          className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute left-3 top-3 flex flex-wrap items-center gap-1.5">
          {resolvedCategory && (
            <span className="rounded-full bg-slate-900/75 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur-md">
              {resolvedCategory}
            </span>
          )}
        </div>
        <div className="absolute right-3 top-3">
          <StockBadge stock={product.stock_quantity} />
        </div>
      </Link>

      <div className="flex flex-1 flex-col justify-between p-5">
        <div>
          <Link
            to={`/products/${product.id}`}
            className="line-clamp-1 text-base font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400"
          >
            {product.name}
          </Link>
          {product.description && (
            <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              {product.description}
            </p>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
          <div>
            <span className="block text-[11px] uppercase tracking-wider text-slate-400">
              Price
            </span>
            <Price
              amount={product.price}
              className="text-lg text-slate-900 dark:text-white"
            />
          </div>

          <Button
            size="sm"
            variant={outOfStock ? "outline" : "primary"}
            disabled={outOfStock}
            loading={addMutation.isPending}
            onClick={handleAddToCart}
            aria-label={
              outOfStock ? `${product.name} out of stock` : `Add ${product.name} to cart`
            }
          >
            <ShoppingBag className="h-3.5 w-3.5" />
            {outOfStock ? "Sold Out" : "Add to Bag"}
          </Button>
        </div>
      </div>
    </article>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
        >
          <Skeleton className="aspect-[4/3] w-full rounded-xl" />
          <Skeleton className="mt-4 h-5 w-3/4" />
          <Skeleton className="mt-2 h-3.5 w-full" />
          <div className="mt-5 flex items-center justify-between">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-9 w-28" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function AiConciergeBanner({ onOpenChat }: { onOpenChat?: () => void }) {
  const setChatDrawerOpen = useUiStore((s) => s.setChatDrawerOpen);
  const handleOpen = onOpenChat ?? (() => setChatDrawerOpen(true));
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-violet-900 p-8 text-white shadow-xl">
      <div className="relative z-10 flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
        <div className="max-w-xl">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-indigo-100 backdrop-blur-sm">
            <Sparkles className="h-3.5 w-3.5" />
            AI Shopping Concierge + Semantic Vector Search
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            Not sure what gear fits your workflow?
          </h2>
          <p className="mt-2 text-sm text-indigo-100/90 leading-relaxed">
            Our AI assistant queries live Elasticsearch &amp; pgvector embeddings to
            recommend real products, compare specs, and verify live warehouse stock.
          </p>
        </div>
        <Button
          size="lg"
          variant="secondary"
          onClick={handleOpen}
          className="shrink-0 !bg-slate-950 !text-white hover:!bg-slate-900 dark:!bg-black dark:!text-white border border-slate-700/60 shadow-lg"
        >
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <span className="font-semibold text-white">Ask AI Assistant</span>
        </Button>
      </div>
    </div>
  );
}
