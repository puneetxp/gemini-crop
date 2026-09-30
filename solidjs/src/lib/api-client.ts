/**
 * CropSense AI API Client Transport Layer (v2)
 *
 * Implements:
 * - Base URL resolution with redundant /api/v1 deduplication
 * - Automatic Firebase Bearer token injection from localStorage
 * - Dynamic timeouts (30s standard, 90s for heavy AI/satellite endpoints)
 * - Exponential backoff retry strategy for idempotent methods (GET, PUT, DELETE)
 * - 401 handling with automatic token refresh
 * - 5-minute in-memory response cache with in-flight deduplication
 */

export interface ApiRequestOptions extends Omit<RequestInit, "cache"> {
  requiresAuth?: boolean;
  timeoutMs?: number;
  skipCache?: boolean;
  retries?: number;
  // Option names used by the services in src/services (from the v1 client); never forwarded to fetch
  params?: Record<string, string | number | boolean | null | undefined>;
  timeout?: number;
  retry?: boolean;
  cache?: boolean;
  cacheTTL?: number;
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  ok: boolean;
  headers: Headers;
}

class ApiClient {
  private baseUrl: string;
  private cache = new Map<string, { data: any; expiry: number }>();
  private inFlightRequests = new Map<string, Promise<any>>();
  private isRefreshingToken = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    const rawEnv = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
    // Deduplicate /api/v1
    this.baseUrl = rawEnv.replace(/\/+$/, "").replace(/\/api\/v1$/, "") + "/api/v1";
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public clearCache(): void {
    this.cache.clear();
    this.inFlightRequests.clear();
  }

  public clearCacheByPattern(pattern: RegExp | string): void {
    const re = typeof pattern === "string" ? new RegExp(pattern) : pattern;
    for (const key of this.cache.keys()) {
      if (re.test(key)) this.cache.delete(key);
    }
  }

  private resolveUrl(path: string, params?: ApiRequestOptions["params"]): string {
    let url: string;
    if (path.startsWith("http://") || path.startsWith("https://")) {
      url = path;
    } else {
      const cleanPath = path.startsWith("/") ? path : `/${path}`;
      // Deduplicate if path already starts with /api/v1
      url = cleanPath.startsWith("/api/v1/")
        ? this.baseUrl.replace(/\/api\/v1$/, "") + cleanPath
        : `${this.baseUrl}${cleanPath}`;
    }
    const query = Object.entries(params || {})
      .filter(([, v]) => v !== undefined && v !== null)
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join("&");
    return query ? `${url}${url.includes("?") ? "&" : "?"}${query}` : url;
  }

  private getTimeoutForPath(path: string, customTimeout?: number): number {
    if (customTimeout) return customTimeout;
    const isHeavy =
      path.includes("/vision/") ||
      path.includes("/satellite/") ||
      path.includes("/annual-strategy") ||
      path.includes("/auth/signin");
    return isHeavy ? 90000 : 30000;
  }

  private getCacheKey(method: string, url: string, body?: any): string {
    return `${method.toUpperCase()}:${url}:${body ? JSON.stringify(body) : ""}`;
  }

  private subscribeTokenRefresh(cb: (token: string) => void) {
    this.refreshSubscribers.push(cb);
  }

  private onTokenRefreshed(token: string) {
    this.refreshSubscribers.forEach((cb) => cb(token));
    this.refreshSubscribers = [];
  }

