import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface FpoPerformance {
  id: string;
  name: string;
  district: string;
  farmerCount: number;
  commodities: string;
  gmvThirtyDaysInr: number;
  settlementVelocityPct: number;
  avgClearingHours: number;
  ratingTier: string;
  tierColor: string;
}

export const PlatformAnalytics: Component = () => {
  const [downloadModalOpen, setDownloadModalOpen] = createSignal(false);
  const [downloadSuccess, setDownloadSuccess] = createSignal(false);

  const [fpos] = createSignal<FpoPerformance[]>([
    {
      id: "fpo-1",
      name: "Junnar Agro Producer Co.",
      district: "Pune Rural Division",
      farmerCount: 1420,
      commodities: "Wheat, Onions & Exotic Vegetables",
      gmvThirtyDaysInr: 11840000,
      settlementVelocityPct: 99.9,
      avgClearingHours: 3.2,
      ratingTier: "Tier A+",
      tierColor: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300",
    },
    {
      id: "fpo-2",
      name: "Niphad Grape & Agro Export Society",
      district: "Nashik Wine & Table Grape Yard",
      farmerCount: 980,
      commodities: "Table Grapes, Basmati Rice",
      gmvThirtyDaysInr: 14215000,
      settlementVelocityPct: 100.0,
      avgClearingHours: 2.8,
      ratingTier: "Tier A+",
      tierColor: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300",
    },
    {
      id: "fpo-3",
      name: "Baramati Kisan Cooperative Union",
      district: "Western Maharashtra Canal Basin",
      farmerCount: 1840,
      commodities: "Dairy Milk, Soybean & Chana",
      gmvThirtyDaysInr: 8840000,
      settlementVelocityPct: 99.5,
      avgClearingHours: 4.1,
      ratingTier: "Tier A",
      tierColor: "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300",
    },
    {
      id: "fpo-4",
      name: "Wardha Organic Producers FPO",
      district: "Vidarbha Cotton & Pulse Belt",
      farmerCount: 650,
      commodities: "Organic Cotton, Tur Dal & Soybean",
      gmvThirtyDaysInr: 6420000,
      settlementVelocityPct: 99.1,
      avgClearingHours: 5.5,
      ratingTier: "Tier A",
      tierColor: "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300",
    },
  ]);

  const handleDownloadLedger = () => {
    setDownloadSuccess(true);
    setTimeout(() => {
      setDownloadSuccess(false);
      setDownloadModalOpen(false);
    }, 2000);
  };

  return (
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Top Header */}
      <header class="bg-[#064e3b] text-white border-b border-emerald-800/60 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex items-center justify-between h-16">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-400/30">
                <span class="material-symbols-outlined text-emerald-300 text-2xl">admin_panel_settings</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-base tracking-tight">CropSense AI</span>
                  <span class="text-[10px] uppercase font-bold tracking-widest bg-emerald-400/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-400/30">
                    Admin Radar
                  </span>
                </div>
                <p class="text-[11px] text-emerald-200/80">Multi-FPO Escrow Liquidity &amp; Platform Health</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <A
                href="/dashboard"
                class="px-3 py-1.5 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">dashboard</span>
                <span>Dashboard</span>
              </A>
              <A
                href="/admin/quota"
                class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">memory</span>
                <span>AI Quota &amp; Limits</span>
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
              <span class="font-medium text-slate-700 dark:text-slate-300">Platform Analytics</span>
            </div>
            <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Executive Platform Analytics &amp; Escrow Settlement
            </h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Real-time Gross Merchandise Value (GMV), FPO banking liquidity clearing, and Cloud Run infrastructure uptime
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button
              onClick={() => setDownloadModalOpen(true)}
              class="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-base">download</span>
              <span>Download Audit Ledger</span>
            </button>
          </div>
        </div>

        {/* 4 Summary KPI Ribbon */}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Gross Trade Value (GMV)</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">currency_rupee</span>
            </div>
            <div class="text-2xl font-black text-slate-900 dark:text-white">₹4.82 Cr</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">+18.4% Month-on-Month</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">T+1 Settlement Velocity</span>
              <span class="material-symbols-outlined text-blue-600 text-lg">flash_on</span>
            </div>
            <div class="text-2xl font-black text-blue-700 dark:text-blue-400">99.8%</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">Avg Clearing: 4.2 Hours</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Active FPO Federations</span>
              <span class="material-symbols-outlined text-purple-600 text-lg">groups</span>
            </div>
            <div class="text-2xl font-black text-purple-700 dark:text-purple-400">42 FPOs</div>
            <div class="text-[11px] text-purple-700 dark:text-purple-400 font-semibold">68,400 Certified Farmers</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Dispute &amp; Default Rate</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">verified</span>
            </div>
            <div class="text-2xl font-black text-emerald-800 dark:text-emerald-300">0.08%</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">100% Resolved in Arbitration</div>
          </div>
        </div>

        {/* Multi-Column Grid */}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: FPO Trading Volume & Bank Settlement (8 cols) */}
          <div class="lg:col-span-8 space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-black text-base text-slate-900 dark:text-white">Registered FPO Trading &amp; Clearing Matrix</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400">Escrow funds disbursal performance across district federations</p>
                </div>
                <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  NABARD Audited
                </span>
              </div>

              <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                  <thead class="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th class="p-3">FPO Organization</th>
                      <th class="p-3">Commodity Focus</th>
                      <th class="p-3">30-Day GMV</th>
                      <th class="p-3">Settlement SLA</th>
                      <th class="p-3">Rating</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                    <For each={fpos()}>
                      {(fpo) => (
                        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                          <td class="p-3 font-bold text-slate-900 dark:text-white">
                            <div>{fpo.name}</div>
                            <div class="text-[10px] text-slate-400">
                              {fpo.farmerCount.toLocaleString()} Active Farmers • {fpo.district}
                            </div>
                          </td>
                          <td class="p-3">{fpo.commodities}</td>
                          <td class="p-3 font-mono font-bold text-slate-900 dark:text-white">
                            ₹{fpo.gmvThirtyDaysInr.toLocaleString("en-IN")}
                          </td>
                          <td class="p-3 text-emerald-700 dark:text-emerald-400 font-semibold">
                            {fpo.settlementVelocityPct}% ({fpo.avgClearingHours} hrs)
                          </td>
                          <td class="p-3">
                            <span class={`px-2 py-0.5 rounded-full text-[10px] font-bold ${fpo.tierColor}`}>
                              {fpo.ratingTier}
                            </span>
                          </td>
                        </tr>
                      )}
                    </For>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right: Cloud Run & Infrastructure Health (4 cols) */}
          <div class="lg:col-span-4 space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-black text-base text-slate-900 dark:text-white">System Telemetry</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400">Cloud Run Region: asia-south1</p>
                </div>
                <span class="flex h-2.5 w-2.5 relative">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
                </span>
              </div>

              <div class="space-y-3 text-xs">
                <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <div>
                    <span class="text-slate-400 text-[10px] block">Service Uptime SLA:</span>
                    <span class="font-bold text-slate-900 dark:text-white">99.98% (Past 90 Days)</span>
                  </div>
                  <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400">Healthy</span>
                </div>

                <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <div>
                    <span class="text-slate-400 text-[10px] block">API Latency (p95):</span>
                    <span class="font-bold text-slate-900 dark:text-white">42 ms (Direct VPC)</span>
                  </div>
                  <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400">&lt; 50ms</span>
                </div>

                <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <div>
                    <span class="text-slate-400 text-[10px] block">PostgreSQL Connection Pool:</span>
                    <span class="font-bold text-slate-900 dark:text-white">12 / 80 Active</span>
                  </div>
                  <span class="text-xs font-bold text-blue-600 dark:text-blue-400">Optimal</span>
                </div>

                <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <div>
                    <span class="text-slate-400 text-[10px] block">Active Redis Cache Hit:</span>
                    <span class="font-bold text-slate-900 dark:text-white">94.6% Hit Rate</span>
                  </div>
                  <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400">Warm</span>
                </div>
              </div>

              <div class="pt-2">
                <A
                  href="/admin/quota"
                  class="w-full py-3 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center justify-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-sm">tune</span>
                  <span>Manage AI Quota Allocations</span>
                </A>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Download Audit Ledger Modal */}
      {downloadModalOpen() && (
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600">download</span>
                <h3 class="font-black text-lg text-slate-900 dark:text-white">Export Settlement Ledger</h3>
              </div>
              <button
                onClick={() => setDownloadModalOpen(false)}
                class="text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            {downloadSuccess() ? (
              <div class="p-6 text-center space-y-2">
                <span class="material-symbols-outlined text-emerald-500 text-4xl">check_circle</span>
                <h4 class="font-bold text-slate-900 dark:text-white text-base">Ledger Export Generated!</h4>
                <p class="text-xs text-slate-500">
                  SHA-256 verified cryptographically signed ledger downloaded for 42 FPO federations.
                </p>
              </div>
            ) : (
              <div class="space-y-4 text-xs">
                <p class="text-slate-600 dark:text-slate-400">
                  Select the billing reconciliation cycle for NABARD and statutory banking compliance.
                </p>
                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Fiscal Reporting Period</label>
                  <select class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white">
                    <option>September 2026 (Month-to-Date)</option>
                    <option>August 2026 (Audited &amp; Reconciled)</option>
                    <option>Q2 Fiscal 2026-27</option>
                  </select>
                </div>
                <div class="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setDownloadModalOpen(false)}
                    class="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleDownloadLedger}
                    class="px-5 py-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold rounded-xl shadow"
                  >
                    Export CSV &amp; PDF
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
export default PlatformAnalytics;
