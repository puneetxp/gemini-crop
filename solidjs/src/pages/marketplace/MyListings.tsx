import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface ProduceListing {
  id: string;
  crop: string;
  variety: string;
  quantity: number;
  unit: string;
  pricePerUnit: number;
  category: "locked" | "open" | "draft";
  statusBadge: string;
  statusColor: string;
  warehouse: string;
  tempRh: string;
  buyerName?: string;
  escrowLockedAmount?: number;
  escrowPercent?: number;
  bidsCount?: number;
  moisture: string;
  proteinClean: string;
}

export const MyListings: Component = () => {
  const [filter, setFilter] = createSignal<string>("all");
  const [showCreateModal, setShowCreateModal] = createSignal(false);
  const [newCropName, setNewCropName] = createSignal("");
  const [newQuantity, setNewQuantity] = createSignal(50);
  const [newPrice, setNewPrice] = createSignal(2500);

  const [listings, setListings] = createSignal<ProduceListing[]>([
    {
      id: "MH-PUN-8402",
      crop: "Sharbati Golden Wheat",
      variety: "High Vitreous Milling Grade A+",
      quantity: 85,
      unit: "Quintals (8.5 MT)",
      pricePerUnit: 2450,
      category: "locked",
      statusBadge: "Escrow Locked (60% Funded)",
      statusColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
      warehouse: "Baramati Agro Cold Hub • Bay 4, Slot #W-14",
      tempRh: "18.2°C • 62% RH",
      buyerName: "Green Agro Mills Ltd",
      escrowLockedAmount: 125000,
      escrowPercent: 60,
      moisture: "11.8%",
      proteinClean: "13.6% Protein • 99.6% Clean",
    },
    {
      id: "MH-NSK-9120",
      crop: "Basmati 1121 Pusa Paddy",
      variety: "Export Standard Extra Long Aromatic",
      quantity: 120,
      unit: "Quintals (12.0 MT)",
      pricePerUnit: 3900,
      category: "locked",
      statusBadge: "Escrow Locked (Gate Inspection)",
      statusColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
      warehouse: "Niphad Valley Farm • Aerated Silo Node #02",
      tempRh: "19.5°C • 58% RH",
      buyerName: "Kohinoor Agri Export Corp",
      escrowLockedAmount: 187200,
      escrowPercent: 40,
      moisture: "13.1%",
      proteinClean: "8.4mm Avg Length • Organic Pass",
    },
    {
      id: "MH-JLG-5501",
      crop: "Desi Chana (Bengal Gram)",
      variety: "Vijay Bold Seed Grade NABL Pass",
      quantity: 65,
      unit: "Quintals (6.5 MT)",
      pricePerUnit: 6100,
      category: "open",
      statusBadge: "Open for Advance Booking",
      statusColor: "bg-amber-50 text-amber-800 border-amber-200",
      warehouse: "Pimpalgaon APMC Central Warehouse Hub",
      tempRh: "Ambient Inspected",
      bidsCount: 4,
      moisture: "9.8%",
      proteinClean: "Defect <0.5% • Seed Grade",
    },
    {
      id: "MH-WRD-3208",
      crop: "Organic Soybean",
      variety: "JS-335 Non-GMO Verified",
      quantity: 50,
      unit: "Quintals (5.0 MT)",
      pricePerUnit: 4650,
      category: "draft",
      statusBadge: "Draft / Assay In-Transit",
      statusColor: "bg-slate-100 text-slate-700 border-slate-300",
      warehouse: "Wardha Krishna Plot B • On-Farm Transit Lot",
      tempRh: "KVK Lab Mobile Van Sampled",
      moisture: "Testing...",
      proteinClean: "Oil Content Assay Pending",
    },
  ]);

  const filteredListings = () => {
    if (filter() === "all") return listings();
    return listings().filter((item) => item.category === filter());
  };

  const handleCreateListing = (e: Event) => {
    e.preventDefault();
    if (!newCropName()) return;

    const newLot: ProduceListing = {
      id: `MH-LOT-${Math.floor(1000 + Math.random() * 9000)}`,
      crop: newCropName(),
      variety: "Standard Commercial Grade",
      quantity: newQuantity(),
      unit: `Quintals (${(newQuantity() / 10).toFixed(1)} MT)`,
      pricePerUnit: newPrice(),
      category: "open",
      statusBadge: "Open for Advance Booking",
      statusColor: "bg-amber-50 text-amber-800 border-amber-200",
      warehouse: "Local APMC Yard Slot #A-1",
      tempRh: "Dry Storage",
      bidsCount: 0,
      moisture: "12.0%",
      proteinClean: "Grading Certified",
    };

    setListings([newLot, ...listings()]);
    setShowCreateModal(false);
    setNewCropName("");
  };

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* Top Breadcrumb & Header Bar */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <A href="/marketplace" class="hover:text-forest transition-colors">Marketplace</A>
            <span>/</span>
            <span class="font-medium text-slate-700">My Listings &amp; Escrow</span>
          </div>
          <h1 class="text-xl lg:text-2xl font-black text-slate-900 tracking-tight">
            Farmer Produce Inventory &amp; Forward Contracts
          </h1>
          <p class="text-xs text-slate-500 mt-0.5">
            Manage NABL-certified lot assays, ICICI escrow tranches, and APMC forward contracts
          </p>
        </div>

        <div class="flex items-center gap-2.5 self-start sm:self-auto">
          <button
            onClick={() => setShowCreateModal(true)}
            class="px-4 py-2.5 bg-forest hover:bg-forest-light text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-base">add_circle</span>
            <span>+ Create Produce Listing</span>
          </button>
        </div>
      </div>

      {/* 4 KPI Summary Cards */}
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Active Lots</span>
            <span class="material-symbols-outlined text-forest text-lg">inventory_2</span>
          </div>
          <div class="text-2xl font-black text-slate-900">4 Lots</div>
          <div class="text-[11px] text-emerald-700 font-semibold">320 Quintals (32 MT)</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Locked Escrow</span>
            <span class="material-symbols-outlined text-emerald-600 text-lg">lock</span>
          </div>
          <div class="text-2xl font-black text-forest">₹3,85,000</div>
          <div class="text-[11px] text-slate-500">ICICI Bank Smart Escrow</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Completed Mandi</span>
            <span class="material-symbols-outlined text-amber-600 text-lg">local_shipping</span>
          </div>
          <div class="text-2xl font-black text-slate-900">₹12.40 L</div>
          <div class="text-[11px] text-emerald-700 font-semibold">+18.4% YoY Deliveries</div>
        </div>

        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-500">Buyer Inquiries</span>
            <span class="material-symbols-outlined text-blue-600 text-lg">contact_mail</span>
          </div>
          <div class="text-2xl font-black text-slate-900">7 Offers</div>
          <div class="text-[11px] text-forest font-semibold">2 Bids Exceeding MSP</div>
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
          All Listings ({listings().length})
        </button>
        <button
          onClick={() => setFilter("locked")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "locked" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Escrow Locked (2)
        </button>
        <button
          onClick={() => setFilter("open")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "open" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Open for Booking (1)
        </button>
        <button
          onClick={() => setFilter("draft")}
          class={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
            filter() === "draft" ? "bg-forest text-white" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Drafts / Assay Pending (1)
        </button>
      </div>

      {/* Commodity Listing Cards Grid */}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <For each={filteredListings()}>
          {(lot) => (
            <div class="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4 hover:shadow-md transition-all flex flex-col justify-between">
              <div class="space-y-3">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-mono font-bold text-slate-400">Lot #{lot.id}</span>
                      <span class={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${lot.statusColor}`}>
                        {lot.statusBadge}
                      </span>
                    </div>
                    <h3 class="font-bold text-base text-slate-900 mt-1">{lot.crop}</h3>
                    <p class="text-xs text-slate-500">{lot.variety}</p>
                  </div>
                  <div class="text-right">
                    <div class="text-lg font-black text-forest">₹{lot.pricePerUnit.toLocaleString("en-IN")}<span class="text-xs text-slate-500 font-normal">/qtl</span></div>
                    <div class="text-xs font-bold text-slate-700">{lot.quantity} Quintals</div>
                  </div>
                </div>

                {/* Storage & Quality Specs */}
                <div class="bg-slate-50 p-3 rounded-xl border border-slate-200/60 text-xs space-y-1.5">
                  <div class="flex items-center justify-between text-slate-600">
                    <span class="flex items-center gap-1">
                      <span class="material-symbols-outlined text-sm text-slate-400">warehouse</span>
                      <span>{lot.warehouse}</span>
                    </span>
                    <span class="font-mono text-[11px] text-slate-500">{lot.tempRh}</span>
                  </div>
                  <div class="flex items-center justify-between text-slate-600 pt-1 border-t border-slate-200/60">
                    <span>Moisture: <strong class="text-forest">{lot.moisture}</strong></span>
                    <span>{lot.proteinClean}</span>
                  </div>
                </div>

                {/* Escrow or Buyer Progress Bar if locked */}
                {lot.buyerName && (
                  <div class="p-3 bg-emerald-50/70 rounded-xl border border-emerald-200 text-xs space-y-1.5">
                    <div class="flex justify-between items-center text-emerald-950">
                      <span class="font-bold">Buyer: {lot.buyerName}</span>
                      <span class="font-black text-forest">₹{lot.escrowLockedAmount?.toLocaleString("en-IN")} In Escrow</span>
                    </div>
                    <div class="w-full bg-emerald-200/60 rounded-full h-1.5">
                      <div class="bg-forest h-1.5 rounded-full" style={`width: ${lot.escrowPercent}%`}></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-emerald-800">
                      <span>Milestone {lot.escrowPercent === 60 ? "3/5: Quality Verified" : "2/5: Gate Inward"}</span>
                      <span>{lot.escrowPercent}% Tranche Locked</span>
                    </div>
                  </div>
                )}

                {/* Bids received banner if open */}
                {lot.bidsCount !== undefined && lot.bidsCount > 0 && (
                  <div class="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs flex items-center justify-between text-amber-900">
                    <div class="flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-amber-700 text-base">gavel</span>
                      <span class="font-bold">{lot.bidsCount} Active Buyer Bids Received</span>
                    </div>
                    <span class="text-xs font-extrabold text-amber-800">+4.8% Above Mandi MSP</span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div class="pt-3 border-t border-slate-100 flex items-center gap-2">
                <A
                  href={`/marketplace/${lot.id}`}
                  class="flex-1 py-2 text-center rounded-xl bg-forest text-white text-xs font-bold hover:bg-forest-light transition-colors"
                >
                  View Lot Inspection
                </A>
                <A
                  href={`/marketplace/bookings/${lot.id}`}
                  class="px-3 py-2 rounded-xl border border-slate-200 text-slate-700 text-xs font-bold hover:bg-slate-50 transition-colors flex items-center gap-1"
                >
                  <span class="material-symbols-outlined text-sm">lock_clock</span>
                  <span>Escrow</span>
                </A>
              </div>
            </div>
          )}
        </For>
      </div>

      {/* Modal for Creating Produce Listing */}
      {showCreateModal() && (
        <div class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 border border-slate-200 shadow-xl">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 class="font-black text-lg text-slate-900">List Harvest Parcel / Commodity</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                class="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleCreateListing} class="space-y-4 text-xs">
              <div class="space-y-1">
                <label class="font-bold text-slate-700">Crop &amp; Variety</label>
                <input
                  type="text"
                  placeholder="e.g. Lokwan Wheat Grade A, Pusa Basmati"
                  value={newCropName()}
                  onInput={(e) => setNewCropName(e.currentTarget.value)}
                  class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-forest text-sm"
                  required
                />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="font-bold text-slate-700">Lot Volume (Quintals)</label>
                  <input
                    type="number"
                    min="5"
                    max="1000"
                    value={newQuantity()}
                    onInput={(e) => setNewQuantity(Number(e.currentTarget.value))}
                    class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-forest text-sm"
                  />
                </div>
                <div class="space-y-1">
                  <label class="font-bold text-slate-700">Asking Price (₹/Qtl)</label>
                  <input
                    type="number"
                    min="500"
                    max="50000"
                    value={newPrice()}
                    onInput={(e) => setNewPrice(Number(e.currentTarget.value))}
                    class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-forest text-sm"
                  />
                </div>
              </div>

              <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-[11px] text-emerald-900 flex items-start gap-2">
                <span class="material-symbols-outlined text-forest text-sm mt-0.5">verified_user</span>
                <div>
                  <strong>NABL Lab Verification:</strong> Upon listing creation, a digital barcode will be issued for sample drop-off at your local KVK or APMC test center.
                </div>
              </div>

              <div class="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  class="px-4 py-2 rounded-xl border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="px-5 py-2 rounded-xl bg-forest hover:bg-forest-light font-bold text-white shadow transition-all"
                >
                  Publish Produce Listing
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
