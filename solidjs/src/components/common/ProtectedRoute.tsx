import { Component, JSX, Show } from "solid-js";
import { Navigate, useLocation } from "@solidjs/router";
import { isAuthenticated, authLoading, userRoles } from "../../stores/auth.store";

interface ProtectedRouteProps {
  children: JSX.Element;
  roles?: string[];
}

export const ProtectedRoute: Component<ProtectedRouteProps> = (props) => {
  const location = useLocation();

  const isAuthorized = () => {
    if (!props.roles || props.roles.length === 0) return true;
    const currentRoles = userRoles();
    return currentRoles.some((r) => props.roles!.includes(r)) || currentRoles.includes("admin");
  };

  return (
    <Show
      when={!authLoading()}
      fallback={
        <div class="min-h-screen flex items-center justify-center bg-canvas">
          <div class="flex flex-col items-center gap-3">
            <div class="w-10 h-10 border-4 border-forest border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm font-semibold text-forest">Loading CropSense…</span>
          </div>
        </div>
      }
    >
      <Show
        when={isAuthenticated()}
        fallback={<Navigate href={`/auth/signin?redirect=${encodeURIComponent(location.pathname + location.search)}`} />}
      >
        <Show
          when={isAuthorized()}
          fallback={
            <div class="min-h-[60vh] flex flex-col items-center justify-center p-8 text-center">
              <span class="material-symbols-outlined text-5xl text-rose-500 mb-2">lock</span>
              <h2 class="text-xl font-bold text-slate-900">Access Restricted</h2>
              <p class="text-sm text-slate-600 mt-1 max-w-md">
                You do not have the required permissions to view this section.
              </p>
            </div>
          }
        >
          {props.children}
        </Show>
      </Show>
    </Show>
  );
};
