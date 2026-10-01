import { Component, createResource, createSignal, For, Show } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { apiClient } from "../../lib/api-client";

interface FarmOption {
  id: number;
  name: string;
  badge: string;
  area: string;
  gutNo: string;
  location: string;
  soil: string;
  irrigation: string;
  readiness: number;
  readinessLabel: string;
  readinessColor: string;
  features: string[];
  note?: string;
  lastPlanned?: string;
}

export const SelectFarm: Component = () => {
  const navigate = useNavigate();
  const [selectedFarmId, setSelectedFarmId] = createSignal<number>(0);
  const [filterQuery, setFilterQuery] = createSignal<string>("");

  const titleCase = (v?: string | null) =>
    v ? v.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "";

  // The signed-in farmer's farms; profile completeness = how much field data the AI planner gets to work with
  const [farmList] = createResource(async () => {
    const res = await apiClient.get<any>("/farms", { skipCache: true });
    if (!res.ok) throw new Error(res.data?.detail || "Could not load your farms");
    const rows: FarmOption[] = (res.data?.farms ?? []).map((f: any, i: number) => {
      const known = [f.primary_soil_type, f.irrigation_type, f.pincode, f.total_area_acres];
      const readiness = Math.round((known.filter(Boolean).length / known.length) * 100);
      return {
        id: f.id,
        name: f.name || `Farm #${f.id}`,
        badge: i === 0 ? "Primary Farm" : "Farm",
        area: f.total_area_acres ? `${f.total_area_acres} Ac` : "Area not set",
        gutNo: f.survey_number ? `Survey #${f.survey_number}` : `Pincode ${f.pincode || "—"}`,
        location: [f.village, f.district, f.state].filter(Boolean).join(", "),
        soil: titleCase(f.primary_soil_type) || "Soil type not set",
        irrigation: titleCase(f.irrigation_type) || "Irrigation not set",
        readiness,
        readinessLabel: `Profile ${readiness}% complete`,
        readinessColor: readiness === 100 ? "bg-emerald-500" : "bg-amber-500",
        features: [f.district && `${f.district} district soil & weather`, f.pincode && `Pincode ${f.pincode}`].filter(Boolean),
        note: readiness < 100 ? "Missing details are estimated from district soil and weather data." : undefined,
      };
    });
    if (rows.length && !rows.some((r) => r.id === selectedFarmId())) setSelectedFarmId(rows[0].id);
    return rows;
  });
  const farms = () => farmList() ?? [];

  const handleProceed = (farmId: number) => {
    navigate(`/strategy/request?farmId=${farmId}`);
  };

  const filteredFarms = () => {
    const q = filterQuery().toLowerCase().trim();
    if (!q) return farms();
    return farms().filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        f.location.toLowerCase().includes(q) ||
        f.gutNo.toLowerCase().includes(q)
    );
  };

  return (
    <div class="space-y-6 pb-16">
      {/* Top Banner & Breadcrumb */}
      <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-6 shadow-sm">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
              <span class="material-symbols-outlined text-sm">psychiatry</span>
              <span>AI CROP STRATEGY PLAN</span>
              <span>•</span>
              <span>STEP 1 OF 3</span>
            </div>
            <h1 class="text-2xl lg:text-3xl font-bold text-on-surface dark:text-white">
              Select Target Farm
            </h1>
            <p class="text-sm text-on-surface-variant dark:text-slate-400 mt-1 max-w-2xl">
              Select an onboarded cadastral parcel to formulate your multi-season crop rotation,
              macro/micro-nutrient budget, water allotment, and forward APMC market hedge.
            </p>
          </div>

          <div class="flex items-center gap-3">
            <A
              href={`/crops/annual-strategy/${selectedFarmId()}`}
              class="px-4 py-2.5 rounded-xl border border-outline-variant/40 bg-surface-container-low dark:bg-slate-800 text-on-surface dark:text-slate-200 text-sm font-semibold hover:bg-surface-container transition-colors flex items-center gap-2"
            >
              <span class="material-symbols-outlined text-base">history</span>
              <span>Past Strategies</span>
            </A>
            <A
              href="/farm/register"
              class="px-4 py-2.5 rounded-xl bg-primary-container text-white text-sm font-bold hover:bg-emerald-800 shadow-sm flex items-center gap-2 transition-transform active:scale-95"
            >
              <span class="material-symbols-outlined text-base">add_location_alt</span>
              <span>+ Register New Farm</span>
            </A>
          </div>
        </div>

        {/* Filter bar */}
        <div class="mt-6 flex flex-col sm:flex-row gap-3">
          <div class="relative flex-1">
            <span class="material-symbols-outlined absolute left-3.5 top-3 text-slate-400 text-lg">
              search
            </span>
            <input
              type="text"
              placeholder="Search by farm name, gut number, or district..."
              value={filterQuery()}
              onInput={(e) => setFilterQuery(e.currentTarget.value)}
              class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-container-low dark:bg-slate-800 border border-outline-variant/30 text-sm text-on-surface dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
            />
          </div>
          <div class="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 px-2">
            <span>Showing {filteredFarms().length} of {farms().length} farms</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Column Farm Cards (8 col), Right Column Intelligence Sidebar (4 col) */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Farm Cards */}
        <div class="lg:col-span-8 space-y-4">
          <Show when={farmList.loading}>
            <div class="rounded-2xl p-6 border border-outline-variant/30 text-sm text-slate-500">Loading your farms…</div>
          </Show>
          <Show when={farmList.error}>
            <div class="rounded-2xl p-6 border border-red-200 bg-red-50 text-sm text-red-700">{String(farmList.error?.message || farmList.error)}</div>
          </Show>
          <Show when={!farmList.loading && !farmList.error && farms().length === 0}>
            <div class="rounded-2xl p-6 border border-outline-variant/30 text-sm text-slate-600">
              No farms yet. Register a farm first; its pincode provides the district's soil and weather telemetry.
            </div>
          </Show>
          <For each={filteredFarms()}>
            {(farm) => {
              const isSelected = () => selectedFarmId() === farm.id;
              return (
                <div
                  onClick={() => setSelectedFarmId(farm.id)}
                  class={`rounded-2xl p-5 lg:p-6 transition-all cursor-pointer border-2 ${
                    isSelected()
                      ? "border-emerald-600 bg-emerald-50/30 dark:bg-emerald-950/20 shadow-md ring-2 ring-emerald-500/20"
                      : "border-outline-variant/30 bg-surface-container-lowest dark:bg-slate-900 hover:border-emerald-500/50"
                  }`}
                >
                  <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div class="space-y-1">
                      <div class="flex items-center gap-2">
                        <h2 class="text-xl font-bold text-on-surface dark:text-white">
                          {farm.name}
                        </h2>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300">
                          {farm.badge}
                        </span>
                      </div>
                      <p class="text-xs text-on-surface-variant dark:text-slate-400 flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-sm text-emerald-600">
                          location_on
                        </span>
                        <span>
                          {farm.area} • {farm.gutNo} • {farm.location}
                        </span>
                      </p>
                    </div>

                    <div class="flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-surface-container dark:bg-slate-800 text-on-surface dark:text-slate-300 border border-outline-variant/30">
                      <span class={`w-2 h-2 rounded-full ${farm.readinessColor}`}></span>
                      <span>{farm.readinessLabel}</span>
                    </div>
                  </div>

                  {/* Soil & Water Specs */}
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 text-xs">
                    <div class="p-3 rounded-xl bg-surface-container-low dark:bg-slate-800/60 border border-outline-variant/20 space-y-1">
                      <span class="font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-[10px]">
                        Soil Profile
                      </span>
                      <div class="font-semibold text-on-surface dark:text-slate-200">
                        {farm.soil}
                      </div>
                    </div>
                    <div class="p-3 rounded-xl bg-surface-container-low dark:bg-slate-800/60 border border-outline-variant/20 space-y-1">
                      <span class="font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-[10px]">
                        Water & Irrigation
                      </span>
                      <div class="font-semibold text-on-surface dark:text-slate-200">
                        {farm.irrigation}
                      </div>
                    </div>
                  </div>

                  {/* Feature chips */}
                  <div class="flex flex-wrap gap-2 mt-3">
                    <For each={farm.features}>
                      {(feat) => (
                        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container dark:bg-slate-800 text-on-surface-variant dark:text-slate-300 text-xs border border-outline-variant/20">
                          <span class="material-symbols-outlined text-emerald-600 text-xs">
                            check_circle
                          </span>
                          <span>{feat}</span>
                        </span>
                      )}
                    </For>
                  </div>

                  {farm.note && (
                    <div class="mt-3 p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/40 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2">
                      <span class="material-symbols-outlined text-sm mt-0.5">info</span>
                      <span>{farm.note}</span>
                    </div>
                  )}

                  {/* Action Bar */}
                  <div class="mt-5 pt-4 border-t border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <span class="text-xs text-slate-500 dark:text-slate-400">
                      Last Strategy: <strong class="text-on-surface dark:text-slate-200">{farm.lastPlanned || "None yet"}</strong>
                    </span>

                    <div class="flex items-center gap-3 w-full sm:w-auto">
                      <A
                        href={`/farm/${farm.id}`}
                        onClick={(e) => e.stopPropagation()}
                        class="px-4 py-2 rounded-xl border border-outline-variant/40 hover:bg-surface-container dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors"
                      >
                        Inspect Land Card
                      </A>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFarmId(farm.id);
                          handleProceed(farm.id);
                        }}
                        class={`flex-1 sm:flex-initial px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm transition-transform active:scale-95 ${
                          isSelected()
                            ? "bg-primary-container text-white hover:bg-emerald-800"
                            : "bg-surface-container hover:bg-emerald-600 hover:text-white text-on-surface dark:text-white"
                        }`}
                      >
                        <span>Select & Configure</span>
                        <span class="material-symbols-outlined text-sm">arrow_forward</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            }}
          </For>

          {/* Import New Parcel Banner */}
          <div class="border-2 border-dashed border-outline-variant/60 rounded-2xl p-6 bg-surface-container-low/30 dark:bg-slate-900/40 hover:border-emerald-500/60 transition-colors flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-surface-container-lowest dark:bg-slate-800 border border-outline-variant/30 flex items-center justify-center text-emerald-600">
                <span class="material-symbols-outlined text-2xl">add_location_alt</span>
              </div>
              <div>
                <h3 class="font-bold text-on-surface dark:text-white">
                  Register Another Cadastral Parcel
                </h3>
                <p class="text-xs text-on-surface-variant dark:text-slate-400 mt-0.5">
                  Import boundary vectors via Maharashtra 7/12 Land Records, PM-KISAN, or handheld GPS walk.
                </p>
              </div>
            </div>
            <A
              href="/farm/register"
              class="px-4 py-2.5 rounded-xl bg-surface-container-lowest dark:bg-slate-800 border border-outline-variant/40 hover:bg-surface-container text-xs font-bold text-on-surface dark:text-white whitespace-nowrap shadow-sm"
            >
              + Import Parcel
            </A>
          </div>
        </div>

        {/* Right Column: Intelligence & Showcase Sidebar */}
        <div class="lg:col-span-4 space-y-6">
          {/* Engine Card */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div class="flex items-center gap-2.5 pb-2 border-b border-outline-variant/20">
              <div class="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-800 dark:text-emerald-400">
                <span class="material-symbols-outlined text-lg">neurology</span>
              </div>
              <div>
                <h3 class="font-bold text-sm text-on-surface dark:text-white">
                  AgriSense AI Strategy Engine
                </h3>
                <span class="text-[11px] text-slate-500">Autonomous Agricultural Planner</span>
              </div>
            </div>

            <ul class="space-y-3 text-xs">
              <li class="flex items-start gap-2.5">
                <span class="material-symbols-outlined text-emerald-600 text-sm mt-0.5">
                  published_with_changes
                </span>
                <div>
                  <strong class="text-on-surface dark:text-slate-200">Multi-Season Crop Rotation:</strong>
                  <p class="text-slate-500 dark:text-slate-400 mt-0.5 text-[11px]">
                    Schedules Kharif, Rabi, and Zaid cash/pulse pairings to break pest cycles.
                  </p>
                </div>
              </li>

              <li class="flex items-start gap-2.5">
                <span class="material-symbols-outlined text-emerald-600 text-sm mt-0.5">
                  eco
                </span>
                <div>
                  <strong class="text-on-surface dark:text-slate-200">Soil Organic Carbon (SOC):</strong>
                  <p class="text-slate-500 dark:text-slate-400 mt-0.5 text-[11px]">
                    N-Positive biological nitrogen budgeting tailored to Vertisol profile.
                  </p>
                </div>
              </li>

              <li class="flex items-start gap-2.5">
                <span class="material-symbols-outlined text-amber-600 text-sm mt-0.5">
                  trending_up
                </span>
                <div>
                  <strong class="text-on-surface dark:text-slate-200">Forward APMC Hedging:</strong>
                  <p class="text-slate-500 dark:text-slate-400 mt-0.5 text-[11px]">
                    e-NAM price forecasts aligned to peak harvest arrival periods.
                  </p>
                </div>
              </li>

              <li class="flex items-start gap-2.5">
                <span class="material-symbols-outlined text-blue-600 text-sm mt-0.5">
                  water
                </span>
                <div>
                  <strong class="text-on-surface dark:text-slate-200">Precision Water Budgeting:</strong>
                  <p class="text-slate-500 dark:text-slate-400 mt-0.5 text-[11px]">
                    Micro-irrigation schedules tied directly to IMD 15-day satellite precipitation.
                  </p>
                </div>
              </li>
            </ul>
          </div>

          {/* KVK Helpline Card */}
          <div class="bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 rounded-2xl p-5 space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-xl">headset_mic</span>
              </div>
              <div>
                <h4 class="font-bold text-xs text-emerald-950 dark:text-emerald-200">
                  Need Help Selecting Land?
                </h4>
                <p class="text-[11px] text-emerald-800 dark:text-emerald-400">
                  Talk to an agriculture expert in your language (free).
                </p>
              </div>
            </div>

            <a
              href="tel:18001801551"
              class="w-full bg-white dark:bg-slate-800 hover:bg-emerald-50 text-emerald-800 dark:text-emerald-300 text-xs font-bold py-2.5 px-4 rounded-xl border border-emerald-300 dark:border-emerald-700/50 flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              <span class="material-symbols-outlined text-sm">call</span>
              <span>Kisan Call Centre: 1800-180-1551</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
