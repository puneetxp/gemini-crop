import { Component, createSignal, onMount, For, Show } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { apiClient } from "../../lib/api-client";

interface CropItem {
  id: string;
  name: string;
  variety: string;
  plotName: string;
  acreage: number;
  stageName: string;
  stagePercent: number;
  stageType: "vegetative" | "flowering" | "ripening";
  qualityGrade: string;
  image?: string;
  gddCurrent?: number;
  gddTarget?: number;
  ndvi?: number;
  moistureVwc?: number;
  waterDailyMm?: number;
  alert?: {
    type: "warning" | "info";
    title: string;
    description: string;
    action: string;
  };
  stages: { name: string; status: "done" | "active" | "pending"; targetDate?: string }[];
}

export const MyCrops: Component = () => {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = createSignal<string>("all");
  const [isLoading, setIsLoading] = createSignal(false);

  const defaultCrops: CropItem[] = [
    {
      id: "crop-1",
      name: "शरबती गेहूं (HD-2967)",
      variety: "Sharbati Golden",
      plotName: "Krishna Farm • Plot 4A",
      acreage: 4.5,
      stageName: "Flowering",
      stagePercent: 65,
      stageType: "flowering",
      qualityGrade: "GRADE A1",
      image: "https://lh3.googleusercontent.com/aida/AEtjO1UH4pQ9KI3pN7k3AQCFJPFSsslmfSRqI4UiA610qbjehZzVvSX8bLu_rtVO5913eF-aXHvGINybxUv0S_7Nv1a7ouRVQb86_Jx3YDRWwyjxBozzuj0ISXN50t8HBhXcWEJhAKBi4SijlSLRQwsuOXTYSOct_9NWHd9CnTXcfWCMlMuPyVmVZocQ-lSFdTYsQHNabIEVJVW4_uLANVbh3j9RBeTI0ojsItM0c3T3QNbWMsY5absxLXSyESc",
      ndvi: 0.81,
      moistureVwc: 42.4,
      waterDailyMm: 4.2,
      stages: [
        { name: "Planted", status: "done" },
        { name: "Vegetative", status: "done" },
        { name: "Flowering", status: "active" },
        { name: "Ripening", status: "pending", targetDate: "2026-11-15" },
      ],
    },
    {
      id: "crop-2",
      name: "स्वीट कॉर्न संकर मक्का",
      variety: "Sugar-75 Hybrid",
      plotName: "Krishna Farm • Plot 2B",
      acreage: 2.0,
      stageName: "Vegetative",
      stagePercent: 40,
      stageType: "vegetative",
      qualityGrade: "PREMIUM",
      image: "https://lh3.googleusercontent.com/aida/AEtjO1XQPHJBsetogv6RoQ-cPg70CSfKt9WKPcv0-YhQ4AjdNq0APaJafaE2Hymj-9SHR7H2u7qcoODEvDbeQNHgW4kF9OgBptpkGy8Y9VqB1VR_HAe4xqG64hzs83XIZegFTV9tFC7d2TMqEnTTSkLcfoSdLqcaQ8rz14_CqoC110qs2aONuX1hKcoEND-bMVxNj_SJcaxh7Zz2RJ7ADhBVIywBgsogM_Xf8gTY4gh0Fi2VbwHVskyXBTIDX3I",
      ndvi: 0.74,
      moistureVwc: 38.0,
      waterDailyMm: 5.1,
      stages: [
        { name: "Planted", status: "done" },
        { name: "Vegetative", status: "active" },
        { name: "Flowering", status: "pending" },
        { name: "Ripening", status: "pending", targetDate: "2026-12-01" },
      ],
    },
  ];

  // Initial mock crops matching Stitch screen
  const [crops, setCrops] = createSignal<CropItem[]>(defaultCrops);
  const [loadError, setLoadError] = createSignal("");

  // Map GET /crops/my-crops rows onto the card model
  const stageFor = (status: string): Pick<CropItem, "stageName" | "stagePercent" | "stageType"> => {
    switch ((status || "").toLowerCase()) {
      case "flowering":
        return { stageName: "Flowering", stagePercent: 60, stageType: "flowering" };
      case "harvesting":
      case "ripening":
      case "harvested":
        return { stageName: "Ripening", stagePercent: 90, stageType: "ripening" };
      case "growing":
        return { stageName: "Vegetative", stagePercent: 35, stageType: "vegetative" };
      default:
        return { stageName: "Planted", stagePercent: 10, stageType: "vegetative" };
    }
  };

  const toCropItem = (c: any): CropItem => {
    const stage = stageFor(c.status);
    const order = ["Planted", "Vegetative", "Flowering", "Ripening"];
    const idx = order.indexOf(stage.stageName);
    const isWheat = (c.crop_name || "").toLowerCase().includes("wheat");
    return {
      id: String(c.id),
      name: c.crop_name || "Crop",
      variety: c.crop_variety || "—",
      plotName: [c.farm_name, c.plot_name].filter(Boolean).join(" • ") || "Plot",
      acreage: Number(c.area) || 0,
      image: isWheat
        ? "https://lh3.googleusercontent.com/aida/AEtjO1UH4pQ9KI3pN7k3AQCFJPFSsslmfSRqI4UiA610qbjehZzVvSX8bLu_rtVO5913eF-aXHvGINybxUv0S_7Nv1a7ouRVQb86_Jx3YDRWwyjxBozzuj0ISXN50t8HBhXcWEJhAKBi4SijlSLRQwsuOXTYSOct_9NWHd9CnTXcfWCMlMuPyVmVZocQ-lSFdTYsQHNabIEVJVW4_uLANVbh3j9RBeTI0ojsItM0c3T3QNbWMsY5absxLXSyESc"
        : "https://lh3.googleusercontent.com/aida/AEtjO1XQPHJBsetogv6RoQ-cPg70CSfKt9WKPcv0-YhQ4AjdNq0APaJafaE2Hymj-9SHR7H2u7qcoODEvDbeQNHgW4kF9OgBptpkGy8Y9VqB1VR_HAe4xqG64hzs83XIZegFTV9tFC7d2TMqEnTTSkLcfoSdLqcaQ8rz14_CqoC110qs2aONuX1hKcoEND-bMVxNj_SJcaxh7Zz2RJ7ADhBVIywBgsogM_Xf8gTY4gh0Fi2VbwHVskyXBTIDX3I",
      ...stage,
      qualityGrade: (c.season || "").toUpperCase() || (c.crop_role || "main").toUpperCase(),
      stages: order.map((name, i) => ({
        name,
        status: i < idx ? "done" : i === idx ? "active" : "pending",
        targetDate: name === "Ripening" && c.expected_harvest_date ? String(c.expected_harvest_date).slice(0, 10) : undefined,
      })),
    };
  };

  onMount(async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.get<{ crops: any[] }>("/crops/my-crops", { skipCache: true });
      if (res.ok && res.data?.crops && res.data.crops.length > 0) {
        setCrops(res.data.crops.map(toCropItem));
      }
    } catch {
      // Keep rich default crops
    } finally {
      setIsLoading(false);
    }
  });

  const filteredCrops = () => {
    const f = activeFilter();
    if (f === "all") return crops();
    return crops().filter((c) => c.stageType === f);
  };

  return (
    <div class="flex flex-col min-h-screen bg-slate-50 text-slate-800 pb-28">
      {/* HEADER & TOP APP BAR */}
      <header class="bg-white border-b border-slate-200 px-4 md:px-8 py-3.5 sticky top-0 z-20 shadow-xs">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 max-w-7xl mx-auto w-full">
          <div>
            <div class="flex items-center gap-1.5 text-xs text-slate-500">
              <A href="/dashboard" class="hover:text-emerald-700">Home</A>
              <span class="material-symbols-outlined text-[12px]">chevron_right</span>
              <A href="/farm" class="hover:text-emerald-700">My Farms</A>
              <span class="material-symbols-outlined text-[12px]">chevron_right</span>
              <span class="text-slate-600">All Farms</span>
              <span class="material-symbols-outlined text-[12px]">chevron_right</span>
              <span class="text-emerald-800 font-bold">Active Crops</span>
            </div>
            <div class="flex items-center gap-2 mt-1">
              <h1 class="text-xl md:text-2xl font-bold text-emerald-950 tracking-tight">
                Active Crop Portfolio & Phenology Lifecycle
              </h1>
              <span class="hidden sm:inline-flex px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-200">
                {crops().reduce((sum, c) => sum + c.acreage, 0)} Ac • {crops().length} Active Crops
              </span>
            </div>
          </div>

          {/* Action CTAs */}
          <div class="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={() => alert("Exporting Agronomic Crop Portfolio Audit (CSV/PDF)...")}
              class="flex items-center gap-1 px-3 py-2 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
            >
              <span class="material-symbols-outlined text-sm">download</span>
              <span class="hidden sm:inline">Export Audit</span>
            </button>

            <A
              href="/crops/plant"
              class="flex items-center gap-1.5 px-4 py-2 bg-emerald-800 text-white text-xs font-bold rounded-lg hover:bg-emerald-900 transition-transform active:scale-98 shadow-sm shadow-emerald-900/20"
            >
              <span class="material-symbols-outlined text-base">add_circle</span>
              <span>+ Plant New Crop</span>
            </A>
          </div>
        </div>

        {/* FILTER CHIPS BAR */}
        <div class="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2 overflow-x-auto max-w-7xl mx-auto w-full">
          <button
            onClick={() => setActiveFilter("all")}
            class={`px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeFilter() === "all"
                ? "bg-emerald-800 text-white shadow-xs"
                : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>All Crops</span>
            <span class={`px-1.5 py-0.2 rounded-full text-[10px] ${activeFilter() === "all" ? "bg-emerald-900 text-white" : "bg-slate-100 text-slate-700"}`}>
              {crops().length}
            </span>
          </button>

          <button
            onClick={() => setActiveFilter("vegetative")}
            class={`px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeFilter() === "vegetative"
                ? "bg-emerald-800 text-white shadow-xs"
                : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>Vegetative</span>
            <span class={`px-1.5 py-0.2 rounded-full text-[10px] ${activeFilter() === "vegetative" ? "bg-emerald-900 text-white" : "bg-slate-100 text-slate-700"}`}>
              2
            </span>
          </button>

          <button
            onClick={() => setActiveFilter("ripening")}
            class={`px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeFilter() === "ripening"
                ? "bg-emerald-800 text-white shadow-xs"
                : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>Ripening & Harvest</span>
            <span class={`px-1.5 py-0.2 rounded-full text-[10px] ${activeFilter() === "ripening" ? "bg-emerald-900 text-white" : "bg-slate-100 text-slate-700"}`}>
              1
            </span>
          </button>
        </div>
      </header>

      {/* 4-CARD AGRONOMIC KPI STRIP */}
      <section class="max-w-7xl mx-auto w-full px-4 md:px-8 pt-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Cultivation</span>
              <span class="material-symbols-outlined text-emerald-800 text-lg">crop_free</span>
            </div>
            <p class="text-xl md:text-2xl font-bold text-emerald-950">14.80 <span class="text-xs font-normal text-slate-500">Acres</span></p>
            <p class="text-[11px] text-emerald-700 font-semibold mt-1">+2.4 Ac vs Kharif 2023</p>
          </div>

          <div class="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Mean Health (NDVI)</span>
              <span class="material-symbols-outlined text-emerald-800 text-lg">eco</span>
            </div>
            <p class="text-xl md:text-2xl font-bold text-emerald-950">0.79 <span class="text-xs font-normal text-emerald-700 font-bold">Vibrant</span></p>
            <p class="text-[11px] text-slate-500 mt-1">Sentinel-2 sync 2h ago</p>
          </div>

          <div class="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Next Harvest</span>
              <span class="material-symbols-outlined text-amber-700 text-lg">event_upcoming</span>
            </div>
            <p class="text-xl md:text-2xl font-bold text-amber-800">28 Days</p>
            <p class="text-[11px] text-slate-500 mt-1">Pomegranate Block A (14 MT)</p>
          </div>

          <div class="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-xs">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Season Expense Log</span>
              <span class="material-symbols-outlined text-emerald-800 text-lg">payments</span>
            </div>
            <p class="text-xl md:text-2xl font-bold text-emerald-950">₹1,42,800</p>
            <p class="text-[11px] text-emerald-700 font-semibold mt-1">77% budget utilized</p>
          </div>
        </div>
      </section>

      {/* MAIN 12-COLUMN CONTENT */}
      <main class="max-w-7xl mx-auto w-full px-4 md:px-8 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT 8-COLS: ACTIVE CROP PORTFOLIO CARDS */}
        <div class="lg:col-span-8 space-y-6">
          <Show when={isLoading()}>
            <div class="bg-white rounded-2xl border border-slate-200/90 p-8 text-center text-xs text-slate-500">Loading crops…</div>
          </Show>
          <Show when={loadError()}>
            <div role="alert" class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-xl text-xs font-bold">{loadError()}</div>
          </Show>
          <Show when={!isLoading() && !loadError() && crops().length === 0}>
            <div class="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center space-y-3">
              <span class="material-symbols-outlined text-4xl text-slate-300">yard</span>
              <p class="text-sm font-bold text-slate-700">No crops planted yet</p>
              <p class="text-xs text-slate-500">Plant a crop on one of your plots to track it here.</p>
              <A href="/crops/plant" class="px-4 py-2 bg-emerald-800 text-white text-xs font-bold rounded-lg inline-flex items-center gap-1.5">
                <span class="material-symbols-outlined text-base">add_circle</span>
                <span>Plant a crop</span>
              </A>
            </div>
          </Show>
          <For each={filteredCrops()}>
            {(crop) => (
              <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
                {/* Header Band */}
                <div class="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
                  <div class="flex items-start gap-3">
                    <div class="w-14 h-14 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 shrink-0 shadow-xs">
                      {crop.image ? (
                        <img src={crop.image} alt={crop.name} class="w-full h-full object-cover" />
                      ) : (
                        <div class="w-full h-full bg-emerald-800 text-white flex items-center justify-center">
                          <span class="material-symbols-outlined text-2xl">yard</span>
                        </div>
                      )}
                    </div>
                    <div>
                      <div class="flex items-center gap-2 flex-wrap">
                        <h2 class="text-base font-bold text-slate-900">{crop.name}</h2>
                        <span class="text-xs font-semibold text-emerald-800">({crop.variety})</span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900">
                          {crop.qualityGrade}
                        </span>
                      </div>
                      <p class="text-xs text-slate-500 mt-0.5">
                        {crop.plotName} • {crop.acreage} Acres
                      </p>
                    </div>
                  </div>

                  <span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-200 self-start sm:self-center">
                    {crop.stageName} • {crop.stagePercent}% Stage
                  </span>
                </div>

                {/* Body Content */}
                <div class="p-5 space-y-4">
                  {/* BBCH Phenological Staging Stepper */}
                  <div>
                    <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-2">
                      BBCH Phenological Stage Timeline
                    </span>
                    <div class="grid grid-cols-3 sm:grid-cols-6 gap-2">
                      <For each={crop.stages}>
                        {(st) => (
                          <div
                            class={`p-2 rounded-lg text-center border ${
                              st.status === "done"
                                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                                : st.status === "active"
                                ? "bg-emerald-800 text-white border-emerald-900 shadow-xs ring-2 ring-emerald-800/30"
                                : "bg-slate-50 border-slate-200 text-slate-400"
                            }`}
                          >
                            <span class="text-[10px] font-bold block truncate">{st.name}</span>
                            <span class="text-[9px] block mt-0.5 opacity-90 truncate">
                              {st.status === "done" ? "✓ Done" : st.targetDate || "Pending"}
                            </span>
                          </div>
                        )}
                      </For>
                    </div>
                  </div>

                  {/* Telemetry Metrics Row (only when sensor data exists) */}
                  <Show when={crop.ndvi != null}>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                    <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                      <span class="text-[10px] text-slate-400 uppercase font-semibold block">Accumulated GDD</span>
                      <span class="text-sm font-bold text-slate-900">{crop.gddCurrent} GDD</span>
                      <span class="text-[10px] text-slate-500 block">Target: {crop.gddTarget}</span>
                    </div>

                    <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                      <span class="text-[10px] text-slate-400 uppercase font-semibold block">Canopy NDVI</span>
                      <span class="text-sm font-bold text-emerald-900">{crop.ndvi}</span>
                      <span class="text-[10px] text-emerald-700 block font-semibold">Dense Canopy</span>
                    </div>

                    <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                      <span class="text-[10px] text-slate-400 uppercase font-semibold block">Soil Moisture</span>
                      <span class="text-sm font-bold text-slate-900">{crop.moistureVwc}% VWC</span>
                      <span class="text-[10px] text-slate-500 block">Valve #E4 Standby</span>
                    </div>

                    <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                      <span class="text-[10px] text-slate-400 uppercase font-semibold block">Water Demand</span>
                      <span class="text-sm font-bold text-slate-900">{crop.waterDailyMm} mm/day</span>
                      <span class="text-[10px] text-slate-500 block">Drip Optimized</span>
                    </div>
                  </div>
                  </Show>

                  {/* Disease / Bio Alert Banner */}
                  <Show when={crop.alert}>
                    <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5">
                      <span class="material-symbols-outlined text-amber-700 text-lg shrink-0 mt-0.5">warning</span>
                      <div class="flex-1">
                        <h4 class="text-xs font-bold text-amber-950">{crop.alert!.title}</h4>
                        <p class="text-[11px] text-amber-900 mt-0.5">{crop.alert!.description}</p>
                      </div>
                      <A
                        href="/diagnose"
                        class="px-2.5 py-1 bg-amber-800 text-white text-[11px] font-bold rounded-lg hover:bg-amber-900 shrink-0 shadow-xs"
                      >
                        {crop.alert!.action}
                      </A>
                    </div>
                  </Show>
                </div>

                {/* Footer Action Buttons */}
                <div class="px-5 py-3 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
                  <div class="flex items-center gap-2">
                    <A
                      href="/diagnose"
                      class="px-3 py-1.5 bg-emerald-800 text-white text-xs font-semibold rounded-lg hover:bg-emerald-900 transition-colors flex items-center gap-1 shadow-xs"
                    >
                      <span class="material-symbols-outlined text-sm">document_scanner</span>
                      <span>Diagnose with AI</span>
                    </A>
                    <button
                      onClick={() => alert(`Logging fertigation / spray for ${crop.name}...`)}
                      class="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      Log Spray / Expense
                    </button>
                  </div>

                  <A
                    href={`/farm/1`}
                    class="text-xs font-bold text-emerald-800 hover:underline flex items-center gap-1"
                  >
                    <span>View Plot Command</span>
                    <span class="material-symbols-outlined text-sm">arrow_forward</span>
                  </A>
                </div>
              </div>
            )}
          </For>
        </div>

        {/* RIGHT 4-COLS: INTELLIGENCE, GANTT & APMC MANDI */}
        <div class="lg:col-span-4 space-y-6">
          {/* CARD 1: AGRO-MET SPRAY ADVISORY */}
          <div class="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-800 text-lg">wb_twilight</span>
                <h3 class="text-sm font-bold text-slate-800">Spray & Fertigation Window</h3>
              </div>
              <span class="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                IMD Niphad Live
              </span>
            </div>

            <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-950">
              <span class="font-bold block text-emerald-900">Optimal Foliar Window Today:</span>
              <p class="text-sm font-bold text-emerald-950 mt-0.5">04:30 PM – 07:15 PM</p>
              <p class="text-[11px] text-emerald-800 mt-1">Wind &lt;8 km/h • 0% Rain Probability • High cuticle absorption</p>
            </div>

            <p class="text-[11px] text-slate-500 leading-tight">
              Postpone systemic copper spraying tomorrow morning due to expected heavy nocturnal dew condensation.
            </p>

            <button
              onClick={() => alert("Scheduled auto-drip fertigation for tomorrow 06:30 AM via Valve #E4")}
              class="w-full py-2 bg-emerald-800 text-white text-xs font-bold rounded-lg hover:bg-emerald-900 transition-colors shadow-xs"
            >
              Schedule Auto-Drip Cycle
            </button>
          </div>

          {/* CARD 2: PHENOLOGICAL HARVEST GANTT TIMELINE */}
          <div class="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-800 text-lg">calendar_month</span>
                <h3 class="text-sm font-bold text-slate-800">Harvest Milestones</h3>
              </div>
              <span class="text-[10px] text-slate-400 font-mono">Q4 2024 - Q1 2025</span>
            </div>

            <div class="space-y-2.5 text-xs">
              <div class="p-2.5 bg-amber-50 rounded-xl border border-amber-200 flex items-center justify-between">
                <div>
                  <span class="text-[10px] font-bold text-amber-800 uppercase block">24 Oct 2024</span>
                  <span class="font-bold text-slate-900">Pomegranate Block A</span>
                </div>
                <span class="text-xs font-bold text-amber-900">~14 MT</span>
              </div>

              <div class="p-2.5 bg-emerald-50 rounded-xl border border-emerald-200 flex items-center justify-between">
                <div>
                  <span class="text-[10px] font-bold text-emerald-800 uppercase block">18 Nov 2024</span>
                  <span class="font-bold text-slate-900">Table Grapes Plot E</span>
                </div>
                <span class="text-xs font-bold text-emerald-900">~18 MT</span>
              </div>

              <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span class="text-[10px] font-bold text-slate-500 uppercase block">10 Jan 2025</span>
                  <span class="font-bold text-slate-900">Sharbati Wheat Plot B</span>
                </div>
                <span class="text-xs font-bold text-slate-800">~52 Qtl</span>
              </div>
            </div>
          </div>

          {/* CARD 3: APMC MANDI REAL-TIME SPOT PRICE INDEX */}
          <div class="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-800 text-lg">storefront</span>
                <h3 class="text-sm font-bold text-slate-800">APMC Mandi Spot Index</h3>
              </div>
              <span class="text-[10px] font-bold text-emerald-800">Nashik & Vashi</span>
            </div>

            <div class="space-y-2 text-xs">
              <div class="flex justify-between items-center p-2 bg-slate-50 rounded-lg">
                <span class="font-semibold text-slate-800">Export Table Grapes:</span>
                <span class="font-bold text-emerald-900">₹125/kg <span class="text-[10px] text-emerald-700">▲ +₹8.50</span></span>
              </div>
              <div class="flex justify-between items-center p-2 bg-slate-50 rounded-lg">
                <span class="font-semibold text-slate-800">Bhagwa Pomegranate:</span>
                <span class="font-bold text-emerald-900">₹145/kg <span class="text-[10px] text-emerald-700">▲ +₹12.00</span></span>
              </div>
              <div class="flex justify-between items-center p-2 bg-slate-50 rounded-lg">
                <span class="font-semibold text-slate-800">Sharbati Wheat C-306:</span>
                <span class="font-bold text-emerald-900">₹2,650/Qtl <span class="text-[10px] text-emerald-700">▲ +₹40.00</span></span>
              </div>
            </div>

            <A
              href="/marketplace"
              class="w-full py-2 bg-amber-600 text-white text-xs font-bold rounded-lg hover:bg-amber-700 transition-colors flex items-center justify-center gap-1.5 shadow-xs"
            >
              <span class="material-symbols-outlined text-sm">lock</span>
              <span>Lock Advance Escrow Contract</span>
            </A>
          </div>

          {/* CARD 4: ICAR KVK HOTLINE */}
          <div class="p-4 bg-gradient-to-br from-emerald-900 to-emerald-950 text-white rounded-2xl shadow-xs flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-emerald-800 text-white flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-xl">call</span>
            </div>
            <div>
              <p class="text-xs font-bold">ICAR KVK Agronomist Hotline</p>
              <p class="text-[11px] text-emerald-200">Toll-free 1800-180-1551 (Nashik Hub)</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
