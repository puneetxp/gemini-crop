import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface ServiceQuotaMetric {
  id: string;
  name: string;
  model: string;
  callCount: number;
  tokenCount: number;
  percentOfTotal: number;
  cacheHitPct: number;
  barColor: string;
  statusBadge: string;
}

interface TierPolicy {
  tierName: string;
  userCount: number;
  monthlyScanLimit: string;
  rateLimitWindow: string;
  features: string;
  badgeColor: string;
}

export const QuotaMonitoring: Component = () => {
  const [grantModalOpen, setGrantModalOpen] = createSignal(false);
  const [grantSuccess, setGrantSuccess] = createSignal(false);
  const [selectedUserEmail, setSelectedUserEmail] = createSignal("farmer@baramati.agro");
  const [grantAmount, setGrantAmount] = createSignal("50");

  const [services] = createSignal<ServiceQuotaMetric[]>([
    {
      id: "vision-1",
      name: "Crop Disease Vision Diagnostic",
      model: "Vision AI Pathology",
      callCount: 14200,
      tokenCount: 2450000,
      percentOfTotal: 50.8,
      cacheHitPct: 99.8,
      barColor: "bg-emerald-600",
      statusBadge: "50.8% of Total",
    },
    {
      id: "satellite-1",
      name: "Satellite Cadastral Soil & NDVI Ingestion",
      model: "Sentinel-2 L2A + AI Reasoning",
      callCount: 2800,
      tokenCount: 1120000,
      percentOfTotal: 23.2,
      cacheHitPct: 92.4,
      barColor: "bg-blue-600",
      statusBadge: "23.2% of Total",
    },
    {
      id: "strategy-1",
      name: "Seasonal Crop Strategy & Agronomy Engine",
      model: "Agronomy Strategic AI",
      callCount: 940,
      tokenCount: 820000,
      percentOfTotal: 17.0,
      cacheHitPct: 88.0,
      barColor: "bg-purple-600",
      statusBadge: "17.0% of Total",
    },
    {
      id: "voice-1",
      name: "Multilingual Pashu Voice Assistant",
      model: "Voice Agronomist Audio",
      callCount: 470,
      tokenCount: 430000,
      percentOfTotal: 9.0,
      cacheHitPct: 75.0,
      barColor: "bg-amber-600",
      statusBadge: "9.0% of Total",
    },
  ]);

  const [tiers] = createSignal<TierPolicy[]>([
    {
      tierName: "Free Kisan Tier",
      userCount: 12400,
      monthlyScanLimit: "5 Scans / Mo",
      rateLimitWindow: "2 requests / minute (Sliding Window)",
      features: "Basic leaf diagnostic, APMC mandi rates",
      badgeColor: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300",
    },
    {
      tierName: "Pro Kisan Tier",
      userCount: 4120,
      monthlyScanLimit: "50 Scans / Mo",
      rateLimitWindow: "10 requests / minute",
      features: "Satellite NDVI plot mapping, annual strategy AI, priority vet queue",
      badgeColor: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300",
    },
    {
      tierName: "FPO Enterprise",
      userCount: 310,
      monthlyScanLimit: "Unlimited",
      rateLimitWindow: "60 requests / minute (Dedicated Endpoint)",
      features: "Full cadastral federation batch inference, custom SLA",
      badgeColor: "bg-purple-100 dark:bg-purple-950/60 text-purple-800 dark:text-purple-300",
    },
  ]);

  const handleGrantQuota = (e: Event) => {
    e.preventDefault();
    setGrantSuccess(true);
    setTimeout(() => {
      setGrantSuccess(false);
      setGrantModalOpen(false);
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
                <span class="material-symbols-outlined text-emerald-300 text-2xl">memory</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-base tracking-tight">CropSense AI</span>
                  <span class="text-[10px] uppercase font-bold tracking-widest bg-emerald-400/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-400/30">
                    Admin Quota
                  </span>
                </div>
                <p class="text-[11px] text-emerald-200/80">AI Token Allocations &amp; Sliding Window Rate Limits</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <A
                href="/admin/analytics"
                class="px-3 py-1.5 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">admin_panel_settings</span>
                <span>Platform Radar</span>
              </A>
              <A
                href="/quota/history"
                class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">history</span>
                <span>User Quota Log</span>
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
              <A href="/admin/analytics" class="hover:text-emerald-600 transition-colors">Admin</A>
              <span>/</span>
              <span class="font-medium text-slate-700 dark:text-slate-300">AI Quota Monitoring</span>
            </div>
            <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              AI Token Quota &amp; Rate Limiter Governance
            </h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Real-time AI token burn rate, sliding window throttle exceptions, and tier allocation grants
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button
              onClick={() => setGrantModalOpen(true)}
              class="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-base">add_moderator</span>
              <span>Grant Emergency Quota</span>
            </button>
          </div>
        </div>

        {/* 4 Summary KPI Ribbon */}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">24h Token Consumption</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">data_usage</span>
            </div>
            <div class="text-2xl font-black text-slate-900 dark:text-white">4.82M / 10M</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">48.2% Daily Quota Burn</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Vision Diagnostics</span>
              <span class="material-symbols-outlined text-blue-600 text-lg">photo_camera</span>
            </div>
            <div class="text-2xl font-black text-blue-700 dark:text-blue-400">18,420 Scans</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">Avg Latency: 820ms</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Rate Limit Throttles</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">speed</span>
            </div>
            <div class="text-2xl font-black text-emerald-800 dark:text-emerald-300">0 Throttles</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">Redis Fail-Open Active</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Active Tier Members</span>
              <span class="material-symbols-outlined text-purple-600 text-lg">badge</span>
            </div>
            <div class="text-2xl font-black text-purple-700 dark:text-purple-400">16,830 Farmers</div>
            <div class="text-[11px] text-purple-700 dark:text-purple-400 font-semibold">4,120 Pro • 310 Enterprise</div>
          </div>
        </div>

        {/* Multi-Column Grid: Services Burn & Tier Governance */}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Service Breakdown (7 cols) */}
          <div class="lg:col-span-7 space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-black text-base text-slate-900 dark:text-white">Token Consumption by AI Microservice</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400">Vision AI, Satellite NDVI and Voice processing loads</p>
                </div>
                <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Telemetry
                </span>
              </div>

              <div class="space-y-4 text-xs">
                <For each={services()}>
                  {(svc) => (
                    <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-2">
                      <div class="flex items-center justify-between">
                        <div>
                          <h4 class="font-black text-sm text-slate-900 dark:text-white">{svc.name}</h4>
                          <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                            Model: <span class="font-mono text-slate-700 dark:text-slate-300">{svc.model}</span> • {svc.callCount.toLocaleString()} Calls • {(svc.tokenCount / 1000000).toFixed(2)}M Tokens
                          </div>
                        </div>
                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300">
                          {svc.statusBadge}
                        </span>
                      </div>
                      <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          class={`h-2 rounded-full ${svc.barColor}`}
                          style={{ width: `${svc.percentOfTotal}%` }}
                        />
                      </div>
                      <div class="flex justify-between text-[10px] text-slate-400 pt-0.5">
                        <span>Cache Hit: {svc.cacheHitPct}%</span>
                        <span>Fail-Open Active</span>
                      </div>
                    </div>
                  )}
                </For>
              </div>
            </div>
          </div>

          {/* Right: Tier Allocations & Policies (5 cols) */}
          <div class="lg:col-span-5 space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 class="font-black text-base text-slate-900 dark:text-white">Subscription Tier Limits</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400">Monthly allowances &amp; sliding window rules</p>
                </div>
                <span class="text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-lg border border-emerald-200 dark:border-emerald-800">
                  Policy v2.4
                </span>
              </div>

              <div class="space-y-3 text-xs">
                <For each={tiers()}>
                  {(tier) => (
                    <div class="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1">
                      <div class="flex justify-between font-bold text-slate-900 dark:text-white">
                        <span>{tier.tierName} ({tier.userCount.toLocaleString()} Users)</span>
                        <span class="text-emerald-700 dark:text-emerald-400 font-bold">{tier.monthlyScanLimit}</span>
                      </div>
                      <div class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                        {tier.rateLimitWindow}
                      </div>
                      <div class="text-[10px] text-slate-400 mt-0.5">
                        {tier.features}
                      </div>
                    </div>
                  )}
                </For>
              </div>

              <div class="pt-2">
                <A
                  href="/quota/history"
                  class="w-full py-3 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center justify-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-sm">history</span>
                  <span>Inspect Audit Logs</span>
                </A>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Grant Quota Modal */}
      {grantModalOpen() && (
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600">add_moderator</span>
                <h3 class="font-black text-lg text-slate-900 dark:text-white">Grant Emergency AI Quota</h3>
              </div>
              <button
                onClick={() => setGrantModalOpen(false)}
                class="text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            {grantSuccess() ? (
              <div class="p-6 text-center space-y-2">
                <span class="material-symbols-outlined text-emerald-500 text-4xl">check_circle</span>
                <h4 class="font-bold text-slate-900 dark:text-white text-base">Quota Successfully Granted!</h4>
                <p class="text-xs text-slate-500">
                  Added +{grantAmount()} diagnostic scans to {selectedUserEmail()}.
                </p>
              </div>
            ) : (
              <form onSubmit={handleGrantQuota} class="space-y-4 text-xs">
                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Target Farmer Email / ID</label>
                  <input
                    type="text"
                    value={selectedUserEmail()}
                    onInput={(e) => setSelectedUserEmail(e.currentTarget.value)}
                    class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Additional Scans to Credit</label>
                  <select
                    value={grantAmount()}
                    onChange={(e) => setGrantAmount(e.currentTarget.value)}
                    class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="25">+25 Vision Diagnostic Scans</option>
                    <option value="50">+50 Vision Diagnostic Scans (Standard Relief)</option>
                    <option value="100">+100 Vision Diagnostic Scans</option>
                    <option value="500">+500 Scans (FPO Outbreak Investigation)</option>
                  </select>
                </div>

                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Reason for Administrative Grant</label>
                  <input
                    type="text"
                    value="Pest epidemic emergency relief in Junnar subdivision"
                    class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div class="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setGrantModalOpen(false)}
                    class="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="px-5 py-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold rounded-xl shadow"
                  >
                    Credit Account
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
export default QuotaMonitoring;
