import { Component } from "solid-js";
import { A, useLocation } from "@solidjs/router";
import { t } from "../../stores/i18n.store";

export const BottomDock: Component = () => {
  const location = useLocation();

  const dockItems = [
    { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
    { href: "/farm", label: "Farms", icon: "agriculture" },
    { href: "/diagnose", label: "AI Doctor", icon: "psychology" },
    { href: "/livestock", label: "Pashu", icon: "pets" },
    { href: "/marketplace", label: "Mandi", icon: "storefront" },
  ];

  return (
    <nav class="lg:hidden fixed bottom-0 left-0 right-0 max-w-lg mx-auto w-full z-50 glass-dock px-3 py-2 flex items-center justify-around shadow-2xl rounded-t-2xl border-t border-slate-200">
      {dockItems.map((item) => {
        const isActive = () =>
          location.pathname === item.href || (item.href !== "/dashboard" && location.pathname.startsWith(item.href));
        return (
          <A
            href={item.href}
            class={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-xl transition-all duration-150 ${
              isActive() ? "text-forest font-bold scale-105" : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span
              class={`material-symbols-outlined text-2xl transition-transform ${
                isActive() ? "text-forest fill" : "text-slate-400"
              }`}
            >
              {item.icon}
            </span>
            <span class="text-[10px] tracking-tight">{item.label}</span>
          </A>
        );
      })}
    </nav>
  );
};
