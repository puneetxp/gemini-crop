import { Component, createResource, For, Show } from "solid-js";
import { A } from "@solidjs/router";
import { apiClient } from "../../lib/api-client";

interface FarmSummary {
  id: number;
  name: string;
  state: string;
  district: string;
  village: string;
  total_area_acres: number;
  primary_soil_type?: string | null;
  irrigation_type?: string | null;
}

const titleCase = (v?: string | null) =>
  v ? v.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "—";

export const FarmIndex: Component = () => {
  const [farmList] = createResource(async () => {
    const res = await apiClient.get<{ farms: FarmSummary[]; total: number }>("/farms", {
      skipCache: true,
    });
    if (!res.ok) throw new Error(`Could not load farms (${res.status})`);
    return res.data?.farms ?? [];
  });
  const farms = () => farmList() ?? [];

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

      <Show when={farmList.loading}>
        <div class="bg-white rounded-2xl border border-slate-200/80 p-8 text-center text-xs text-slate-500">Loading farms…</div>
      </Show>
      <Show when={farmList.error}>
        <div role="alert" class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-xl text-xs font-bold">
          {String(farmList.error?.message || farmList.error)}
        </div>
      </Show>
      <Show when={!farmList.loading && !farmList.error && farms().length === 0}>
        <div class="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center space-y-3">
          <span class="material-symbols-outlined text-4xl text-slate-300">agriculture</span>
          <p class="text-sm font-bold text-slate-700">No farms registered yet</p>
          <p class="text-xs text-slate-500">Register your first farm to get field-level advice.</p>
          <A
            href="/farm/register"
            class="px-4 py-2.5 bg-forest hover:bg-forest-light text-white text-xs font-bold rounded-xl shadow inline-flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-base">add_location_alt</span>
            <span>Register farm</span>
          </A>
        </div>
      </Show>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <For each={farms()}>
          {(farm) => (
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4 hover:shadow-md transition-all">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="font-bold text-base text-slate-900">{farm.name}</h3>
                  <div class="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                    <span class="material-symbols-outlined text-sm text-slate-400">location_on</span>
                    <span>{[farm.village, farm.district, farm.state].filter(Boolean).join(", ")}</span>
                  </div>
                </div>
                <span class="text-[11px] font-bold px-2 py-1 rounded-lg text-emerald-600 bg-emerald-50">
                  #{farm.id}
                </span>
              </div>

              <div class="grid grid-cols-3 gap-2 py-3 border-y border-slate-100 text-center text-xs">
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Total Area</span>
                  <span class="font-bold text-slate-800">{farm.total_area_acres} Acres</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Soil</span>
                  <span class="font-bold text-slate-800">{titleCase(farm.primary_soil_type)}</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Irrigation</span>
                  <span class="font-bold text-forest">{titleCase(farm.irrigation_type)}</span>
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
