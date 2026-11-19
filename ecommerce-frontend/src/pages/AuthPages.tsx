import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  KeyRound,
  LogOut,
  Mail,
  Package,
  Shield,
  ShoppingBag,
  User as UserIcon,
} from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button, Input } from "../components/ui/Primitives";
import { api, ApiError, fieldErrors } from "../lib/api/client";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const nextPath = searchParams.get("next") || "/";
  const queryClient = useQueryClient();

  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const setDemoMode = useAuthStore((s) => s.setDemoMode);
  const addToast = useUiStore((s) => s.addToast);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFields({});
    setLoading(true);
    setDemoMode(false);

    try {
      const tokens = await api.auth.login(email.trim(), password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await api.auth.me();
      setUser(me);
      queryClient.clear();
      addToast({
        title: `Welcome back, ${me.full_name}`,
        description: `Signed in as ${me.email}`,
        tone: "success",
      });
      navigate(nextPath);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 422) {
          setFields(fieldErrors(err));
          setFormError("Please check the highlighted fields.");
        } else if (err.status === 429) {
          setFormError("Too many login attempts. Please wait a minute before trying again.");
        } else {
          setFormError(err.detail);
        }
      } else {
        setFormError("Could not reach the backend server on http://localhost:8000.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[75vh] max-w-md flex-col justify-center px-4 py-12 sm:px-6">
      <div className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-7 shadow-sm sm:p-9">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--primary)] text-white shadow-sm">
            <KeyRound className="h-6 w-6" />
          </div>
          <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-[var(--fg)]">
            Sign in to Commercify
          </h1>
          <p className="mt-1.5 text-xs text-[var(--muted-fg)]">
            Access your shopping bag, order history, and AI shopping concierge.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <Input
            label="Email address"
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={fields.username || fields.email}
          />

          <Input
            label="Password"
            type="password"
            required
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fields.password}
          />

          {formError && (
            <div
              role="alert"
              className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs font-medium text-rose-600 dark:text-rose-400"
            >
              {formError}
            </div>
          )}

          <Button type="submit" size="lg" loading={loading} className="w-full">
            Sign In
            <ArrowRight className="h-4 w-4" />
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-[var(--muted-fg)]">
          New to Commercify?{" "}
          <Link
            to={`/register?next=${encodeURIComponent(nextPath)}`}
            className="font-semibold text-[var(--primary)] hover:underline"
          >
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const nextPath = searchParams.get("next") || "/";
  const queryClient = useQueryClient();

  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const setDemoMode = useAuthStore((s) => s.setDemoMode);
  const addToast = useUiStore((s) => s.addToast);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFields({});
    setDemoMode(false);

    if (password.length < 8) {
      setFields({ password: "Password must be at least 8 characters." });
      return;
    }

    setLoading(true);
    try {
      await api.auth.register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
      });
      const tokens = await api.auth.login(email.trim(), password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await api.auth.me();
      setUser(me);
      queryClient.clear();
      addToast({
        title: "Account created!",
        description: `Welcome to Commercify, ${me.full_name}.`,
        tone: "success",
      });
      navigate(nextPath);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 422) {
          setFields(fieldErrors(err));
          setFormError("Please fix the validation errors below.");
        } else if (err.status === 409) {
          setFields({ email: err.detail });
          setFormError(err.detail);
        } else if (err.status === 429) {
          setFormError("Rate limit reached. Please wait a moment and try again.");
        } else {
          setFormError(err.detail);
        }
      } else {
        setFormError("Unable to reach server. Please check that the backend is running.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[75vh] max-w-md flex-col justify-center px-4 py-12 sm:px-6">
      <div className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-7 shadow-sm sm:p-9">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--primary)] text-white shadow-sm">
            <UserIcon className="h-6 w-6" />
          </div>
          <h1 className="mt-4 text-2xl font-extrabold tracking-tight text-[var(--fg)]">
            Create your account
          </h1>
          <p className="mt-1.5 text-xs text-[var(--muted-fg)]">
            Join Commercify for persistent carts, instant checkout, and AI concierge history.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <Input
            label="Full name"
            type="text"
            required
            placeholder="Saksham Rimal"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            error={fields.full_name}
          />

          <Input
            label="Email address"
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={fields.email}
          />

          <Input
            label="Password"
            type="password"
            required
            autoComplete="new-password"
            placeholder="At least 8 characters"
            hint="Minimum 8 characters required"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fields.password}
          />

          {formError && (
            <div
              role="alert"
              className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs font-medium text-rose-600 dark:text-rose-400"
            >
              {formError}
            </div>
          )}

          <Button type="submit" size="lg" loading={loading} className="w-full">
            Create Account
            <ArrowRight className="h-4 w-4" />
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-[var(--muted-fg)]">
          Already have an account?{" "}
          <Link
            to={`/login?next=${encodeURIComponent(nextPath)}`}
            className="font-semibold text-[var(--primary)] hover:underline"
          >
            Sign in instead
          </Link>
        </p>
      </div>
    </div>
  );
}

export function AccountPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const addToast = useUiStore((s) => s.addToast);
  const [loggingOut, setLoggingOut] = useState(false);

  if (!user) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <p className="text-sm text-[var(--muted-fg)]">You are not currently signed in.</p>
        <Button className="mt-4" onClick={() => navigate("/login")}>
          Go to Sign In
        </Button>
      </div>
    );
  }

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await api.auth.logout(refreshToken);
    } finally {
      clearAuth();
      queryClient.clear();
      setLoggingOut(false);
      addToast({ title: "Signed out", description: "See you next time!", tone: "info" });
      navigate("/");
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xs sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-xl font-extrabold text-[var(--primary)]">
              {user.full_name.slice(0, 1).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-extrabold text-[var(--fg)]">{user.full_name}</h1>
                <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold uppercase text-[var(--primary)]">
                  {user.role}
                </span>
              </div>
              <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--muted-fg)]">
                <Mail className="h-3.5 w-3.5" />
                {user.email}
              </p>
            </div>
          </div>

          <Button variant="danger" size="sm" loading={loggingOut} onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Sign Out
          </Button>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <Link
            to="/orders"
            className="flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-5 transition hover:border-[var(--primary)]"
          >
            <Package className="h-6 w-6 text-[var(--primary)]" />
            <div className="mt-4">
              <h2 className="font-semibold text-[var(--fg)]">Your Orders</h2>
              <p className="mt-0.5 text-xs text-[var(--muted-fg)]">
                Track status, inspect line items, or cancel pending orders.
              </p>
            </div>
          </Link>

          <Link
            to="/cart"
            className="flex flex-col justify-between rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-5 transition hover:border-[var(--primary)]"
          >
            <ShoppingBag className="h-6 w-6 text-[var(--primary)]" />
            <div className="mt-4">
              <h2 className="font-semibold text-[var(--fg)]">Shopping Bag</h2>
              <p className="mt-0.5 text-xs text-[var(--muted-fg)]">
                Review saved items and proceed to idempotent checkout.
              </p>
            </div>
          </Link>

          {user.role === "admin" && (
            <Link
              to="/admin/products"
              className="flex flex-col justify-between rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-5 transition hover:border-[var(--primary)]"
            >
              <Shield className="h-6 w-6 text-[var(--primary)]" />
              <div className="mt-4">
                <h2 className="font-semibold text-[var(--fg)]">Admin Console</h2>
                <p className="mt-0.5 text-xs text-[var(--muted-fg)]">
                  Manage catalog products, pricing, stock, and categories.
                </p>
              </div>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
