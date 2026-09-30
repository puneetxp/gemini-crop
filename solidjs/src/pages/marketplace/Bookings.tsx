import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface EscrowBooking {
  id: string;
  crop: string;
  cropGrade: string;
  farmerFpo: string;
  buyerName: string;
  quantity: number;
  totalValue: number;
  ratePerQtl: number;
  escrowDeposit: number;
  currentStage: number; // 1 to 5
  stageName: string;
  category: "locked" | "transit" | "assay" | "settled";
  telemetryNotes: string;
  assayNotes: string;
}

export const Bookings: Component = () => {
  const [filter, setFilter] = createSignal<string>("all");
  const [approvedContracts, setApprovedContracts] = createSignal<Record<string, boolean>>({});

  const [contracts] = createSignal<EscrowBooking[]>([
    {
      id: "BK-8924",
      crop: "Sharbati Golden Wheat",
      cropGrade: "A+ Premium Milling Grade",
      farmerFpo: "Sahyadri Farmers Producer Co. (Ramesh Patil)",
      buyerName: "Green Agro Mills Pvt Ltd (Navi Mumbai)",
      quantity: 100,
      totalValue: 265000,
      ratePerQtl: 2650,
      escrowDeposit: 106000,
      currentStage: 4,
      stageName: "Weighbridge Quality Assay",
      category: "assay",
      telemetryNotes: "WDRA Baramati Bay 4 • Reefer Temp: 18.2°C",
      assayNotes: "NABL Assay Passed: 13.8% Protein • 11.2% Moisture (Target <12%)",
    },
    {
      id: "BK-9120",
      crop: "Basmati 1121 Pusa Paddy",
      cropGrade: "Super Fine Export Standard (8.4mm)",
      farmerFpo: "Niphad Valley Agro Producer Co.",
      buyerName: "Kohinoor Agri Export Corp (Delhi)",
      quantity: 120,
      totalValue: 468000,
      ratePerQtl: 3900,
      escrowDeposit: 187200,
      currentStage: 3,
      stageName: "Dispatch / Cold Chain Transit",
      category: "transit",
      telemetryNotes: "Reefer Truck MH-15-EG-8421 • 64 km to Sonipat Silo (ETA 3.2 hrs)",
      assayNotes: "Gate Pass QR Issued • Tamper Seal Verified",
    },
    {
      id: "BK-7840",
      crop: "Desi Chana (Bengal Gram)",
      cropGrade: "Vijay Bold Seed Grade NABL Cleared",
      farmerFpo: "Jalgaon Taluka FPO Consortium",
      buyerName: "Patanjali Foods Ltd (Haridwar Hub)",
      quantity: 65,
      totalValue: 378300,
      ratePerQtl: 5820,
      escrowDeposit: 75660,
      currentStage: 1,
      stageName: "Advance Escrow Locked",
      category: "locked",
      telemetryNotes: "Pre-Harvest Sowing Block #04 • Cadastral Verified",
      assayNotes: "Seed Purity 99.4% • Moisture 9.8%",
    },
    {
      id: "BK-6512",
      crop: "Organic Soybean (JS-335)",
      cropGrade: "Non-GMO Verified • Oil Grade 1",
      farmerFpo: "Wardha Krishna Basin FPO",
      buyerName: "Adani Wilmar Institutional Node",
      quantity: 50,
      totalValue: 232500,
      ratePerQtl: 4650,
      escrowDeposit: 93000,
      currentStage: 4,
      stageName: "Weighbridge Quality Assay",
      category: "assay",
      telemetryNotes: "Wardha APMC Gate #02 • Truck Weighing Completed",
      assayNotes: "Mobile NABL Van Testing • Cleanliness 99.1%",
    },
    {
      id: "BK-5190",
      crop: "Lokwan Milling Wheat",
      cropGrade: "Standard Milling Grade",
      farmerFpo: "Pune District Agritech FPO",
      buyerName: "Parle Agro Processing Unit",
      quantity: 110,
      totalValue: 269500,
      ratePerQtl: 2450,
      escrowDeposit: 269500,
      currentStage: 5,
      stageName: "Autonomous RTGS Disbursed",
      category: "settled",
      telemetryNotes: "Delivered to ITC Warehouse • Silo Slot #09",
      assayNotes: "100% Milestone Disbursed • UTR #ICICIR49201948291",
    },
  ]);

  const stagesList = [
    "1. Advance Deposit",
    "2. Harvest & Pack",
    "3. Dispatch Transit",
    "4. Weighbridge Assay",
    "5. Final Payout",
  ];

  const filteredContracts = () => {
    if (filter() === "all") return contracts();
    return contracts().filter((c) => c.category === filter());
  };

  const handleApproveRelease = (id: string) => {
    setApprovedContracts({ ...approvedContracts(), [id]: true });
  };

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* Top Header & Breadcrumb */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <A href="/marketplace" class="hover:text-forest transition-colors">Marketplace</A>
            <span>/</span>
            <span class="font-medium text-slate-700">Advance Bookings &amp; Escrow Ledger</span>
          </div>
          <h1 class="text-xl lg:text-2xl font-black text-slate-900 tracking-tight">
            Advance Forward Bookings &amp; Escrow Ledger
          </h1>
          <p class="text-xs text-slate-500 mt-0.5">
            Governed by ICICI Bank Virtual Escrow Trustee, NABL assays, and automated weighbridge clearance
          </p>
        </div>

        <div class="flex items-center gap-2 self-start sm:self-auto">
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            ICICI Trustee Node #409 Active
          </span>
        </div>
      </div>

      {/* 4 Summary KPI Metric Cards */}
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Active Contracts</span>
            <span class="material-symbols-outlined text-forest text-lg">contract</span>
          </div>
          <div class="text-2xl font-black text-slate-900">5 Bookings</div>
          <div class="text-[11px] text-emerald-700 font-semibold">₹16.50 Lakhs Total Value</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Escrow in Trust</span>
            <span class="material-symbols-outlined text-emerald-600 text-lg">lock</span>
          </div>
          <div class="text-2xl font-black text-forest">₹4,92,000</div>
          <div class="text-[11px] text-slate-500">Tranches 2 &amp; 3 Pending Release</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Pending Assays</span>
            <span class="material-symbols-outlined text-amber-600 text-lg">biotech</span>
          </div>
          <div class="text-2xl font-black text-slate-900">2 Lots</div>
          <div class="text-[11px] text-amber-700 font-semibold">NABL Gate Mobile Lab</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Settled Payouts</span>
            <span class="material-symbols-outlined text-blue-600 text-lg">verified</span>
          </div>
          <div class="text-2xl font-black text-slate-900">₹11.58 L</div>
          <div class="text-[11px] text-emerald-700 font-semibold">100% Zero-Default RTGS</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div class="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setFilter("all")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "all" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          All Bookings ({contracts().length})
        </button>
        <button
          onClick={() => setFilter("locked")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "locked" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Advance Locked (1)
        </button>
        <button
          onClick={() => setFilter("transit")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "transit" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          In-Transit / Dispatch (1)
        </button>
        <button
          onClick={() => setFilter("assay")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "assay" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Weighbridge Quality Assay (2)
        </button>
        <button
          onClick={() => setFilter("settled")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "settled" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Settled / Disbursed (1)
        </button>
      </div>

      {/* Detailed Booking Cards */}
      <div class="space-y-5">
        <For each={filteredContracts()}>
          {(item) => {
            const isApproved = () => approvedContracts()[item.id];
            return (
              <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5 hover:shadow-md transition-all">
                <div class="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-mono font-bold text-forest bg-forest/10 px-2 py-0.5 rounded-md">
                        #{item.id}
                      </span>
                      <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                        {item.stageName}
                      </span>
                      {isApproved() && (
                        <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          ✓ Payout Authorized
                        </span>
                      )}
                    </div>
                    <h3 class="text-lg font-black text-slate-900">{item.crop} ({item.quantity} Quintals)</h3>
                    <p class="text-xs text-slate-500">{item.cropGrade}</p>
                    <div class="text-xs text-slate-600 pt-1">
                      <span class="font-semibold text-slate-800">Farmer:</span> {item.farmerFpo} ↔ <span class="font-semibold text-slate-800">Buyer:</span> {item.buyerName}
                    </div>
                  </div>

                  <div class="flex flex-wrap lg:flex-col items-end gap-1 bg-slate-50 lg:bg-transparent p-3 lg:p-0 rounded-xl">
                    <div class="text-sm font-semibold text-slate-500">Contract Valuation</div>
                    <div class="text-2xl font-black text-forest">₹{item.totalValue.toLocaleString("en-IN")}</div>
                    <div class="text-xs text-slate-500 font-medium">Rate: ₹{item.ratePerQtl}/Qtl • Escrow Held: <strong class="text-emerald-700">₹{item.escrowDeposit.toLocaleString("en-IN")}</strong></div>
                  </div>
                </div>

                {/* 5-Stage Milestone Stepper */}
                <div class="space-y-2 pt-2">
                  <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
                    {stagesList.map((stg, idx) => {
                      const stepNum = idx + 1;
                      const isPast = stepNum < item.currentStage;
                      const isCurrent = stepNum === item.currentStage;
                      return (
                        <div
                          class={`p-2.5 rounded-xl border text-center transition-all ${
                            isCurrent
                              ? "bg-forest text-white border-forest font-bold shadow-sm"
                              : isPast
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold"
                              : "bg-slate-50 text-slate-400 border-slate-200"
                          }`}
                        >
                          <div class="text-[10px] uppercase font-bold tracking-wider opacity-80">
                            {isPast ? "✓ Done" : isCurrent ? "● Active" : "Pending"}
                          </div>
                          <div class="text-xs mt-0.5 truncate">{stg}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Telemetry & Assay Info Strip */}
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200/60 text-xs">
                  <div class="flex items-center gap-2 text-slate-600">
                    <span class="material-symbols-outlined text-forest text-base flex-shrink-0">local_shipping</span>
                    <span>{item.telemetryNotes}</span>
                  </div>
                  <div class="flex items-center gap-2 text-slate-600">
                    <span class="material-symbols-outlined text-emerald-600 text-base flex-shrink-0">biotech</span>
                    <span>{item.assayNotes}</span>
                  </div>
                </div>

                {/* Card Actions */}
                <div class="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  <div class="flex items-center gap-2">
                    <A
                      href={`/marketplace/bookings/${item.id}`}
                      class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-colors flex items-center gap-1.5"
                    >
                      <span class="material-symbols-outlined text-sm">visibility</span>
                      <span>Inspect Escrow Milestone Contract</span>
                    </A>
                  </div>

                  <div class="flex items-center gap-2">
                    {item.currentStage === 4 && !isApproved() && (
                      <button
                        onClick={() => handleApproveRelease(item.id)}
                        class="px-4 py-2 bg-forest hover:bg-forest-light text-white font-bold text-xs rounded-xl shadow transition-all flex items-center gap-1.5"
                      >
                        <span class="material-symbols-outlined text-sm">task_alt</span>
                        <span>Approve Quality Release (₹{item.escrowDeposit.toLocaleString("en-IN")})</span>
                      </button>
                    )}
                    {isApproved() && (
                      <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200 flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm">check_circle</span>
                        RTGS Dispatched to Farmer
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          }}
        </For>
      </div>
    </div>
  );
};
