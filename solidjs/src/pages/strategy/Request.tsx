import { Component, createSignal, For } from "solid-js";
import { A, useNavigate, useSearchParams } from "@solidjs/router";

interface SeasonOption {
  id: string;
  name: string;
  period: string;
  profile: string;
  temp: string;
  defaultChecked: boolean;
}

interface GoalOption {
  id: string;
  title: string;
  badge: string;
  desc: string;
  icon: string;
}

export const RequestStrategy: Component = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const farmId = () => searchParams.farmId || "1";

  // Form State
  const [selectedSeasons, setSelectedSeasons] = createSignal<string[]>([
    "kharif",
    "rabi",
    "zaid"
  ]);
  const [selectedGoal, setSelectedGoal] = createSignal<string>("profit");
  const [budget, setBudget] = createSignal<number>(450000);
  const [riskTolerance, setRiskTolerance] = createSignal<string>("balanced");
  const [isGenerating, setIsGenerating] = createSignal<boolean>(false);

  // Crop Inclusions & Exclusions
  const [crops, setCrops] = createSignal<{ name: string; type: "include" | "exclude" }[]>([
    { name: "Sharbati Wheat", type: "include" },
    { name: "Soybean (JS-335)", type: "include" },
    { name: "Pomegranate (Bhagwa)", type: "include" },
    { name: "Chickpea (Desi Gram)", type: "include" },
    { name: "Nashik Red Onion", type: "include" },
    { name: "Sugarcane (Water Intensive)", type: "exclude" },
    { name: "Bt Cotton (Pest Vulnerable)", type: "exclude" }
  ]);

  const seasons: SeasonOption[] = [
    {
      id: "kharif",
      name: "Kharif 2024",
      period: "Jun – Oct 2024",
      profile: "Monsoon Pulses & Soybean (640mm Rain)",
      temp: "26°C – 32°C",
      defaultChecked: true
    },
    {
      id: "rabi",
      name: "Rabi 2024–25",
      period: "Nov 2024 – Mar 2025",
      profile: "Sharbati Wheat & Gram (Cool Nights)",
      temp: "12°C – 28°C",
      defaultChecked: true
    },
    {
      id: "zaid",
      name: "Zaid 2025",
      period: "Apr – Jun 2025",
      profile: "Short-Cycle Moong & Multi-Cut Fodder",
      temp: "28°C – 41°C",
      defaultChecked: true
    }
  ];

  const goals: GoalOption[] = [
    {
      id: "profit",
      title: "Max Profit & Cashflow",
      badge: "+24% Margin",
      desc: "Optimizes harvest timing with e-NAM peak price arrival windows and forward contract delivery.",
      icon: "trending_up"
    },
    {
      id: "carbon",
      title: "Soil Carbon & Health",
      badge: "N-Positive",
      desc: "Bio-mass mulching and biological nitrogen budgeting to rebuild Vertisol organic carbon profile.",
      icon: "compost"
    },
    {
      id: "water",
      title: "Water Scarcity Resilience",
      badge: "-35% Demand",
      desc: "Micro-drip sensor scheduling, rootzone moisture telemetry, and drought-hardy pulses.",
      icon: "water_drop"
    },
    {
      id: "organic",
      title: "Export Organic Quality",
      badge: "NABL Ready",
      desc: "Zero chemical synthetic residue adherence, APEDA export standards, and neem bio-shielding.",
      icon: "verified"
    }
  ];

  const toggleSeason = (seasonId: string) => {
    if (selectedSeasons().includes(seasonId)) {
      if (selectedSeasons().length > 1) {
        setSelectedSeasons(selectedSeasons().filter((s) => s !== seasonId));
      }
    } else {
      setSelectedSeasons([...selectedSeasons(), seasonId]);
    }
  };

  const removeCrop = (index: number) => {
    setCrops(crops().filter((_, i) => i !== index));
  };

  const toggleCropType = (index: number) => {
    const updated = [...crops()];
    updated[index].type = updated[index].type === "include" ? "exclude" : "include";
    setCrops(updated);
  };

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      navigate("/crops/annual-strategy/1");
    }, 1200);
  };

  // Dynamic calculations based on slider
  const seedsCost = () => Math.round(budget() * 0.18);
  const fertigationCost = () => Math.round(budget() * 0.32);
  const dripCost = () => Math.round(budget() * 0.25);
  const droneCost = () => Math.round(budget() * 0.15);
  const contingencyCost = () => Math.round(budget() * 0.10);

  const projectedGrossMin = () => Math.round(budget() * 2.18);
  const projectedGrossMax = () => Math.round(budget() * 2.75);
  const projectedNet = () => Math.round((projectedGrossMin() + projectedGrossMax()) / 2 - budget());

  return (
    <div class="space-y-6 pb-20">
      {/* Top Breadcrumb & Selected Farm Header */}
      <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-6 shadow-sm">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
              <span class="material-symbols-outlined text-sm">psychiatry</span>
              <span>GEMINI 2.0 AGRI-STRATEGY ENGINE</span>
              <span>•</span>
              <span>STEP 2 OF 3: PARAMETER CALIBRATION</span>
            </div>
            <h1 class="text-2xl lg:text-3xl font-bold text-on-surface dark:text-white">
              Configure Multi-Season Parameters
            </h1>
            <p class="text-sm text-on-surface-variant dark:text-slate-400 mt-1 max-w-3xl">
              Calibrate operational capital, crop rotation choices, risk tolerance, and water quotas.
              Gemini will synthesize a 365-day crop roadmap with input scheduling and forward hedging.
            </p>
          </div>

          <A
            href="/strategy/select-farm"
            class="px-4 py-2.5 rounded-xl border border-outline-variant/40 bg-surface-container-low dark:bg-slate-800 text-on-surface dark:text-slate-200 text-xs font-bold hover:bg-surface-container transition-colors flex items-center gap-2 self-start md:self-auto shrink-0"
          >
            <span class="material-symbols-outlined text-sm">swap_horiz</span>
            <span>Change Target Farm</span>
          </A>
        </div>

        {/* Selected Farm Pill */}
        <div class="mt-5 p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2.5">
            <span class="material-symbols-outlined text-emerald-700 dark:text-emerald-400 text-lg">
              agriculture
            </span>
            <div>
              <strong class="text-emerald-950 dark:text-emerald-200 text-sm font-bold">
                {farmId() === "2"
                  ? "Sahyadri Terrace Agro (12.0 Ac)"
                  : farmId() === "3"
                  ? "Khandesh Alluvial Tract (24.0 Ac)"
                  : "Krishna Valley Farm (18.5 Ac Cultivated)"}
              </strong>
              <span class="text-emerald-800 dark:text-emerald-400 ml-2">
                Cadastral Gut #142/2A • Deep Black Vertisol (pH 7.2) • Nashik MH
              </span>
            </div>
          </div>
          <span class="px-2.5 py-1 rounded-full bg-emerald-200/80 dark:bg-emerald-900/60 text-emerald-900 dark:text-emerald-300 font-bold text-[11px]">
            ✓ 100% Calibrated Baseline
          </span>
        </div>
      </div>

      {/* Main 12-Column Layout: Form (8-col) + Simulation execution card (4-col) */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8-Columns: Parameter Customizer */}
        <div class="lg:col-span-8 space-y-6">
          {/* Section 1: Target Seasons */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-base font-bold text-on-surface dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-emerald-600 text-lg">calendar_month</span>
                  <span>1. Planning Horizon & Target Seasons</span>
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                  Select which cropping windows to optimize across the 365-day agricultural cycle.
                </p>
              </div>
              <span class="text-xs font-semibold text-emerald-600">
                {selectedSeasons().length} of 3 Seasons Active
              </span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <For each={seasons}>
                {(season) => {
                  const isActive = () => selectedSeasons().includes(season.id);
                  return (
                    <div
                      onClick={() => toggleSeason(season.id)}
                      class={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        isActive()
                          ? "border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-xs"
                          : "border-outline-variant/30 bg-surface-container-low dark:bg-slate-800/40 opacity-70"
                      }`}
                    >
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-sm text-on-surface dark:text-white">
                          {season.name}
                        </span>
                        <input
                          type="checkbox"
                          checked={isActive()}
                          onChange={() => toggleSeason(season.id)}
                          class="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4 cursor-pointer"
                        />
                      </div>
                      <div class="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                        {season.period}
                      </div>
                      <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                        {season.profile}
                      </div>
                      <div class="mt-2 text-[10px] text-slate-400 flex items-center gap-1">
                        <span class="material-symbols-outlined text-xs">thermostat</span>
                        <span>{season.temp}</span>
                      </div>
                    </div>
                  );
                }}
              </For>
            </div>
          </div>

          {/* Section 2: Strategic Goal */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div>
              <h3 class="text-base font-bold text-on-surface dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600 text-lg">flag</span>
                <span>2. Primary Strategic Goal</span>
              </h3>
              <p class="text-xs text-slate-500 mt-0.5">
                Steers Gemini's crop rotation optimization function and input allocations.
              </p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <For each={goals}>
                {(goal) => {
                  const isSelected = () => selectedGoal() === goal.id;
                  return (
                    <div
                      onClick={() => setSelectedGoal(goal.id)}
                      class={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        isSelected()
                          ? "border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-sm"
                          : "border-outline-variant/30 bg-surface-container-low dark:bg-slate-800/40 hover:border-emerald-500/40"
                      }`}
                    >
                      <div class="flex items-center justify-between mb-1.5">
                        <div class="flex items-center gap-2">
                          <span class="material-symbols-outlined text-emerald-600 text-lg">
                            {goal.icon}
                          </span>
                          <span class="font-bold text-sm text-on-surface dark:text-white">
                            {goal.title}
                          </span>
                        </div>
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-300">
                          {goal.badge}
                        </span>
                      </div>
                      <p class="text-xs text-on-surface-variant dark:text-slate-400 mt-1">
                        {goal.desc}
                      </p>
                    </div>
                  );
                }}
              </For>
            </div>
          </div>

          {/* Section 3: Capital Budget */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 class="text-base font-bold text-on-surface dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-emerald-600 text-lg">payments</span>
                  <span>3. Operational Capital & Input Budget</span>
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                  Total seasonal outlay for seeds, water soluble fertigation, and bio-protection.
                </p>
              </div>

              <div class="text-right">
                <span class="text-2xl font-bold text-emerald-700 dark:text-emerald-400 font-mono">
                  ₹{budget().toLocaleString("en-IN")}
                </span>
                <span class="block text-[10px] text-slate-500">
                  (₹{Math.round(budget() / 18.5).toLocaleString("en-IN")}/Acre)
                </span>
              </div>
            </div>

            {/* Slider */}
            <div class="space-y-2 pt-2">
              <input
                type="range"
                min="150000"
                max="900000"
                step="25000"
                value={budget()}
                onInput={(e) => setBudget(parseInt(e.currentTarget.value, 10))}
                class="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
              />
              <div class="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>₹1.5L (Low input / Organic)</span>
                <span>₹4.5L (Recommended)</span>
                <span>₹9.0L (High-Density Hort)</span>
              </div>
            </div>

            {/* Cost Breakdown Bar */}
            <div class="pt-2">
              <div class="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
                Automated Working Capital Allocation:
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
                <div class="p-2 rounded-lg bg-surface-container dark:bg-slate-800">
                  <div class="font-bold text-on-surface dark:text-white">
                    ₹{seedsCost().toLocaleString("en-IN")}
                  </div>
                  <div class="text-[10px] text-slate-500">Seeds (18%)</div>
                </div>
                <div class="p-2 rounded-lg bg-surface-container dark:bg-slate-800">
                  <div class="font-bold text-on-surface dark:text-white">
                    ₹{fertigationCost().toLocaleString("en-IN")}
                  </div>
                  <div class="text-[10px] text-slate-500">Fertigation (32%)</div>
                </div>
                <div class="p-2 rounded-lg bg-surface-container dark:bg-slate-800">
                  <div class="font-bold text-on-surface dark:text-white">
                    ₹{dripCost().toLocaleString("en-IN")}
                  </div>
                  <div class="text-[10px] text-slate-500">Irrigation (25%)</div>
                </div>
                <div class="p-2 rounded-lg bg-surface-container dark:bg-slate-800">
                  <div class="font-bold text-on-surface dark:text-white">
                    ₹{droneCost().toLocaleString("en-IN")}
                  </div>
                  <div class="text-[10px] text-slate-500">Drone Spray (15%)</div>
                </div>
                <div class="p-2 rounded-lg bg-surface-container dark:bg-slate-800 col-span-2 sm:col-span-1">
                  <div class="font-bold text-on-surface dark:text-white">
                    ₹{contingencyCost().toLocaleString("en-IN")}
                  </div>
                  <div class="text-[10px] text-slate-500">Contingency (10%)</div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 4: Risk Tolerance */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div>
              <h3 class="text-base font-bold text-on-surface dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600 text-lg">shield</span>
                <span>4. Risk Tolerance & Market Hedging</span>
              </h3>
              <p class="text-xs text-slate-500 mt-0.5">
                Balances assured MSP staple crops against volatile, high-return cash crops.
              </p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                {
                  id: "conservative",
                  title: "Conservative (80% MSP)",
                  desc: "Guaranteed procurement via FCI/Nafed. Lowest downside risk."
                },
                {
                  id: "balanced",
                  title: "Balanced 60/40",
                  desc: "Optimal split of staple pulses and cash vegetables for peak APMC gain."
                },
                {
                  id: "aggressive",
                  title: "Aggressive Exotics",
                  desc: "High-value horticulture and forward contract export varieties."
                }
              ].map((r) => (
                <div
                  onClick={() => setRiskTolerance(r.id)}
                  class={`p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                    riskTolerance() === r.id
                      ? "border-emerald-600 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-xs"
                      : "border-outline-variant/30 bg-surface-container-low dark:bg-slate-800/40"
                  }`}
                >
                  <div class="font-bold text-xs text-on-surface dark:text-white mb-1">
                    {r.title}
                  </div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                    {r.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 5: Crop Preferences & Exclusions */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-base font-bold text-on-surface dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-emerald-600 text-lg">spa</span>
                  <span>5. Crop Preferences & Exclusions</span>
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                  Click any crop tag to toggle between included (green) or excluded (red).
                </p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2">
              <For each={crops()}>
                {(crop, index) => (
                  <div
                    onClick={() => toggleCropType(index())}
                    class={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer border transition-transform active:scale-95 ${
                      crop.type === "include"
                        ? "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800"
                        : "bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-300 border-red-300 dark:border-red-800 line-through"
                    }`}
                  >
                    <span class="material-symbols-outlined text-xs">
                      {crop.type === "include" ? "check" : "block"}
                    </span>
                    <span>{crop.name}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeCrop(index());
                      }}
                      class="ml-1 hover:text-slate-900 dark:hover:text-white text-xs font-bold"
                    >
                      ×
                    </button>
                  </div>
                )}
              </For>
            </div>
          </div>
        </div>

        {/* Right 4-Columns: Real-Time Simulation & Execution */}
        <div class="lg:col-span-4 space-y-6">
          {/* Gemini 2.0 Pre-flight Simulation */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border-2 border-emerald-600/60 rounded-2xl p-6 shadow-md space-y-5 sticky top-20">
            <div class="flex items-center justify-between pb-3 border-b border-outline-variant/20">
              <div class="flex items-center gap-2">
                <span class="relative flex h-3 w-3">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <h3 class="font-bold text-sm text-on-surface dark:text-white">
                  Gemini 2.0 Live Simulation
                </h3>
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-300">
                96% Confidence
              </span>
            </div>

            {/* Projected Metrics */}
            <div class="space-y-3">
              <div class="p-3.5 rounded-xl bg-surface-container-low dark:bg-slate-800/80 border border-outline-variant/20">
                <span class="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                  Projected Gross Revenue
                </span>
                <div class="text-xl font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                  ₹{projectedGrossMin().toLocaleString("en-IN")} – ₹{projectedGrossMax().toLocaleString("en-IN")}
                </div>
                <div class="text-[10px] text-emerald-700 dark:text-emerald-400 mt-0.5">
                  +22% vs. 2023-24 single-crop monoculture
                </div>
              </div>

              <div class="grid grid-cols-2 gap-2 text-center text-xs">
                <div class="p-3 rounded-xl bg-surface-container-low dark:bg-slate-800/80 border border-outline-variant/20">
                  <div class="text-lg font-bold text-amber-600 font-mono">
                    ₹{projectedNet().toLocaleString("en-IN")}
                  </div>
                  <div class="text-[10px] text-slate-500">Estimated Net</div>
                </div>

                <div class="p-3 rounded-xl bg-surface-container-low dark:bg-slate-800/80 border border-outline-variant/20">
                  <div class="text-lg font-bold text-blue-600 font-mono">
                    +28%
                  </div>
                  <div class="text-[10px] text-slate-500">Water Saved</div>
                </div>
              </div>
            </div>

            {/* Quota Cost */}
            <div class="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/40 text-xs flex items-center gap-2 text-amber-900 dark:text-amber-300">
              <span class="material-symbols-outlined text-base">bolt</span>
              <span>
                Consumes <strong>1 Strategic Planning Credit</strong> (4/10 remaining).
              </span>
            </div>

            {/* Primary Action Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating()}
              class="w-full py-4 px-6 rounded-xl bg-primary-container hover:bg-emerald-800 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <span class="material-symbols-outlined text-lg">auto_awesome</span>
              <span>
                {isGenerating()
                  ? "Calibrating Gemini 2.0 Model..."
                  : "Generate 365-Day Strategy"}
              </span>
            </button>

            {/* Secondary Actions */}
            <div class="grid grid-cols-2 gap-2 pt-1">
              <button
                onClick={() => alert("Parameters saved to local draft!")}
                class="py-2 px-3 rounded-xl border border-outline-variant/40 hover:bg-surface-container text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors text-center"
              >
                Save Draft
              </button>
              <A
                href="/crops/annual-strategy/1"
                class="py-2 px-3 rounded-xl border border-outline-variant/40 hover:bg-surface-container text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors text-center"
              >
                View Past Plan
              </A>
            </div>

            {/* KVK Support */}
            <div class="pt-3 border-t border-outline-variant/20 text-center">
              <div class="text-[11px] text-slate-500 mb-2">
                Need guidance before generating?
              </div>
              <a
                href="tel:18001801551"
                class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:underline"
              >
                <span class="material-symbols-outlined text-sm">call</span>
                <span>KVK Helpline: 1800-180-1551</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
