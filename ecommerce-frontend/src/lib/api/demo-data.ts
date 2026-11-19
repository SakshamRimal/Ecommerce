import { multiplyMoney, parseCents, sumMoney } from "../money";
import type {
  Cart,
  Category,
  ChatMessage,
  Order,
  Product,
  ProductCreate,
  ProductUpdate,
  SearchResponse,
  User,
} from "./types";

const CAT_AUDIO = "11111111-1111-4111-8111-111111111101";
const CAT_OUTDOOR = "11111111-1111-4111-8111-111111111102";
const CAT_COFFEE = "11111111-1111-4111-8111-111111111103";
const CAT_DESK = "11111111-1111-4111-8111-111111111104";

let demoCategories: Category[] = [
  { id: CAT_AUDIO, name: "Audio & Acoustics", slug: "audio-acoustics" },
  { id: CAT_OUTDOOR, name: "Trail & Outdoor", slug: "trail-outdoor" },
  { id: CAT_COFFEE, name: "Specialty Coffee", slug: "specialty-coffee" },
  { id: CAT_DESK, name: "Workspace & Desk", slug: "workspace-desk" },
];

let demoProducts: Product[] = [
  {
    id: "22222222-2222-4222-8222-222222222201",
    name: "Aether Studio Wireless Headphones",
    description:
      "Reference-grade planar magnetic wireless headphones with adaptive hybrid ANC, 48-hour battery life, and CNC-machined anodized aluminum earcups.",
    image_url:
      "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
    price: "349.00",
    stock_quantity: 14,
    category: demoCategories[0],
  },
  {
    id: "22222222-2222-4222-8222-222222222202",
    name: "Apex GTX Alpine Trail Runner",
    description:
      "Ultralight waterproof trail running shoe engineered with Vibram Megagrip lugs, nitrogen-infused midsole foam, and ripstop ballistic mesh for technical mountain terrain.",
    image_url:
      "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
    price: "168.50",
    stock_quantity: 9,
    category: demoCategories[1],
  },
  {
    id: "22222222-2222-4222-8222-222222222203",
    name: "fellowship Precision Burr Grinder",
    description:
      "64mm flat stainless steel burrs with 41 stepless grind settings, low-retention magnetic catch cup, and whisper-quiet brushless DC motor for pour-over and espresso.",
    image_url:
      "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=900&q=80",
    price: "225.00",
    stock_quantity: 4,
    category: demoCategories[2],
  },
  {
    id: "22222222-2222-4222-8222-222222222204",
    name: "Monolith Mechanical Keybaord 75%",
    description:
      "Gasket-mounted CNC aluminum mechanical keyboard with hot-swappable tactile switches, PBT double-shot keycaps, and QMK/VIA programmable rotary encoder.",
    image_url:
      "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80",
    price: "199.00",
    stock_quantity: 18,
    category: demoCategories[3],
  },
  {
    id: "22222222-2222-4222-8222-222222222205",
    name: "Nordic Titanium Insulated Flask 750ml",
    description:
      "Double-wall vacuum insulated pure grade-1 titanium bottle that keeps beverages ice-cold for 36 hours or piping hot for 18 hours on backcountry expeditions.",
    image_url:
      "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=80",
    price: "64.00",
    stock_quantity: 25,
    category: demoCategories[1],
  },
  {
    id: "22222222-2222-4222-8222-222222222206",
    name: "Artisan Gooseneck Variable Temp Kettle",
    description:
      "Precision pour-over kettle with degree-by-degree PID temperature control, built-in brew stopwatch, and counterbalanced walnut handle.",
    image_url:
      "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=900&q=80",
    price: "145.00",
    stock_quantity: 3,
    category: demoCategories[2],
  },
  {
    id: "22222222-2222-4222-8222-222222222207",
    name: "Lumen Architectural Desk Lamp",
    description:
      "High-CRI 98+ cantilevered LED task bar with ambient bias lighting, touchless gesture dimming, and warm-to-daylight color temperature tuning.",
    image_url:
      "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",
    price: "129.00",
    stock_quantity: 11,
    category: demoCategories[3],
  },
  {
    id: "22222222-2222-4222-8222-222222222208",
    name: "Sonora Nearfield Studio Monitors (Pair)",
    description:
      "Bi-amplified 5-inch Kevlar woofer + silk dome tweeter desktop reference monitors with DSP room correction and balanced TRS/XLR inputs.",
    image_url:
      "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80",
    price: "420.00",
    stock_quantity: 0,
    category: demoCategories[0],
  },
];

