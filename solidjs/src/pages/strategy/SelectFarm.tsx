import { Component, createSignal, For } from "solid-js";
import { A, useNavigate } from "@solidjs/router";

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
  const [selectedFarmId, setSelectedFarmId] = createSignal<number>(1);
  const [filterQuery, setFilterQuery] = createSignal<string>("");

  const farms: FarmOption[] = [
    {
      id: 1,
      name: "Krishna Valley Farm",
      badge: "Primary Farm",
      area: "18.5 Ac Cultivated",
      gutNo: "Cadastral Gut #142/2A",
      location: "Nashik, Maharashtra",
      soil: "Deep Black Vertisol (pH 7.2) • 14.8 Ac Active",
      irrigation: "Drip Micro-Fertigation • Solar 7.5 HP (Godavari Sub-Basin)",
      readiness: 100,
      readinessLabel: "100% Ready • All Datasets Synced",
      readinessColor: "bg-emerald-500",
      features: [
        "RTK GNSS Demarcated (0.4m)",
        "LoRaWAN Soil Nodes Synced",
        "Sentinel-2 NDVI: 0.79 (Healthy)"
      ],
      lastPlanned: "Kharif 2024 (98% harvest goal achieved)"
    },
    {
      id: 2,
      name: "Sahyadri Terrace Agro",
      badge: "Secondary Farm",
      area: "12.0 Ac Cultivated",
      gutNo: "Cadastral Gut #89/B",
      location: "Dindori, Nashik",
      soil: "Red Sandy Loam (Alfisol, pH 6.4) • 8.5 Ac Active",
      irrigation: "Canal Lift + Sprinkler Grid • Rotation Basin",
      readiness: 94,
      readinessLabel: "94% Ready • Pending Zinc/Boron",
      readinessColor: "bg-amber-500",
      features: [
        "Canal Basin Demarcated",
        "Automated Soil Moisture Vane",
        "Sentinel-2 NDVI: 0.71 (Moderate)"
      ],
      note: "Gemini will estimate micronutrient levels from regional KVK soil samples.",
      lastPlanned: "Rabi 2024"
    },
    {
      id: 3,
      name: "Khandesh Alluvial Tract",
      badge: "Cash Crop Parcel",
      area: "24.0 Ac Cultivated",
      gutNo: "Cadastral Gut #301",
      location: "Jalgaon, Maharashtra",
      soil: "Alluvial Clay Loam (pH 7.8) • 20.0 Ac Active",
      irrigation: "Borewell + Deep Trench Recharge",
      readiness: 88,
      readinessLabel: "88% Ready • Weather Radar Calibrating",
      readinessColor: "bg-blue-500",
      features: [
        "Aadhaar Land Registry Synced",
        "IMD Micro-radar Linked",
        "Cotton / Maize Historical Yields"
      ],
      lastPlanned: "Zaid 2023"
    }
  ];

  const handleProceed = (farmId: number) => {
    navigate(`/strategy/request?farmId=${farmId}`);
  };

  const filteredFarms = () => {
    const q = filterQuery().toLowerCase().trim();
    if (!q) return farms;
    return farms.filter(
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
              <span>GEMINI 2.0 AGRI-STRATEGY ENGINE</span>
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
              href="/crops/annual-strategy/1"
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
            <span>Showing {filteredFarms().length} of {farms.length} Onboarded Parcels</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Column Farm Cards (8 col), Right Column Intelligence Sidebar (4 col) */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Farm Cards */}
        <div class="lg:col-span-8 space-y-4">
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
                      Last Strategy: <strong class="text-on-surface dark:text-slate-200">{farm.lastPlanned}</strong>
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
                  Gemini 2.0 Agronomy Core
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

          {/* Past Outcome Widget */}
          <div class="bg-surface-container-low dark:bg-slate-900/60 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-outline-variant/20">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600 text-base">
                  history_edu
                </span>
                <h4 class="font-bold text-xs text-on-surface dark:text-white uppercase tracking-wider">
                  2023-24 Strategy Audit
                </h4>
              </div>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300">
                Verified
              </span>
            </div>

            <div>
              <div class="text-xs font-bold text-on-surface dark:text-white">
                Krishna Valley Farm (18.5 Ac)
              </div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Crop Cycle: Sharbati Wheat → Durum → Moong Pulse
              </div>
            </div>

            <div class="grid grid-cols-3 gap-2 text-center">
              <div class="p-2.5 rounded-xl bg-surface-container-lowest dark:bg-slate-800 border border-outline-variant/20">
                <div class="text-base font-bold text-emerald-600">+14.2%</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Yield Gain</div>
              </div>
              <div class="p-2.5 rounded-xl bg-surface-container-lowest dark:bg-slate-800 border border-outline-variant/20">
                <div class="text-base font-bold text-amber-600">₹4.8L</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Net Profit</div>
              </div>
              <div class="p-2.5 rounded-xl bg-surface-container-lowest dark:bg-slate-800 border border-outline-variant/20">
                <div class="text-base font-bold text-blue-600">32%</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Water Saved</div>
              </div>
            </div>

            <A
              href="/crops/annual-strategy/1"
              class="block text-center text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline pt-1"
            >
              View Audited Multi-Season Plan →
            </A>
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
                  Speak directly with Krishi Vigyan Kendra agronomists.
                </p>
              </div>
            </div>

            <a
              href="tel:18001801551"
              class="w-full bg-white dark:bg-slate-800 hover:bg-emerald-50 text-emerald-800 dark:text-emerald-300 text-xs font-bold py-2.5 px-4 rounded-xl border border-emerald-300 dark:border-emerald-700/50 flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              <span class="material-symbols-outlined text-sm">call</span>
              <span>KVK Helpline: 1800-180-1551</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
