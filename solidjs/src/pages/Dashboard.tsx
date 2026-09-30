import { Component, createSignal, onMount } from "solid-js";
import { A } from "@solidjs/router";
import { user } from "../stores/auth.store";
import { apiClient } from "../lib/api-client";

export const Dashboard: Component = () => {
  const [activeFarm, setActiveFarm] = createSignal("Green Valley Plot 4A");
  const [telemetry, setTelemetry] = createSignal({
    ndvi: 0.74,
    moisture: 68,
    nitrogen: 240,
    phosphorus: 18,
    potassium: 310,
    temperature: 28,
    humidity: 62,
  });

  onMount(async () => {
    try {
      const res = await apiClient.get("/analytics/profile-status");
      if (res.ok && res.data) {
        // update telemetry if API returns live values
      }
    } catch {
      // offline fallback
    }
  });

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-20">
      {/* Top Bar / Farm Header */}
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">
              Krishi Command Center
            </h1>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Live STAC
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">
            Welcome back, <span class="font-semibold text-slate-800">{user()?.name || "Farmer"}</span> &bull; Showing analytics for
            <span class="font-semibold text-forest ml-1">{activeFarm()}</span>
          </p>
        </div>

        {/* Live Weather Capsule */}
        <div class="flex items-center gap-3 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200/70">
          <span class="material-symbols-outlined text-amber-500 text-2xl">partly_cloudy_day</span>
          <div>
            <div class="text-sm font-bold text-slate-900">{telemetry().temperature}&deg;C Partly Sunny</div>
            <div class="text-[11px] text-slate-500">Humidity {telemetry().humidity}% &bull; Wind 12 km/h</div>
          </div>
        </div>
      </div>

      {/* Critical Alert Banner */}
      <div class="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl flex items-start gap-3 shadow-sm">
        <span class="material-symbols-outlined text-amber-600 text-xl mt-0.5">warning</span>
        <div class="flex-1">
          <h4 class="text-xs font-bold text-amber-900">Pre-Monsoon Shower Approaching in 36 Hours</h4>
          <p class="text-xs text-amber-800 mt-0.5">
            Heavy rainfall (35-50mm) forecasted for your sub-district. Conclude nitrogen top-dressing and secure drainage in low-lying plots.
          </p>
        </div>
        <A href="/soil/hub" class="text-xs font-bold text-amber-900 underline hover:text-amber-950 shrink-0">
          Review Plots &rarr;
        </A>
      </div>

      {/* Primary KPI Grid */}
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Predicted Yield */}
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Projected Yield</span>
            <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-lg">trending_up</span>
            </div>
          </div>
          <div class="mt-3">
            <span class="text-2xl font-black text-slate-900 tracking-tight">8.4 MT/ha</span>
            <span class="text-xs text-emerald-600 font-semibold ml-2 inline-flex items-center">
              +14% vs District
            </span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">Wheat (HD-2967) &bull; Flowering Stage</p>
        </div>

        {/* KPI 2: Satellite Canopy Health */}
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">NDVI Health Index</span>
            <div class="w-8 h-8 rounded-lg bg-forest/10 text-forest flex items-center justify-center">
              <span class="material-symbols-outlined text-lg">satellite_alt</span>
            </div>
          </div>
          <div class="mt-3">
            <span class="text-2xl font-black text-slate-900 tracking-tight">{telemetry().ndvi}</span>
            <span class="text-xs text-emerald-600 font-semibold ml-2 bg-emerald-50 px-1.5 py-0.5 rounded">
              High Vigour
            </span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">Sentinel-2 STAC &bull; Updated 2 days ago</p>
        </div>

        {/* KPI 3: Pashu Herd */}
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Livestock Portfolio</span>
            <div class="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-lg">pets</span>
            </div>
          </div>
          <div class="mt-3">
            <span class="text-2xl font-black text-slate-900 tracking-tight">14 Animals</span>
            <span class="text-xs text-slate-500 font-medium ml-2">92 L Milk / day</span>
          </div>
          <p class="text-[11px] text-emerald-600 font-medium mt-1">100% vaccinated &bull; Next due 12 Oct</p>
        </div>

        {/* KPI 4: Forward Mandi Escrow */}
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Forward Contract</span>
            <div class="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-lg">verified</span>
            </div>
          </div>
          <div class="mt-3">
            <span class="text-2xl font-black text-slate-900 tracking-tight">&#8377;4,85,000</span>
            <span class="text-xs text-sky-700 font-bold ml-2 bg-sky-50 px-1.5 py-0.5 rounded">
              Escrow Secured
            </span>
          </div>
          <p class="text-[11px] text-slate-400 mt-1">AgroCorp India Ltd &bull; 200 Quintals</p>
        </div>
      </div>

      {/* Two Column Section: Satellite Telemetry + Action Hub */}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Sentinel-2 Multispectral Preview */}
        <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="font-bold text-slate-900 text-base">Sentinel-2 STAC Multispectral Analysis</h3>
              <p class="text-xs text-slate-500">Plot 4A (4.2 Ha) &bull; Crop: Wheat HD-2967</p>
            </div>
            <A
              href="/soil/hub"
              class="text-xs font-semibold text-forest hover:text-forest-light px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-200"
            >
              Full GIS View &rarr;
            </A>
          </div>

          {/* Synthetic NDVI Heatmap View */}
          <div class="relative h-64 rounded-xl overflow-hidden bg-gradient-to-tr from-emerald-900 via-emerald-600 to-lime-400 flex items-center justify-center shadow-inner">
            <div class="absolute inset-0 bg-black/10"></div>
            <div class="relative z-10 text-center text-white p-4">
              <span class="material-symbols-outlined text-4xl mb-1 drop-shadow">radar</span>
              <div class="font-extrabold text-lg drop-shadow">Optimal Canopy Biomass (NDVI 0.74)</div>
              <div class="text-xs text-emerald-100 max-w-md mx-auto mt-1 drop-shadow">
                No signs of nitrogen stress or fungal infestation detected in the central cluster.
              </div>
            </div>
            {/* GIS Legend Tag */}
            <div class="absolute bottom-3 left-3 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-200 text-[11px] font-bold text-slate-800 shadow">
              NDVI Legend: <span class="text-red-500">&bull; 0.2</span> <span class="text-yellow-500">&bull; 0.5</span> <span class="text-emerald-600">&bull; 0.8+</span>
            </div>
          </div>

          {/* Soil Telemetry Bar */}
          <div class="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-100 text-center">
            <div class="bg-slate-50 p-2.5 rounded-xl">
              <span class="text-[10px] text-slate-500 font-bold uppercase block">Nitrogen (N)</span>
              <span class="text-sm font-bold text-slate-900">{telemetry().nitrogen} kg/ha</span>
              <span class="text-[10px] text-emerald-600 block font-semibold">Adequate</span>
            </div>
            <div class="bg-slate-50 p-2.5 rounded-xl">
              <span class="text-[10px] text-slate-500 font-bold uppercase block">Phosphorus (P)</span>
              <span class="text-sm font-bold text-slate-900">{telemetry().phosphorus} kg/ha</span>
              <span class="text-[10px] text-amber-600 block font-semibold">Slightly Low</span>
            </div>
            <div class="bg-slate-50 p-2.5 rounded-xl">
              <span class="text-[10px] text-slate-500 font-bold uppercase block">Potassium (K)</span>
              <span class="text-sm font-bold text-slate-900">{telemetry().potassium} kg/ha</span>
              <span class="text-[10px] text-emerald-600 block font-semibold">High</span>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Quick Actions & Agronomist Recommendations */}
        <div class="space-y-4">
          <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
            <h3 class="font-bold text-slate-900 text-sm">Quick Actions</h3>
            <div class="grid grid-cols-2 gap-2">
              <A
                href="/diagnose"
                class="flex flex-col items-center justify-center p-3 rounded-xl bg-forest/5 hover:bg-forest/10 border border-forest/15 text-forest font-semibold text-xs transition-all"
              >
                <span class="material-symbols-outlined text-2xl mb-1">photo_camera</span>
                <span>Scan Leaf</span>
              </A>
              <A
                href="/strategy/select-farm"
                class="flex flex-col items-center justify-center p-3 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200/60 text-amber-800 font-semibold text-xs transition-all"
              >
                <span class="material-symbols-outlined text-2xl mb-1">auto_awesome</span>
                <span>AI Strategy</span>
              </A>
              <A
                href="/livestock"
                class="flex flex-col items-center justify-center p-3 rounded-xl bg-sky-50 hover:bg-sky-100 border border-sky-200/60 text-sky-800 font-semibold text-xs transition-all"
              >
                <span class="material-symbols-outlined text-2xl mb-1">medical_services</span>
                <span>Call Vet</span>
              </A>
              <A
                href="/marketplace"
                class="flex flex-col items-center justify-center p-3 rounded-xl bg-purple-50 hover:bg-purple-100 border border-purple-200/60 text-purple-800 font-semibold text-xs transition-all"
              >
                <span class="material-symbols-outlined text-2xl mb-1">store</span>
                <span>Mandi Prices</span>
              </A>
            </div>
          </div>

          {/* AI Recommendation Widget */}
          <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-amber-500">lightbulb</span>
              <h3 class="font-bold text-slate-900 text-sm">Gemini Agronomist Insight</h3>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed">
              Based on your soil test and approaching humidity spike, apply 25 kg/ha Potassium Sulfate prior to irrigation on Plot 2.
            </p>
            <A
              href="/soil/hub"
              class="inline-block text-xs font-bold text-forest hover:underline"
            >
              View Fertilizer Plan &rarr;
            </A>
          </div>
        </div>
      </div>
    </div>
  );
};
