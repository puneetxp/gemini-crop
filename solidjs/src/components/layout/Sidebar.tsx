import { Component, For } from "solid-js";
import { A, useLocation } from "@solidjs/router";
import { currentLanguage, setLanguage, SupportedLanguage, t } from "../../stores/i18n.store";
import { user, isAuthenticated, signOut, signInWithMock } from "../../stores/auth.store";

export const Sidebar: Component = () => {
  const location = useLocation();

  const navItems = [
    { href: "/dashboard", labelKey: "nav.dashboard", icon: "dashboard" },
    { href: "/farm", labelKey: "nav.farms", icon: "agriculture" },
    { href: "/diagnose", labelKey: "nav.diagnose", icon: "psychology" },
    { href: "/livestock", labelKey: "nav.livestock", icon: "pets" },
    { href: "/soil/hub", labelKey: "nav.soil", icon: "satellite_alt" },
    { href: "/marketplace", labelKey: "nav.marketplace", icon: "storefront" },
    { href: "/crops/annual-strategy/1", labelKey: "nav.strategy", icon: "calendar_month" },
    { href: "/assistant", labelKey: "nav.assistant", icon: "mic" },
    { href: "/settings", labelKey: "nav.settings", icon: "settings" },
  ];

  return (
    <aside class="hidden lg:flex flex-col w-64 border-r border-slate-200/80 bg-white/90 backdrop-blur-md h-screen p-5 fixed left-0 top-0 bottom-0 z-30 shadow-sm">
      {/* Brand Header */}
      <div class="flex items-center gap-3 px-2 mb-8">
        <div class="w-10 h-10 rounded-xl bg-forest flex items-center justify-center text-white shadow-md shadow-forest/20">
          <span class="material-symbols-outlined text-2xl">eco</span>
        </div>
        <div>
          <span class="font-bold text-lg text-forest tracking-tight block">CropSense AI</span>
          <span class="text-[11px] font-medium text-emerald bg-emerald/10 px-2 py-0.5 rounded-full inline-block">
            Premier AgriOS
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav class="flex-1 space-y-1 overflow-y-auto pr-1">
        <For each={navItems}>
          {(item) => {
            const isActive = () => location.pathname === item.href || location.pathname.startsWith(item.href + "/");
            return (
              <A
                href={item.href}
                class={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                  isActive()
                    ? "bg-forest text-white shadow-sm shadow-forest/20 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                }`}
              >
                <span class={`material-symbols-outlined text-xl ${isActive() ? "text-amber" : "text-slate-400"}`}>
                  {item.icon}
                </span>
                <span>{t(item.labelKey)}</span>
              </A>
            );
          }}
        </For>
      </nav>

      {/* Language Selector & User Profile Footer */}
      <div class="pt-4 border-t border-slate-200 space-y-3">
        {/* Language Selector */}
        <div class="flex items-center justify-between px-2">
          <span class="text-xs text-slate-500 font-medium">Language</span>
          <select
            class="text-xs font-medium bg-slate-100 border border-slate-200 rounded-lg px-2 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-forest"
            value={currentLanguage()}
            onChange={(e) => setLanguage(e.currentTarget.value as SupportedLanguage)}
          >
            <option value="en">English (EN)</option>
            <option value="hi">हिंदी (HI)</option>
            <option value="mr">मराठी (MR)</option>
            <option value="pa">ਪੰਜਾਬੀ (PA)</option>
          </select>
        </div>

        {/* User Card */}
        {isAuthenticated() && user() ? (
          <div class="bg-slate-50/90 rounded-xl p-3 border border-slate-200/80 flex items-center justify-between">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 rounded-full bg-forest/10 text-forest font-bold flex items-center justify-center text-sm shrink-0">
                {user()?.name?.[0] || "U"}
              </div>
              <div class="truncate">
                <span class="text-xs font-bold text-slate-900 block truncate">{user()?.name}</span>
                <span class="text-[10px] text-emerald font-semibold uppercase">{user()?.role || "Farmer"}</span>
              </div>
            </div>
            <button
              onClick={() => signOut()}
              title="Sign Out"
              class="text-slate-400 hover:text-rose-600 transition-colors p-1"
            >
              <span class="material-symbols-outlined text-lg">logout</span>
            </button>
          </div>
        ) : (
          <div class="flex flex-col gap-1.5">
            <A
              href="/auth/signin"
              class="w-full text-center py-2 px-3 bg-forest text-white rounded-xl text-xs font-semibold shadow hover:bg-forest-light transition-all"
            >
              Sign In
            </A>
            <button
              onClick={() => signInWithMock()}
              class="w-full text-center py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-[11px] font-medium transition-all"
            >
              Demo Auto-Login
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
