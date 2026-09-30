import { Component, createSignal } from "solid-js";
import { A, useParams } from "@solidjs/router";

export const MarketplaceDetail: Component = () => {
  const params = useParams();
  const lotId = () => params.id || "MH-PUN-8402";

  const [quantity, setQuantity] = createSignal(40);
  const [depositPct, setDepositPct] = createSignal(20);
  const [isLocked, setIsLocked] = createSignal(false);

  const pricePerQtl = 2450;
  const maxAvailable = 85;

  const totalValue = () => quantity() * pricePerQtl;
  const escrowDeposit = () => Math.round(totalValue() * (depositPct() / 100));
  const balanceDue = () => totalValue() - escrowDeposit();

  const handleLockEscrow = () => {
    setIsLocked(true);
  };

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* Top Breadcrumb & Live Ticker */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <A href="/marketplace" class="hover:text-forest flex items-center gap-1 font-medium transition-colors">
            <span class="material-symbols-outlined text-sm">arrow_back</span>
            <span>Back to Marketplace</span>
          </A>
          <span>/</span>
          <span class="font-mono text-slate-700 font-semibold">Lot #{lotId()}</span>
        </div>
        <div class="flex items-center gap-2 self-start sm:self-auto">
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
            <span class="material-symbols-outlined text-xs">trending_up</span>
            APMC Mandi Benchmark: +4.2% Premium
          </span>
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <span class="material-symbols-outlined text-xs">verified</span>
            NABL Certified
          </span>
        </div>
      </div>

      {/* Lot Hero Header */}
      <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div class="space-y-2">
            <div class="flex flex-wrap items-center gap-2">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-forest/10 text-forest">
                Grade A+ Premium Milling
              </span>
              <span class="text-xs text-slate-400 font-mono">Lot #{lotId()}</span>
              <span class="inline-flex items-center gap-1 text-xs text-emerald-700 font-medium">
                <span class="material-symbols-outlined text-sm text-emerald-600">check_circle</span>
                Sahyadri FPO Verified
              </span>
            </div>
            <h1 class="text-2xl lg:text-3xl font-black text-slate-900 tracking-tight">
              Sharbati Golden Wheat (High Vitreous)
            </h1>
            <p class="text-xs text-slate-500">
              Harvest: Oct 2024 Rabi • Baramati Agro Cold Chain Hub, Pune Division
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200/70">
            <div>
              <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Spot Price</div>
              <div class="text-2xl font-black text-forest">₹{pricePerQtl.toLocaleString("en-IN")}<span class="text-xs font-medium text-slate-500">/qtl</span></div>
            </div>
            <div class="h-8 w-px bg-slate-200 hidden sm:block"></div>
            <div>
              <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Available Volume</div>
              <div class="text-2xl font-black text-slate-800">{maxAvailable} <span class="text-xs font-medium text-slate-500">Qtl (8.5 MT)</span></div>
            </div>
            <div class="h-8 w-px bg-slate-200 hidden sm:block"></div>
            <div>
              <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Min Order</div>
              <div class="text-xl font-bold text-slate-700">10 <span class="text-xs font-medium text-slate-500">Qtl</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Content */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Quality Assay & Warehouse Telemetry (7 cols) */}
        <div class="lg:col-span-7 space-y-6">
          {/* NABL Lab Quality Assay Card */}
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-forest text-xl">biotech</span>
                <div>
                  <h3 class="font-bold text-sm text-slate-900">NABL Quality Inspection Assay</h3>
                  <p class="text-[11px] text-slate-500">Accreditation #NQL-9042 • Dr. V. Kulkarni, Lead Assayer</p>
                </div>
              </div>
              <button class="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">download</span>
                <span>Assay PDF</span>
              </button>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
                <div class="text-[11px] text-slate-500 font-medium">Moisture Content</div>
                <div class="text-lg font-black text-forest mt-1">11.8%</div>
                <div class="text-[10px] text-emerald-700 font-semibold mt-0.5">Target &lt;12.0% (Optimal)</div>
              </div>
              <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
                <div class="text-[11px] text-slate-500 font-medium">Grain Luster</div>
                <div class="text-lg font-black text-slate-900 mt-1">94/100</div>
                <div class="text-[10px] text-slate-500 font-medium mt-0.5">High Vitreous Index</div>
              </div>
              <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
                <div class="text-[11px] text-slate-500 font-medium">Foreign Matter</div>
                <div class="text-lg font-black text-forest mt-1">0.4%</div>
                <div class="text-[10px] text-emerald-700 font-semibold mt-0.5">Permissible &lt;1.0%</div>
              </div>
              <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
                <div class="text-[11px] text-slate-500 font-medium">Protein (Gluten)</div>
                <div class="text-lg font-black text-slate-900 mt-1">13.6%</div>
                <div class="text-[10px] text-slate-500 font-medium mt-0.5">Milling Premium</div>
              </div>
              <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
                <div class="text-[11px] text-slate-500 font-medium">Pesticide Residue</div>
                <div class="text-lg font-black text-emerald-700 mt-1">0.00 ppm</div>
                <div class="text-[10px] text-emerald-700 font-semibold mt-0.5">Multi-Residue Clear</div>
              </div>
              <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
                <div class="text-[11px] text-slate-500 font-medium">Hectolitre Weight</div>
                <div class="text-lg font-black text-slate-900 mt-1">81.2 kg/hL</div>
                <div class="text-[10px] text-slate-500 font-medium mt-0.5">Heavy Bold Kernel</div>
              </div>
            </div>
          </div>

          {/* Warehouse & Cold Storage Telemetry */}
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-forest text-xl">warehouse</span>
                <div>
                  <h3 class="font-bold text-sm text-slate-900">Cold Chain Storage &amp; Telemetry</h3>
                  <p class="text-[11px] text-slate-500">Baramati Agro Cold Chain Hub • Bay 4, Slot #W-14</p>
                </div>
              </div>
              <span class="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                LoRa Live Sync
              </span>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-center">
                <div class="text-[10px] font-bold uppercase text-slate-400">Ambient Temp</div>
                <div class="text-base font-black text-slate-800 mt-0.5">18.2°C</div>
                <div class="text-[10px] text-emerald-700 font-medium">Controlled 16-20°C</div>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-center">
                <div class="text-[10px] font-bold uppercase text-slate-400">Rel. Humidity</div>
                <div class="text-base font-black text-slate-800 mt-0.5">62% RH</div>
                <div class="text-[10px] text-emerald-700 font-medium">Anti-spoilage</div>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-center">
                <div class="text-[10px] font-bold uppercase text-slate-400">Geo Tag</div>
                <div class="text-xs font-mono font-bold text-slate-700 mt-1">18.15° N, 74.57° E</div>
                <div class="text-[10px] text-slate-500 font-medium">Pune District</div>
              </div>
              <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-center">
                <div class="text-[10px] font-bold uppercase text-slate-400">E-Slip No.</div>
                <div class="text-xs font-mono font-bold text-forest mt-1">NERL-88412</div>
                <div class="text-[10px] text-slate-500 font-medium">WDRA Insured</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Advance Escrow Calculator & Order Action (5 cols) */}
        <div class="lg:col-span-5 space-y-6">
          <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5 sticky top-20">
            <div>
              <h3 class="font-bold text-base text-slate-900">Advance Escrow Booking</h3>
              <p class="text-xs text-slate-500 mt-0.5">Lock price today with ICICI Bank regulated smart contract escrow</p>
            </div>

            {/* Quantity Selector */}
            <div class="space-y-2">
              <div class="flex items-center justify-between text-xs">
                <label class="font-bold text-slate-700">Order Quantity (Quintals)</label>
                <span class="font-bold text-forest">{quantity()} Qtl</span>
              </div>
              <div class="flex items-center gap-2">
                <button
                  onClick={() => setQuantity((q) => Math.max(10, q - 5))}
                  class="w-10 h-10 rounded-xl border border-slate-200 font-bold text-lg text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center"
                >
                  -
                </button>
                <input
                  type="range"
                  min="10"
                  max={maxAvailable}
                  step="5"
                  value={quantity()}
                  onInput={(e) => setQuantity(Number(e.currentTarget.value))}
                  class="w-full accent-forest cursor-pointer"
                />
                <button
                  onClick={() => setQuantity((q) => Math.min(maxAvailable, q + 5))}
                  class="w-10 h-10 rounded-xl border border-slate-200 font-bold text-lg text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center"
                >
                  +
                </button>
              </div>
              <div class="flex gap-2 pt-1">
                {[20, 40, maxAvailable].map((val) => (
                  <button
                    onClick={() => setQuantity(val)}
                    class={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
                      quantity() === val ? "bg-forest text-white border-forest" : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {val === maxAvailable ? `Full Lot (${val} Qtl)` : `${val} Qtl`}
                  </button>
                ))}
              </div>
            </div>

            {/* Escrow Deposit Pct Slider */}
            <div class="space-y-2 pt-2 border-t border-slate-100">
              <div class="flex items-center justify-between text-xs">
                <label class="font-bold text-slate-700">Escrow Token Percentage</label>
                <span class="font-bold text-forest">{depositPct()}% Advance</span>
              </div>
              <div class="grid grid-cols-4 gap-2">
                {[20, 30, 40, 50].map((pct) => (
                  <button
                    onClick={() => setDepositPct(pct)}
                    class={`py-1.5 rounded-lg text-xs font-bold border transition-all ${
                      depositPct() === pct ? "bg-forest text-white border-forest" : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {pct}%
                  </button>
                ))}
              </div>
            </div>

            {/* Financial Breakdown Table */}
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200/70 space-y-2.5 text-xs">
              <div class="flex justify-between text-slate-600">
                <span>Produce Valuation ({quantity()} Qtl × ₹2,450)</span>
                <span class="font-bold text-slate-900">₹{totalValue().toLocaleString("en-IN")}</span>
              </div>
              <div class="flex justify-between text-forest font-semibold">
                <span>Escrow Advance Deposit ({depositPct()}%)</span>
                <span>₹{escrowDeposit().toLocaleString("en-IN")}</span>
              </div>
              <div class="flex justify-between text-slate-500">
                <span>Balance Due at Weighbridge Pass</span>
                <span>₹{balanceDue().toLocaleString("en-IN")}</span>
              </div>
              <div class="flex justify-between text-slate-500">
                <span>Digital Escrow Trustee Fee</span>
                <span class="text-emerald-700 font-bold">₹0 (e-NAM Subsidized)</span>
              </div>
              <div class="pt-2 border-t border-slate-200 flex justify-between font-black text-sm text-slate-900">
                <span>Payable Now (Escrow Lock)</span>
                <span class="text-forest text-base">₹{escrowDeposit().toLocaleString("en-IN")}</span>
              </div>
            </div>

            {/* Escrow Guarantee Badge */}
            <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-900 flex items-start gap-2">
              <span class="material-symbols-outlined text-emerald-700 text-base flex-shrink-0 mt-0.5">security</span>
              <div>
                <span class="font-bold">ICICI Bank Smart Escrow:</span> Funds held in RBI-regulated trustee escrow until physical quality verification passes at destination weighbridge.
              </div>
            </div>

            {/* Action Buttons */}
            {isLocked() ? (
              <div class="p-4 bg-forest text-white rounded-xl text-center space-y-2">
                <span class="material-symbols-outlined text-3xl">task_alt</span>
                <div class="font-black text-sm">Escrow Token Locked Successfully!</div>
                <p class="text-xs text-emerald-100">Booking Contract #ESC-{lotId()}-492 has been generated.</p>
                <A href="/marketplace/bookings" class="inline-block mt-2 px-4 py-2 bg-white text-forest text-xs font-bold rounded-lg hover:bg-slate-100 transition-colors">
                  View in My Bookings
                </A>
              </div>
            ) : (
              <div class="space-y-2">
                <button
                  onClick={handleLockEscrow}
                  class="w-full py-3.5 bg-forest hover:bg-forest-light text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
                >
                  <span class="material-symbols-outlined text-base">lock</span>
                  <span>Lock Price &amp; Book Escrow (₹{escrowDeposit().toLocaleString("en-IN")})</span>
                </button>
                <button class="w-full py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-bold text-xs rounded-xl transition-colors flex items-center justify-center gap-1.5">
                  <span class="material-symbols-outlined text-base">science</span>
                  <span>Request Physical Sample (₹250)</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