let demoCart: Cart = {
  id: "33333333-3333-4333-8333-333333333301",
  items: [],
  total: "0.00",
};

let demoOrders: Order[] = [];

let demoMessages: ChatMessage[] = [
  {
    id: "44444444-4444-4444-8444-444444444401",
    role: "assistant",
    content:
      "Welcome to Commercify! Ask me to search our catalog, compare gear, or check live stock availability.",
    created_at: new Date().toISOString(),
  },
];

export const DEMO_USERS: Record<"customer" | "admin", User> = {
  customer: {
    id: "55555555-5555-4555-8555-555555555501",
    email: "shopper@commercify.dev",
    full_name: "Alex Rivera",
    is_active: true,
    role: "customer",
  },
  admin: {
    id: "55555555-5555-4555-8555-555555555502",
    email: "admin@commercify.dev",
    full_name: "Taylor Vance (Admin)",
    is_active: true,
    role: "admin",
  },
};

function recalcCart(): Cart {
  const items = demoCart.items.map((item) => {
    const prod = demoProducts.find((p) => p.id === item.product_id);
    const unitPrice = prod ? prod.price : item.unit_price;
    const subtotal = multiplyMoney(unitPrice, item.quantity);
    return {
      ...item,
      product_name: prod ? prod.name : item.product_name,
      unit_price: unitPrice,
      subtotal,
    };
  });
  demoCart = {
    ...demoCart,
    items,
    total: sumMoney(items.map((i) => i.subtotal)),
  };
  return demoCart;
}

