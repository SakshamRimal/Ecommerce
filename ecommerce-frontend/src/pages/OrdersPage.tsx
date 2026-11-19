import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Package,
  RotateCcw,
  ShoppingBag,
  XCircle,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Button,
  EmptyState,
  ErrorState,
  Price,
  Skeleton,
} from "../components/ui/Primitives";
import { api, ApiError } from "../lib/api/client";
import type { OrderStatus } from "../lib/api/types";
import { multiplyMoney } from "../lib/money";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const styles: Record<OrderStatus, string> = {
    pending: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    confirmed: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    canceled: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
        styles[status] ?? styles.pending
      }`}
    >
      {status === "canceled" ? (
        <XCircle className="h-3.5 w-3.5" />
      ) : status === "confirmed" ? (
        <CheckCircle2 className="h-3.5 w-3.5" />
      ) : (
        <Clock className="h-3.5 w-3.5" />
      )}
      {status}
    </span>
  );
}

export function OrdersPage() {
  const navigate = useNavigate();
  const authStatus = useAuthStore((s) => s.status);
  const demoMode = useAuthStore((s) => s.demoMode);
  const canView = authStatus === "authenticated" || demoMode;

  const ordersQuery = useQuery({
    queryKey: [...qk.orders({ limit: 20, offset: 0 }), demoMode],
    queryFn: () => api.orders.list({ limit: 20, offset: 0 }),
    enabled: canView,
  });

  if (!canView) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <EmptyState
          icon={<Package className="h-6 w-6" />}
          title="Sign in to view your orders"
          description="Track your order history, view receipts, or cancel pending orders."
          action={<Button onClick={() => navigate("/login?next=/orders")}>Sign In</Button>}
        />
      </div>
    );
  }

  const orders = ordersQuery.data ?? [];

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--border)] pb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
            Purchase History
          </span>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-[var(--fg)]">
            Your Orders
          </h1>
        </div>
        <Link to="/products">
          <Button variant="secondary" size="sm">
            <ShoppingBag className="h-4 w-4" />
            Shop More
          </Button>
        </Link>
      </div>

      <div className="mt-8">
        {ordersQuery.isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-28 w-full rounded-2xl" />
            <Skeleton className="h-28 w-full rounded-2xl" />
          </div>
        ) : ordersQuery.isError ? (
          <ErrorState
            message="Failed to load order history."
            onRetry={() => ordersQuery.refetch()}
          />
        ) : orders.length === 0 ? (
          <EmptyState
            icon={<Package className="h-6 w-6" />}
            title="No orders placed yet"
            description="Once you complete checkout, your orders and itemized receipts will appear here."
            action={<Button onClick={() => navigate("/products")}>Start Shopping</Button>}
          />
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <Link
                key={order.id}
                to={`/orders/${order.id}`}
                className="block rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-xs transition hover:border-[var(--primary)] hover:shadow-md"
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-bold text-[var(--fg)]">
                        Order #{order.id.slice(0, 8)}
                      </span>
                      <OrderStatusBadge status={order.status} />
                    </div>
                    <p className="mt-1.5 text-xs text-[var(--muted-fg)]">
                      {order.items.reduce((sum, i) => sum + i.quantity, 0)} item(s) ·{" "}
                      {order.items.map((i) => i.product_name).join(", ")}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-xs text-[var(--muted-fg)]">Total Amount</p>
                    <Price
                      amount={order.total_amount}
                      className="text-lg font-extrabold text-[var(--fg)]"
                    />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const demoMode = useAuthStore((s) => s.demoMode);
  const addToast = useUiStore((s) => s.addToast);

  const orderQuery = useQuery({
    queryKey: [...qk.order(orderId ?? ""), demoMode],
    queryFn: () => api.orders.get(orderId!),
    enabled: Boolean(orderId),
  });

  const cancelMutation = useMutation({
    mutationFn: () => api.orders.cancel(orderId!),
    onSuccess: (updated) => {
      queryClient.setQueryData([...qk.order(orderId!), demoMode], updated);
      queryClient.invalidateQueries({ queryKey: qk.orders() });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      addToast({
        title: "Order canceled",
        description: "Your order has been canceled and reserved inventory has been restored.",
        tone: "info",
      });
    },
    onError: (err) => {
      addToast({
        title: "Could not cancel order",
        description: err instanceof ApiError ? err.detail : "Please try again.",
        tone: "error",
      });
    },
  });

  if (orderQuery.isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <Skeleton className="h-64 w-full rounded-3xl" />
      </div>
    );
  }

  if (orderQuery.isError || !orderQuery.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <ErrorState
          title="Order not found"
          message="We could not locate this order or you do not have permission to view it."
          onRetry={() => navigate("/orders")}
        />
      </div>
    );
  }

  const order = orderQuery.data;
  const canCancel = order.status !== "canceled";

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Link
        to="/orders"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--muted-fg)] hover:text-[var(--fg)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to All Orders
      </Link>

      <div className="mt-4 rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xs sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--border)] pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-extrabold text-[var(--fg)]">
                Order #{order.id.slice(0, 8)}
              </h1>
              <OrderStatusBadge status={order.status} />
            </div>
            <p className="mt-1 font-mono text-xs text-[var(--muted-fg)]">Full ID: {order.id}</p>
          </div>

          {canCancel && (
            <Button
              variant="danger"
              size="sm"
              loading={cancelMutation.isPending}
              onClick={() => cancelMutation.mutate()}
            >
              <RotateCcw className="h-4 w-4" />
              Cancel Order &amp; Restock
            </Button>
          )}
        </div>

        <div className="mt-6">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-fg)]">
            Order Line Items
          </h2>
          <ul className="mt-3 divide-y divide-[var(--border)]">
            {order.items.map((item) => (
              <li key={item.product_id} className="flex items-center justify-between py-4 text-sm">
                <div>
                  <Link
                    to={`/products/${item.product_id}`}
                    className="font-semibold text-[var(--fg)] hover:text-[var(--primary)]"
                  >
                    {item.product_name}
                  </Link>
                  <p className="mt-0.5 text-xs text-[var(--muted-fg)]">
                    Quantity: {item.quantity} × <Price amount={item.unit_price} />
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

        <div className="mt-6 flex items-center justify-between border-t border-[var(--border)] pt-6">
          <span className="text-base font-bold text-[var(--fg)]">Order Total</span>
          <Price
            amount={order.total_amount}
            className="text-2xl font-extrabold text-[var(--fg)]"
          />
        </div>
      </div>
    </div>
  );
}
