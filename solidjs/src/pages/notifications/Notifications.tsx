import { Component, createSignal, For } from "solid-js";

export const Notifications: Component = () => {
  const [notifications] = createSignal([
    {
      id: 1,
      title: "Pre-Monsoon Shower Warning",
      message: "Heavy rain (45mm) forecast for Ludhiana in next 36 hours. Secure drainage.",
      time: "1 hour ago",
      unread: true,
      icon: "thunderstorm",
      color: "text-amber-600 bg-amber-50",
    },
    {
      id: 2,
      title: "Buyer Interest in Wheat Parcel 4A",
      message: "AgroCorp India Ltd initiated a forward contract interest for 350 Quintals.",
      time: "5 hours ago",
      unread: true,
      icon: "storefront",
      color: "text-emerald-600 bg-emerald-50",
    },
    {
      id: 3,
      title: "Sentinel-2 Satellite Image Updated",
      message: "Fresh multispectral pass processed. NDVI average index increased to 0.74.",
      time: "Yesterday",
      unread: false,
      icon: "satellite_alt",
      color: "text-sky-600 bg-sky-50",
    },
  ]);

  return (
    <div class="space-y-6 max-w-4xl mx-auto pb-20">
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
        <div>
          <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">System Alerts & Notifications</h1>
          <p class="text-xs text-slate-500 mt-0.5">Real-time agricultural telemetries, buyer leads and weather warnings</p>
        </div>
      </div>

      <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm divide-y divide-slate-100 overflow-hidden">
        <For each={notifications()}>
          {(notif) => (
            <div class={`p-4 flex items-start gap-3.5 transition-colors ${notif.unread ? "bg-emerald-50/20" : ""}`}>
              <div class={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${notif.color}`}>
                <span class="material-symbols-outlined text-xl">{notif.icon}</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <h4 class="font-bold text-xs text-slate-900">{notif.title}</h4>
                  <span class="text-[10px] text-slate-400 font-medium">{notif.time}</span>
                </div>
                <p class="text-xs text-slate-600 mt-0.5">{notif.message}</p>
              </div>
            </div>
          )}
        </For>
      </div>
    </div>
  );
};
