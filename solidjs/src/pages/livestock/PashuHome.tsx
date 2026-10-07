import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

export const PashuHome: Component = () => {
  const [animals] = createSignal([
    {
      id: "TAG-4091",
      breed: "Murrah Buffalo",
      gender: "Female (Milking)",
      dailyYield: "14.5 Litres",
      healthStatus: "Optimal",
      nextVaccination: "12 Oct 2026 (FMD Booster)",
      statusColor: "text-emerald-700 bg-emerald-50",
      image: "/images/murrah-buffalo.jpg",
    },
    {
      id: "TAG-4092",
      breed: "Sahiwal Cow",
      gender: "Female (Pregnant)",
      dailyYield: "11.0 Litres",
      healthStatus: "Checkup Due",
      nextVaccination: "02 Nov 2026 (Brucellosis)",
      statusColor: "text-amber-700 bg-amber-50",
      image: "/images/sahiwal-cow.jpg",
    },
    {
      id: "TAG-4093",
      breed: "Gir Cow",
      gender: "Female (Milking)",
      dailyYield: "12.8 Litres",
      healthStatus: "Optimal",
      nextVaccination: "12 Oct 2026 (FMD Booster)",
      statusColor: "text-emerald-700 bg-emerald-50",
      image: "/images/gir-cow.jpg",
    },
  ]);

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-20">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Pashu Hub (Livestock)</h1>
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-900">
              14 Total Animals
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">Herd telemetry, lactation analytics, diet planning & veterinary access</p>
        </div>
        <div class="flex items-center gap-2">
          <A
            href="/livestock/doctors"
            class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl transition-all inline-flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-base">medical_services</span>
            <span>Book Vet</span>
          </A>
          <button class="px-4 py-2 bg-forest hover:bg-forest-light text-white text-xs font-bold rounded-xl shadow transition-all inline-flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base">add</span>
            <span>Add Animal</span>
          </button>
        </div>
      </div>

      {/* Herd Summary Bar */}
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Daily Milk Production</span>
          <span class="text-xl font-black text-slate-900">92 Litres</span>
          <span class="text-[10px] text-emerald-600 font-semibold block">+4.2% this week</span>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Milking Animals</span>
          <span class="text-xl font-black text-slate-900">8 / 14</span>
          <span class="text-[10px] text-slate-500 font-medium block">6 Dry / Heifers</span>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Vaccinations Done</span>
          <span class="text-xl font-black text-emerald-700">100%</span>
          <span class="text-[10px] text-emerald-600 font-medium block">All current</span>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm text-center">
          <span class="text-[10px] text-slate-400 font-bold uppercase block">Estimated Portfolio Value</span>
          <span class="text-xl font-black text-slate-900">&#8377;11.4 Lakh</span>
          <span class="text-[10px] text-slate-500 font-medium block">Based on live Mandi rates</span>
        </div>
      </div>

      {/* Animal Roster Table */}
      <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between">
          <h3 class="font-bold text-sm text-slate-900">Herd Portfolio Roster</h3>
          <span class="text-xs text-slate-400">RFID Tag Integrated</span>
        </div>

        <div class="divide-y divide-slate-100">
          <For each={animals()}>
            {(animal) => (
              <div class="p-4 hover:bg-slate-50/80 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 shrink-0">
                    <img src={animal.image} alt={animal.breed} class="w-full h-full object-cover" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="font-bold text-sm text-slate-900">{animal.id}</span>
                      <span class="text-xs text-slate-500 font-medium">({animal.breed})</span>
                    </div>
                    <div class="text-xs text-slate-400 mt-0.5">{animal.gender} &bull; Next Vaccine: {animal.nextVaccination}</div>
                  </div>
                </div>

                <div class="flex items-center gap-4 self-end sm:self-center">
                  <div class="text-right">
                    <span class="text-[10px] text-slate-400 uppercase font-bold block">Avg Yield</span>
                    <span class="text-sm font-bold text-slate-900">{animal.dailyYield}</span>
                  </div>
                  <span class={`text-xs font-bold px-2.5 py-1 rounded-lg ${animal.statusColor}`}>
                    {animal.healthStatus}
                  </span>
                </div>
              </div>
            )}
          </For>
        </div>
      </div>
    </div>
  );
};
