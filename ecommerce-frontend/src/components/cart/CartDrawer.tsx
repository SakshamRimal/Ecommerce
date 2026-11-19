import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ShoppingBag, Trash2, X } from "lucide-react";
import { api } from "../../lib/api/client";
import { qk } from "../../lib/query-keys";
import { useAuthStore } from "../../stores/auth-store";
import { useUiStore } from "../../stores/ui-store";
import {
  Button,
  EmptyState,
  Price,
  QuantityStepper,
} from "../ui/Primitives";

export function CartDrawer() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { status } = useAuthStore();
  const { cartDrawerOpen, setCartDrawerOpen, addToast } = useUiStore();

  const { data: cart, isLoading } = useQuery({
    queryKey: qk.cart(),
    queryFn: api.cart.get,
    enabled: status === "authenticated",
    staleTime: 0,
  });

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && cartDrawerOpen) {
        setCartDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [cartDrawerOpen, setCartDrawerOpen]);

  const updateMutation = useMutation({
    mutationFn: ({
      productId,
      quantity,
    }: {
      productId: string;
      quantity: number;
    }) => api.cart.updateItem(productId, { quantity }),
    onSuccess: (updated) => {
      queryClient.setQueryData(qk.cart(), updated);
    },
    onError: (err: Error) => {
      queryClient.invalidateQueries({ queryKey: qk.cart() });
      addToast({
        tone: "error",
        title: "Stock limit reached",
        description: err.message,
      });
    },
  });

  const removeMutation = useMutation({
    mutationFn: (productId: string) => api.cart.removeItem(productId),
    onSuccess: (updated) => {
      queryClient.setQueryData(qk.cart(), updated);
    },
  });

  const clearMutation = useMutation({
    mutationFn: () => api.cart.clear(),
    onSuccess: (updated) => {
      queryClient.setQueryData(qk.cart(), updated);
      addToast({ tone: "info", title: "Cart cleared" });
    },
  });

  if (!cartDrawerOpen) return null;

  const itemCount =
    cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0;

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-label="Shopping cart"
    >
      <div
        className="fixed inset-0 bg-slate-950/50 backdrop-blur-xs transition-opacity"
        onClick={() => setCartDrawerOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 flex max-w-full pl-10">
        <div className="flex w-screen max-w-md flex-col bg-white shadow-2xl dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <ShoppingBag className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Your Bag
              </h2>
              <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                {itemCount}
              </span>
            </div>
            <button
              type="button"
              aria-label="Close cart drawer"
              onClick={() => setCartDrawerOpen(false)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {status !== "authenticated" ? (
              <EmptyState
                title="Sign in to view your cart"
                description="Your shopping bag is synced securely with your account."
                action={
                  <Button
                    onClick={() => {
                      setCartDrawerOpen(false);
                      navigate("/login?next=/cart");
                    }}
                  >
                    Sign In
                  </Button>
                }
              />
            ) : isLoading ? (
              <div className="space-y-4">
                {[1, 2].map((n) => (
                  <div
                    key={n}
                    className="h-24 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-800"
                  />
                ))}
              </div>
            ) : !cart || cart.items.length === 0 ? (
              <EmptyState
                title="Your bag is empty"
                description="Explore our curated collection and add items to get started."
                action={
                  <Button
                    variant="outline"
                    onClick={() => {
                      setCartDrawerOpen(false);
                      navigate("/products");
                    }}
                  >
                    Browse Catalog
                  </Button>
                }
              />
            ) : (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => clearMutation.mutate()}
                    className="text-xs font-medium text-slate-500 hover:text-red-600 cursor-pointer"
                  >
                    Clear all items
                  </button>
                </div>

                {cart.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 p-4 dark:border-slate-800"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          to={`/products/${item.product_id}`}
                          onClick={() => setCartDrawerOpen(false)}
                          className="font-semibold text-slate-900 hover:text-indigo-600 dark:text-slate-100"
                        >
                          {item.product_name}
                        </Link>
                        <p className="mt-0.5 text-xs text-slate-500">
                          <Price amount={item.unit_price} /> each
                        </p>
                      </div>
                      <button
                        type="button"
                        aria-label={`Remove ${item.product_name}`}
                        onClick={() => removeMutation.mutate(item.product_id)}
                        className="rounded-lg p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 cursor-pointer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <QuantityStepper
                        value={item.quantity}
                        min={1}
                        disabled={updateMutation.isPending}
                        onChange={(qty) =>
                          updateMutation.mutate({
                            productId: item.product_id,
                            quantity: qty,
                          })
                        }
                      />
                      <Price
                        amount={item.subtotal}
                        className="text-base text-slate-900 dark:text-white"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {status === "authenticated" && cart && cart.items.length > 0 && (
            <div className="border-t border-slate-200 bg-slate-50/80 p-6 dark:border-slate-800 dark:bg-slate-900/90">
              <div className="flex items-center justify-between text-base">
                <span className="font-medium text-slate-600 dark:text-slate-300">
                  Order Total
                </span>
                <Price
                  amount={cart.total}
                  className="text-xl font-bold text-slate-900 dark:text-white"
                />
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Stock is locked atomically at checkout.
              </p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setCartDrawerOpen(false);
                    navigate("/cart");
                  }}
                >
                  View Full Bag
                </Button>
                <Button
                  onClick={() => {
                    setCartDrawerOpen(false);
                    navigate("/checkout");
                  }}
                >
                  Checkout
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

