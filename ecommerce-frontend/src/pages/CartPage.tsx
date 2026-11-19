import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ShieldCheck, ShoppingBag, Trash2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { getProductImageUrl } from "../components/catalog/ProductCard";
import {
  Button,
  EmptyState,
  Price,
  QuantityStepper,
  Skeleton,
} from "../components/ui/Primitives";
import { api, ApiError } from "../lib/api/client";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

export function CartPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const authStatus = useAuthStore((s) => s.status);
  const demoMode = useAuthStore((s) => s.demoMode);
  const addToast = useUiStore((s) => s.addToast);

  const canFetch = authStatus === "authenticated" || demoMode;

  const cartQuery = useQuery({
    queryKey: [...qk.cart(), demoMode],
    queryFn: () => api.cart.get(),
    enabled: canFetch,
  });

  const updateMutation = useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      api.cart.updateItem(productId, { quantity }),
    onSuccess: (updated) => {
      queryClient.setQueryData(qk.cart(), updated);
      queryClient.invalidateQueries({ queryKey: qk.cart() });
    },
    onError: (err) => {
      addToast({
        title: "Could not update quantity",
        description: err instanceof ApiError ? err.detail : "Please try again.",
        tone: "error",
      });
      queryClient.invalidateQueries({ queryKey: qk.cart() });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (productId: string) => api.cart.removeItem(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.cart() });
      addToast({ title: "Item removed from bag", tone: "info" });
    },
  });

  const clearMutation = useMutation({
    mutationFn: () => api.cart.clear(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.cart() });
      addToast({ title: "Shopping bag cleared", tone: "info" });
    },
  });

  if (!canFetch) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <EmptyState
          icon={<ShoppingBag className="h-6 w-6" />}
          title="Sign in to view your shopping bag"
          description="Your cart is synced across sessions when signed in, or you can toggle Demo Mode in the top bar."
          action={
            <Button onClick={() => navigate("/login?next=/cart")}>Sign In to Continue</Button>
          }
        />
      </div>
    );
  }

  const cart = cartQuery.data;
  const items = cart?.items ?? [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
            Your Selection
          </span>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-[var(--fg)]">
            Shopping Bag
          </h1>
        </div>
        {items.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            loading={clearMutation.isPending}
            onClick={() => clearMutation.mutate()}
            className="text-[var(--muted-fg)] hover:text-rose-500"
          >
            <Trash2 className="h-4 w-4" />
            Clear All Items
          </Button>
        )}
      </div>

      {cartQuery.isLoading ? (
        <div className="mt-8 grid gap-8 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-8">
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
          </div>
          <Skeleton className="h-72 w-full rounded-2xl lg:col-span-4" />
        </div>
      ) : items.length === 0 ? (
        <div className="mt-12">
          <EmptyState
            icon={<ShoppingBag className="h-6 w-6" />}
            title="Your shopping bag is empty"
            description="Explore our curated collection of audio, workspace essentials, and everyday carry."
            action={
              <Button onClick={() => navigate("/products")}>
                Explore Products
                <ArrowRight className="h-4 w-4" />
              </Button>
            }
          />
        </div>
      ) : (
        <div className="mt-8 grid gap-8 lg:grid-cols-12">
          {/* Line Items */}
          <div className="space-y-4 lg:col-span-8">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex flex-col justify-between gap-4 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-xs sm:flex-row sm:items-center"
              >
                <div className="flex items-center gap-4">
                  <Link
                    to={`/products/${item.product_id}`}
                    className="h-24 w-24 shrink-0 overflow-hidden rounded-xl bg-[var(--muted)]"
                  >
                    <img
                      src={getProductImageUrl(item.product_id)}
                      alt={item.product_name}
                      className="h-full w-full object-cover"
                    />
                  </Link>
                  <div>
                    <Link
                      to={`/products/${item.product_id}`}
                      className="text-base font-semibold text-[var(--fg)] hover:text-[var(--primary)]"
                    >
                      {item.product_name}
                    </Link>
                    <div className="mt-1 flex items-center gap-2 text-xs text-[var(--muted-fg)]">
                      <span>Unit price:</span>
                      <Price amount={item.unit_price} className="font-medium text-[var(--fg)]" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-6 sm:justify-end">
                  <QuantityStepper
                    value={item.quantity}
                    min={1}
                    max={99}
                    disabled={updateMutation.isPending}
                    onChange={(qty) =>
                      updateMutation.mutate({ productId: item.product_id, quantity: qty })
                    }
                  />
                  <div className="min-w-24 text-right">
                    <Price amount={item.subtotal} className="text-base font-bold text-[var(--fg)]" />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeMutation.mutate(item.product_id)}
                    aria-label={`Remove ${item.product_name}`}
                    className="rounded-lg p-2 text-[var(--muted-fg)] transition hover:bg-rose-500/10 hover:text-rose-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-4">
            <div className="sticky top-24 rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xs">
              <h2 className="text-lg font-bold text-[var(--fg)]">Order Summary</h2>
              <div className="mt-5 space-y-3 text-sm">
                <div className="flex items-center justify-between text-[var(--muted-fg)]">
                  <span>Items ({items.reduce((sum, i) => sum + i.quantity, 0)})</span>
                  <Price amount={cart?.total ?? "0.00"} className="font-medium text-[var(--fg)]" />
                </div>
                <div className="flex items-center justify-between text-[var(--muted-fg)]">
                  <span>Express Shipping</span>
                  <span className="font-medium text-emerald-600 dark:text-emerald-400">Free</span>
                </div>
                <div className="border-t border-[var(--border)] pt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-base font-semibold text-[var(--fg)]">Estimated Total</span>
                    <Price
                      amount={cart?.total ?? "0.00"}
                      className="text-xl font-extrabold text-[var(--fg)]"
                    />
                  </div>
                </div>
              </div>

              <Button
                size="lg"
                className="mt-6 w-full"
                onClick={() => navigate("/checkout")}
              >
                Proceed to Checkout
                <ArrowRight className="h-4 w-4" />
              </Button>

              <div className="mt-4 flex items-center justify-center gap-2 text-xs text-[var(--muted-fg)]">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                <span>Idempotent atomic checkout protection</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
