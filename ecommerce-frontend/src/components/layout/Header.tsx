import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Layers,
  Moon,
  Search,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Sun,
  User as UserIcon,
} from "lucide-react";
import { api } from "../../lib/api/client";
import { qk } from "../../lib/query-keys";
import { useAuthStore } from "../../stores/auth-store";
import { useUiStore } from "../../stores/ui-store";
import { Button } from "../ui/Primitives";

export function Header() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");

  const { user, status } = useAuthStore();
  const {
    theme,
    toggleTheme,
    setCartDrawerOpen,
    setChatDrawerOpen,
  } = useUiStore();

  const { data: cart } = useQuery({
    queryKey: qk.cart(),
    queryFn: api.cart.get,
    enabled: status === "authenticated",
  });

  const itemCount =
    cart?.items.reduce((acc, item) => acc + item.quantity, 0) ?? 0;

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    navigate(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/85 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/85">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-indigo-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        Skip to content
      </a>

      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link
            to="/"
            className="flex items-center gap-2.5 text-lg font-extrabold tracking-tight text-slate-900 dark:text-white"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm shadow-indigo-600/30">
              <Layers className="h-5 w-5" />
            </span>
            <span>Commercify</span>
          </Link>

          <nav
            aria-label="Main navigation"
            className="hidden items-center gap-1 md:flex"
          >
            {[
              { to: "/", label: "Home" },
              { to: "/products", label: "Catalog" },
              { to: "/search", label: "Search" },
              ...(status === "authenticated"
                ? [{ to: "/orders", label: "My Orders" }]
                : []),
            ].map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `rounded-xl px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}

            {user?.role === "admin" && (
              <NavLink
                to="/admin/products"
                className={({ isActive }) =>
                  `inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold transition ${
                    isActive
                      ? "bg-violet-100 text-violet-700 dark:bg-violet-950/80 dark:text-violet-300"
                      : "text-violet-600 hover:bg-violet-50 dark:text-violet-400 dark:hover:bg-violet-950/40"
                  }`
                }
              >
                <ShieldCheck className="h-4 w-4" />
                Admin
              </NavLink>
            )}
          </nav>
        </div>

        <form
          onSubmit={handleSearchSubmit}
          className="hidden max-w-xs flex-1 lg:block"
        >
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              aria-label="Quick search products"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search products or meaning…"
              className="w-full rounded-xl border border-slate-200 bg-slate-100/70 py-2 pl-9 pr-3 text-xs text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>
        </form>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setChatDrawerOpen(true)}
            aria-label="Open AI Shopping Assistant"
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-950/70 dark:text-indigo-300 cursor-pointer"
          >
            <Sparkles className="h-4 w-4" />
            <span className="hidden sm:inline">Ask AI</span>
          </button>

          <button
            type="button"
            onClick={() => setCartDrawerOpen(true)}
            aria-label={`Shopping bag with ${itemCount} items`}
            className="relative inline-flex items-center justify-center rounded-xl p-2.5 text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 cursor-pointer"
          >
            <ShoppingBag className="h-5 w-5" />
            {itemCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-indigo-600 px-1 text-[11px] font-bold text-white">
                {itemCount}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle color theme"
            className="rounded-xl p-2.5 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 cursor-pointer"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>

          {status === "authenticated" && user ? (
            <Link
              to="/account"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <UserIcon className="h-3.5 w-3.5 text-indigo-600" />
              <span className="hidden max-w-[130px] truncate sm:inline">
                {user.full_name}
              </span>
            </Link>
          ) : (
            <Button size="sm" onClick={() => navigate("/login")}>
              Sign In
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mt-20 border-t border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
          <div>
            <p className="text-base font-bold text-slate-900 dark:text-white">
              Commercify Storefront
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Powered by FastAPI, PostgreSQL + pgvector, Redis, Elasticsearch &amp;
              OpenAI Tool Calling.
            </p>
          </div>
          <div className="flex flex-wrap gap-6 text-xs font-medium text-slate-500 dark:text-slate-400">
            <Link to="/products" className="hover:text-indigo-600">
              All Products
            </Link>
            <Link to="/search" className="hover:text-indigo-600">
              AI &amp; Keyword Search
            </Link>
            <Link to="/cart" className="hover:text-indigo-600">
              Shopping Bag
            </Link>
            <Link to="/account" className="hover:text-indigo-600">
              Account
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
