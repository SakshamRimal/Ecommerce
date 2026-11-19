import { create } from "zustand";
import type { Order } from "../lib/api/types";

export interface ToastItem {
  id: string;
  tone: "success" | "error" | "info";
  title: string;
  description?: string;
}

export type ToastInput = {
  title: string;
  description?: string;
  tone?: "success" | "error" | "info";
  variant?: "success" | "error" | "info";
};

interface UiState {
  cartDrawerOpen: boolean;
  chatDrawerOpen: boolean;
  chatPrompt: string | null;
  mobileNavOpen: boolean;
  theme: "light" | "dark";
  toasts: ToastItem[];
  lastOrder: Order | null;
  setCartDrawerOpen: (open: boolean) => void;
  setChatDrawerOpen: (open: boolean) => void;
  openChatWithPrompt: (prompt?: string) => void;
  clearChatPrompt: () => void;
  setMobileNavOpen: (open: boolean) => void;
  setTheme: (theme: "light" | "dark") => void;
  toggleTheme: () => void;
  addToast: (toast: ToastInput) => void;
  removeToast: (id: string) => void;
  setLastOrder: (order: Order | null) => void;
}

function getInitialTheme(): "light" | "dark" {
  try {
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem("commercify_theme");
      if (saved === "dark" || saved === "light") return saved;
    }
  } catch {
    // ignore
  }
  return "light";
}

export const useUiStore = create<UiState>((set) => ({
  cartDrawerOpen: false,
  chatDrawerOpen: false,
  chatPrompt: null,
  mobileNavOpen: false,
  theme: getInitialTheme(),
  toasts: [],
  lastOrder: null,

  setCartDrawerOpen: (open) => set({ cartDrawerOpen: open }),
  setChatDrawerOpen: (open) => set({ chatDrawerOpen: open }),
  openChatWithPrompt: (prompt) =>
    set({
      chatDrawerOpen: true,
      chatPrompt: prompt ?? null,
    }),
  clearChatPrompt: () => set({ chatPrompt: null }),
  setMobileNavOpen: (open) => set({ mobileNavOpen: open }),

  setTheme: (next) => {
    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("commercify_theme", next);
        document.documentElement.classList.toggle("dark", next === "dark");
      }
    } catch {
      // ignore
    }
    set({ theme: next });
  },

  toggleTheme: () =>
    set((state) => {
      const next = state.theme === "light" ? "dark" : "light";
      try {
        if (typeof window !== "undefined") {
          window.localStorage.setItem("commercify_theme", next);
          document.documentElement.classList.toggle("dark", next === "dark");
        }
      } catch {
        // ignore
      }
      return { theme: next };
    }),

  addToast: (toast) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const tone = toast.tone ?? toast.variant ?? "info";
    set((state) => ({
      toasts: [
        ...state.toasts,
        { id, tone, title: toast.title, description: toast.description },
      ],
    }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 4500);
  },

  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),

  setLastOrder: (order) => set({ lastOrder: order }),
}));
