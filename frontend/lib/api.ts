const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

class APIError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("velora_access_token");
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {}, signal } = options;

  const token = getToken();
  const allHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };
  if (token) allHeaders["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: allHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });

  if (!res.ok) {
    let code = "UNKNOWN_ERROR";
    let message = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      code = err?.error?.code ?? code;
      message = err?.error?.message ?? message;
    } catch {
      // non-JSON error body
    }
    throw new APIError(res.status, code, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export { APIError };
