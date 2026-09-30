import { Component } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { isAuthenticated, user, signInDemo } from "../stores/auth.store";
import { showToast } from "../components/ui/Toast";
import { t } from "../stores/i18n.store";

export const Home: Component = () => {
  const navigate = useNavigate();
  return (
    <div class="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Hero Section */}
      <section class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-forest via-emerald-800 to-emerald-950 text-white p-8 md:p-12 shadow-xl shadow-forest/15">
        <div class="relative z-10 max-w-2xl space-y-4">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-semibold text-amber-300">
            <span class="material-symbols-outlined text-sm">auto_awesome</span>
            <span>Next-Gen Agricultural Intelligence</span>
          </div>
          <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
            Smart Farming, <br />
            <span class="text-amber-400">Higher Yields</span> & Guaranteed Buyers
          </h1>
          <p class="text-emerald-100 text-sm md:text-base leading-relaxed">
            CropSense AI unifies satellite NDVI indices, multimodal plant pathology, livestock health records,
            and advance harvest contracts into a unified Krishi Command Center.
          </p>
          <div class="flex flex-wrap items-center gap-3 pt-4">
            <A
              href="/dashboard"
              class="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-sm shadow-lg shadow-amber-500/25 transition-all flex items-center gap-2"
            >
              <span>Launch Command Center</span>
              <span class="material-symbols-outlined text-lg">arrow_forward</span>
            </A>
            {!isAuthenticated() && (
              <button
                onClick={async () => {
                  const res = await signInDemo();
                  if (res.success) navigate("/dashboard");
                  else showToast("error", res.error || "Could not start a demo session");
                }}
                class="px-5 py-3 bg-white/10 hover:bg-white/20 border border-white/30 text-white font-semibold rounded-xl text-sm transition-all"
              >
                Instant Demo Access
              </button>
            )}
          </div>
        </div>

        {/* Ambient Decorative Badge */}
        <div class="absolute -right-10 -bottom-10 opacity-10 pointer-events-none">
          <span class="material-symbols-outlined text-[320px]">psychology_alt</span>
        </div>
      </section>

      {/* Quick Access Grid */}
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <A
          href="/dashboard"
          class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between"
        >
          <div>
            <div class="w-12 h-12 rounded-xl bg-forest/10 text-forest flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-2xl">dashboard</span>
            </div>
            <h3 class="font-bold text-slate-900 group-hover:text-forest transition-colors">Command Center</h3>
            <p class="text-xs text-slate-500 mt-1">Multi-plot telemetry, weather warnings, and crop health metrics.</p>
          </div>
          <span class="text-xs font-semibold text-emerald mt-4 inline-flex items-center gap-1">
            Open Dashboard &rarr;
          </span>
        </A>

        <A
          href="/diagnose"
          class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between"
        >
          <div>
            <div class="w-12 h-12 rounded-xl bg-emerald/10 text-emerald flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-2xl">psychology</span>
            </div>
            <h3 class="font-bold text-slate-900 group-hover:text-emerald transition-colors">AI Crop Doctor</h3>
            <p class="text-xs text-slate-500 mt-1">Snap leaf photos for instant pathology and chemical treatment safety.</p>
          </div>
          <span class="text-xs font-semibold text-emerald mt-4 inline-flex items-center gap-1">
            Diagnose Crop &rarr;
          </span>
        </A>

        <A
          href="/livestock"
          class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between"
        >
          <div>
            <div class="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-2xl">pets</span>
            </div>
            <h3 class="font-bold text-slate-900 group-hover:text-amber-700 transition-colors">Pashu Hub</h3>
            <p class="text-xs text-slate-500 mt-1">Herd management, milk production logging, and vet appointment bookings.</p>
          </div>
          <span class="text-xs font-semibold text-amber-700 mt-4 inline-flex items-center gap-1">
            Manage Herd &rarr;
          </span>
        </A>

        <A
          href="/marketplace"
          class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all group flex flex-col justify-between"
        >
          <div>
            <div class="w-12 h-12 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-2xl">storefront</span>
            </div>
            <h3 class="font-bold text-slate-900 group-hover:text-sky-700 transition-colors">Mandi Marketplace</h3>
            <p class="text-xs text-slate-500 mt-1">Pre-harvest forward contracts with escrow payments and verified buyers.</p>
          </div>
          <span class="text-xs font-semibold text-sky-700 mt-4 inline-flex items-center gap-1">
            Explore Mandi &rarr;
          </span>
        </A>
      </section>
    </div>
  );
};
