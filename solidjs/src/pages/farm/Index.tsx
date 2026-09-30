import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

export const FarmIndex: Component = () => {
  const [farms] = createSignal([
    {
      id: 1,
      name: "Sukhdev Singh Farm - Sector 4",
      location: "Ludhiana District, Punjab",
      totalAcres: 12.5,
      activePlots: 3,
      primaryCrop: "Wheat (HD-2967)",
      ndviStatus: "0.78 (Optimal)",
      healthColor: "text-emerald-600 bg-emerald-50",
    },
    {
      id: 2,
      name: "Bhatinda Organic Parcel B",
      location: "Bhatinda, Punjab",
      totalAcres: 8.0,
      activePlots: 2,
      primaryCrop: "Mustard (Pusa Bold)",
      ndviStatus: "0.64 (Moderate)",
      healthColor: "text-amber-600 bg-amber-50",
    },
  ]);

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-20">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Farm & Parcel Directory</h1>
          <p class="text-xs text-slate-500 mt-0.5">Manage registered land holdings, GPS geo-fences and plot assignments</p>
        </div>
        <A
          href="/farm/register"
          class="px-4 py-2.5 bg-forest hover:bg-forest-light text-white text-xs font-bold rounded-xl shadow transition-all inline-flex items-center gap-2 self-start sm:self-auto"
        >
          <span class="material-symbols-outlined text-base">add_location_alt</span>
          <span>Register New Farm</span>
        </A>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <For each={farms()}>
          {(farm) => (
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4 hover:shadow-md transition-all">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="font-bold text-base text-slate-900">{farm.name}</h3>
                  <div class="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                    <span class="material-symbols-outlined text-sm text-slate-400">location_on</span>
                    <span>{farm.location}</span>
                  </div>
                </div>
                <span class={`text-[11px] font-bold px-2 py-1 rounded-lg ${farm.healthColor}`}>
                  NDVI {farm.ndviStatus}
                </span>
              </div>

              <div class="grid grid-cols-3 gap-2 py-3 border-y border-slate-100 text-center text-xs">
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Total Area</span>
                  <span class="font-bold text-slate-800">{farm.totalAcres} Acres</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Active Plots</span>
                  <span class="font-bold text-slate-800">{farm.activePlots} Plots</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Current Crop</span>
                  <span class="font-bold text-forest">{farm.primaryCrop}</span>
                </div>
              </div>

              <div class="flex items-center justify-between pt-1">
                <A
                  href={`/farm/${farm.id}`}
                  class="text-xs font-bold text-forest hover:underline inline-flex items-center gap-1"
                >
                  <span>Farm Dashboard</span>
                  <span class="material-symbols-outlined text-sm">arrow_forward</span>
                </A>
                <A
                  href={`/analytics/farm/${farm.id}`}
                  class="text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg"
                >
                  Analytics
                </A>
              </div>
            </div>
          )}
        </For>
      </div>
    </div>
  );
};
