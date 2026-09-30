import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface RFQItem {
  id: string;
  crop: string;
  targetVolume: number;
  fulfilledVolume: number;
  priceCeiling: number;
  destination: string;
  deadline: string;
  moistureLimit: string;
  qualitySpec: string;
  matchingLotsCount: number;
  status: string;
}

interface MatchedLot {
  id: string;
  crop: string;
  farmerFpo: string;
  matchScore: number;
  matchedRfqId: string;
  quantity: number;
  pricePerUnit: number;
  advanceDeposit: number;
  warehouse: string;
  distanceKm: number;
  moisture: string;
  assayBadge: string;
  telemetry: string;
}

export const BuyerDashboard: Component = () => {
  const [rfqs, setRfqs] = createSignal<RFQItem[]>([
    {
      id: "ITC-WHT-2024-09",
      crop: "Sharbati Golden Wheat",
      targetVolume: 500,
      fulfilledVolume: 420,
      priceCeiling: 2600,
      destination: "ITC Chandausi Processing Plant",
      deadline: "25 Oct 2026",
      moistureLimit: "< 12.0%",
      qualitySpec: "Protein > 13.5% • Foreign Matter < 0.5%",
      matchingLotsCount: 4,
      status: "Active • 84% Sourced",
    },
    {
      id: "ITC-PAD-2024-11",
      crop: "Basmati 1121 Pusa Paddy",
      targetVolume: 800,
      fulfilledVolume: 520,
      priceCeiling: 3850,
      destination: "Sonipat Central Silo Hub",
      deadline: "05 Nov 2026",
      moistureLimit: "13.0% Max",
      qualitySpec: "Grain Length > 8.3mm • Export Standard",
      matchingLotsCount: 5,
      status: "Active • 65% Sourced",
    },
    {
      id: "ITC-CHN-2024-14",
      crop: "Desi Chana (Bengal Gram)",
      targetVolume: 300,
      fulfilledVolume: 100,
      priceCeiling: 6000,
      destination: "Nagpur Mill Logistics Hub",
      deadline: "30 Oct 2026",
      moistureLimit: "< 10.0%",
      qualitySpec: "Defect < 0.5% • Seed Grade Bold",
      matchingLotsCount: 3,
      status: "New Tender • 33% Sourced",
    },
  ]);

  const [matchedLots, setMatchedLots] = createSignal<MatchedLot[]>([
    {
      id: "MH-PUN-8402",
      crop: "Sharbati Golden Wheat",
      farmerFpo: "Sahyadri Farmers Producer Co. Ltd (#MH-NSK-2894)",
      matchScore: 98.2,
      matchedRfqId: "ITC-WHT-2024-09",
      quantity: 85,
      pricePerUnit: 2450,
      advanceDeposit: 41650,
      warehouse: "WDRA Baramati Cold Hub Bay 4, Slot #W-14",
      distanceKm: 64,
      moisture: "11.8%",
      assayBadge: "NABL #NQL-9042 Pass",
      telemetry: "18.2°C • 62% RH",
    },
    {
      id: "MH-NSK-9120",
      crop: "Basmati 1121 Pusa Paddy",
      farmerFpo: "Niphad Valley Agro Producers (ICAR Partner)",
      matchScore: 95.8,
      matchedRfqId: "ITC-PAD-2024-11",
      quantity: 120,
      pricePerUnit: 3900,
      advanceDeposit: 93600,
      warehouse: "On-Farm Aerated Silo Node #02, Niphad",
      distanceKm: 118,
      moisture: "13.1%",
      assayBadge: "Export Clean Certified",
      telemetry: "19.5°C • 58% RH",
    },
    {
      id: "MH-JLG-5501",
      crop: "Desi Chana (Bengal Gram)",
      farmerFpo: "Pimpalgaon APMC Warehouse Hub, Jalgaon",
      matchScore: 92.4,
      matchedRfqId: "ITC-CHN-2024-14",
      quantity: 65,
      pricePerUnit: 5820,
      advanceDeposit: 75660,
      warehouse: "Jalgaon Taluka Central Bay 12",
      distanceKm: 142,
      moisture: "9.8%",
      assayBadge: "Weevil Defect <0.5%",
      telemetry: "Dry Regulated Silo",
    },
  ]);

  const [showRfqModal, setShowRfqModal] = createSignal(false);
  const [rfqCrop, setRfqCrop] = createSignal("");
  const [rfqVolume, setRfqVolume] = createSignal(400);
  const [rfqMaxPrice, setRfqMaxPrice] = createSignal(2500);

  const handleCreateRfq = (e: Event) => {
    e.preventDefault();
    if (!rfqCrop()) return;

    const newRfq: RFQItem = {
      id: `ITC-RFQ-${Math.floor(1000 + Math.random() * 9000)}`,
      crop: rfqCrop(),
      targetVolume: rfqVolume(),
      fulfilledVolume: 0,
      priceCeiling: rfqMaxPrice(),
      destination: "Central Food Processing Plant #1",
      deadline: "15 Nov 2026",
      moistureLimit: "< 12.0%",
      qualitySpec: "Grade A Industrial Spec",
      matchingLotsCount: 2,
      status: "New Tender • 0% Sourced",
    };

    setRfqs([newRfq, ...rfqs()]);
    setShowRfqModal(false);
    setRfqCrop("");
  };

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* Top Corporate Header */}
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <A href="/marketplace" class="hover:text-forest transition-colors">Marketplace</A>
            <span>/</span>
            <span class="font-medium text-slate-700">Institutional Procurement Console</span>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="text-xl lg:text-2xl font-black text-slate-900 tracking-tight">
              Buyer Procurement Dashboard &amp; RFQ Engine
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-forest/10 text-forest border border-forest/20">
              Corporate Buyer Level-4
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">
            ITC Agri-Business Division • Direct-to-FPO Pre-Harvest Procurement &amp; Escrow Management
          </p>
        </div>

        <div class="flex items-center gap-2.5 self-start lg:self-auto">
          <button
            onClick={() => setShowRfqModal(true)}
            class="px-4 py-2.5 bg-forest hover:bg-forest-light text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-base">add_circle</span>
            <span>+ Post New Supply RFQ</span>
          </button>
        </div>
      </div>

      {/* 4 Top KPI Metric Cards */}
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Active RFQ Tenders</span>
            <span class="material-symbols-outlined text-forest text-lg">contract</span>
          </div>
          <div class="text-2xl font-black text-slate-900">3 Live</div>
          <div class="text-[11px] text-emerald-700 font-semibold">1,600 MT Aggregate Demand</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">AI Matched Lots</span>
            <span class="material-symbols-outlined text-blue-600 text-lg">smart_toy</span>
          </div>
          <div class="text-2xl font-black text-slate-900">12 Lots</div>
          <div class="text-[11px] text-forest font-semibold">96.4% Avg Match Score</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Escrow Committed</span>
            <span class="material-symbols-outlined text-emerald-600 text-lg">lock</span>
          </div>
          <div class="text-2xl font-black text-forest">₹8.40 Lakhs</div>
          <div class="text-[11px] text-slate-500">ICICI Trustee Account</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Procurement Savings</span>
            <span class="material-symbols-outlined text-amber-600 text-lg">savings</span>
          </div>
          <div class="text-2xl font-black text-amber-700">-5.2%</div>
          <div class="text-[11px] text-emerald-700 font-semibold">₹1.82L Direct FPO Arbitrage</div>
        </div>
      </div>

      {/* Main Multi-Column: RFQs on Left (5 cols), Matched Lots on Right (7 cols) */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Active RFQs (5 cols) */}
        <div class="lg:col-span-5 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-base font-black text-slate-900">Active Supply RFQs</h2>
              <p class="text-xs text-slate-500">Live commodity tenders published to FPO network</p>
            </div>
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
              {rfqs().length} Open
            </span>
          </div>

          <div class="space-y-4">
            <For each={rfqs()}>
              {(rfq) => {
                const percent = Math.round((rfq.fulfilledVolume / rfq.targetVolume) * 100);
                return (
                  <div class="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-3 hover:border-forest/40 transition-colors">
                    <div class="flex items-start justify-between">
                      <div>
                        <div class="text-[10px] font-mono font-bold text-slate-400">RFQ #{rfq.id}</div>
                        <h3 class="font-bold text-sm text-slate-900 mt-0.5">{rfq.crop}</h3>
                        <p class="text-[11px] text-slate-500 mt-0.5">{rfq.destination}</p>
                      </div>
                      <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {rfq.status}
                      </span>
                    </div>

                    <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200/60 text-xs space-y-1">
                      <div class="flex justify-between text-slate-600">
                        <span>Ceiling Price: <strong class="text-forest">₹{rfq.priceCeiling}/Qtl</strong></span>
                        <span>Moisture: <strong>{rfq.moistureLimit}</strong></span>
                      </div>
                      <div class="text-[11px] text-slate-500">{rfq.qualitySpec}</div>
                    </div>

                    {/* Progress Bar */}
                    <div class="space-y-1">
                      <div class="flex justify-between text-[11px] font-medium text-slate-600">
                        <span>Fulfillment: {rfq.fulfilledVolume} / {rfq.targetVolume} Qtl</span>
                        <span class="font-bold text-forest">{percent}%</span>
                      </div>
                      <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div class="bg-forest h-2 rounded-full transition-all" style={`width: ${percent}%`}></div>
                      </div>
                    </div>

                    <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span class="text-slate-500">Closing: {rfq.deadline}</span>
                      <button class="font-bold text-forest hover:text-forest-light transition-colors flex items-center gap-1">
                        <span>View Matching Lots ({rfq.matchingLotsCount})</span>
                        <span class="material-symbols-outlined text-sm">chevron_right</span>
                      </button>
                    </div>
                  </div>
                );
              }}
            </For>
          </div>
        </div>

        {/* Right Column: AI Matched Farmer & FPO Lots (7 cols) */}
        <div class="lg:col-span-7 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-base font-black text-slate-900">AI Matched Farmer &amp; FPO Lots</h2>
              <p class="text-xs text-slate-500">Algorithmically certified lots matching your active RFQ tolerances</p>
            </div>
            <div class="flex items-center gap-1 text-xs text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              <span class="material-symbols-outlined text-sm">verified</span>
              <span>100% NABL Verified</span>
            </div>
          </div>

          <div class="space-y-4">
            <For each={matchedLots()}>
              {(lot) => (
                <div class="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4 hover:shadow-md transition-all">
                  <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-forest text-white">
                          {lot.matchScore}% Match
                        </span>
                        <span class="text-xs font-mono font-bold text-slate-400">Lot #{lot.id}</span>
                        <span class="text-[11px] text-slate-500 font-medium">for RFQ #{lot.matchedRfqId}</span>
                      </div>
                      <h3 class="font-bold text-base text-slate-900 mt-1">{lot.crop} ({lot.quantity} Quintals)</h3>
                      <p class="text-xs text-slate-600 font-medium">{lot.farmerFpo}</p>
                    </div>
                    <div class="sm:text-right">
                      <div class="text-xl font-black text-forest">₹{lot.pricePerUnit.toLocaleString("en-IN")}<span class="text-xs text-slate-500 font-normal">/qtl</span></div>
                      <div class="text-xs text-slate-500">Lot Value: ₹{(lot.quantity * lot.pricePerUnit).toLocaleString("en-IN")}</div>
                    </div>
                  </div>

                  {/* Quality & Telemetry Grid */}
                  <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 bg-slate-50 p-3 rounded-xl border border-slate-200/60 text-xs">
                    <div>
                      <span class="text-[10px] text-slate-400 font-bold uppercase">Moisture Assay</span>
                      <div class="font-bold text-forest mt-0.5">{lot.moisture}</div>
                    </div>
                    <div>
                      <span class="text-[10px] text-slate-400 font-bold uppercase">Certification</span>
                      <div class="font-bold text-slate-800 mt-0.5">{lot.assayBadge}</div>
                    </div>
                    <div>
                      <span class="text-[10px] text-slate-400 font-bold uppercase">Storage Telemetry</span>
                      <div class="font-bold text-slate-800 mt-0.5">{lot.telemetry}</div>
                    </div>
                    <div class="col-span-2 sm:col-span-3 text-slate-500 text-[11px] pt-1 border-t border-slate-200/60 flex items-center justify-between">
                      <span>Warehouse: {lot.warehouse}</span>
                      <span class="font-semibold text-slate-700">{lot.distanceKm} km from plant</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div class="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                    <A
                      href={`/marketplace/${lot.id}`}
                      class="text-xs font-bold text-forest hover:text-forest-light flex items-center gap-1 transition-colors"
                    >
                      <span class="material-symbols-outlined text-sm">visibility</span>
                      <span>Inspect Assay Report</span>
                    </A>

                    <A
                      href={`/marketplace/${lot.id}`}
                      class="px-4 py-2 rounded-xl bg-forest hover:bg-forest-light text-white text-xs font-bold shadow transition-all flex items-center gap-1.5"
                    >
                      <span class="material-symbols-outlined text-sm">lock</span>
                      <span>Issue Forward Escrow Contract (₹{lot.advanceDeposit.toLocaleString("en-IN")})</span>
                    </A>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>
      </div>

      {/* Modal for Posting New Supply RFQ */}
      {showRfqModal() && (
        <div class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 border border-slate-200 shadow-xl">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 class="font-black text-lg text-slate-900">Post Institutional Supply RFQ</h3>
                <p class="text-xs text-slate-500">Broadcast pre-harvest procurement tender to verified FPOs</p>
              </div>
              <button
                onClick={() => setShowRfqModal(false)}
                class="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateRfq} class="space-y-4 text-xs">
              <div class="space-y-1">
                <label class="font-bold text-slate-700">Commodity &amp; Grade</label>
                <input
                  type="text"
                  placeholder="e.g. Sharbati Wheat, Pusa Basmati, Mustard 42% Oil"
                  value={rfqCrop()}
                  onInput={(e) => setRfqCrop(e.currentTarget.value)}
                  class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-forest text-sm"
                  required
                />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="font-bold text-slate-700">Procurement Target (Qtl)</label>
                  <input
                    type="number"
                    min="50"
                    max="10000"
                    value={rfqVolume()}
                    onInput={(e) => setRfqVolume(Number(e.currentTarget.value))}
                    class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-forest text-sm"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-bold text-slate-700">Price Ceiling (₹/Qtl)</label>
                  <input
                    type="number"
                    min="1000"
                    max="50000"
                    value={rfqMaxPrice()}
                    onInput={(e) => setRfqMaxPrice(Number(e.currentTarget.value))}
                    class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-forest text-sm"
                  />
                </div>
              </div>

              <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-[11px] text-emerald-900 flex items-start gap-2">
                <span class="material-symbols-outlined text-forest text-sm mt-0.5">shield</span>
                <div>
                  <strong>ICICI Smart Escrow Guarantee:</strong> Once matching lots are selected, advance escrow deposit (20%) is locked automatically to guarantee price and supply.
                </div>
              </div>

              <div class="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowRfqModal(false)}
                  class="px-4 py-2 rounded-xl border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="px-5 py-2 rounded-xl bg-forest hover:bg-forest-light font-bold text-white shadow transition-all"
                >
                  Broadcast Tender to FPOs
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
