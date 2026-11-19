export type UUID = string;
export type Money = string; // Decimal string e.g. "19.99"

export type UserRole = "customer" | "admin";

export interface User {
  id: UUID;
  email: string;
  full_name: string;
  is_active: boolean;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer" | string;
}

export interface Category {
  id: UUID;
  name: string;
  slug: string;
}

export interface ProductListItem {
  id: UUID;
  name: string;
  description?: string | null;
  image_url?: string | null;
  price: Money;
  stock_quantity: number;
  category?: Category;
}

export interface Product {
  id: UUID;
  name: string;
  description: string | null;
  image_url?: string | null;
  price: Money;
  stock_quantity: number;
  category: Category;
}

export interface ProductCreate {
  name: string;
  description?: string | null;
  image_url?: string | null;
  price: Money;
  stock_quantity: number;
  category_id: UUID;
}

export interface ProductUpdate {
  name?: string;
  description?: string | null;
  image_url?: string | null;
  price?: Money;
  stock_quantity?: number;
  category_id?: UUID;
}

export interface CartItem {
  id: UUID;
  product_id: UUID;
  product_name: string;
  unit_price: Money;
  quantity: number;
  subtotal: Money;
}

export interface Cart {
  id: UUID;
  items: CartItem[];
  total: Money;
}

export interface OrderItem {
  product_id: UUID;
  product_name: string;
  unit_price: Money;
  quantity: number;
}

export type OrderStatus = "pending" | "confirmed" | "canceled";

export interface Order {
  id: UUID;
  status: OrderStatus;
  total_amount: Money;
  items: OrderItem[];
}

export interface SearchResult {
  id: UUID;
  name: string;
  description: string | null;
  image_url?: string | null;
  category_name: string;
  price: Money;
  stock_quantity: number;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
  limit?: number;
  offset?: number;
}

export interface ChatResponse {
  reply: string;
}

export interface ChatMessage {
  id: UUID;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

export interface HealthResponse {
  status: "ok" | "degraded" | string;
  database: "up" | "down" | string;
}

export interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiErrorBody {
  detail?: string | ValidationIssue[];
}

