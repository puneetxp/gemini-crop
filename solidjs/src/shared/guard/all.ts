/**
 * Auth guard utilities for shared services.
 */

export function isLogin(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("access_token");
}
