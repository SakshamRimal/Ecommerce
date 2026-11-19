import { API_BASE } from "../env";
import { useAuthStore } from "../../stores/auth-store";
import { DEMO_USERS, demoBackend } from "./demo-data";
import type {
  ApiErrorBody,
  Cart,
  Category,
  ChatHistoryResponse,
  ChatResponse,
  HealthResponse,
  Order,
  Product,
  ProductCreate,
  ProductListItem,
  ProductUpdate,
  SearchResponse,
  TokenResponse,
  User,
  ValidationIssue,
} from "./types";

export class ApiError extends Error {
  public status: number;
  public detail: string;
  public issues: ValidationIssue[];
  public requestId?: string | null;

  constructor(
    status: number,
    body?: ApiErrorBody | null,
    requestId?: string | null,
  ) {
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : Array.isArray(body?.detail) && body.detail.length > 0
          ? body.detail.map((i) => i.msg).join(", ")
          : status === 401
            ? "Unauthorized — please sign in"
            : status === 403
              ? "You do not have permission to perform this action"
              : status === 404
                ? "Requested resource was not found"
                : status === 429
                  ? "Too many requests — please wait a moment and try again"
                  : "Something went wrong. Please try again.";
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.issues = Array.isArray(body?.detail) ? body.detail : [];
    this.requestId = requestId;
  }
}

export function fieldErrors(err: unknown): Record<string, string> {
  if (!(err instanceof ApiError)) return {};
  return Object.fromEntries(
    err.issues.map((issue) => [String(issue.loc.at(-1)), issue.msg]),
  );
}

let refreshPromise: Promise<TokenResponse> | null = null;

async function performRefresh(): Promise<TokenResponse> {
  const { refreshToken, setTokens, clearAuth } = useAuthStore.getState();
  if (!refreshToken) {
    clearAuth();
    throw new ApiError(401, { detail: "Session expired" });
  }

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    clearAuth();
    let body: ApiErrorBody | null = null;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, body, res.headers.get("X-Request-ID"));
  }

  const tokens = (await res.json()) as TokenResponse;
  setTokens(tokens.access_token, tokens.refresh_token);
  return tokens;
}

export function refreshSingleFlight(): Promise<TokenResponse> {
  refreshPromise ??= performRefresh().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  formEncoded?: boolean;
  skipAuthRetry?: boolean;
}

async function wrapDemoCall<T>(fn: () => T): Promise<T> {
  try {
    return fn();
  } catch (err) {
    if (err && typeof err === "object" && "status" in err) {
      const e = err as { status: number; detail?: string };
      throw new ApiError(e.status, { detail: e.detail ?? "Demo error" });
    }
    throw err;
  }
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    body,
    formEncoded = false,
    skipAuthRetry = false,
    headers: customHeaders,
    ...rest
  } = options;

  const { accessToken } = useAuthStore.getState();
  const headers = new Headers(customHeaders);

  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let serializedBody: BodyInit | undefined;
  if (body !== undefined) {
    if (formEncoded && body instanceof URLSearchParams) {
      headers.set("Content-Type", "application/x-www-form-urlencoded");
      serializedBody = body.toString();
    } else if (body instanceof URLSearchParams) {
      headers.set("Content-Type", "application/x-www-form-urlencoded");
      serializedBody = body.toString();
    } else {
      headers.set("Content-Type", "application/json");
      serializedBody = JSON.stringify(body);
    }
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      headers,
      body: serializedBody,
    });
  } catch {
    throw new ApiError(0, {
      detail:
        "Unable to reach the backend server. Check that FastAPI is running on port 8000 or enable Demo Mode.",
    });
  }

  const isAuthEndpoint =
    path.startsWith("/auth/login") ||
    path.startsWith("/auth/register") ||
    path.startsWith("/auth/refresh");

  if (res.status === 401 && !skipAuthRetry && !isAuthEndpoint) {
    try {
      const newTokens = await refreshSingleFlight();
      headers.set("Authorization", `Bearer ${newTokens.access_token}`);
      res = await fetch(`${API_BASE}${path}`, {
        ...rest,
        headers,
        body: serializedBody,
      });
    } catch (refreshErr) {
      throw refreshErr instanceof ApiError
        ? refreshErr
        : new ApiError(401, { detail: "Session expired — please sign in again." });
    }
  }

  if (res.status === 204) {
    return undefined as T;
  }

  let parsed: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = { detail: text };
    }
  }

  if (!res.ok) {
    throw new ApiError(
      res.status,
      (parsed ?? {}) as ApiErrorBody,
      res.headers.get("X-Request-ID"),
    );
  }

  return parsed as T;
}

