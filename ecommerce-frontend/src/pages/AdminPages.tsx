import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Edit3,
  FolderPlus,
  Layers,
  Lock,
  PackagePlus,
  Plus,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Button,
  EmptyState,
  Input,
  Price,
  StockBadge,
} from "../components/ui/Primitives";
import { api, ApiError, fieldErrors } from "../lib/api/client";
import type { Category, Product } from "../lib/api/types";
import { isValidMoneyInput } from "../lib/money";
import { qk } from "../lib/query-keys";
import { useAuthStore } from "../stores/auth-store";
import { useUiStore } from "../stores/ui-store";

export function AdminConsolePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const user = useAuthStore((s) => s.user);
  const demoMode = useAuthStore((s) => s.demoMode);
  const addToast = useUiStore((s) => s.addToast);

  const activeTab = location.pathname.includes("/categories") ? "categories" : "products";

  // Product Form State
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [showProductForm, setShowProductForm] = useState(false);
  const [prodName, setProdName] = useState("");
  const [prodDesc, setProdDesc] = useState("");
  const [prodPrice, setProdPrice] = useState("");
  const [prodStock, setProdStock] = useState("10");
  const [prodImage, setProdImage] = useState("");
  const [prodCategoryId, setProdCategoryId] = useState("");
  const [prodErrors, setProdErrors] = useState<Record<string, string>>({});

  // Category Form State
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [catName, setCatName] = useState("");
  const [catError, setCatError] = useState<string | null>(null);

  const categoriesQuery = useQuery({
    queryKey: [...qk.categories(), demoMode],
    queryFn: () => api.categories.list(),
    enabled: user?.role === "admin",
  });

  const productsQuery = useQuery({
    queryKey: [...qk.products({ limit: 100, offset: 0 }), demoMode],
    queryFn: () => api.products.list({ limit: 100, offset: 0 }),
    enabled: user?.role === "admin",
  });

  const saveProductMutation = useMutation({
    mutationFn: async () => {
      const resolvedCategoryId =
        prodCategoryId || categoriesQuery.data?.[0]?.id || "";
      const payload = {
        name: prodName.trim(),
        description: prodDesc.trim() || null,
        price: prodPrice.trim(),
        stock_quantity: Number.parseInt(prodStock, 10) || 0,
        image_url: prodImage.trim() || null,
        category_id: resolvedCategoryId,
      };
      if (editingProduct) {
        return api.products.update(editingProduct.id, payload);
      }
      return api.products.create(payload);
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.setQueryData(qk.product(saved.id), saved);
      addToast({
        title: editingProduct ? "Product updated" : "Product created",
        description: `${saved.name} saved to catalog.`,
        tone: "success",
      });
      resetProductForm();
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setProdErrors(fieldErrors(err));
      } else {
        addToast({
          title: "Could not save product",
          description: err instanceof ApiError ? err.detail : "Please check inputs.",
          tone: "error",
        });
      }
    },
  });

  const deleteProductMutation = useMutation({
    mutationFn: (id: string) => api.products.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      addToast({ title: "Product deleted", tone: "info" });
    },
  });

  const saveCategoryMutation = useMutation({
    mutationFn: async () => {
      if (editingCategory) {
        return api.categories.update(editingCategory.id, { name: catName.trim() });
      }
      return api.categories.create({ name: catName.trim() });
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: qk.categories() });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      addToast({
        title: editingCategory ? "Category renamed" : "Category created",
        description: `${saved.name} (#${saved.slug})`,
        tone: "success",
      });
      setEditingCategory(null);
      setCatName("");
      setCatError(null);
    },
    onError: (err) => {
      setCatError(err instanceof ApiError ? err.detail : "Could not save category.");
    },
  });

  const deleteCategoryMutation = useMutation({
    mutationFn: (id: string) => api.categories.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.categories() });
      addToast({ title: "Category deleted", tone: "info" });
    },
  });

  // Role Guard
  if (!user) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <EmptyState
          icon={<Lock className="h-6 w-6" />}
          title="Administrator Sign-In Required"
          description="Sign in with an admin account or enable Demo Mode in the header to manage catalog products and categories."
          action={<Button onClick={() => navigate("/login?next=/admin/products")}>Sign In</Button>}
        />
      </div>
    );
  }

  if (user.role !== "admin") {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <EmptyState
          icon={<ShieldAlert className="h-6 w-6 text-rose-500" />}
          title="403 — Administrator Access Required"
          description="Your account is signed in with the customer role. Only administrators can create, update, or delete products and categories."
          action={<Button onClick={() => navigate("/")}>Return to Storefront</Button>}
        />
      </div>
    );
  }

  const resetProductForm = () => {
    setEditingProduct(null);
    setShowProductForm(false);
    setProdName("");
    setProdDesc("");
    setProdPrice("");
    setProdStock("10");
    setProdImage("");
    setProdCategoryId("");
    setProdErrors({});
  };

  const startEditProduct = async (productId: string) => {
    const full = await api.products.get(productId);
    setEditingProduct(full);
    setProdName(full.name);
    setProdDesc(full.description ?? "");
    setProdPrice(full.price);
    setProdStock(String(full.stock_quantity));
    setProdImage(full.image_url ?? "");
    setProdCategoryId(full.category?.id ?? "");
    setProdErrors({});
    setShowProductForm(true);
  };

  const handleProductSubmit = (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!prodName.trim()) errs.name = "Product name is required.";
    if (!isValidMoneyInput(prodPrice.trim()) || Number(prodPrice) <= 0) {
      errs.price = "Enter a valid positive decimal price (e.g. 49.99).";
    }
    const parsedStock = Number.parseInt(prodStock, 10);
    if (Number.isNaN(parsedStock) || parsedStock < 0) {
      errs.stock = "Stock must be a non-negative integer.";
    }
    if (Object.keys(errs).length > 0) {
      setProdErrors(errs);
      return;
    }
    saveProductMutation.mutate();
  };

  const handleCategorySubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!catName.trim()) {
      setCatError("Category name is required.");
      return;
    }
    saveCategoryMutation.mutate();
  };

  const categories = categoriesQuery.data ?? [];
  const products = productsQuery.data ?? [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Header & Tabs */}
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[var(--border)] pb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--primary)]">
            Backoffice Management
          </span>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-[var(--fg)]">
            Admin Catalog Console
          </h1>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--muted)] p-1">
          <Link
            to="/admin/products"
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition ${
              activeTab === "products"
                ? "bg-[var(--card)] text-[var(--fg)] shadow-xs"
                : "text-[var(--muted-fg)] hover:text-[var(--fg)]"
            }`}
          >
            Products ({products.length})
          </Link>
          <Link
            to="/admin/categories"
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition ${
              activeTab === "categories"
                ? "bg-[var(--card)] text-[var(--fg)] shadow-xs"
                : "text-[var(--muted-fg)] hover:text-[var(--fg)]"
            }`}
          >
            Categories ({categories.length})
          </Link>
        </div>
      </div>

      {/* PRODUCTS TAB */}
      {activeTab === "products" && (
        <div className="mt-8 space-y-8">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[var(--muted-fg)]">
              Create, update, or remove products. Prices are transmitted as exact decimal strings.
            </p>
            {!showProductForm && (
              <Button onClick={() => setShowProductForm(true)}>
                <Plus className="h-4 w-4" />
                New Product
              </Button>
            )}
          </div>

          {showProductForm && (
            <form
              onSubmit={handleProductSubmit}
              className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-sm sm:p-8"
            >
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
                <h2 className="flex items-center gap-2 text-lg font-bold text-[var(--fg)]">
                  <PackagePlus className="h-5 w-5 text-[var(--primary)]" />
                  {editingProduct ? `Edit Product: ${editingProduct.name}` : "Create New Product"}
                </h2>
                <Button type="button" variant="ghost" size="sm" onClick={resetProductForm}>
                  Cancel
                </Button>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <Input
                  label="Product Name"
                  required
                  value={prodName}
                  onChange={(e) => setProdName(e.target.value)}
                  error={prodErrors.name}
                  placeholder="Aether ANC Studio Headphones"
                />

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-[var(--fg)]">
                    Category
                  </label>
                  <select
                    value={prodCategoryId}
                    onChange={(e) => setProdCategoryId(e.target.value)}
                    className="h-10 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3.5 text-sm text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
                  >
                    <option value="">Select Category</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Price (USD Decimal)"
                  required
                  inputMode="decimal"
                  value={prodPrice}
                  onChange={(e) => setProdPrice(e.target.value)}
                  error={prodErrors.price}
                  placeholder="249.00"
                />

                <Input
                  label="Inventory Stock"
                  required
                  type="number"
                  min={0}
                  value={prodStock}
                  onChange={(e) => setProdStock(e.target.value)}
                  error={prodErrors.stock}
                />

                <div className="sm:col-span-2">
                  <Input
                    label="Image URL (Optional)"
                    type="url"
                    value={prodImage}
                    onChange={(e) => setProdImage(e.target.value)}
                    placeholder="https://images.unsplash.com/..."
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-[var(--fg)]">
                    Description
                  </label>
                  <textarea
                    rows={3}
                    value={prodDesc}
                    onChange={(e) => setProdDesc(e.target.value)}
                    placeholder="Detailed product features, materials, and specifications..."
                    className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] p-3.5 text-sm text-[var(--fg)] focus:border-[var(--primary)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={resetProductForm}>
                  Discard
                </Button>
                <Button type="submit" loading={saveProductMutation.isPending}>
                  {editingProduct ? "Save Changes" : "Publish Product"}
                </Button>
              </div>
            </form>
          )}

          {/* Products Table */}
          <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)] shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-[var(--border)] bg-[var(--muted)]/60 text-xs font-semibold uppercase tracking-wider text-[var(--muted-fg)]">
                  <tr>
                    <th className="px-5 py-3.5">Product</th>
                    <th className="px-5 py-3.5">Category</th>
                    <th className="px-5 py-3.5">Price</th>
                    <th className="px-5 py-3.5">Stock</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {products.map((p) => (
                    <tr key={p.id} className="hover:bg-[var(--muted)]/30">
                      <td className="px-5 py-4 font-semibold text-[var(--fg)]">
                        <Link to={`/products/${p.id}`} className="hover:text-[var(--primary)]">
                          {p.name}
                        </Link>
                      </td>
                      <td className="px-5 py-4 text-xs text-[var(--muted-fg)]">
                        {p.category?.name ?? "—"}
                      </td>
                      <td className="px-5 py-4">
                        <Price amount={p.price} className="font-bold text-[var(--fg)]" />
                      </td>
                      <td className="px-5 py-4">
                        <StockBadge stock={p.stock_quantity} />
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="inline-flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => startEditProduct(p.id)}
                            className="rounded-lg p-2 text-[var(--muted-fg)] hover:bg-[var(--muted)] hover:text-[var(--fg)]"
                            aria-label={`Edit ${p.name}`}
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteProductMutation.mutate(p.id)}
                            className="rounded-lg p-2 text-[var(--muted-fg)] hover:bg-rose-500/10 hover:text-rose-600"
                            aria-label={`Delete ${p.name}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* CATEGORIES TAB */}
      {activeTab === "categories" && (
        <div className="mt-8 grid gap-8 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <form
              onSubmit={handleCategorySubmit}
              className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-xs"
            >
              <h2 className="flex items-center gap-2 text-lg font-bold text-[var(--fg)]">
                <FolderPlus className="h-5 w-5 text-[var(--primary)]" />
                {editingCategory ? `Rename "${editingCategory.name}"` : "Create Category"}
              </h2>
              <p className="mt-1 text-xs text-[var(--muted-fg)]">
                URL slugs are generated and updated automatically by the backend.
              </p>

              <div className="mt-5">
                <Input
                  label="Category Name"
                  required
                  value={catName}
                  onChange={(e) => setCatName(e.target.value)}
                  error={catError ?? undefined}
                  placeholder="Audio & Studio"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2">
                {editingCategory && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setEditingCategory(null);
                      setCatName("");
                      setCatError(null);
                    }}
                  >
                    Cancel
                  </Button>
                )}
                <Button type="submit" loading={saveCategoryMutation.isPending}>
                  {editingCategory ? "Rename Category" : "Create Category"}
                </Button>
              </div>
            </form>
          </div>

          <div className="lg:col-span-7">
            <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)] shadow-xs">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-[var(--border)] bg-[var(--muted)]/60 text-xs font-semibold uppercase tracking-wider text-[var(--muted-fg)]">
                  <tr>
                    <th className="px-5 py-3.5">Name</th>
                    <th className="px-5 py-3.5">Generated Slug</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {categories.map((c) => (
                    <tr key={c.id} className="hover:bg-[var(--muted)]/30">
                      <td className="px-5 py-4 font-semibold text-[var(--fg)]">
                        <span className="inline-flex items-center gap-2">
                          <Layers className="h-4 w-4 text-[var(--primary)]" />
                          {c.name}
                        </span>
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-[var(--muted-fg)]">
                        #{c.slug}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="inline-flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => {
                              setEditingCategory(c);
                              setCatName(c.name);
                              setCatError(null);
                            }}
                            className="rounded-lg p-2 text-[var(--muted-fg)] hover:bg-[var(--muted)] hover:text-[var(--fg)]"
                            aria-label={`Rename ${c.name}`}
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteCategoryMutation.mutate(c.id)}
                            className="rounded-lg p-2 text-[var(--muted-fg)] hover:bg-rose-500/10 hover:text-rose-600"
                            aria-label={`Delete ${c.name}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
