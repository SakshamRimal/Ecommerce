import React from "react";
import clsx from "clsx";
import {
  AlertCircle,
  CheckCircle2,
  Info,
  Loader2,
  Minus,
  PackageOpen,
  Plus,
  RefreshCw,
  X,
} from "lucide-react";
import { formatMoney } from "../../lib/money";
import type { Money } from "../../lib/api/types";
import { useUiStore } from "../../stores/ui-store";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "dark" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    const base =
      "inline-flex items-center justify-center gap-2 font-medium rounded-xl transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none cursor-pointer active:scale-[0.99]";

    const variants = {
      primary:
        "bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm shadow-indigo-600/20",
      secondary:
        "border border-slate-200 bg-white text-slate-900 shadow-xs hover:border-indigo-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
      dark:
        "bg-slate-950 text-white hover:bg-slate-900 border border-slate-700/60 shadow-lg",
      outline:
        "border border-slate-200 bg-white text-slate-800 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800",
      ghost:
        "text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800",
      danger:
        "bg-red-600 text-white hover:bg-red-500 shadow-sm shadow-red-600/20",
    };

    const sizes = {
      sm: "px-3 py-1.5 text-xs",
      md: "px-4 py-2.5 text-sm",
      lg: "px-6 py-3 text-base",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={clsx(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const errorId = `${inputId}-error`;
    const hintId = `${inputId}-hint`;

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-slate-700 dark:text-slate-200"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          className={clsx(
            "w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition focus:outline-none focus:ring-2 dark:bg-slate-900 dark:text-slate-100",
            error
              ? "border-red-500 focus:ring-red-500/30"
              : "border-slate-200 focus:border-indigo-500 focus:ring-indigo-500/20 dark:border-slate-700",
            className,
          )}
          {...props}
        />
        {error ? (
          <p id={errorId} className="text-xs font-medium text-red-600 dark:text-red-400">
            {error}
          </p>
        ) : hint ? (
          <p id={hintId} className="text-xs text-slate-500 dark:text-slate-400">
            {hint}
          </p>
        ) : null}
      </div>
    );
  },
);
Input.displayName = "Input";

export function Price({
  amount,
  className,
}: {
  amount: Money | number | null | undefined;
  className?: string;
}) {
  return (
    <span className={clsx("tabular-nums font-semibold", className)}>
      {formatMoney(amount)}
    </span>
  );
}

export function StockBadge({ stock }: { stock: number }) {
  if (stock <= 0) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20 dark:bg-red-950/60 dark:text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Out of stock
      </span>
    );
  }
  if (stock <= 5) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20 dark:bg-amber-950/60 dark:text-amber-300">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
        Only {stock} left
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-950/60 dark:text-emerald-300">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      In stock ({stock})
    </span>
  );
}

export function QuantityStepper({
  value,
  min = 1,
  max = 99,
  disabled = false,
  onChange,
}: {
  value: number;
  min?: number;
  max?: number;
  disabled?: boolean;
  onChange: (next: number) => void;
}) {
  return (
    <div className="inline-flex items-center rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <button
        type="button"
        aria-label="Decrease quantity"
        disabled={disabled || value <= min}
        onClick={() => onChange(Math.max(min, value - 1))}
        className="p-2 text-slate-600 hover:text-slate-900 disabled:opacity-40 cursor-pointer dark:text-slate-300"
      >
        <Minus className="h-3.5 w-3.5" />
      </button>
      <span
        aria-live="polite"
        className="min-w-[2.25rem] text-center text-sm font-semibold tabular-nums"
      >
        {value}
      </span>
      <button
        type="button"
        aria-label="Increase quantity"
        disabled={disabled || value >= max}
        onClick={() => onChange(Math.min(max, value + 1))}
        className="p-2 text-slate-600 hover:text-slate-900 disabled:opacity-40 cursor-pointer dark:text-slate-300"
      >
        <Plus className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={clsx(
        "animate-pulse rounded-xl bg-slate-200/80 dark:bg-slate-800",
        className,
      )}
    />
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 px-6 py-14 text-center dark:border-slate-800 dark:bg-slate-900/50">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
        {icon ?? <PackageOpen className="h-6 w-6" />}
      </div>
      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
        {title}
      </h3>
      <p className="mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "Unable to load data",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50/60 px-6 py-10 text-center dark:border-red-900/50 dark:bg-red-950/20"
    >
      <AlertCircle className="mb-3 h-8 w-8 text-red-600 dark:text-red-400" />
      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
        {title}
      </h3>
      <p className="mt-1 max-w-md text-sm text-slate-600 dark:text-slate-300">
        {message}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-4"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Try again
        </Button>
      )}
    </div>
  );
}

export function ToastViewport() {
  const { toasts, removeToast } = useUiStore();
  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      className="fixed bottom-5 right-5 z-50 flex w-full max-w-sm flex-col gap-2.5 px-4 sm:px-0"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={clsx(
            "flex items-start gap-3 rounded-2xl border p-4 shadow-xl backdrop-blur-md transition-all",
            t.tone === "success" &&
              "border-emerald-200 bg-white/95 text-slate-900 dark:border-emerald-800 dark:bg-slate-900/95 dark:text-slate-100",
            t.tone === "error" &&
              "border-red-200 bg-white/95 text-slate-900 dark:border-red-800 dark:bg-slate-900/95 dark:text-slate-100",
            t.tone === "info" &&
              "border-indigo-200 bg-white/95 text-slate-900 dark:border-indigo-800 dark:bg-slate-900/95 dark:text-slate-100",
          )}
        >
          {t.tone === "success" && (
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
          )}
          {t.tone === "error" && (
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          )}
          {t.tone === "info" && (
            <Info className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600" />
          )}
          <div className="flex-1 text-sm">
            <p className="font-semibold">{t.title}</p>
            {t.description && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                {t.description}
              </p>
            )}
          </div>
          <button
            type="button"
            aria-label="Dismiss notification"
            onClick={() => removeToast(t.id)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