  private async attemptTokenRefresh(): Promise<string | null> {
    const refreshToken = localStorage.getItem("refresh_token");
    const username = localStorage.getItem("username") || localStorage.getItem("email");

    if (!refreshToken) return null;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken, username }),
      });

      if (!response.ok) {
        // Clear auth on invalid refresh token
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        return null;
      }

      const data = await response.json();
      const newToken = data.access_token || data.token;
      if (newToken) {
        localStorage.setItem("access_token", newToken);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        return newToken;
      }
      return null;
    } catch {
      return null;
    }
  }

  public async request<T = any>(
    path: string,
    rawOptions: ApiRequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const { params, timeout, retry, cache, cacheTTL, requiresAuth, timeoutMs, skipCache, retries, ...init } = rawOptions;
    const options = {
      ...init,
      requiresAuth,
      timeoutMs: timeoutMs ?? timeout,
      skipCache: skipCache ?? cache === false,
      retries: retries ?? (retry === false ? 0 : undefined),
    };
    const cacheMs = cacheTTL ?? 5 * 60 * 1000;
    const method = (options.method || "GET").toUpperCase();
    const fullUrl = this.resolveUrl(path, params);
    const isIdempotent = ["GET", "PUT", "DELETE", "HEAD"].includes(method);
    const maxRetries = options.retries ?? (isIdempotent ? 3 : 0);

    // 1. In-memory GET Cache Check
    const cacheKey = this.getCacheKey(method, fullUrl, options.body);
    if (method === "GET" && !options.skipCache) {
      const cached = this.cache.get(cacheKey);
      if (cached && cached.expiry > Date.now()) {
        return {
          data: cached.data,
          status: 200,
          ok: true,
          headers: new Headers({ "x-cache": "HIT" }),
        };
      }

      // Check in-flight deduplication
      if (this.inFlightRequests.has(cacheKey)) {
        return this.inFlightRequests.get(cacheKey)!;
      }
    }

    const executeRequest = async (attempt: number = 0): Promise<ApiResponse<T>> => {
      const timeoutMs = this.getTimeoutForPath(path, options.timeoutMs);
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);

      const headers = new Headers(options.headers || {});
      if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
      }

      // Inject Bearer token
      if (options.requiresAuth !== false) {
        const token = localStorage.getItem("access_token");
        if (token) {
          headers.set("Authorization", `Bearer ${token}`);
        }
      }

      try {
        const res = await fetch(fullUrl, {
          ...init,
          method,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timer);

        // 2. Handle 401 Unauthorized with token refresh
        if (res.status === 401 && options.requiresAuth !== false && attempt === 0) {
          if (!this.isRefreshingToken) {
            this.isRefreshingToken = true;
            const newToken = await this.attemptTokenRefresh();
            this.isRefreshingToken = false;

            if (newToken) {
              this.onTokenRefreshed(newToken);
              return executeRequest(attempt + 1);
            }
          } else {
            // Queue waiting for ongoing refresh
            return new Promise((resolve) => {
              this.subscribeTokenRefresh(() => {
                resolve(executeRequest(attempt + 1));
              });
            });
          }
        }

        // Retry on 5xx server errors for idempotent requests
        if (!res.ok && res.status >= 500 && attempt < maxRetries && isIdempotent) {
          const delay = Math.pow(2, attempt) * 1000;
          await new Promise((r) => setTimeout(r, delay));
          return executeRequest(attempt + 1);
        }

        let responseData: any;
        const contentType = res.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          responseData = await res.json();
        } else {
          responseData = await res.text();
        }

        const result: ApiResponse<T> = {
          data: responseData,
          status: res.status,
          ok: res.ok,
          headers: res.headers,
        };

        // Cache successful GET responses (5 minutes unless cacheTTL is given)
        if (res.ok && method === "GET" && !options.skipCache) {
          this.cache.set(cacheKey, {
            data: responseData,
            expiry: Date.now() + cacheMs,
          });
        }

        return result;
      } catch (err: any) {
        clearTimeout(timer);

        if (err.name === "AbortError") {
          return {
            data: { error: "Request timeout", detail: `Exceeded ${timeoutMs}ms limit` } as any,
            status: 408,
            ok: false,
            headers: new Headers(),
          };
        }

        if (attempt < maxRetries && isIdempotent) {
          const delay = Math.pow(2, attempt) * 1000;
          await new Promise((r) => setTimeout(r, delay));
          return executeRequest(attempt + 1);
        }

        throw err;
      }
    };

    if (method === "GET" && !options.skipCache) {
      const promise = executeRequest().finally(() => {
        this.inFlightRequests.delete(cacheKey);
      });
      this.inFlightRequests.set(cacheKey, promise);
      return promise;
    }

    return executeRequest();
  }

  public get<T = any>(path: string, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  public post<T = any>(path: string, body?: any, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(path, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  public put<T = any>(path: string, body?: any, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(path, {
      ...options,
      method: "PUT",
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  }

  public delete<T = any>(path: string, options?: ApiRequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(path, { ...options, method: "DELETE" });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