function isDemo(): boolean {
  return useAuthStore.getState().demoMode;
}

export const api = {
  health: {
    check: async (): Promise<HealthResponse> => {
      if (isDemo()) {
        return { status: "ok", database: "up" };
      }
      return request<HealthResponse>("/health");
    },
  },

  auth: {
    register: async (payload: {
      email: string;
      password: string;
      full_name: string;
    }): Promise<User> => {
      useAuthStore.getState().setDemoMode(false);
      return request<User>("/auth/register", {
        method: "POST",
        body: payload,
      });
    },

    login: async (email: string, password: string): Promise<TokenResponse> => {
      useAuthStore.getState().setDemoMode(false);
      const form = new URLSearchParams({
        username: email,
        password,
      });
      return request<TokenResponse>("/auth/login", {
        method: "POST",
        body: form,
        formEncoded: true,
      });
    },

    refresh: async (refresh_token: string): Promise<TokenResponse> => {
      if (isDemo()) {
        return {
          access_token: "demo-access-refreshed",
          refresh_token: "demo-refresh-refreshed",
          token_type: "bearer",
        };
      }
      return request<TokenResponse>("/auth/refresh", {
        method: "POST",
        body: { refresh_token },
        skipAuthRetry: true,
      });
    },

    logout: async (refresh_token?: string | null): Promise<{ detail: string }> => {
      if (isDemo()) {
        return { detail: "Logged out" };
      }
      return request<{ detail: string }>("/auth/logout", {
        method: "POST",
        body: { refresh_token: refresh_token ?? null },
        skipAuthRetry: true,
      });
    },

    me: async (): Promise<User> => {
      if (isDemo()) {
        const current = useAuthStore.getState().user;
        return current ?? DEMO_USERS.customer;
      }
      return request<User>("/auth/me");
    },
  },

  products: {
    list: async (params?: {
      limit?: number;
      offset?: number;
      category_id?: string;
    }): Promise<ProductListItem[]> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.listProducts(params ?? {}));
      }
      const qs = new URLSearchParams();
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      if (params?.offset !== undefined) qs.set("offset", String(params.offset));
      if (params?.category_id) qs.set("category_id", params.category_id);
      const suffix = qs.toString() ? `?${qs.toString()}` : "";
      return request<ProductListItem[]>(`/products${suffix}`);
    },

    get: async (id: string): Promise<Product> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.getProduct(id));
      }
      return request<Product>(`/products/${id}`);
    },

    create: async (payload: ProductCreate): Promise<Product> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.createProduct(payload));
      }
      return request<Product>("/products", {
        method: "POST",
        body: payload,
      });
    },

    update: async (id: string, payload: ProductUpdate): Promise<Product> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.updateProduct(id, payload));
      }
      return request<Product>(`/products/${id}`, {
        method: "PATCH",
        body: payload,
      });
    },

    delete: async (id: string): Promise<void> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.deleteProduct(id));
      }
      return request<void>(`/products/${id}`, {
        method: "DELETE",
      });
    },
  },

  categories: {
    list: async (params?: {
      limit?: number;
      offset?: number;
    }): Promise<Category[]> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.listCategories());
      }
      const qs = new URLSearchParams();
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      if (params?.offset !== undefined) qs.set("offset", String(params.offset));
      const suffix = qs.toString() ? `?${qs.toString()}` : "";
      return request<Category[]>(`/categories${suffix}`);
    },

    get: async (id: string): Promise<Category> => {
      if (isDemo()) {
        return wrapDemoCall(() => {
          const cat = demoBackend.getCategory(id);
          if (!cat) throw { status: 404, detail: "Category not found" };
          return cat;
        });
      }
      return request<Category>(`/categories/${id}`);
    },

    create: async (payload: { name: string }): Promise<Category> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.createCategory(payload.name));
      }
      return request<Category>("/categories", {
        method: "POST",
        body: payload,
      });
    },

    update: async (id: string, payload: { name: string }): Promise<Category> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.updateCategory(id, payload.name));
      }
      return request<Category>(`/categories/${id}`, {
        method: "PATCH",
        body: payload,
      });
    },

    delete: async (id: string): Promise<void> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.deleteCategory(id));
      }
      return request<void>(`/categories/${id}`, {
        method: "DELETE",
      });
    },
  },

  cart: {
    get: async (): Promise<Cart> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.getCart());
      }
      return request<Cart>("/cart");
    },

    addItem: async (payload: {
      product_id: string;
      quantity: number;
    }): Promise<Cart> => {
      if (isDemo()) {
        return wrapDemoCall(() =>
          demoBackend.addCartItem(payload.product_id, payload.quantity),
        );
      }
      return request<Cart>("/cart/items", {
        method: "POST",
        body: payload,
      });
    },

    updateItem: async (
      product_id: string,
      payload: { quantity: number },
    ): Promise<Cart> => {
      if (isDemo()) {
        return wrapDemoCall(() =>
          demoBackend.updateCartItem(product_id, payload.quantity),
        );
      }
      return request<Cart>(`/cart/items/${product_id}`, {
        method: "PATCH",
        body: payload,
      });
    },

    removeItem: async (product_id: string): Promise<Cart> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.removeCartItem(product_id));
      }
      return request<Cart>(`/cart/items/${product_id}`, {
        method: "DELETE",
      });
    },

    clear: async (): Promise<Cart> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.clearCart());
      }
      return request<Cart>("/cart", {
        method: "DELETE",
      });
    },
  },

  orders: {
    create: async (payload: { idempotency_key: string }): Promise<Order> => {
      if (isDemo()) {
        return wrapDemoCall(() =>
          demoBackend.createOrder(payload.idempotency_key),
        );
      }
      return request<Order>("/orders", {
        method: "POST",
        body: payload,
      });
    },

    list: async (params?: {
      limit?: number;
      offset?: number;
    }): Promise<Order[]> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.listOrders());
      }
      const qs = new URLSearchParams();
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      if (params?.offset !== undefined) qs.set("offset", String(params.offset));
      const suffix = qs.toString() ? `?${qs.toString()}` : "";
      return request<Order[]>(`/orders${suffix}`);
    },

    get: async (id: string): Promise<Order> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.getOrder(id));
      }
      return request<Order>(`/orders/${id}`);
    },

    cancel: async (id: string): Promise<Order> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.cancelOrder(id));
      }
      return request<Order>(`/orders/${id}/cancel`, {
        method: "POST",
      });
    },
  },

  search: {
    products: async (
      params: {
        q: string;
        limit?: number;
        offset?: number;
        min_price?: string;
        max_price?: string;
        category_id?: string;
      },
      signal?: AbortSignal,
    ): Promise<SearchResponse> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.searchProducts(params));
      }
      const qs = new URLSearchParams({ q: params.q });
      if (params.limit !== undefined) qs.set("limit", String(params.limit));
      if (params.offset !== undefined) qs.set("offset", String(params.offset));
      if (params.min_price) qs.set("min_price", params.min_price);
      if (params.max_price) qs.set("max_price", params.max_price);
      if (params.category_id) qs.set("category_id", params.category_id);
      return request<SearchResponse>(`/search/products?${qs.toString()}`, {
        signal,
      });
    },

    semantic: async (
      params: {
        q: string;
        limit?: number;
        offset?: number;
        min_price?: string;
        max_price?: string;
        category_id?: string;
      },
      signal?: AbortSignal,
    ): Promise<ProductListItem[]> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.semanticSearch(params));
      }
      const qs = new URLSearchParams({ q: params.q });
      if (params.limit !== undefined) qs.set("limit", String(params.limit));
      if (params.offset !== undefined) qs.set("offset", String(params.offset));
      if (params.min_price) qs.set("min_price", params.min_price);
      if (params.max_price) qs.set("max_price", params.max_price);
      if (params.category_id) qs.set("category_id", params.category_id);
      return request<ProductListItem[]>(
        `/search/products/semantic?${qs.toString()}`,
        { signal },
      );
    },
  },

  chat: {
    send: async (
      message: string,
      signal?: AbortSignal,
    ): Promise<ChatResponse> => {
      if (isDemo()) {
        return wrapDemoCall(() => demoBackend.chat(message));
      }
      return request<ChatResponse>("/chat", {
        method: "POST",
        body: { message },
        signal,
      });
    },

    history: async (limit = 50): Promise<ChatHistoryResponse> => {
      if (isDemo()) {
        return wrapDemoCall(() => ({ messages: demoBackend.chatHistory() }));
      }
      return request<ChatHistoryResponse>(`/chat/history?limit=${limit}`);
    },

    clearHistory: async (): Promise<void> => {
      if (isDemo()) {
        return;
      }
      return request<void>("/chat/history", {
        method: "DELETE",
      });
    },
  },
};

