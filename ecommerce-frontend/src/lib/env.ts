const envApiUrl =
  typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL !== undefined
    ? String(import.meta.env.VITE_API_URL)
    : undefined;

const isProd =
  typeof import.meta !== "undefined" && Boolean(import.meta.env?.PROD);

const rawUrl =
  envApiUrl !== undefined
    ? envApiUrl
    : isProd
      ? ""
      : "http://localhost:8000";

export const API_URL = rawUrl.replace(/\/+$/, "");
export const API_BASE = `${API_URL}/api/v1`;
