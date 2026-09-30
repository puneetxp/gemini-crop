import { Component } from "solid-js";
import { useParams, A } from "@solidjs/router";

export const BookingDetails: Component = () => {
  const params = useParams();

  return (
    <div class="space-y-6 max-w-4xl mx-auto pb-20">
      <div class="flex items-center gap-3">
        <A href="/marketplace" class="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900">
          <span class="material-symbols-outlined text-xl">arrow_back</span>
        </A>
        <div>
          <h1 class="text-xl font-black text-slate-900">Advance Forward Booking: {params.id || "MANDI-102"}</h1>
          <p class="text-xs text-slate-500">Escrow Contract & Quality Verification Workflow</p>
        </div>
      </div>

      <div class="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/60">
          <div>
            <span class="text-xs font-bold text-slate-400 uppercase">Contracted Value</span>
            <div class="text-2xl font-black text-slate-900">&#8377;9,27,500</div>
            <div class="text-xs text-slate-500">350 Quintals @ &#8377;2,650/Qtl</div>
          </div>
          <div class="sm:text-right">
            <span class="text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-1 rounded-full">
              Escrow Funded (15%)
            </span>
            <div class="text-xs text-slate-500 mt-1">Held in Axis Bank Agricultural Escrow</div>
          </div>
        </div>

        {/* Milestone Steps */}
        <div class="space-y-4">
          <h3 class="font-bold text-sm text-slate-900">Execution Milestones</h3>
          <div class="space-y-3">
            <div class="flex items-start gap-3 p-3 bg-emerald-50/50 rounded-xl border border-emerald-100">
              <span class="material-symbols-outlined text-emerald-600 text-xl mt-0.5">check_circle</span>
              <div class="flex-1">
                <h4 class="text-xs font-bold text-slate-900">1. Advance Agreement Confirmed</h4>
                <p class="text-xs text-slate-500">Signed with Aadhaar e-Sign on 14 September 2026</p>
              </div>
            </div>

            <div class="flex items-start gap-3 p-3 bg-emerald-50/50 rounded-xl border border-emerald-100">
              <span class="material-symbols-outlined text-emerald-600 text-xl mt-0.5">check_circle</span>
              <div class="flex-1">
                <h4 class="text-xs font-bold text-slate-900">2. Mid-Season Satellite Verification</h4>
                <p class="text-xs text-slate-500">Sentinel-2 confirmed 98% germination and healthy biomass</p>
              </div>
            </div>

            <div class="flex items-start gap-3 p-3 bg-amber-50 rounded-xl border border-amber-200">
              <span class="material-symbols-outlined text-amber-600 text-xl mt-0.5">hourglass_top</span>
              <div class="flex-1">
                <h4 class="text-xs font-bold text-amber-900">3. Harvest Quality Testing & Moisture Audit</h4>
                <p class="text-xs text-amber-800">Scheduled for 15 April 2027 upon plot harvest</p>
              </div>
            </div>

            <div class="flex items-start gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span class="material-symbols-outlined text-slate-400 text-xl mt-0.5">payments</span>
              <div class="flex-1">
                <h4 class="text-xs font-bold text-slate-700">4. Escrow Release & Transport Logistics</h4>
                <p class="text-xs text-slate-400">Final 85% settlement disbursed directly to farmer bank account</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
