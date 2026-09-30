import { createSignal, createMemo } from "solid-js";
import { apiClient } from "../lib/api-client";

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  phone?: string | null;
  role?: string;
  roles?: string[];
  enable?: number;
  language_preference?: string;
}

const [currentUser, setCurrentUser] = createSignal<UserProfile | null>(null);
const [isLoading, setIsLoading] = createSignal<boolean>(true);

export const user = createMemo(() => currentUser());
export const isAuthenticated = createMemo(() => !!currentUser());
export const authLoading = createMemo(() => isLoading());
export const userRoles = createMemo(() => currentUser()?.roles || [currentUser()?.role || "farmer"]);

export function hasRole(requiredRole: string): boolean {
  const roles = userRoles();
  return roles.includes(requiredRole) || roles.includes("admin");
}

export async function initializeAuth(): Promise<void> {
  setIsLoading(true);
  const token = localStorage.getItem("access_token");

  if (!token) {
    setCurrentUser(null);
    setIsLoading(false);
    return;
  }

  // Restore cached user profile immediately for fast UI boot
  const cachedUser = localStorage.getItem("user_data");
  if (cachedUser) {
    try {
      setCurrentUser(JSON.parse(cachedUser));
    } catch {
      // ignore JSON parse error
    }
  }

  // Preserve mock demo accounts without remote verification (development mode only)
  if (import.meta.env.DEV && (token.startsWith("mock-token-") || token.startsWith("mock-"))) {
    setIsLoading(false);
    return;
  }

  try {
    const res = await apiClient.get<UserProfile>("/auth/user");
    if (res.ok && res.data) {
      setCurrentUser(res.data);
      localStorage.setItem("user_data", JSON.stringify(res.data));
    } else {
      // If unauthorized, token is expired
      if (res.status === 401) {
        await signOut();
      }
    }
  } catch {
    // If offline, preserve cached user
    if (!navigator.onLine && cachedUser) {
      console.info("Offline mode: running with cached profile");
    }
  } finally {
    setIsLoading(false);
  }
}

const FIREBASE_ERRORS: Record<string, string> = {
  INVALID_LOGIN_CREDENTIALS: "Wrong email or password.",
  EMAIL_NOT_FOUND: "No account with this email. Please register first.",
  INVALID_PASSWORD: "Wrong email or password.",
  USER_DISABLED: "This account is disabled.",
  TOO_MANY_ATTEMPTS_TRY_LATER: "Too many attempts. Please try again later.",
};

/** Readable message from a FastAPI error body (string detail or 422 validation list) */
export function apiErrorMessage(data: any, fallback: string): string {
  const d = data?.detail;
  if (typeof d === "string") {
    const code = Object.keys(FIREBASE_ERRORS).find((k) => d.includes(k));
    return code ? FIREBASE_ERRORS[code] : d.replace(/^Sign in failed: /, "");
  }
  if (Array.isArray(d) && d.length) return d.map((e: any) => String(e.msg || "").replace(/^Value error, /, "")).join(" ");
  return fallback;
}

export async function signInWithEmail(email: string, password: string): Promise<{ success: boolean; error?: string }> {
  setIsLoading(true);
  try {
    const res = await apiClient.post("/auth/signin", { username: email, password }, { requiresAuth: false });
    if (res.ok && res.data) {
      const token = res.data.access_token || res.data.token;
      if (token) {
        localStorage.setItem("access_token", token);
        if (res.data.refresh_token) {
          localStorage.setItem("refresh_token", res.data.refresh_token);
        }
        localStorage.setItem("username", email);
      }

      if (res.data.user) {
        setCurrentUser(res.data.user);
        localStorage.setItem("user_data", JSON.stringify(res.data.user));
      } else {
        await initializeAuth();
      }
      return { success: true };
    }
    return { success: false, error: apiErrorMessage(res.data, "Authentication failed") };
  } catch (err: any) {
    return { success: false, error: err.message || "Network error during sign-in" };
  } finally {
    setIsLoading(false);
  }
}

export async function signInWithMock(email: string = "farmer@cropsense.ai"): Promise<void> {
  const mockToken = `mock-token-${email}`;
  localStorage.setItem("access_token", mockToken);
  localStorage.setItem("username", email);
  const mockUser: UserProfile = {
    id: 1,
    name: email.split("@")[0].toUpperCase(),
    email,
    role: "farmer",
    roles: ["farmer"],
    enable: 1,
  };
  setCurrentUser(mockUser);
  localStorage.setItem("user_data", JSON.stringify(mockUser));
}

// One-click demo: a mock token against a dev backend, or a real shared demo account when the
// production build is given VITE_DEMO_EMAIL / VITE_DEMO_PASSWORD (the backend rejects mock tokens there)
const DEMO_EMAIL = (import.meta as any).env?.VITE_DEMO_EMAIL as string | undefined;
const DEMO_PASSWORD = (import.meta as any).env?.VITE_DEMO_PASSWORD as string | undefined;
export const demoSignInAvailable = !!import.meta.env.DEV || !!(DEMO_EMAIL && DEMO_PASSWORD);

export async function signInDemo(): Promise<{ success: boolean; error?: string }> {
  if (import.meta.env.DEV) {
    await signInWithMock();
    return { success: true };
  }
  if (DEMO_EMAIL && DEMO_PASSWORD) return signInWithEmail(DEMO_EMAIL, DEMO_PASSWORD);
  return { success: false, error: "Demo sign-in is not configured" };
}

export async function signOut(): Promise<void> {
  // 1. Clear in-memory API cache
  apiClient.clearCache();

  // 2. Clear localStorage authentication keys
  localStorage.removeItem("access_token");
  localStorage.removeItem("id_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("username");
  localStorage.removeItem("user_data");
  localStorage.removeItem("assistant_chat");

  // 3. Notify Service Worker to purge API cache
  if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({ type: "CLEAR_API_CACHE" });
  }

  // 4. Reset reactive state
  setCurrentUser(null);
}
