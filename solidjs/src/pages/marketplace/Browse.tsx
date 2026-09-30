import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

export const MarketplaceBrowse: Component = () => {
  const [listings] = createSignal([
    {
      id: "MANDI-102",
      crop: "Wheat (Sharbati A-Grade)",
      farmer: "Gurpreet Singh (Ludhiana)",
      quantity: "350 Quintals",
      expectedHarvest: "15 April 2027",
      contractPrice: "₹2,650 / Qtl",
      mspBenchmark: "₹2,275 MSP",
      escrowRequired: "15% (₹1,39,125)",
      status: "Open for Advance Contract",
    },
    {
      id: "MANDI-103",
      crop: "Basmati Rice (Pusa 1121)",
      farmer: "Rajeshwar Rao (Karnal)",
      quantity: "500 Quintals",
      expectedHarvest: "20 November 2026",
      contractPrice: "₹4,100 / Qtl",
      mspBenchmark: "Market Linked",
      escrowRequired: "20% (₹4,10,000)",
      status: "2 Buyer Interests Received",
    },
  ]);

  return (
    <div class="space-y-6 max-w-6xl mx-auto pb-20">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">Mandi Forward Marketplace</h1>
          <p class="text-xs text-slate-500 mt-0.5">Pre-harvest forward contracts with bank-guaranteed escrow lock</p>
        </div>
        <A
          href="/marketplace/my-listings"
          class="px-4 py-2 bg-forest text-white text-xs font-bold rounded-xl shadow hover:bg-forest-light transition-all inline-flex items-center gap-1.5 self-start sm:self-auto"
        >
          <span class="material-symbols-outlined text-base">add_business</span>
          <span>List Harvest Parcel</span>
        </A>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <For each={listings()}>
          {(item) => (
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4 hover:shadow-md transition-all">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="font-bold text-base text-slate-900">{item.crop}</h3>
                  <div class="text-xs text-slate-500 mt-0.5">Farmer: {item.farmer}</div>
                </div>
                <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                  {item.contractPrice}
                </span>
              </div>

              <div class="grid grid-cols-3 gap-2 py-3 border-y border-slate-100 text-center text-xs">
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Quantity</span>
                  <span class="font-bold text-slate-800">{item.quantity}</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Est. Harvest</span>
                  <span class="font-bold text-slate-800">{item.expectedHarvest}</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px] uppercase font-bold">Escrow Lock</span>
                  <span class="font-bold text-forest">{item.escrowRequired}</span>
                </div>
              </div>

              <div class="flex items-center justify-between pt-1">
                <span class="text-xs text-slate-500 font-medium">{item.status}</span>
                <A
                  href={`/marketplace/bookings/${item.id}`}
                  class="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg shadow-sm transition-all"
                >
                  View Contract Details &rarr;
                </A>
              </div>
            </div>
          )}
        </For>
      </div>
    </div>
  );
};