export const demoBackend = {
  listCategories(): Category[] {
    return [...demoCategories];
  },

  getCategory(id: string): Category | undefined {
    return demoCategories.find((c) => c.id === id);
  },

  createCategory(name: string): Category {
    const slug = name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    if (demoCategories.some((c) => c.slug === slug)) {
      throw { status: 409, detail: `Category with slug '${slug}' already exists` };
    }
    const created: Category = {
      id: crypto.randomUUID(),
      name: name.trim(),
      slug,
    };
    demoCategories = [...demoCategories, created];
    return created;
  },

  updateCategory(id: string, name: string): Category {
    const idx = demoCategories.findIndex((c) => c.id === id);
    if (idx === -1) throw { status: 404, detail: "Category not found" };
    const slug = name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    if (demoCategories.some((c) => c.slug === slug && c.id !== id)) {
      throw { status: 409, detail: `Category with slug '${slug}' already exists` };
    }
    const updated = { ...demoCategories[idx], name: name.trim(), slug };
    demoCategories[idx] = updated;
    demoProducts = demoProducts.map((p) =>
      p.category.id === id ? { ...p, category: updated } : p,
    );
    return updated;
  },

  deleteCategory(id: string): void {
    if (demoProducts.some((p) => p.category.id === id)) {
      throw {
        status: 409,
        detail: "Cannot delete category: it still has products referenced by catalog",
      };
    }
    demoCategories = demoCategories.filter((c) => c.id !== id);
  },

  listProducts(params: {
    limit?: number;
    offset?: number;
    category_id?: string;
  }): Product[] {
    const filtered = params.category_id
      ? demoProducts.filter((p) => p.category.id === params.category_id)
      : demoProducts;
    const offset = params.offset ?? 0;
    const limit = params.limit ?? 20;
    return filtered.slice(offset, offset + limit);
  },

  getProduct(id: string): Product {
    const prod = demoProducts.find((p) => p.id === id);
    if (!prod) throw { status: 404, detail: `Product with id '${id}' not found` };
    return prod;
  },

  createProduct(data: ProductCreate): Product {
    const cat = demoCategories.find((c) => c.id === data.category_id);
    if (!cat) throw { status: 404, detail: "Category not found" };
    const created: Product = {
      id: crypto.randomUUID(),
      name: data.name.trim(),
      description: data.description ?? null,
      image_url: data.image_url ?? null,
      price: data.price,
      stock_quantity: data.stock_quantity,
      category: cat,
    };
    demoProducts = [created, ...demoProducts];
    return created;
  },

  updateProduct(id: string, data: ProductUpdate): Product {
    const idx = demoProducts.findIndex((p) => p.id === id);
    if (idx === -1) throw { status: 404, detail: "Product not found" };
    const existing = demoProducts[idx];
    const cat = data.category_id
      ? demoCategories.find((c) => c.id === data.category_id) ?? existing.category
      : existing.category;
    const updated: Product = {
      ...existing,
      name: data.name !== undefined ? data.name.trim() : existing.name,
      description:
        data.description !== undefined ? data.description : existing.description,
      image_url:
        data.image_url !== undefined ? data.image_url : existing.image_url,
      price: data.price !== undefined ? data.price : existing.price,
      stock_quantity:
        data.stock_quantity !== undefined
          ? data.stock_quantity
          : existing.stock_quantity,
      category: cat,
    };
    demoProducts[idx] = updated;
    return updated;
  },

  deleteProduct(id: string): void {
    if (demoCart.items.some((i) => i.product_id === id)) {
      throw {
        status: 409,
        detail: "Cannot delete product: it is still referenced by a cart or order",
      };
    }
    demoProducts = demoProducts.filter((p) => p.id !== id);
  },

  getCart(): Cart {
    return recalcCart();
  },

  addCartItem(product_id: string, quantity: number): Cart {
    const prod = demoProducts.find((p) => p.id === product_id);
    if (!prod) throw { status: 404, detail: "Product not found" };
    const existing = demoCart.items.find((i) => i.product_id === product_id);
    const nextQty = (existing ? existing.quantity : 0) + quantity;
    if (prod.stock_quantity < nextQty) {
      throw {
        status: 409,
        detail: `Insufficient stock for '${prod.name}' (requested ${nextQty}, available ${prod.stock_quantity})`,
      };
    }
    if (existing) {
      existing.quantity = nextQty;
    } else {
      demoCart.items.push({
        id: crypto.randomUUID(),
        product_id: prod.id,
        product_name: prod.name,
        unit_price: prod.price,
        quantity,
        subtotal: multiplyMoney(prod.price, quantity),
      });
    }
    return recalcCart();
  },

  updateCartItem(product_id: string, quantity: number): Cart {
    const existing = demoCart.items.find((i) => i.product_id === product_id);
    if (!existing) throw { status: 404, detail: "Item not in cart" };
    if (quantity <= 0) {
      demoCart.items = demoCart.items.filter((i) => i.product_id !== product_id);
      return recalcCart();
    }
    const prod = demoProducts.find((p) => p.id === product_id);
    if (prod && prod.stock_quantity < quantity) {
      throw {
        status: 409,
        detail: `Insufficient stock for '${prod.name}' (requested ${quantity}, available ${prod.stock_quantity})`,
      };
    }
    existing.quantity = quantity;
    return recalcCart();
  },

  removeCartItem(product_id: string): Cart {
    demoCart.items = demoCart.items.filter((i) => i.product_id !== product_id);
    return recalcCart();
  },

  clearCart(): Cart {
    demoCart.items = [];
    return recalcCart();
  },

  createOrder(idempotencyKey: string): Order {
    const existing = demoOrders.find(
      (o) => (o as Order & { key?: string }).key === idempotencyKey,
    );
    if (existing) return existing;
    const cart = recalcCart();
    if (cart.items.length === 0) {
      throw { status: 409, detail: "Cart is empty — nothing to order" };
    }
    for (const item of cart.items) {
      const prod = demoProducts.find((p) => p.id === item.product_id);
      if (!prod || prod.stock_quantity < item.quantity) {
        throw {
          status: 409,
          detail: `Insufficient stock for '${item.product_name}'`,
        };
      }
    }
    for (const item of cart.items) {
      const prod = demoProducts.find((p) => p.id === item.product_id);
      if (prod) prod.stock_quantity -= item.quantity;
    }
    const order: Order & { key?: string } = {
      id: crypto.randomUUID(),
      status: "confirmed",
      total_amount: cart.total,
      items: cart.items.map((i) => ({
        product_id: i.product_id,
        product_name: i.product_name,
        unit_price: i.unit_price,
        quantity: i.quantity,
      })),
      key: idempotencyKey,
    };
    demoOrders = [order, ...demoOrders];
    demoCart.items = [];
    recalcCart();
    return order;
  },

  listOrders(): Order[] {
    return [...demoOrders];
  },

  getOrder(id: string): Order {
    const order = demoOrders.find((o) => o.id === id);
    if (!order) throw { status: 404, detail: `Order with id '${id}' not found` };
    return order;
  },

  cancelOrder(id: string): Order {
    const order = demoOrders.find((o) => o.id === id);
    if (!order) throw { status: 404, detail: `Order with id '${id}' not found` };
    if (order.status === "canceled") {
      throw { status: 409, detail: "Order is already canceled" };
    }
    for (const item of order.items) {
      const prod = demoProducts.find((p) => p.id === item.product_id);
      if (prod) prod.stock_quantity += item.quantity;
    }
    order.status = "canceled";
    return { ...order };
  },

  searchProducts(params: {
    q: string;
    limit?: number;
    offset?: number;
    min_price?: string;
    max_price?: string;
    category_id?: string;
  }): SearchResponse {
    const tokens = params.q
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);
    const minCents = params.min_price ? parseCents(params.min_price) : null;
    const maxCents = params.max_price ? parseCents(params.max_price) : null;

    const matched = demoProducts
      .filter((p) => {
        if (params.category_id && p.category.id !== params.category_id) return false;
        const cents = parseCents(p.price);
        if (minCents !== null && cents < minCents) return false;
        if (maxCents !== null && cents > maxCents) return false;
        const hay = `${p.name} ${p.description ?? ""} ${p.category.name}`.toLowerCase();
        return tokens.every((t) => hay.includes(t)) || hay.includes(params.q.toLowerCase());
      })
      .map((p, idx) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        category_name: p.category.name,
        price: p.price,
        stock_quantity: p.stock_quantity,
        score: Number((4.8 - idx * 0.35).toFixed(2)),
      }));

    return {
      query: params.q,
      total: matched.length,
      results: matched.slice(params.offset ?? 0, (params.offset ?? 0) + (params.limit ?? 20)),
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
    };
  },

  semanticSearch(params: {
    q: string;
    limit?: number;
    offset?: number;
    min_price?: string;
    max_price?: string;
    category_id?: string;
  }): Product[] {
    const minCents = params.min_price ? parseCents(params.min_price) : null;
    const maxCents = params.max_price ? parseCents(params.max_price) : null;
    const qLower = params.q.toLowerCase();

    return demoProducts
      .filter((p) => {
        if (params.category_id && p.category.id !== params.category_id) return false;
        const cents = parseCents(p.price);
        if (minCents !== null && cents < minCents) return false;
        if (maxCents !== null && cents > maxCents) return false;
        return true;
      })
      .sort((a, b) => {
        const aText = `${a.name} ${a.description ?? ""} ${a.category.name}`.toLowerCase();
        const bText = `${b.name} ${b.description ?? ""} ${b.category.name}`.toLowerCase();
        const aScore = qLower
          .split(/\s+/)
          .reduce((acc, w) => acc + (aText.includes(w) ? 2 : 0), 0);
        const bScore = qLower
          .split(/\s+/)
          .reduce((acc, w) => acc + (bText.includes(w) ? 2 : 0), 0);
        return bScore - aScore;
      })
      .slice(params.offset ?? 0, (params.offset ?? 0) + (params.limit ?? 10));
  },

  chat(message: string): { reply: string } {
    const q = message.toLowerCase();
    const matches = demoProducts.filter((p) => {
      const text = `${p.name} ${p.description ?? ""} ${p.category.name}`.toLowerCase();
      return q
        .split(/\s+/)
        .filter((w) => w.length > 3)
        .some((w) => text.includes(w));
    });
    const top = (matches.length > 0 ? matches : demoProducts.slice(0, 3)).slice(0, 3);
    const summary = top
      .map(
        (p) =>
          `• **${p.name}** ($${p.price}) — ${
            p.stock_quantity > 0 ? `${p.stock_quantity} in stock` : "currently out of stock"
          }`,
      )
      .join("\n");
    const reply = `Based on our live catalog, here are the best matches:\n\n${summary}\n\nWould you like full specs on any of these or help checking stock?`;

    demoMessages = [
      ...demoMessages,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      },
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: reply,
        created_at: new Date().toISOString(),
      },
    ];
    return { reply };
  },

  chatHistory(): ChatMessage[] {
    return [...demoMessages];
  },
};

