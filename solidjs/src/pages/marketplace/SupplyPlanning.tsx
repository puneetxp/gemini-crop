import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface CommodityPlan {
  id: string;
  name: string;
  category: string;
  estimatedHarvestMt: number;
  institutionalDemandMt: number;
  balanceMt: number;
  balanceType: "surplus" | "deficit";
  progressPercent: number;
  peakInflowWindow: string;
  recommendation: string;
  urgency: "normal" | "warning" | "high";
}

interface ClusterTimeline {
  cluster: string;
  crop: string;
  stage: string;
  stagePercent: number;
  harvestWindow: string;
  farmersCount: number;
  volumeMt: number;
}

export const SupplyPlanning: Component = () => {
  const [selectedSeason, setSelectedSeason] = createSignal("Rabi Season 2026");
  const [tenderModalOpen, setTenderModalOpen] = createSignal(false);
  const [tenderSuccess, setTenderSuccess] = createSignal(false);

  const [commodities] = createSignal<CommodityPlan[]>([
    {
      id: "wheat-1",
      name: "Sharbati Milling Wheat",
      category: "Cereal Grain",
      estimatedHarvestMt: 6400,
      institutionalDemandMt: 5100,
      balanceMt: 1300,
      balanceType: "surplus",
      progressPercent: 80,
      peakInflowWindow: "25 Oct – 15 Nov",
      recommendation: "Hold 40% in WDRA Silo for late winter premium",
      urgency: "normal",
    },
    {
      id: "basmati-1",
      name: "Basmati 1121 Pusa Paddy",
      category: "Export Grain",
      estimatedHarvestMt: 3200,
      institutionalDemandMt: 3800,
      balanceMt: -600,
      balanceType: "deficit",
      progressPercent: 100,
      peakInflowWindow: "10 Nov – 30 Nov",
      recommendation: "Immediate Forward Lock Advised (Middle East demand)",
      urgency: "high",
    },
    {
      id: "soybean-1",
      name: "Organic Soybean (JS-335)",
      category: "Oilseed",
      estimatedHarvestMt: 2900,
      institutionalDemandMt: 3400,
      balanceMt: -500,
      balanceType: "deficit",
      progressPercent: 85,
      peakInflowWindow: "18 Oct – 05 Nov",
      recommendation: "Crushers Restocking: Pre-Harvest Escrows Active",
      urgency: "warning",
    },
    {
      id: "chana-1",
      name: "Desi Chana (Vijay Bold)",
      category: "Pulse",
      estimatedHarvestMt: 2300,
      institutionalDemandMt: 2500,
      balanceMt: -200,
      balanceType: "deficit",
      progressPercent: 92,
      peakInflowWindow: "01 Nov – 20 Nov",
      recommendation: "NAFED Procurement Buffer Meeting Price Support",
      urgency: "warning",
    },
  ]);

  const [clusters] = createSignal<ClusterTimeline[]>([
    {
      cluster: "Junnar & Baramati Cluster",
      crop: "Wheat",
      stage: "Ripening",
      stagePercent: 88,
      harvestWindow: "18 Oct – 28 Oct",
      farmersCount: 1850,
      volumeMt: 4200,
    },
    {
      cluster: "Niphad Valley Cluster",
      crop: "Basmati Paddy",
      stage: "Grain Fill",
      stagePercent: 74,
      harvestWindow: "02 Nov – 15 Nov",
      farmersCount: 920,
      volumeMt: 2800,
    },
    {
      cluster: "Wardha Basin Cluster",
      crop: "Soybean",
      stage: "Pod Maturity",
      stagePercent: 92,
      harvestWindow: "12 Oct – 22 Oct",
      farmersCount: 1400,
      volumeMt: 3100,
    },
    {
      cluster: "Satara Foothills Cluster",
      crop: "Desi Chana",
      stage: "Pod Hardening",
      stagePercent: 82,
      harvestWindow: "25 Oct – 08 Nov",
      farmersCount: 840,
      volumeMt: 1950,
    },
  ]);

  const handleLaunchTender = (e: Event) => {
    e.preventDefault();
    setTenderSuccess(true);
    setTimeout(() => {
      setTenderSuccess(false);
      setTenderModalOpen(false);
    }, 2000);
  };

  return (
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Top Header */}
      <header class="bg-forest-900 text-white border-b border-forest-800 sticky top-0 z-40 bg-[#064e3b]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex items-center justify-between h-16">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-400/30">
                <span class="material-symbols-outlined text-emerald-300 text-2xl">event_available</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-base tracking-tight">CropSense AI</span>
                  <span class="text-[10px] uppercase font-bold tracking-widest bg-emerald-400/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-400/30">
                    Planning
                  </span>
                </div>
                <p class="text-[11px] text-emerald-200/80">Regional Harvest Cadence &amp; Supply Forecasting</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <A
                href="/marketplace"
                class="px-3 py-1.5 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">storefront</span>
                <span>Marketplace</span>
              </A>
              <A
                href="/marketplace/buyer-dashboard"
                class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">shopping_cart</span>
                <span>Buyer Console</span>
              </A>
            </div>
          </div>
        </div>
      </header>

      <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Breadcrumb & Action Banner */}
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div>
            <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <A href="/" class="hover:text-emerald-600 transition-colors">Home</A>
              <span>/</span>
              <A href="/marketplace" class="hover:text-emerald-600 transition-colors">Marketplace</A>
              <span>/</span>
              <span class="font-medium text-slate-700 dark:text-slate-300">Supply Planning</span>
            </div>
            <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Regional Harvest Cadence &amp; Supply Planning
            </h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Satellite crop acreage estimation, predicted harvest inflow dates, and institutional demand deficits
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button
              onClick={() => setTenderModalOpen(true)}
              class="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-base">campaign</span>
              <span>Launch Procurement Tender</span>
            </button>
          </div>
        </div>

        {/* 4 Summary KPI Metric Ribbon */}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">60-Day District Harvest</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">agriculture</span>
            </div>
            <div class="text-2xl font-black text-slate-900 dark:text-white">14,800 MT</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">Across Pune &amp; Nashik Divisions</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Institutional Deficit</span>
              <span class="material-symbols-outlined text-red-600 text-lg">trending_down</span>
            </div>
            <div class="text-2xl font-black text-red-600 dark:text-red-400">-2,400 MT</div>
            <div class="text-[11px] text-red-600 dark:text-red-400 font-semibold">High Pre-Booking Competition</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Peak Harvest Glut</span>
              <span class="material-symbols-outlined text-amber-600 text-lg">event</span>
            </div>
            <div class="text-2xl font-black text-amber-700 dark:text-amber-400">15 Oct – 10 Nov</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">Recommended Storage Window</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Cold Chain Capacity</span>
              <span class="material-symbols-outlined text-blue-600 text-lg">warehouse</span>
            </div>
            <div class="text-2xl font-black text-slate-900 dark:text-white">68% Utilized</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">3,200 MT WDRA Buffer Left</div>
          </div>
        </div>

        {/* Multi-Column Layout */}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Commodity Balance & Forecasts (7 cols) */}
          <div class="lg:col-span-7 space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-black text-base text-slate-900 dark:text-white">Commodity Supply vs Institutional Demand</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400">Cadastral satellite acreage forecast vs corporate procurement tenders</p>
                </div>
                <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  {selectedSeason()}
                </span>
              </div>

              {/* Commodity Cards */}
              <div class="space-y-4 text-xs">
                <For each={commodities()}>
                  {(item) => (
                    <div
                      class={`p-4 rounded-xl border transition-all ${
                        item.urgency === "high"
                          ? "border-red-200 dark:border-red-900/60 bg-red-50/50 dark:bg-red-950/20"
                          : item.urgency === "warning"
                          ? "border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20"
                          : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40"
                      }`}
                    >
                      <div class="flex items-center justify-between">
                        <div>
                          <div class="flex items-center gap-2">
                            <h4 class="font-black text-sm text-slate-900 dark:text-white">{item.name}</h4>
                            <span class="text-[10px] text-slate-500 px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700">
                              {item.category}
                            </span>
                          </div>
                          <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                            Estimated Harvest: <span class="font-bold text-slate-700 dark:text-slate-300">{item.estimatedHarvestMt.toLocaleString()} MT</span> • Demand: <span class="font-bold text-slate-700 dark:text-slate-300">{item.institutionalDemandMt.toLocaleString()} MT</span>
                          </div>
                        </div>
                        <span
                          class={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                            item.balanceType === "surplus"
                              ? "bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300"
                              : "bg-red-100 dark:bg-red-900/60 text-red-800 dark:text-red-300"
                          }`}
                        >
                          {item.balanceType === "surplus" ? `+${item.balanceMt.toLocaleString()} MT Surplus` : `${item.balanceMt.toLocaleString()} MT Deficit`}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 my-2">
                        <div
                          class={`h-2 rounded-full ${
                            item.urgency === "high"
                              ? "bg-red-500"
                              : item.urgency === "warning"
                              ? "bg-amber-500"
                              : "bg-emerald-600"
                          }`}
                          style={{ width: `${Math.min(item.progressPercent, 100)}%` }}
                        />
                      </div>

                      <div class="flex flex-wrap justify-between text-[11px] text-slate-500 dark:text-slate-400 gap-1">
                        <span>Peak Inflow: <strong class="text-slate-700 dark:text-slate-300">{item.peakInflowWindow}</strong></span>
                        <span>{item.recommendation}</span>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </div>

          {/* Right Column: Regional Cluster Timeline (5 cols) */}
          <div class="lg:col-span-5 space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-black text-base text-slate-900 dark:text-white">Cluster Harvest Timeline</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400">Cadastral phenology stage radar</p>
                </div>
                <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Sentinel-2 Sync
                </span>
              </div>

              <div class="space-y-3 text-xs">
                <For each={clusters()}>
                  {(c) => (
                    <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                      <div class="flex justify-between font-bold text-slate-900 dark:text-white">
                        <span>{c.cluster} ({c.crop})</span>
                        <span class="text-emerald-700 dark:text-emerald-400">{c.stage} ({c.stagePercent}%)</span>
                      </div>
                      <div class="text-[11px] text-slate-500 dark:text-slate-400">
                        Expected Harvest Window: {c.harvestWindow}
                      </div>
                      <div class="flex justify-between text-[10px] text-emerald-700 dark:text-emerald-400 font-semibold pt-1">
                        <span>{c.farmersCount.toLocaleString()} Farmers Ready</span>
                        <span>{c.volumeMt.toLocaleString()} MT Predicted</span>
                      </div>
                    </div>
                  )}
                </For>
              </div>

              <div class="pt-2">
                <A
                  href="/marketplace/bookings"
                  class="w-full py-3 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center justify-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-sm">lock_clock</span>
                  <span>Reserve Cold Silo Slot (#W-14)</span>
                </A>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Procurement Tender Modal */}
      {tenderModalOpen() && (
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600">campaign</span>
                <h3 class="font-black text-lg text-slate-900 dark:text-white">Launch Institutional Tender</h3>
              </div>
              <button
                onClick={() => setTenderModalOpen(false)}
                class="text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            {tenderSuccess() ? (
              <div class="p-6 text-center space-y-2">
                <span class="material-symbols-outlined text-emerald-500 text-4xl">check_circle</span>
                <h4 class="font-bold text-slate-900 dark:text-white text-base">Tender Published to 3,200 Farmers</h4>
                <p class="text-xs text-slate-500">Escrow smart contract broadcasted across Pune &amp; Nashik clusters.</p>
              </div>
            ) : (
              <form onSubmit={handleLaunchTender} class="space-y-4 text-xs">
                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Target Commodity</label>
                  <select class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white">
                    <option>Sharbati Milling Wheat (Grade-A)</option>
                    <option>Basmati 1121 Pusa Paddy</option>
                    <option>Organic Soybean (JS-335)</option>
                    <option>Desi Chana (Vijay)</option>
                  </select>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Required Quantity (MT)</label>
                    <input
                      type="number"
                      value="500"
                      class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-mono"
                    />
                  </div>
                  <div>
                    <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Target Price (₹/Quintal)</label>
                    <input
                      type="number"
                      value="2750"
                      class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Delivery Window</label>
                  <input
                    type="text"
                    value="20 Oct – 05 Nov 2026"
                    class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div class="p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-200 dark:border-emerald-800 text-[11px] text-emerald-800 dark:text-emerald-300">
                  ⚡ <strong>Advance Escrow Lock</strong>: 15% booking deposit (₹2,06,250) will be placed into ICICI/HDFC Escrow Vault upon first farmer bid acceptance.
                </div>

                <div class="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setTenderModalOpen(false)}
                    class="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="px-5 py-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold rounded-xl shadow"
                  >
                    Publish Tender
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
export default SupplyPlanning;
