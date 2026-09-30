import { Component, JSX, onMount } from "solid-js";
import { A, useLocation } from "@solidjs/router";
import { Sidebar } from "./components/layout/Sidebar";
import { BottomDock } from "./components/layout/BottomDock";
import { OfflineIndicator } from "./components/common/OfflineIndicator";
import ToastContainer from "./components/ui/Toast";
import VoiceAssistant from "./components/assistant/VoiceAssistant";
import { initializeAuth, user, isAuthenticated } from "./stores/auth.store";

export const App: Component<{ children?: JSX.Element }> = (props) => {
  const location = useLocation();

  onMount(() => {
    initializeAuth();
  });

  return (
    <div class="min-h-screen bg-canvas flex flex-col text-slate-900 font-sans antialiased">
      <ToastContainer />
      <VoiceAssistant />
      <OfflineIndicator />
      <Sidebar />

      {/* Main Content Area */}
      <div class="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Navbar */}
        <header class="h-16 px-4 md:px-8 border-b border-slate-200/80 bg-white/70 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="lg:hidden font-bold text-base text-forest">CropSense</span>
            <span class="hidden md:inline-block text-xs font-medium text-slate-400">
              AgriSense Premier v2.5 &bull; Operational
            </span>
          </div>

          <div class="flex items-center gap-3">
            <A
              href="/assistant"
              class="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 border border-amber-200/80 text-amber-900 rounded-xl text-xs font-bold transition-all"
            >
              <span class="material-symbols-outlined text-base text-amber-600">mic</span>
              <span class="hidden sm:inline">Voice Assistant</span>
            </A>

            <A
              href="/notifications"
              title="Notifications"
              class="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100/80 transition-all relative"
            >
              <span class="material-symbols-outlined text-xl">notifications</span>
              <span class="w-2 h-2 rounded-full bg-emerald-500 absolute top-2 right-2 ring-2 ring-white"></span>
            </A>

            <A
              href={isAuthenticated() ? "/users/profile" : "/auth/signin"}
              class="flex items-center gap-2 pl-2 border-l border-slate-200"
            >
              <div class="w-8 h-8 rounded-full bg-forest text-white font-bold text-xs flex items-center justify-center shadow-sm">
                {user()?.name?.[0] || "U"}
              </div>
              <span class="hidden md:inline text-xs font-semibold text-slate-800">
                {user()?.name || "Sign In"}
              </span>
            </A>
          </div>
        </header>

        {/* Dynamic Route View */}
        <main class={location.pathname === "/assistant" ? "flex-1 w-full" : "flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto"}>
          {props.children}
        </main>
      </div>

      <BottomDock />
    </div>
  );
};
