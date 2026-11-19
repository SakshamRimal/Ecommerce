import { create } from "zustand";
import type { User } from "../lib/api/types";

const ACCESS_STORAGE_KEY = "commercify_access_token";
const REFRESH_STORAGE_KEY = "commercify_refresh_token";
const USER_STORAGE_KEY = "commercify_user";
const LEGACY_DEMO_KEY = "commercify_demo_mode";

function clearLegacyDemoMode(): void {
  try {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(LEGACY_DEMO_KEY);
    }
  } catch {
    // ignore
  }
}

function readStoredString(key: string): string | null {
  try {
    return typeof window !== "undefined"
      ? window.localStorage.getItem(key)
      : null;
  } catch {
    return null;
  }
}

function readStoredUser(): User | null {
  try {
    if (typeof window === "undefined") return null;
    const raw = window.localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as User;
    // Never restore the old hardcoded demo user ("Alex Rivera")
    if (parsed?.id?.startsWith("00000000-0000-4000-8000-00000000000")) {
      window.localStorage.removeItem(USER_STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

clearLegacyDemoMode();

const initialAccess = readStoredString(ACCESS_STORAGE_KEY);
const initialRefresh = readStoredString(REFRESH_STORAGE_KEY);
const initialUser = readStoredUser();

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  status: "loading" | "authenticated" | "anonymous";
  demoMode: boolean;
  setTokens: (accessToken: string | null, refreshToken: string | null) => void;
  setUser: (user: User | null) => void;
  setStatus: (status: "loading" | "authenticated" | "anonymous") => void;
  clearAuth: () => void;
  setDemoMode: (enabled: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: initialAccess?.startsWith("demo-") ? null : initialAccess,
  refreshToken: initialRefresh?.startsWith("demo-") ? null : initialRefresh,
  user: initialUser,
  status: initialUser
    ? "authenticated"
    : initialAccess || initialRefresh
      ? "loading"
      : "anonymous",
  demoMode: false,

  setTokens: (accessToken, refreshToken) => {
    try {
      if (typeof window !== "undefined") {
        if (accessToken) {
          window.localStorage.setItem(ACCESS_STORAGE_KEY, accessToken);
        } else {
          window.localStorage.removeItem(ACCESS_STORAGE_KEY);
        }
        if (refreshToken) {
          window.localStorage.setItem(REFRESH_STORAGE_KEY, refreshToken);
        } else {
          window.localStorage.removeItem(REFRESH_STORAGE_KEY);
        }
      }
    } catch {
      // ignore storage errors
    }
    set({ accessToken, refreshToken });
  },

  setUser: (user) => {
    try {
      if (typeof window !== "undefined") {
        if (user) {
          window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
        } else {
          window.localStorage.removeItem(USER_STORAGE_KEY);
        }
      }
    } catch {
      // ignore
    }
    set({
      user,
      status: user ? "authenticated" : "anonymous",
    });
  },

  setStatus: (status) => set({ status }),

  clearAuth: () => {
    try {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(ACCESS_STORAGE_KEY);
        window.localStorage.removeItem(REFRESH_STORAGE_KEY);
        window.localStorage.removeItem(USER_STORAGE_KEY);
        window.localStorage.removeItem(LEGACY_DEMO_KEY);
        window.sessionStorage.removeItem(REFRESH_STORAGE_KEY);
      }
    } catch {
      // ignore
    }
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      status: "anonymous",
      demoMode: false,
    });
  },

  setDemoMode: (enabled) => {
    set({ demoMode: enabled });
  },
}));
