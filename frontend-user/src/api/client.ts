import axios, { AxiosError, type AxiosInstance } from "axios";

export interface ApiError {
  code: string;
  message: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  message: string;
  error?: ApiError;
}

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const httpClient: AxiosInstance = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// --- Token storage (module-level, mirrored into the auth store) ---
let accessToken: string | null = localStorage.getItem("sportx.accessToken");
let refreshToken: string | null = localStorage.getItem("sportx.refreshToken");

export function setTokens(access: string | null, refresh?: string | null) {
  accessToken = access;
  if (access) localStorage.setItem("sportx.accessToken", access);
  else localStorage.removeItem("sportx.accessToken");

  if (refresh !== undefined) {
    refreshToken = refresh;
    if (refresh) localStorage.setItem("sportx.refreshToken", refresh);
    else localStorage.removeItem("sportx.refreshToken");
  }
}

export function getAccessToken() {
  return accessToken;
}

httpClient.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

// --- Refresh handling ---
let refreshing: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
  if (!refreshToken) return null;
  try {
    const res = await axios.post<ApiEnvelope<{ access_token: string; refresh_token?: string }>>(
      `${baseURL}/auth/refresh`,
      { refresh_token: refreshToken },
    );
    const data = res.data.data;
    if (data?.access_token) {
      setTokens(data.access_token, data.refresh_token ?? refreshToken);
      return data.access_token;
    }
  } catch {
    /* fall through to logout */
  }
  setTokens(null, null);
  window.dispatchEvent(new CustomEvent("sportx:logout"));
  return null;
}

httpClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError<ApiEnvelope<unknown>>) => {
    const original = error.config as (typeof error.config & { _retry?: boolean }) | undefined;
    if (error.response?.status === 401 && original && !original._retry && refreshToken) {
      original._retry = true;
      refreshing = refreshing ?? performRefresh();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return httpClient(original);
      }
    }
    return Promise.reject(normalizeError(error));
  },
);

export function normalizeError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const envelope = error.response?.data as ApiEnvelope<unknown> | undefined;
    if (envelope?.error) return envelope.error;
    return { code: "NETWORK_ERROR", message: error.message };
  }
  return { code: "UNKNOWN", message: "Something went wrong" };
}

/** Unwrap the success envelope, returning `data` or throwing the ApiError. */
export async function unwrap<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  const res = await promise;
  if (res.data.success) return res.data.data as T;
  throw res.data.error ?? { code: "UNKNOWN", message: res.data.message };
}
