import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface MandiRate {
  mandi: string;
  region: string;
  spotPrice: number;
  transportCost: number;
  distanceKm: number;
  transitHours: number;
  netMargin: number;
  statusBadge: string;
  highlight?: boolean;
}

export const MarketIntelligence: Component = () => {
  const [selectedCrop, setSelectedCrop] = createSignal("Wheat (Sharbati Golden)");

  const cropList = [
    "Wheat (Sharbati Golden)",
    "Basmati 1121 Paddy",
    "Desi Chana (Vijay)",
    "Organic Soybean (JS-335)",
    "Cotton (Medium Staple)",
  ];

  const [mandiRates] = createSignal<MandiRate[]>([
    {
      mandi: "Vashi APMC (Navi Mumbai)",
      region: "Coastal Maharashtra Mega-Terminal",
      spotPrice: 2730,
      transportCost: 85,
      distanceKm: 154,
      transitHours: 4.2,
      netMargin: 195,
      statusBadge: "Peak Net Margin",
      highlight: true,
    },
    {
      mandi: "Pune Gultekdi APMC",
      region: "Western Maharashtra Main Yard",
      spotPrice: 2580,
      transportCost: 45,
      distanceKm: 62,
      transitHours: 1.8,
      netMargin: 85,
      statusBadge: "High Volume",
    },
    {
      mandi: "Baramati Local APMC",
      region: "Pune Rural Subdivision",
      spotPrice: 2450,
      transportCost: 15,
      distanceKm: 18,
      transitHours: 0.5,
      netMargin: 0,
      statusBadge: "Local Baseline",
    },
    {
      mandi: "Nashik Dindori Mandi",
      region: "North Maharashtra Agro Hub",
      spotPrice: 2490,
      transportCost: 90,
      distanceKm: 180,
      transitHours: 4.8,
      netMargin: 20,
      statusBadge: "Moderate Demand",
    },
  ]);

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* Top Header & Breadcrumbs */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <A href="/marketplace" class="hover:text-forest transition-colors">Marketplace</A>
            <span>/</span>
            <span class="font-medium text-slate-700">Market Intelligence &amp; Forecasts</span>
          </div>
          <h1 class="text-xl lg:text-2xl font-black text-slate-900 tracking-tight">
            Hyperlocal Mandi Price Forecasts &amp; Arbitrage
          </h1>
          <p class="text-xs text-slate-500 mt-0.5">
            AI predictive price curves, arrival volatility, and inter-mandi net arbitrage margins
          </p>
        </div>

        <div class="flex items-center gap-2 self-start sm:self-auto">
          <span class="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
            <span class="material-symbols-outlined text-sm">lightbulb</span>
            AI Advisory: Hold 30% Lot for Nov Peak (+7.1%)
          </span>
        </div>
      </div>

      {/* 4 Summary KPI Metric Cards */}
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Current Spot Price</span>
            <span class="material-symbols-outlined text-forest text-lg">currency_rupee</span>
          </div>
          <div class="text-2xl font-black text-slate-900">₹2,540 / Qtl</div>
          <div class="text-[11px] text-emerald-700 font-semibold">+6.8% Above State MSP (₹2,275)</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">30-Day AI Forecast</span>
            <span class="material-symbols-outlined text-emerald-600 text-lg">insights</span>
          </div>
          <div class="text-2xl font-black text-forest">₹2,720 / Qtl</div>
          <div class="text-[11px] text-emerald-700 font-semibold">+7.1% Post-Diwali Surge</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Peak Arbitrage Spread</span>
            <span class="material-symbols-outlined text-blue-600 text-lg">compare_arrows</span>
          </div>
          <div class="text-2xl font-black text-slate-900">₹280 / Qtl</div>
          <div class="text-[11px] text-slate-500">Pune vs Vashi APMC</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Market Volatility</span>
            <span class="material-symbols-outlined text-amber-600 text-lg">equalizer</span>
          </div>
          <div class="text-2xl font-black text-amber-700">14.2 (Low)</div>
          <div class="text-[11px] text-forest font-semibold">Stable Forward Contract Window</div>
        </div>
      </div>

      {/* Commodity Filter Tabs */}
      <div class="flex flex-wrap items-center gap-2 bg-white p-2.5 rounded-2xl border border-slate-200/80 shadow-sm">
        <For each={cropList}>
          {(crop) => (
            <button
              onClick={() => setSelectedCrop(crop)}
              class={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                selectedCrop() === crop
                  ? "bg-forest text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {crop}
            </button>
          )}
        </For>
      </div>

      {/* Multi-Column Main Layout */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Predictive Forecast Curve (7 cols) */}
        <div class="lg:col-span-7 space-y-6">
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
              <div>
                <h3 class="font-black text-base text-slate-900">
                  Predictive Price Trajectory ({selectedCrop()})
                </h3>
                <p class="text-xs text-slate-500">Historical 90-day spot rates + 30-day ensemble forecast</p>
              </div>
              <span class="inline-flex items-center gap-1 text-[11px] font-bold text-forest bg-forest/10 px-2.5 py-1 rounded-lg">
                <span class="w-1.5 h-1.5 rounded-full bg-forest animate-pulse"></span>
                94.8% Confidence Band
              </span>
            </div>

            {/* SVG Visual Curve */}
            <div class="p-4 bg-slate-50 rounded-xl border border-slate-200/60 space-y-3">
              <div class="flex items-center justify-between text-xs text-slate-500">
                <span>Aug: ₹2,320</span>
                <span class="font-bold text-forest">Current Oct: ₹2,450</span>
                <span class="font-bold text-amber-700">Nov Forecast: ₹2,720</span>
              </div>

              <div class="relative h-44 w-full">
                <svg class="w-full h-full" viewBox="0 0 600 160" preserveAspectRatio="none">
                  <line x1="0" y1="40" x2="600" y2="40" stroke="#e2e8f0" stroke-dasharray="4" />
                  <line x1="0" y1="80" x2="600" y2="80" stroke="#e2e8f0" stroke-dasharray="4" />
                  <line x1="0" y1="120" x2="600" y2="120" stroke="#e2e8f0" stroke-dasharray="4" />

                  {/* Confidence Interval Band */}
                  <polygon points="350,75 420,60 500,45 600,30 600,60 500,75 420,90 350,85" fill="#d1fae5" opacity="0.6" />

                  {/* Historical Line */}
                  <polyline fill="none" stroke="#065f46" stroke-width="3" points="0,130 80,120 160,115 240,100 300,92 350,80" />

                  {/* Forecast Line */}
                  <polyline fill="none" stroke="#d97706" stroke-width="3" stroke-dasharray="6" points="350,80 420,68 500,52 600,40" />

                  <circle cx="350" cy="80" r="5" fill="#065f46" />
                  <circle cx="600" cy="40" r="5" fill="#d97706" />
                </svg>
              </div>

              <div class="grid grid-cols-4 text-center text-[11px] text-slate-400 font-semibold pt-1">
                <div>Aug 2026</div>
                <div>Sep 2026</div>
                <div class="text-forest font-bold">Oct 2026 (Live)</div>
                <div class="text-amber-700 font-bold">Nov 2026 (Pred)</div>
              </div>
            </div>

            {/* Market Drivers Matrix */}
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span class="text-[10px] font-bold uppercase text-slate-400">Arrivals Inflow</span>
                <div class="text-base font-black text-slate-800 mt-0.5">42,000 Qtl</div>
                <p class="text-[10px] text-slate-500 mt-0.5">Arrivals tapering down -4.1%</p>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span class="text-[10px] font-bold uppercase text-slate-400">Institutional Demand</span>
                <div class="text-base font-black text-forest mt-0.5">High (+18%)</div>
                <p class="text-[10px] text-emerald-700 mt-0.5">Flour mills restocking for festival</p>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span class="text-[10px] font-bold uppercase text-slate-400">Govt Buffer Stock</span>
                <div class="text-base font-black text-slate-800 mt-0.5">Adequate</div>
                <p class="text-[10px] text-slate-500 mt-0.5">No immediate OMSS dump</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Inter-Mandi Arbitrage Matrix (5 cols) */}
        <div class="lg:col-span-5 space-y-6">
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 class="font-black text-base text-slate-900">Inter-Mandi Arbitrage Matrix</h3>
                <p class="text-xs text-slate-500">Real-time net margin after logistics deduction</p>
              </div>
              <span class="text-xs font-bold text-forest">Live Feeds</span>
            </div>

            <div class="space-y-3 text-xs">
              <For each={mandiRates()}>
                {(item) => (
                  <div
                    class={`p-3.5 rounded-xl border transition-all space-y-2 ${
                      item.highlight
                        ? "border-emerald-200 bg-emerald-50/60"
                        : "border-slate-200 bg-slate-50"
                    }`}
                  >
                    <div class="flex items-start justify-between">
                      <div>
                        <div class="flex items-center gap-1.5">
                          <span class="font-black text-sm text-slate-900">{item.mandi}</span>
                          <span
                            class={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              item.highlight ? "bg-forest text-white" : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {item.statusBadge}
                          </span>
                        </div>
                        <div class="text-[11px] text-slate-500">
                          {item.distanceKm} km • {item.transitHours} hrs transit
                        </div>
                      </div>
                      <div class="text-right">
                        <div class="text-base font-black text-slate-900">
                          ₹{item.spotPrice.toLocaleString("en-IN")}<span class="text-[10px] font-normal text-slate-500">/qtl</span>
                        </div>
                        {item.netMargin > 0 ? (
                          <div class="text-[10px] text-emerald-800 font-bold">
                            Net: +₹{item.netMargin}/Qtl Margin
                          </div>
                        ) : (
                          <div class="text-[10px] text-slate-500 font-medium">Baseline Benchmark</div>
                        )}
                      </div>
                    </div>

                    <div class="flex items-center justify-between text-[11px] text-slate-600 pt-1 border-t border-slate-200/60">
                      <span>Logistics Est: ₹{item.transportCost}/Qtl</span>
                      <A href="/marketplace" class="font-bold text-forest hover:underline">
                        Explore Buyers &rarr;
                      </A>
                    </div>
                  </div>
                )}
              </For>
            </div>

            <div class="pt-2">
              <A
                href="/marketplace/my-listings"
                class="w-full py-3 bg-forest hover:bg-forest-light text-white text-xs font-bold rounded-xl shadow transition-all flex items-center justify-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">lock</span>
                <span>Lock Pre-Harvest Forward Contract</span>
              </A>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
