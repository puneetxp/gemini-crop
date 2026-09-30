import { Component } from "solid-js";

export const SoilFertilizerHub: Component = () => {
  return (
    <div class="space-y-6 max-w-6xl mx-auto pb-20">
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Soil Health & Satellite GIS Hub</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Soil Health Card (SHC) laboratory test tracking, SLUSI land capability, and Sentinel-2 vegetation indices
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
          <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Soil pH & Texture</span>
          <div class="text-2xl font-black text-slate-900">7.2 (Neutral)</div>
          <p class="text-xs text-slate-500">Clay Loam with 0.68% Organic Carbon (Moderate)</p>
          <div class="w-full bg-slate-100 rounded-full h-2 mt-2">
            <div class="bg-emerald-500 h-2 rounded-full w-[72%]"></div>
          </div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
          <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">NPK Balance Ratio</span>
          <div class="text-2xl font-black text-forest">4 : 1.2 : 2.8</div>
          <p class="text-xs text-slate-500">Balanced nitrogen reserve. Add Muriate of Potash before heading.</p>
          <div class="w-full bg-slate-100 rounded-full h-2 mt-2">
            <div class="bg-forest h-2 rounded-full w-[85%]"></div>
          </div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-3">
          <span class="text-xs font-bold text-slate-500 uppercase tracking-wider block">Micronutrient Status</span>
          <div class="text-2xl font-black text-amber-600">Zinc Deficient</div>
          <p class="text-xs text-slate-500">Apply Zinc Sulphate (ZnSO4 21%) @ 25 kg/ha basal application.</p>
          <div class="w-full bg-slate-100 rounded-full h-2 mt-2">
            <div class="bg-amber-500 h-2 rounded-full w-[45%]"></div>
          </div>
        </div>
      </div>
    </div>
  );
};
