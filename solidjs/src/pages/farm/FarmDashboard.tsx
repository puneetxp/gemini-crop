import { Component, createSignal, For, Show, onMount } from "solid-js";
import { A, useParams } from "@solidjs/router";
import { apiClient } from "../../lib/api-client";

interface PlotItem {
  id: string;
  name: string;
  gatNo: string;
  crop: string;
  acres: number;
  stage: string;
  progressPercent: number;
  ndvi: number;
  ndviStatus: string;
  soilMoisture: string;
  alertTitle?: string;
  alertMsg?: string;
  alertType?: "warning" | "info" | "success";
  borderColor: string;
}

export const FarmDashboard: Component = () => {
  const params = useParams();
  const farmId = () => params.id || "1";

  const [loading, setLoading] = createSignal(false);
  const [activeTab, setActiveTab] = createSignal<"grid" | "gis">("grid");
  const [viewMode, setViewMode] = createSignal<"all" | "active" | "fallow">("all");

  // Farm details
  const [farmData, setFarmData] = createSignal({
    id: 1,
    name: "Krishna Valley Farm",
    icarId: "MH-NSK-2024-8841",
    location: "Niphad, Nashik, Maharashtra",
    totalAcres: 18.5,
    cultivatedAcres: 13.5,
    fallowAcres: 5.0,
    plotsCount: 4,
    meanNdvi: 0.76,
    soilMoisture: "38.4% VWC",
    activeIotNodes: 6,
    estRevenue: "₹4,12,000",
    expendedBudget: "₹1,24,000",
    projectedRoi: "+68%",
  });

  const plots: PlotItem[] = [
    {
      id: "plot-a",
      name: "Plot A • North Orchard",
      gatNo: "Gat No. 142/2A",
      crop: "Thomson Seedless Grapes",
      acres: 5.2,
      stage: "Berry Development • Day 64 of 120",
      progressPercent: 55,
      ndvi: 0.82,
      ndviStatus: "Lush Canopy",
      soilMoisture: "38.2% VWC",
      alertTitle: "Drip Fertigation in 3h",
      alertMsg: "Soluble NPK 00:52:34 scheduled via Micro-jet",
      alertType: "info",
      borderColor: "border-t-emerald-700",
    },
    {
      id: "plot-b",
      name: "Plot B • Central Parcel",
      gatNo: "Gat No. 142/2B",
      crop: "Sharbati Durum Wheat",
      acres: 4.8,
      stage: "Crown Root Initiation • Day 22 of 110",
      progressPercent: 20,
      ndvi: 0.74,
      ndviStatus: "Vigorous",
      soilMoisture: "41.0% VWC",
      alertTitle: "Urea Top-Dress Alert",
      alertMsg: "1st Split Nitrogen dosage recommended within 48h",
      alertType: "warning",
      borderColor: "border-t-amber-600",
    },
    {
      id: "plot-c",
      name: "Plot C • South Terrace",
      gatNo: "Gat No. 143/1",
      crop: "Bhagwa Pomegranate",
      acres: 3.5,
      stage: "Flowering & Fruit Setting • Day 48",
      progressPercent: 40,
      ndvi: 0.79,
      ndviStatus: "Healthy",
      soilMoisture: "34.1% VWC",
      alertTitle: "Pheromone Trap Check",
      alertMsg: "Fruit borer preventive maintenance due tomorrow",
      alertType: "warning",
      borderColor: "border-t-emerald-700",
    },
    {
      id: "plot-d",
      name: "Plot D • Lower Basin",
      gatNo: "Gat No. 143/2",
      crop: "Dhaincha Green Manure",
      acres: 5.0,
      stage: "Soil Reconditioning • Pre-Kharif",
      progressPercent: 75,
      ndvi: 0.68,
      ndviStatus: "Moderate Cover",
      soilMoisture: "32.0% VWC",
      alertTitle: "Incorporation Scheduled",
      alertMsg: "In-situ rotavator green manure biomass incorporation at 45d",
      alertType: "info",
      borderColor: "border-t-slate-400",
    },
  ];

  onMount(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<any>(`/farms/${farmId()}`);
      if (res) {
        setFarmData((prev) => ({
          ...prev,
          name: res.name || prev.name,
          location: res.location || prev.location,
          totalAcres: res.total_acres || prev.totalAcres,
        }));
      }
    } catch {
      // Graceful offline mock fallback
    } finally {
      setLoading(false);
    }
  });

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* TOP HEADER & WEATHER TELEMETRY STRIP */}
      <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          {/* Breadcrumbs */}
          <div class="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <A href="/dashboard" class="hover:text-emerald-700">Home</A>
            <span>/</span>
            <A href="/farm" class="hover:text-emerald-700">My Farms & Plots</A>
            <span>/</span>
            <span class="text-slate-900 font-semibold">{farmData().name}</span>
          </div>

          <div class="flex flex-wrap items-center gap-2.5 mt-1.5">
            <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">
              {farmData().name} Operations Hub
            </h1>
            <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              ICAR ID #{farmData().icarId}
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">{farmData().location} • 4 Cadastral Plots Registered</p>
        </div>

        {/* Live Microclimate Station Pill */}
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2 bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200 text-xs">
            <span class="material-symbols-outlined text-amber-500 text-base">sunny</span>
            <div>
              <span class="font-bold text-slate-900 block leading-tight">28°C • Sunny</span>
              <span class="text-[10px] text-slate-500">62% RH • Wind 11 km/h W • AQI 42</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div class="flex items-center gap-2">
            <A
              href="/crops/plant"
              class="px-3.5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all active:scale-98"
            >
              <span class="material-symbols-outlined text-sm">agriculture</span>
              <span>Plant Crop</span>
            </A>
            <A
              href="/farm/register"
              class="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <span class="material-symbols-outlined text-sm">add_location_alt</span>
              <span>+ Add Plot</span>
            </A>
          </div>
        </div>
      </div>

      {/* TOP TELEMETRY KPI METRICS ROW */}
      <div class="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        {/* KPI 1 */}
        <div class="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-1">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>Total Holding</span>
            <span class="material-symbols-outlined text-base text-emerald-700">yard</span>
          </div>
          <p class="text-xl font-black text-slate-900">{farmData().totalAcres} Acres</p>
          <p class="text-[11px] text-slate-500 font-medium">13.5 Ac Sown • 5.0 Ac Fallow</p>
        </div>

        {/* KPI 2 */}
        <div class="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-1">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>Sentinel-2 NDVI</span>
            <span class="material-symbols-outlined text-base text-emerald-600">satellite_alt</span>
          </div>
          <p class="text-xl font-black text-emerald-800">{farmData().meanNdvi} Optimal</p>
          <p class="text-[11px] text-emerald-700 font-semibold flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Vigorous Growth (10m)</span>
          </p>
        </div>

        {/* KPI 3 */}
        <div class="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-1">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>Rootzone Moisture</span>
            <span class="material-symbols-outlined text-base text-blue-600">water_drop</span>
          </div>
          <p class="text-xl font-black text-slate-900">{farmData().soilMoisture}</p>
          <p class="text-[11px] text-blue-700 font-medium">Safe Buffer (35-45%)</p>
        </div>

        {/* KPI 4 */}
        <div class="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-1">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>IoT Sensor Mesh</span>
            <span class="material-symbols-outlined text-base text-emerald-600">sensors</span>
          </div>
          <p class="text-xl font-black text-slate-900">{farmData().activeIotNodes} Online</p>
          <p class="text-[11px] text-emerald-700 font-semibold">0 Offline • 99.8% Uptime</p>
        </div>

        {/* KPI 5 */}
        <div class="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-1 col-span-2 md:col-span-1">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span>Rabi Projected P&L</span>
            <span class="material-symbols-outlined text-base text-amber-600">monetization_on</span>
          </div>
          <p class="text-xl font-black text-slate-900">{farmData().estRevenue}</p>
          <p class="text-[11px] text-emerald-700 font-bold">{farmData().projectedRoi} Projected ROI</p>
        </div>
      </div>

      {/* AGRO-ADVISORY & SPRAY WINDOW BANNER */}
      <div class="bg-gradient-to-r from-emerald-950 to-emerald-900 text-white rounded-2xl p-4 sm:p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-800/80 flex items-center justify-center text-emerald-300 shrink-0">
            <span class="material-symbols-outlined text-xl">air</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="bg-emerald-700 text-emerald-100 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                IMD & KVK Real-time Advisory
              </span>
              <span class="text-xs text-emerald-300 font-semibold">Today: 04:30 PM — 07:15 PM</span>
            </div>
            <h3 class="text-base font-bold text-white mt-0.5">Optimal Pesticide & Micronutrient Spray Window</h3>
            <p class="text-xs text-emerald-200/90 mt-0.5 leading-relaxed">
              Wind velocity &lt;8 km/h, relative humidity at 58%, and no rain forecast in next 36 hours. Ideal for prophylactic Powdery Mildew spray on Plot A Grapes.
            </p>
          </div>
        </div>

        <A
          href="/strategy/select-farm"
          class="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-emerald-950 font-bold text-xs rounded-xl transition-all shrink-0 self-start md:self-auto"
        >
          View Full Advisory
        </A>
      </div>

      {/* PLOT DIRECTORY SECTION & CONTROLS */}
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-black text-slate-900">Demarcated Cadastral Plots (4)</h2>
            <p class="text-xs text-slate-500">Live vegetative telemetry, crop stage trackers, and IoT node assignments</p>
          </div>

          <div class="flex items-center gap-2">
            <div class="flex items-center p-1 bg-slate-100 rounded-xl border border-slate-200 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveTab("grid")}
                class={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  activeTab() === "grid" ? "bg-white text-slate-900 shadow-xs font-bold" : "text-slate-500"
                }`}
              >
                <span class="material-symbols-outlined text-sm">grid_view</span>
                <span>Plot Cards</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("gis")}
                class={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  activeTab() === "gis" ? "bg-white text-slate-900 shadow-xs font-bold" : "text-slate-500"
                }`}
              >
                <span class="material-symbols-outlined text-sm">satellite_alt</span>
                <span>GIS Map</span>
              </button>
            </div>
          </div>
        </div>

        {/* VIEW 1: PLOT CARDS GRID */}
        <Show when={activeTab() === "grid"}>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <For each={plots}>
              {(plot) => (
                <div class={`bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between border-t-4 ${plot.borderColor} hover:shadow-md transition-all`}>
                  <div class="space-y-3">
                    <div class="flex items-start justify-between">
                      <div>
                        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">{plot.gatNo}</span>
                        <h3 class="font-bold text-sm text-slate-900 mt-0.5">{plot.crop}</h3>
                        <p class="text-xs text-slate-500">{plot.name}</p>
                      </div>
                      <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {plot.acres} Ac
                      </span>
                    </div>

                    {/* Stage & Progress Bar */}
                    <div>
                      <div class="flex items-center justify-between text-xs text-slate-600 mb-1">
                        <span class="font-semibold text-emerald-800">{plot.stage}</span>
                        <span class="text-[10px] text-slate-400">{plot.progressPercent}%</span>
                      </div>
                      <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-emerald-600 h-full rounded-full" style={{ width: `${plot.progressPercent}%` }}></div>
                      </div>
                    </div>

                    {/* Metrics Breakdown */}
                    <div class="grid grid-cols-2 gap-2 text-xs">
                      <div class="p-2 rounded-xl bg-slate-50 border border-slate-100">
                        <span class="text-[10px] text-slate-400 block">Plot NDVI</span>
                        <span class="text-xs font-black text-emerald-800">{plot.ndvi} ({plot.ndviStatus})</span>
                      </div>
                      <div class="p-2 rounded-xl bg-slate-50 border border-slate-100">
                        <span class="text-[10px] text-slate-400 block">Soil Moisture</span>
                        <span class="text-xs font-black text-slate-900">{plot.soilMoisture}</span>
                      </div>
                    </div>

                    {/* Advisory Alert */}
                    <Show when={plot.alertTitle}>
                      <div class={`p-2.5 rounded-xl border text-xs flex items-center gap-2 ${
                        plot.alertType === "warning"
                          ? "bg-amber-50 border-amber-200 text-amber-900"
                          : "bg-emerald-50 border-emerald-200 text-emerald-900"
                      }`}>
                        <span class="material-symbols-outlined text-base shrink-0">
                          {plot.alertType === "warning" ? "pest_control" : "water_drop"}
                        </span>
                        <div class="text-[11px] leading-tight">
                          <span class="font-bold block">{plot.alertTitle}</span>
                          <span>{plot.alertMsg}</span>
                        </div>
                      </div>
                    </Show>
                  </div>

                  {/* Actions footer */}
                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <A
                      href="/diagnose"
                      class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold flex items-center gap-1 transition-colors"
                    >
                      <span class="material-symbols-outlined text-sm">qr_code_scanner</span>
                      <span>AI Scan</span>
                    </A>
                    <A
                      href={`/soil/hub`}
                      class="font-bold text-emerald-700 hover:text-emerald-800 flex items-center gap-0.5"
                    >
                      <span>Telemetry</span>
                      <span class="material-symbols-outlined text-sm">arrow_forward</span>
                    </A>
                  </div>
                </div>
              )}
            </For>
          </div>
        </Show>

        {/* VIEW 2: GIS SATELLITE MAP */}
        <Show when={activeTab() === "gis"}>
          <div class="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div class="relative bg-slate-950 h-[400px] w-full flex items-center justify-center select-none overflow-hidden">
              <div
                class="absolute inset-0 opacity-40 bg-cover bg-center"
                style={{
                  "background-image":
                    "radial-gradient(#10b981 0.75px, transparent 0.75px), radial-gradient(#10b981 0.75px, #042f2e 0.75px)",
                  "background-size": "30px 30px",
                }}
              />
              <svg class="absolute inset-0 w-full h-full" viewBox="0 0 600 400" preserveAspectRatio="none">
                <polygon points="60,60 280,80 270,320 80,300" fill="rgba(16, 185, 129, 0.25)" stroke="#10b981" stroke-width="2" />
                <polygon points="290,80 520,95 490,330 280,320" fill="rgba(245, 158, 11, 0.25)" stroke="#f59e0b" stroke-width="2" />
              </svg>
              <div class="z-10 bg-slate-900/90 backdrop-blur-md border border-emerald-500/40 p-4 rounded-xl text-center shadow-xl max-w-sm">
                <span class="material-symbols-outlined text-emerald-400 text-2xl">satellite_alt</span>
                <p class="text-white text-sm font-bold mt-1">Sentinel-2B True Orthomosaic Multispectral View</p>
                <p class="text-slate-400 text-xs mt-0.5">Plot A (0.82 NDVI), Plot B (0.74 NDVI), Plot C (0.79 NDVI), Plot D (0.68 NDVI)</p>
                <p class="text-emerald-400 text-[11px] font-mono mt-2">Next Satellite Overpass: Tomorrow 11:24 AM IST</p>
              </div>
            </div>
          </div>
        </Show>
      </div>

      {/* BOTTOM SECTION: APMC MANDI RATES & SOIL HEALTH */}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* APMC Mandi Benchmark Rates */}
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-100">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-emerald-700">storefront</span>
              <h3 class="font-bold text-sm text-slate-900">APMC Nashik & Pimpalgaon Live Rates</h3>
            </div>
            <span class="text-[10px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">Today 11:30 AM</span>
          </div>

          <div class="space-y-2 text-xs">
            <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-50">
              <div>
                <span class="font-bold text-slate-900 block">Export Grapes (Thomson)</span>
                <span class="text-[11px] text-slate-500">Nashik Main Yard</span>
              </div>
              <div class="text-right">
                <span class="font-bold text-emerald-800 text-sm">₹92 / kg</span>
                <span class="text-[10px] text-emerald-600 block font-semibold">+₹4.50 Today</span>
              </div>
            </div>

            <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-50">
              <div>
                <span class="font-bold text-slate-900 block">Sharbati Durum Wheat</span>
                <span class="text-[11px] text-slate-500">Lasalgaon APMC</span>
              </div>
              <div class="text-right">
                <span class="font-bold text-emerald-800 text-sm">₹2,840 / Qtl</span>
                <span class="text-[10px] text-slate-500 block">MSP: ₹2,275</span>
              </div>
            </div>

            <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-50">
              <div>
                <span class="font-bold text-slate-900 block">Pomegranate (Bhagwa Grade-A)</span>
                <span class="text-[11px] text-slate-500">Dindori Mandi</span>
              </div>
              <div class="text-right">
                <span class="font-bold text-emerald-800 text-sm">₹145 / kg</span>
                <span class="text-[10px] text-emerald-600 block font-semibold">+₹8.00 Strong</span>
              </div>
            </div>
          </div>
        </div>

        {/* Soil Chemical & NPK Status */}
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-100">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-emerald-700">science</span>
              <h3 class="font-bold text-sm text-slate-900">Soil Chemical & NPK Status</h3>
            </div>
            <span class="text-xs text-slate-500 font-medium">NABL Accredited</span>
          </div>

          <div class="space-y-2.5 text-xs">
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-700 font-medium">Nitrogen (N) - Medium</span>
                <span class="font-bold text-slate-900">264 kg/Ha <span class="text-slate-400 font-normal">(Optimal 280)</span></span>
              </div>
              <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div class="bg-amber-500 h-full rounded-full" style="width: 70%"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-700 font-medium">Phosphorus (P₂O₅) - High</span>
                <span class="font-bold text-emerald-800">38 kg/Ha <span class="text-slate-400 font-normal">(Optimal 25)</span></span>
              </div>
              <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div class="bg-emerald-600 h-full rounded-full" style="width: 90%"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-700 font-medium">Potassium (K₂O) - Ideal</span>
                <span class="font-bold text-emerald-800">312 kg/Ha <span class="text-slate-400 font-normal">(Optimal 300)</span></span>
              </div>
              <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div class="bg-emerald-600 h-full rounded-full" style="width: 85%"></div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2 pt-1 text-center">
              <div class="p-2 rounded-xl bg-slate-50">
                <span class="text-[10px] text-slate-400 block">Soil pH</span>
                <span class="text-xs font-bold text-slate-900">7.2 (Neutral)</span>
              </div>
              <div class="p-2 rounded-xl bg-slate-50">
                <span class="text-[10px] text-slate-400 block">Electrical Cond.</span>
                <span class="text-xs font-bold text-slate-900">0.42 dS/m (Safe)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
