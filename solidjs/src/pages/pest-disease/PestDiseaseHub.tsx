import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface PestOutbreak {
  id: string;
  name: string;
  scientificName: string;
  cropTarget: string;
  distanceKm: number;
  threatLevel: "critical" | "high" | "moderate" | "watch";
  affectedPlotsCount: number;
  activeLifeStage: string;
  recommendedAction: string;
}

interface BioInput {
  id: string;
  name: string;
  category: "microbial" | "botanical" | "parasitoid" | "chemical";
  dosage: string;
  price: string;
  stockStatus: string;
  cibrcReg: string;
  fpoCenter: string;
}

export const PestDiseaseHub: Component = () => {
  const [radiusFilter, setRadiusFilter] = createSignal<5 | 15 | 50>(15);
  const [activeIpmTab, setActiveIpmTab] = createSignal<"bio" | "parasitoid" | "chemical">("bio");
  const [reserveSuccess, setReserveSuccess] = createSignal<string | null>(null);

  const outbreaks: PestOutbreak[] = [
    {
      id: "out-1",
      name: "Fall Armyworm (FAW)",
      scientificName: "Spodoptera frugiperda",
      cropTarget: "Maize / Sweetcorn & Sorghum",
      distanceKm: 3.2,
      threatLevel: "critical",
      affectedPlotsCount: 48,
      activeLifeStage: "Larval Instar L2 (Critical Spray Window)",
      recommendedAction: "Apply Bacillus thuringiensis (Bt) or Chlorantraniliprole immediately in whorls."
    },
    {
      id: "out-2",
      name: "Downy Mildew",
      scientificName: "Plasmopara viticola",
      cropTarget: "Grape Vineyards (Thompson Seedless)",
      distanceKm: 7.8,
      threatLevel: "high",
      affectedPlotsCount: 26,
      activeLifeStage: "Active Sporulation (High Leaf Moisture)",
      recommendedAction: "Foliar spray of Potassium Phosphonate (3g/L) + Mancozeb (2g/L)."
    },
    {
      id: "out-3",
      name: "Purple Blotch & Thrips",
      scientificName: "Alternaria porri & Thrips tabaci",
      cropTarget: "Kharif Red Onion",
      distanceKm: 11.4,
      threatLevel: "moderate",
      affectedPlotsCount: 15,
      activeLifeStage: "Early Lesion Development",
      recommendedAction: "Spray Neem Azadirachtin 10,000 ppm (3ml/L) + Bio-fungicide Beauveria."
    },
    {
      id: "out-4",
      name: "Yellow Stem Borer",
      scientificName: "Scirpophaga incertulas",
      cropTarget: "Basmati Paddy",
      distanceKm: 14.1,
      threatLevel: "watch",
      affectedPlotsCount: 9,
      activeLifeStage: "Adult Moth Flight Detection",
      recommendedAction: "Install 8 Pheromone traps/acre with Scirpo-lure."
    }
  ];

  const bioInputs: BioInput[] = [
    {
      id: "bio-1",
      name: "Neem Azadirachtin 10,000 ppm (Godrej Achook)",
      category: "botanical",
      dosage: "3.0 ml / Liter water",
      price: "₹420 / 500ml",
      stockStatus: "12 Bottles Available",
      cibrcReg: "CIR-11482/2014-Azadirachtin",
      fpoCenter: "Sahyadri FPO • Pimpalgaon Hub"
    },
    {
      id: "bio-2",
      name: "Beauveria bassiana 1x10⁸ CFU/g (Biomax)",
      category: "microbial",
      dosage: "5.0 g / Liter water",
      price: "₹280 / 1 kg",
      stockStatus: "8 Packets Available",
      cibrcReg: "CIR-29014/2019-Beauveria",
      fpoCenter: "KVK Niphad Input Counter"
    },
    {
      id: "bio-3",
      name: "Bacillus thuringiensis var. kurstaki (Dipel 8L)",
      category: "microbial",
      dosage: "2.0 ml / Liter water",
      price: "₹560 / 1 Liter",
      stockStatus: "15 Cans Available",
      cibrcReg: "CIR-44910/2021-Bt",
      fpoCenter: "Sahyadri FPO • Pimpalgaon Hub"
    },
    {
      id: "bio-4",
      name: "Trichogramma pretiosum Egg Cards",
      category: "parasitoid",
      dosage: "50,000 parasitized eggs / acre",
      price: "₹150 / sheet",
      stockStatus: "Cold-chain 24h dispatch",
      cibrcReg: "Bio-Agent Certified ICAR-NBAIR",
      fpoCenter: "Biological Control Lab, Pune"
    },
    {
      id: "bio-5",
      name: "Coragen (Chlorantraniliprole 18.5% SC)",
      category: "chemical",
      dosage: "0.4 ml / Liter (Last resort emergency)",
      price: "₹1,850 / 150ml",
      stockStatus: "6 Bottles in Stock",
      cibrcReg: "CIR-8842/2009-Chlorantraniliprole",
      fpoCenter: "Sahyadri FPO • Pimpalgaon Hub"
    }
  ];

  const handleReserve = (product: BioInput) => {
    setReserveSuccess(product.name);
    setTimeout(() => setReserveSuccess(null), 3500);
  };

  return (
    <div class="space-y-6">
      {/* Header & Breadcrumb */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
            <A href="/dashboard" class="hover:underline">Home</A>
            <span>/</span>
            <A href="/crops/my-crops" class="hover:underline">Crop Protection</A>
            <span>/</span>
            <span class="text-brand-600 dark:text-brand-400 font-medium">Pest &amp; Disease Radar</span>
          </div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <span class="material-symbols-outlined text-brand-600 text-3xl">pest_control</span>
            Pest &amp; Disease Outbreak Radar &amp; IPM Hub
          </h1>
          <p class="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
            Hyperlocal quarantine outbreak radar, degree-day biological life-cycle forecasts, and ICAR-CIBRC certified bio-control protocols.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <A
            href="/diagnose"
            class="px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-all flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-base">photo_camera</span>
            AI Leaf Scanner
          </A>
        </div>
      </div>

      {/* REGIONAL QUARANTINE OUTBREAK BANNER */}
      <div class="rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 text-white p-5 shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="relative z-10 flex items-start gap-3.5">
          <div class="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/30">
            <span class="material-symbols-outlined text-2xl text-white animate-pulse">crisis_alert</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-black uppercase tracking-wider bg-white/25 px-2 py-0.5 rounded-full">
                Regional Quarantine Alert
              </span>
              <span class="text-xs font-medium text-red-100">Nashik &amp; Jalgaon Agricultural Belt</span>
            </div>
            <h3 class="text-lg font-black mt-1">Fall Armyworm (FAW) Critical Surge • 48 Farms Affected</h3>
            <p class="text-xs text-red-100 mt-0.5 max-w-2xl leading-relaxed">
              Larval instar L2 stage observed in maize &amp; sweetcorn within 3.2km radius. Spodolure pheromone trap catch exceeded threshold (12 moths/trap/night). Urgent whorl application recommended within 48 hours.
            </p>
          </div>
        </div>

        <div class="relative z-10 flex items-center gap-2 shrink-0">
          <button
            onClick={() => alert("Broadcasting FAW advisory to WhatsApp Farmer Group #NiphadAgriWatch")}
            class="px-4 py-2.5 rounded-xl bg-white text-red-700 hover:bg-red-50 text-xs font-black shadow-md transition-all flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-base">share</span>
            Broadcast to Workers
          </button>
        </div>
      </div>

      {/* AI SCANNER LAUNCH CARD */}
      <div class="bg-gradient-to-r from-emerald-900 to-slate-900 text-white rounded-2xl p-5 border border-emerald-800/60 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-3xl text-emerald-400">psychiatry</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300">
                CropSense Vision AI
              </span>
              <span class="text-xs text-emerald-200">98.4% Pathology Accuracy • 0.8s Inference</span>
            </div>
            <h3 class="text-base font-black mt-1">Instant Foliar Lesion &amp; Pest Visual Scanner</h3>
            <p class="text-xs text-slate-300 mt-0.5">
              Take a close-up photo of infected leaf, stem, or fruit to identify pathogens and generate targeted organic prescriptions.
            </p>
          </div>
        </div>

        <A
          href="/diagnose"
          class="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs shadow-md transition-all flex items-center justify-center gap-2 shrink-0"
        >
          <span class="material-symbols-outlined text-lg">camera</span>
          Launch Leaf Scanner
        </A>
      </div>

      {/* RADAR & GDD LIFE-CYCLE FORECASTING SECTION */}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Outbreak Heatmap & Radar (2 cols) */}
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-brand-600">radar</span>
                Regional Outbreak Radar &amp; Spore Trajectory
              </h2>
              <p class="text-xs text-slate-500 mt-0.5">Real-time data from 24 IoT pheromone traps &amp; spore detection nodes</p>
            </div>

            {/* Radius Filters */}
            <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs">
              <button
                onClick={() => setRadiusFilter(5)}
                class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  radiusFilter() === 5
                    ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                5 km Ward
              </button>
              <button
                onClick={() => setRadiusFilter(15)}
                class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  radiusFilter() === 15
                    ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                15 km Taluka
              </button>
              <button
                onClick={() => setRadiusFilter(50)}
                class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  radiusFilter() === 50
                    ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                50 km District
              </button>
            </div>
          </div>

          {/* Outbreak Threat List */}
          <div class="space-y-3">
            <For each={outbreaks}>
              {outbreak => (
                <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all space-y-2">
                  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div class="flex items-center gap-2.5">
                      <span
                        class={`w-3 h-3 rounded-full ${
                          outbreak.threatLevel === "critical"
                            ? "bg-red-500 animate-pulse"
                            : outbreak.threatLevel === "high"
                            ? "bg-amber-500"
                            : outbreak.threatLevel === "moderate"
                            ? "bg-yellow-500"
                            : "bg-blue-500"
                        }`}
                      />
                      <div>
                        <div class="flex items-center gap-2">
                          <h4 class="text-xs font-black text-slate-900 dark:text-white">{outbreak.name}</h4>
                          <span class="text-[11px] font-serif italic text-slate-400">({outbreak.scientificName})</span>
                        </div>
                        <p class="text-[11px] text-slate-500">Target Crop: {outbreak.cropTarget}</p>
                      </div>
                    </div>

                    <div class="flex items-center gap-3">
                      <span class="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
                        {outbreak.distanceKm} km away
                      </span>
                      <span
                        class={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                          outbreak.threatLevel === "critical"
                            ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                            : outbreak.threatLevel === "high"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                            : "bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300"
                        }`}
                      >
                        {outbreak.threatLevel}
                      </span>
                    </div>
                  </div>

                  <div class="text-xs bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200/80 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <span class="text-slate-500">
                      Phase: <strong class="text-slate-800 dark:text-slate-200">{outbreak.activeLifeStage}</strong>
                    </span>
                    <span class="text-brand-600 dark:text-brand-400 font-medium">{outbreak.recommendedAction}</span>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>

        {/* Life-Cycle Degree-Day (GDD) Tracker (1 col) */}
        <div class="space-y-6">
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div>
              <div class="flex items-center justify-between">
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-base text-brand-600">timelapse</span>
                  Life-Cycle Degree-Day (GDD)
                </h3>
                <span class="text-xs font-mono font-bold text-brand-600">342.6 GDD</span>
              </div>
              <h4 class="text-sm font-black text-slate-900 dark:text-white mt-1">Fall Armyworm Biological Clock</h4>
              <p class="text-xs text-slate-500 mt-0.5">Accumulated heat units since first moth flight trigger</p>
            </div>

            <div class="relative pl-5 border-l-2 border-slate-200 dark:border-slate-700 space-y-4 text-xs">
              <div class="relative">
                <span class="absolute -left-[27px] top-0.5 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900" />
                <span class="text-slate-400 text-[10px] block">Stage 1 • Completed</span>
                <span class="font-bold text-slate-800 dark:text-slate-200">Egg Masses in Foliar Underside</span>
              </div>

              <div class="relative bg-emerald-50 dark:bg-emerald-950/60 p-2.5 rounded-xl border border-emerald-300 dark:border-emerald-800">
                <span class="absolute -left-[27px] top-3.5 w-3.5 h-3.5 rounded-full bg-brand-600 border-2 border-white dark:border-slate-900 animate-ping" />
                <span class="text-emerald-700 dark:text-emerald-300 font-black text-[10px] uppercase block">
                  Stage 2 • ACTIVE CRITICAL SPRAY WINDOW
                </span>
                <span class="font-bold text-slate-900 dark:text-white block mt-0.5">Larval Instar L1–L2 (Vulnerable)</span>
                <p class="text-[11px] text-emerald-800 dark:text-emerald-200 mt-0.5">
                  Bio-agents (Bt and Beauveria) achieve 92% efficacy now before larvae burrow into leaf whorls.
                </p>
              </div>

              <div class="relative opacity-60">
                <span class="absolute -left-[27px] top-0.5 w-3.5 h-3.5 rounded-full bg-slate-300 dark:bg-slate-600 border-2 border-white dark:border-slate-900" />
                <span class="text-slate-400 text-[10px] block">Stage 3 • In 3 Days</span>
                <span class="font-semibold text-slate-700 dark:text-slate-300">Voracious Instar L3–L6 (Heavy Foliar Loss)</span>
              </div>

              <div class="relative opacity-40">
                <span class="absolute -left-[27px] top-0.5 w-3.5 h-3.5 rounded-full bg-slate-300 dark:bg-slate-600 border-2 border-white dark:border-slate-900" />
                <span class="text-slate-400 text-[10px] block">Stage 4 • In 9 Days</span>
                <span class="font-semibold text-slate-700 dark:text-slate-300">Pupal Stage in Soil (Deep plowing required)</span>
              </div>
            </div>

            <div class="pt-2 border-t border-slate-100 dark:border-slate-800">
              <div class="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                <span>Pheromone Traps:</span>
                <strong class="text-slate-900 dark:text-white">8 traps/acre (Spodolure)</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* INTEGRATED PEST MANAGEMENT (IPM) PROTOCOLS & FPO INVENTORY */}
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 class="text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-brand-600">inventory_2</span>
              ICAR-CIBRC Certified Bio-Inputs &amp; Local FPO Inventory
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">Reserve authentic microbial cultures and certified parasitoid cards at subsidized FPO prices</p>
          </div>

          <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs">
            <button
              onClick={() => setActiveIpmTab("bio")}
              class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeIpmTab() === "bio"
                  ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Bio-Pesticides
            </button>
            <button
              onClick={() => setActiveIpmTab("parasitoid")}
              class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeIpmTab() === "parasitoid"
                  ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Parasitoids (Cards)
            </button>
            <button
              onClick={() => setActiveIpmTab("chemical")}
              class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeIpmTab() === "chemical"
                  ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Chemical (Last Resort)
            </button>
          </div>
        </div>

        {reserveSuccess() && (
          <div class="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs font-medium flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-base text-emerald-600">check_circle</span>
              <span>Reserved {reserveSuccess()} at Pimpalgaon Hub! OTP token sent to registered mobile.</span>
            </div>
          </div>
        )}

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <For
            each={bioInputs.filter(item => {
              if (activeIpmTab() === "bio") return item.category === "botanical" || item.category === "microbial";
              if (activeIpmTab() === "parasitoid") return item.category === "parasitoid";
              return item.category === "chemical";
            })}
          >
            {item => (
              <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all flex flex-col justify-between">
                <div>
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                      {item.cibrcReg}
                    </span>
                    <span class="text-xs font-black text-brand-600 dark:text-brand-400">{item.price}</span>
                  </div>
                  <h4 class="text-xs font-black text-slate-900 dark:text-white mt-1">{item.name}</h4>
                  <div class="text-[11px] text-slate-500 mt-1 space-y-0.5">
                    <p>Dosage: <strong class="text-slate-700 dark:text-slate-300">{item.dosage}</strong></p>
                    <p>Location: {item.fpoCenter}</p>
                    <p class="text-emerald-600 dark:text-emerald-400 font-semibold">{item.stockStatus}</p>
                  </div>
                </div>

                <button
                  onClick={() => handleReserve(item)}
                  class="mt-4 w-full py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-all flex items-center justify-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-sm">bookmark_add</span>
                  Reserve at FPO Center
                </button>
              </div>
            )}
          </For>
        </div>
      </div>
    </div>
  );
};
