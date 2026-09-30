import { Component } from "solid-js";
import { useParams } from "@solidjs/router";

export const AnnualStrategyDetail: Component = () => {
  const params = useParams();

  return (
    <div class="space-y-6 max-w-5xl mx-auto pb-20">
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Annual Crop Strategy</h1>
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-forest/10 text-forest">
              AI Optimized 2026–2027
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">Farm Strategy #{params.id || "1"} &bull; Soil & Weather RAG Synthesis</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Total Projected Profit</span>
          <span class="text-2xl font-black text-emerald-700">&#8377;6,42,000</span>
          <span class="text-xs text-emerald-600 font-semibold block">+22% over monoculture</span>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Water Consumption Index</span>
          <span class="text-2xl font-black text-slate-900">-18% Litres</span>
          <span class="text-xs text-sky-600 font-medium block">Drip + Legume rotation</span>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Soil Carbon Improvement</span>
          <span class="text-2xl font-black text-forest">+0.14% OC</span>
          <span class="text-xs text-forest font-medium block">Green manuring in May</span>
        </div>
      </div>

      {/* Rotation Timeline */}
      <div class="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
        <h3 class="font-bold text-sm text-slate-900">3-Season Rotation Matrix</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-2">
            <span class="text-[11px] font-bold text-emerald-800 uppercase">Season 1 &bull; Rabi (Oct - Mar)</span>
            <div class="text-base font-black text-slate-900">Wheat (HD-2967)</div>
            <p class="text-xs text-slate-600">High disease resistance & forward market contract locked at &#8377;2,650/qtl.</p>
          </div>

          <div class="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
            <span class="text-[11px] font-bold text-amber-800 uppercase">Season 2 &bull; Zaid (Apr - Jun)</span>
            <div class="text-base font-black text-slate-900">Moong Bean (IPM-205-7)</div>
            <p class="text-xs text-slate-600">60-day summer pulse fixing 35 kg/ha atmospheric nitrogen for Kharif.</p>
          </div>

          <div class="p-4 rounded-xl bg-sky-50 border border-sky-200 space-y-2">
            <span class="text-[11px] font-bold text-sky-800 uppercase">Season 3 &bull; Kharif (Jul - Oct)</span>
            <div class="text-base font-black text-slate-900">Basmati Rice (PB 1509)</div>
            <p class="text-xs text-slate-600">Short duration, premium export value, optimal soil moisture match.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
