export const qk = {
  health: () => ["health"] as const,
  me: () => ["me"] as const,
  products: (params: {
    limit?: number;
    offset?: number;
    categoryId?: string;
  }) =>
    [
      "products",
      {
        limit: params.limit ?? 24,
        offset: params.offset ?? 0,
        categoryId: params.categoryId || undefined,
      },
    ] as const,
  product: (id: string) => ["product", id] as const,
  categories: () => ["categories"] as const,
  category: (id: string) => ["category", id] as const,
  cart: () => ["cart"] as const,
  orders: (params?: { limit?: number; offset?: number }) =>
    ["orders", { limit: params?.limit ?? 20, offset: params?.offset ?? 0 }] as const,
  order: (id: string) => ["order", id] as const,
  search: (params: {
    q: string;
    mode?: "keyword" | "semantic";
    limit?: number;
    offset?: number;
    minPrice?: string;
    maxPrice?: string;
    categoryId?: string;
  }) =>
    [
      "search",
      {
        q: params.q.trim(),
        mode: params.mode ?? "keyword",
        limit: params.limit ?? 24,
        offset: params.offset ?? 0,
        minPrice: params.minPrice || undefined,
        maxPrice: params.maxPrice || undefined,
        categoryId: params.categoryId || undefined,
      },
    ] as const,
  chatHistory: () => ["chat-history"] as const,
};

