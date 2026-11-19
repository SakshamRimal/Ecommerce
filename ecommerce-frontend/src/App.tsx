import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Compass } from "lucide-react";
import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { CartDrawer } from "./components/cart/CartDrawer";
import { AssistantDrawer } from "./components/chat/AssistantDrawer";
import { Footer, Header } from "./components/layout/Header";
import { Button, EmptyState, ToastViewport } from "./components/ui/Primitives";
import { api } from "./lib/api/client";
import { AdminConsolePage } from "./pages/AdminPages";
import { AccountPage, LoginPage, RegisterPage } from "./pages/AuthPages";
import { CartPage } from "./pages/CartPage";
import { CheckoutPage } from "./pages/CheckoutPage";
import { HomePage } from "./pages/HomePage";
import { OrderDetailPage, OrdersPage } from "./pages/OrdersPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { ProductsPage } from "./pages/ProductsPage";
import { SearchPage } from "./pages/SearchPage";
import { useAuthStore } from "./stores/auth-store";
import { useUiStore } from "./stores/ui-store";

const defaultQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [pathname]);
  return null;
}

function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <div className="mx-auto max-w-2xl px-4 py-20 sm:px-6">
      <EmptyState
        icon={<Compass className="h-6 w-6" />}
        title="404 — Page Not Found"
        description="The page you're looking for doesn't exist or has moved."
        action={<Button onClick={() => navigate("/")}>Back to Home</Button>}
      />
    </div>
  );
}

export function AppRoutes() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const demoMode = useAuthStore((s) => s.demoMode);
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  // Sync theme on initial mount
  useEffect(() => {
    setTheme(theme);
  }, [theme, setTheme]);

  // Bootstrap authenticated user session if token exists
  useEffect(() => {
    if (demoMode) return;
    if (!accessToken && !refreshToken) {
      setUser(null);
      return;
    }
    let active = true;
    api.auth
      .me()
      .then((me) => {
        if (active) setUser(me);
      })
      .catch(() => {
        if (active) clearAuth();
      });
    return () => {
      active = false;
    };
  }, [accessToken, refreshToken, demoMode, setUser, clearAuth]);

  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg)] text-[var(--fg)]">
      <ScrollToTop />
      <Header />
      <main id="main-content" className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:productId" element={<ProductDetailPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/:orderId" element={<OrderDetailPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/admin/products" element={<AdminConsolePage />} />
          <Route path="/admin/categories" element={<AdminConsolePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
      <CartDrawer />
      <AssistantDrawer />
      <ToastViewport />
    </div>
  );
}

export function App() {
  return (
    <QueryClientProvider client={defaultQueryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
