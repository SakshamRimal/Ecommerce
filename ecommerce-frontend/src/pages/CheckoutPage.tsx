import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  Banknote,
  CheckCircle2,
  CreditCard,
  KeyRound,
  Lock,
  MapPin,
  PackageCheck,
  ShieldCheck,
  ShoppingBag,
  Wallet,
} from "lucide-react";
import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, EmptyState, Price, Skeleton } from "../components/ui/Primitives";
import { api, ApiError } from "../lib/api/client";
import type { Order } from "../lib/api/types";
import { multiplyMoney } from "../lib/money";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

type PaymentMethod = "card" | "wallet" | "cod";

function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function CheckoutPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const authStatus = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const demoMode = useAuthStore((s) => s.demoMode);
  const addToast = useUiStore((s) => s.addToast);
  const setLastOrder = useUiStore((s) => s.setLastOrder);

  const [idempotencyKey, setIdempotencyKey] = useState<string>(() => generateIdempotencyKey());
  const [confirmedOrder, setConfirmedOrder] = useState<Order | null>(null);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("card");
  const [shippingAddress, setShippingAddress] = useState<string>("Kathmandu Metro, Bagmati");
  const [cardLast4, setCardLast4] = useState<string>("4242");
  const inFlightRef = useRef(false);

  const canCheckout = authStatus === "authenticated" || demoMode;

  const cartQuery = useQuery({
    queryKey: [...qk.cart(), demoMode],
    queryFn: () => api.cart.get(),
    enabled: canCheckout && !confirmedOrder,
  });

  const placeOrderMutation = useMutation({
    mutationFn: async (key: string) => {
      return api.orders.create({ idempotency_key: key });
    },
    onSuccess: (order) => {
      inFlightRef.current = false;
      setConfirmedOrder(order);
      setLastOrder(order);
      setCheckoutError(null);
      queryClient.invalidateQueries({ queryKey: qk.cart() });
      queryClient.invalidateQueries({ queryKey: qk.orders() });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      addToast({
        title: "Payment & order confirmed!",
        description: `Order #${order.id.slice(0, 8)} has been placed and confirmation email queued.`,
        tone: "success",
      });
    },
    onError: (err) => {
      inFlightRef.current = false;
      if (err instanceof ApiError) {
        setCheckoutError(err.detail);
        if (err.status === 409 || err.status === 400) {
          queryClient.invalidateQueries({ queryKey: qk.cart() });
          setIdempotencyKey(generateIdempotencyKey());
        }
      } else {
        setCheckoutError("Network error while placing order. Safe to retry with the same key.");
      }
    },
  });

  const handleConfirmOrder = () => {
    if (inFlightRef.current || placeOrderMutation.isPending) {
      return;
    }
    if (!shippingAddress.trim()) {
      setCheckoutError("Please provide a delivery address before confirming your order.");
      return;
    }
    inFlightRef.current = true;
    placeOrderMutation.mutate(idempotencyKey);
  };

  if (!canCheckout) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <EmptyState
          icon={<Lock className="h-6 w-6" />}
          title="Sign in required for checkout"
          description="Please sign in to your Commercify account or enable Demo Mode to place an order."
          action={
            <Button onClick={() => navigate("/login?next=/checkout")}>
              Sign In to Checkout
            </Button>
          }
        />
      </div>
    );
  }

  if (confirmedOrder) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <div className="overflow-hidden rounded-3xl border border-[var(--border)] bg-[var(--card)] p-8 shadow-lg">
          <div className="flex flex-col items-center text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-9 w-9" />
            </div>
            <span className="mt-4 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Status: {confirmedOrder.status}
            </span>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--fg)]">
              Thank you for your order!
            </h1>
            <p className="mt-2 max-w-md text-sm text-[var(--muted-fg)]">
              Your items have been reserved and your cart has been cleared. You can view or cancel
              this order anytime from your Orders page.
            </p>
          </div>

          <div className="mt-8 grid gap-4 rounded-2xl border border-[var(--border)] bg-[var(--muted)]/50 p-4 text-xs sm:grid-cols-2">
            <div>
              <p className="text-[var(--muted-fg)]">Order ID</p>
              <p className="mt-1 font-mono font-semibold text-[var(--fg)]">{confirmedOrder.id}</p>
            </div>
            <div>
              <p className="text-[var(--muted-fg)]">Total Charged</p>
              <Price
                amount={confirmedOrder.total_amount}
                className="mt-1 block text-base font-extrabold text-[var(--fg)]"
              />
            </div>
          </div>

          <div className="mt-6">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-fg)]">
              Purchased Line Items
            </h2>
            <ul className="mt-3 divide-y divide-[var(--border)] rounded-2xl border border-[var(--border)] bg-[var(--bg)] px-4">
              {confirmedOrder.items.map((item) => (
                <li key={item.product_id} className="flex items-center justify-between py-3.5 text-sm">
                  <div>
                    <p className="font-semibold text-[var(--fg)]">{item.product_name}</p>
                    <p className="text-xs text-[var(--muted-fg)]">
                      Qty {item.quantity} × <Price amount={item.unit_price} />
                    </p>
                  </div>
                  <Price
                    amount={multiplyMoney(item.unit_price, item.quantity)}
                    className="font-bold text-[var(--fg)]"
                  />
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
            <Link to={`/orders/${confirmedOrder.id}`}>
              <Button variant="secondary">
                <PackageCheck className="h-4 w-4" />
                View Order Details
              </Button>
            </Link>
            <Link to="/products">
              <Button>Continue Shopping</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const cart = cartQuery.data;
  const items = cart?.items ?? [];

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Link
        to="/cart"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--muted-fg)] hover:text-[var(--fg)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Shopping Bag
      </Link>

      <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--fg)]">
        Review &amp; Place Order
      </h1>

      {cartQuery.isLoading ? (
        <div className="mt-8 space-y-4">
          <Skeleton className="h-40 w-full rounded-2xl" />
          <Skeleton className="h-48 w-full rounded-2xl" />
        </div>
      ) : items.length === 0 ? (
        <div className="mt-10">
          <EmptyState
            icon={<ShoppingBag className="h-6 w-6" />}
            title="Your cart is empty"
            description="Add items to your cart before proceeding to checkout."
            action={<Button onClick={() => navigate("/products")}>Browse Catalog</Button>}
          />
        </div>
      ) : (
        <div className="mt-8 grid gap-8 lg:grid-cols-12">
          {/* Left Column: Customer, Payment & Items Review */}
          <div className="space-y-6 lg:col-span-7">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-[var(--primary)]" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted-fg)]">
                  Account &amp; Delivery Address
                </h2>
              </div>
              <p className="mt-2 text-sm font-semibold text-[var(--fg)]">
                {user?.full_name ?? "Customer"} ({user?.email ?? "customer@commercify.dev"})
              </p>
              <div className="mt-3">
                <label
                  htmlFor="shipping-address"
                  className="block text-xs font-medium text-[var(--muted-fg)]"
                >
                  Delivery Destination
                </label>
                <input
                  id="shipping-address"
                  type="text"
                  value={shippingAddress}
                  onChange={(e) => setShippingAddress(e.target.value)}
                  placeholder="Street address, city, postal code"
                  className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3.5 py-2 text-sm text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
                />
              </div>
              <p className="mt-2 text-xs text-[var(--muted-fg)]">
                Row-locked PostgreSQL transaction (`SELECT ... FOR UPDATE`) reserves inventory
                atomically on confirmation.
              </p>
            </div>

            <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted-fg)]">
                Payment Method
              </h2>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <button
                  type="button"
                  onClick={() => setPaymentMethod("card")}
                  className={`flex flex-col items-start rounded-xl border p-3.5 text-left transition ${
                    paymentMethod === "card"
                      ? "border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--fg)]"
                      : "border-[var(--border)] bg-[var(--bg)] text-[var(--muted-fg)] hover:text-[var(--fg)]"
                  }`}
                >
                  <CreditCard className="h-4 w-4 text-[var(--primary)]" />
                  <span className="mt-2 text-xs font-bold">Credit / Debit Card</span>
                  <span className="mt-0.5 text-[11px] opacity-75">Instant authorization</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod("wallet")}
                  className={`flex flex-col items-start rounded-xl border p-3.5 text-left transition ${
                    paymentMethod === "wallet"
                      ? "border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--fg)]"
                      : "border-[var(--border)] bg-[var(--bg)] text-[var(--muted-fg)] hover:text-[var(--fg)]"
                  }`}
                >
                  <Wallet className="h-4 w-4 text-[var(--primary)]" />
                  <span className="mt-2 text-xs font-bold">Digital Wallet</span>
                  <span className="mt-0.5 text-[11px] opacity-75">One-tap express pay</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod("cod")}
                  className={`flex flex-col items-start rounded-xl border p-3.5 text-left transition ${
                    paymentMethod === "cod"
                      ? "border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--fg)]"
                      : "border-[var(--border)] bg-[var(--bg)] text-[var(--muted-fg)] hover:text-[var(--fg)]"
                  }`}
                >
                  <Banknote className="h-4 w-4 text-[var(--primary)]" />
                  <span className="mt-2 text-xs font-bold">Pay on Delivery</span>
                  <span className="mt-0.5 text-[11px] opacity-75">Cash or card at door</span>
                </button>
              </div>
              {paymentMethod === "card" && (
                <div className="mt-3 flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3.5 py-2.5 text-xs">
                  <span className="font-medium text-[var(--fg)]">
                    Visa •••• {cardLast4 || "4242"}
                  </span>
                  <input
                    type="text"
                    maxLength={4}
                    aria-label="Card last 4 digits"
                    value={cardLast4}
                    onChange={(e) => setCardLast4(e.target.value.replace(/\D/g, ""))}
                    className="w-16 rounded-lg border border-[var(--border)] bg-[var(--card)] px-2 py-1 text-center font-mono text-xs text-[var(--fg)]"
                  />
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted-fg)]">
                Items in Order ({items.reduce((acc, i) => acc + i.quantity, 0)})
              </h2>
              <ul className="mt-4 divide-y divide-[var(--border)]">
                {items.map((item) => (
                  <li key={item.id} className="flex items-center justify-between py-3.5">
                    <div>
                      <p className="text-sm font-semibold text-[var(--fg)]">{item.product_name}</p>
                      <p className="text-xs text-[var(--muted-fg)]">
                        Qty: {item.quantity} × <Price amount={item.unit_price} />
                      </p>
                    </div>
                    <Price
                      amount={item.subtotal}
                      className="text-sm font-bold text-[var(--fg)]"
                    />
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right Column: Payment & Idempotency Summary */}
          <div className="lg:col-span-5">
            <div className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-sm">
              <h2 className="text-lg font-bold text-[var(--fg)]">Order Summary</h2>

              <div className="mt-4 space-y-3 text-sm">
                <div className="flex justify-between text-[var(--muted-fg)]">
                  <span>Subtotal</span>
                  <Price amount={cart?.total ?? "0.00"} className="font-medium text-[var(--fg)]" />
                </div>
                <div className="flex justify-between text-[var(--muted-fg)]">
                  <span>Shipping</span>
                  <span className="font-medium text-emerald-600 dark:text-emerald-400">Free</span>
                </div>
                <div className="border-t border-[var(--border)] pt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-base font-bold text-[var(--fg)]">Total Due</span>
                    <Price
                      amount={cart?.total ?? "0.00"}
                      className="text-2xl font-extrabold text-[var(--fg)]"
                    />
                  </div>
                </div>
              </div>

              {/* Idempotency Key Indicator */}
              <div className="mt-5 rounded-xl border border-[var(--border)] bg-[var(--muted)]/60 p-3 text-xs">
                <div className="flex items-center gap-1.5 font-semibold text-[var(--fg)]">
                  <KeyRound className="h-3.5 w-3.5 text-[var(--primary)]" />
                  Idempotency Key Active
                </div>
                <p className="mt-1 truncate font-mono text-[11px] text-[var(--muted-fg)]">
                  {idempotencyKey}
                </p>
              </div>

              {checkoutError && (
                <div
                  role="alert"
                  className="mt-4 flex items-start gap-2.5 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-600 dark:text-rose-400"
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  <div>
                    <p className="font-semibold">Could not complete checkout</p>
                    <p className="mt-0.5">{checkoutError}</p>
                  </div>
                </div>
              )}

              <Button
                size="lg"
                className="mt-6 w-full"
                loading={placeOrderMutation.isPending}
                onClick={handleConfirmOrder}
              >
                <ShieldCheck className="h-4 w-4" />
                Confirm &amp; Place Order
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
