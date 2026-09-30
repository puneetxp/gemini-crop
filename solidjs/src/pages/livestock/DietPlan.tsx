import { Component, createSignal, createMemo, For } from "solid-js";
import { A } from "@solidjs/router";

interface FeedIngredient {
  id: string;
  name: string;
  category: "green" | "dry" | "concentrate" | "supplement";
  dmPercent: number; // Dry Matter %
  cpPercent: number; // Crude Protein % (on DM basis)
  tdnPercent: number; // Total Digestible Nutrients % (on DM basis)
  pricePerKg: number; // ₹ / kg
  defaultAmount: number; // kg
  unit: string;
}

export const DietPlan: Component = () => {
  // Selected Animal Profile
  const [animalType, setAnimalType] = createSignal<string>("murrah");
  const [stage, setStage] = createSignal<string>("peak");
  const [bodyWeight, setBodyWeight] = createSignal<number>(550);
  const [milkYield, setMilkYield] = createSignal<number>(14);
  const [milkFat, setMilkFat] = createSignal<number>(7.2);
  const [milkPricePerLiter, setMilkPricePerLiter] = createSignal<number>(58);

  // Ingredient Inventory & Daily Feeding Amounts (kg)
  const [ingredients, setIngredients] = createSignal<FeedIngredient[]>([
    {
      id: "napier",
      name: "Hybrid Napier Grass (CO-4)",
      category: "green",
      dmPercent: 20,
      cpPercent: 9.5,
      tdnPercent: 55,
      pricePerKg: 1.8,
      defaultAmount: 22,
      unit: "kg"
    },
    {
      id: "lucerne",
      name: "Lucerne / Berseem (Legume)",
      category: "green",
      dmPercent: 22,
      cpPercent: 18.0,
      tdnPercent: 62,
      pricePerKg: 3.2,
      defaultAmount: 8,
      unit: "kg"
    },
    {
      id: "wheat_straw",
      name: "Wheat Straw (Bhusa)",
      category: "dry",
      dmPercent: 90,
      cpPercent: 3.5,
      tdnPercent: 42,
      pricePerKg: 6.5,
      defaultAmount: 5,
      unit: "kg"
    },
    {
      id: "cottonseed_cake",
      name: "Cottonseed Cake (Binola Khal)",
      category: "concentrate",
      dmPercent: 90,
      cpPercent: 24.0,
      tdnPercent: 74,
      pricePerKg: 34,
      defaultAmount: 3.5,
      unit: "kg"
    },
    {
      id: "broken_maize",
      name: "Crushed Yellow Maize Grain",
      category: "concentrate",
      dmPercent: 88,
      cpPercent: 9.0,
      tdnPercent: 82,
      pricePerKg: 24,
      defaultAmount: 2.5,
      unit: "kg"
    },
    {
      id: "mineral_mix",
      name: "Chelated Mineral Mixture & Salt",
      category: "supplement",
      dmPercent: 98,
      cpPercent: 0,
      tdnPercent: 10,
      pricePerKg: 120,
      defaultAmount: 0.15,
      unit: "kg"
    },
    {
      id: "bypass_fat",
      name: "Rumen Bypass Fat (Calcium Soap)",
      category: "supplement",
      dmPercent: 99,
      cpPercent: 0,
      tdnPercent: 160,
      pricePerKg: 240,
      defaultAmount: 0.15,
      unit: "kg"
    }
  ]);

  const [savedNotification, setSavedNotification] = createSignal(false);

  // Update ingredient amount
  const handleAmountChange = (id: string, amount: number) => {
    setIngredients(prev =>
      prev.map(item => (item.id === id ? { ...item, defaultAmount: Math.max(0, amount) } : item))
    );
  };

  // Nutritional Target Models (ICAR / NDRI guidelines)
  const targetDM = createMemo(() => {
    // DM intake target: ~3.0% of body weight + 0.35kg per kg milk
    const base = (bodyWeight() * 2.8) / 100;
    const milkFactor = milkYield() * 0.35;
    return +(base + milkFactor).toFixed(1);
  });

  const targetCP = createMemo(() => {
    // 13% for maintenance, up to 16% for high yield
    return milkYield() > 15 ? 16.0 : milkYield() > 10 ? 14.5 : 13.0;
  });

  const targetTDN = createMemo(() => {
    // 60-68% TDN on dry matter
    return milkYield() > 15 ? 68.0 : milkYield() > 10 ? 64.0 : 58.0;
  });

  // Current Formulation Totals
  const actualDM = createMemo(() => {
    const total = ingredients().reduce((sum, item) => sum + (item.defaultAmount * item.dmPercent) / 100, 0);
    return +total.toFixed(2);
  });

  const actualCP = createMemo(() => {
    const totalDMI = actualDM();
    if (totalDMI === 0) return 0;
    const totalCPWeight = ingredients().reduce((sum, item) => {
      const dm = (item.defaultAmount * item.dmPercent) / 100;
      return sum + (dm * item.cpPercent) / 100;
    }, 0);
    return +((totalCPWeight / totalDMI) * 100).toFixed(1);
  });

  const actualTDN = createMemo(() => {
    const totalDMI = actualDM();
    if (totalDMI === 0) return 0;
    const totalTDNWeight = ingredients().reduce((sum, item) => {
      const dm = (item.defaultAmount * item.dmPercent) / 100;
      return sum + (dm * item.tdnPercent) / 100;
    }, 0);
    return +((totalTDNWeight / totalDMI) * 100).toFixed(1);
  });

  // Financial Economics
  const dailyFeedCost = createMemo(() => {
    const cost = ingredients().reduce((sum, item) => sum + item.defaultAmount * item.pricePerKg, 0);
    return +cost.toFixed(1);
  });

  const dailyMilkRevenue = createMemo(() => {
    return +(milkYield() * milkPricePerLiter()).toFixed(1);
  });

  const dailyNetProfit = createMemo(() => {
    return +(dailyMilkRevenue() - dailyFeedCost()).toFixed(1);
  });

  const feedCostPerLiter = createMemo(() => {
    if (milkYield() === 0) return 0;
    return +(dailyFeedCost() / milkYield()).toFixed(2);
  });

  const handleSaveRation = () => {
    setSavedNotification(true);
    setTimeout(() => setSavedNotification(false), 3500);
  };

  return (
    <div class="space-y-6">
      {/* Header & Breadcrumb */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
            <A href="/livestock" class="hover:underline">Pashu Hub</A>
            <span>/</span>
            <A href="/livestock/hub" class="hover:underline">Herd Registry</A>
            <span>/</span>
            <span class="text-brand-600 dark:text-brand-400 font-medium">Diet &amp; TMR Balancer</span>
          </div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <span class="material-symbols-outlined text-brand-600 text-3xl">nutrition</span>
            Pashu Diet &amp; TMR Balancer
          </h1>
          <p class="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
            ICAR-NDRI scientific formulation engine for optimum milk yield, butterfat %, and feed cost efficiency.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <A
            href="/livestock/doctors"
            class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-base">medical_services</span>
            Consult Nutritionist
          </A>
          <button
            onClick={handleSaveRation}
            class="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-all flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-base">save</span>
            Save Formulation
          </button>
        </div>
      </div>

      {/* Save Notification Toast */}
      {savedNotification() && (
        <div class="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-xs font-medium flex items-center justify-between shadow-sm transition-all">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-base text-emerald-600">check_circle</span>
            <span>Ration formulation saved successfully to Animal Herd Record #1002-8812-4019!</span>
          </div>
          <span class="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold uppercase tracking-wider">Active</span>
        </div>
      )}

      {/* ANIMAL PROFILE CONFIGURATION BAR */}
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-4 flex items-center gap-1.5">
          <span class="material-symbols-outlined text-base text-brand-500">tune</span>
          1. Animal Profile &amp; Production Target
        </h2>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Breed &amp; Species</label>
            <select
              value={animalType()}
              onChange={e => setAnimalType(e.currentTarget.value)}
              class="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="murrah">Murrah Buffalo (High Fat)</option>
              <option value="gir">Gir Cow (A2 Indigenous)</option>
              <option value="hf">HF Crossbred (High Yield)</option>
              <option value="sahiwal">Sahiwal Cow</option>
              <option value="jersey">Jersey Crossbred</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Lactation Stage</label>
            <select
              value={stage()}
              onChange={e => setStage(e.currentTarget.value)}
              class="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="peak">Early / Peak Lactation (1-100 Days)</option>
              <option value="mid">Mid Lactation (101-200 Days)</option>
              <option value="late">Late Lactation (201+ Days)</option>
              <option value="dry">Dry &amp; Advanced Pregnancy</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Live Body Weight (kg)</label>
            <input
              type="number"
              min="250"
              max="900"
              step="10"
              value={bodyWeight()}
              onInput={e => setBodyWeight(+e.currentTarget.value || 500)}
              class="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Target Yield (L/day)</label>
            <input
              type="number"
              min="0"
              max="45"
              step="0.5"
              value={milkYield()}
              onInput={e => setMilkYield(+e.currentTarget.value || 0)}
              class="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Expected Fat %</label>
            <input
              type="number"
              min="3.0"
              max="11.0"
              step="0.1"
              value={milkFat()}
              onInput={e => setMilkFat(+e.currentTarget.value || 6.5)}
              class="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Milk Price (₹/L)</label>
            <input
              type="number"
              min="30"
              max="120"
              step="1"
              value={milkPricePerLiter()}
              onInput={e => setMilkPricePerLiter(+e.currentTarget.value || 55)}
              class="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>
      </div>

      {/* METRIC SCORECARDS: NUTRITIONAL BALANCE & FINANCIAL MARGINS */}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Dry Matter Target vs Actual */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-semibold uppercase tracking-wider">Dry Matter Intake (DMI)</span>
              <span class="material-symbols-outlined text-base text-brand-500">scale</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-2xl font-black text-slate-900 dark:text-white">{actualDM()}</span>
              <span class="text-xs text-slate-500">/ {targetDM()} kg target</span>
            </div>
          </div>
          <div class="mt-3">
            <div class="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                class={`h-full rounded-full transition-all ${
                  Math.abs(actualDM() - targetDM()) <= 1.0 ? "bg-emerald-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.min(100, (actualDM() / targetDM()) * 100)}%` }}
              />
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>{Math.round((actualDM() / targetDM()) * 100)}% Fulfilled</span>
              <span>{actualDM() >= targetDM() ? "Satisfied" : "Deficit"}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Crude Protein Target vs Actual */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-semibold uppercase tracking-wider">Crude Protein (CP)</span>
              <span class="material-symbols-outlined text-base text-amber-500">fitness_center</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-2xl font-black text-slate-900 dark:text-white">{actualCP()}%</span>
              <span class="text-xs text-slate-500">/ {targetCP()}% target</span>
            </div>
          </div>
          <div class="mt-3">
            <div class="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                class={`h-full rounded-full transition-all ${
                  actualCP() >= targetCP() ? "bg-emerald-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.min(100, (actualCP() / targetCP()) * 100)}%` }}
              />
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>{actualCP() >= targetCP() ? "Optimal Muscle & Milk Protein" : "Add Legume / Cake"}</span>
              <span class="font-semibold">{actualCP() >= targetCP() ? "✓" : "!"}</span>
            </div>
          </div>
        </div>

        {/* Card 3: TDN (Energy) */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-semibold uppercase tracking-wider">Energy (TDN %)</span>
              <span class="material-symbols-outlined text-base text-blue-500">bolt</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-2xl font-black text-slate-900 dark:text-white">{actualTDN()}%</span>
              <span class="text-xs text-slate-500">/ {targetTDN()}% target</span>
            </div>
          </div>
          <div class="mt-3">
            <div class="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                class={`h-full rounded-full transition-all ${
                  actualTDN() >= targetTDN() ? "bg-emerald-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.min(100, (actualTDN() / targetTDN()) * 100)}%` }}
              />
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>Rumen Microbial Health</span>
              <span>{actualTDN() >= targetTDN() ? "Sufficient" : "Low Energy"}</span>
            </div>
          </div>
        </div>

        {/* Card 4: Daily Net Profit & Cost/Liter */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-semibold uppercase tracking-wider">Daily Net Margin</span>
              <span class="material-symbols-outlined text-base text-emerald-500">payments</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-2xl font-black text-emerald-600 dark:text-emerald-400">₹{dailyNetProfit()}</span>
              <span class="text-xs text-slate-500">/ animal / day</span>
            </div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs border-t border-slate-100 dark:border-slate-800 pt-2">
            <span class="text-slate-500">Cost/L: ₹{feedCostPerLiter()}</span>
            <span class="text-slate-500">Total Feed: ₹{dailyFeedCost()}/d</span>
          </div>
        </div>
      </div>

      {/* TMR INGREDIENT FORMULATION SLIDERS & BREAKDOWN */}
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-brand-500">skillet</span>
            2. Total Mixed Ration (TMR) Feed Ingredients Formulation
          </h2>
          <span class="text-xs text-slate-500">
            Total Fresh Weight: {ingredients().reduce((sum, item) => sum + item.defaultAmount, 0).toFixed(1)} kg / day
          </span>
        </div>

        <div class="space-y-4">
          <For each={ingredients()}>
            {item => {
              const itemDM = ((item.defaultAmount * item.dmPercent) / 100).toFixed(2);
              const itemCost = (item.defaultAmount * item.pricePerKg).toFixed(1);

              return (
                <div class="p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div class="flex items-center gap-2">
                      <span
                        class={`w-2.5 h-2.5 rounded-full ${
                          item.category === "green"
                            ? "bg-emerald-500"
                            : item.category === "dry"
                            ? "bg-amber-500"
                            : item.category === "concentrate"
                            ? "bg-blue-500"
                            : "bg-purple-500"
                        }`}
                      />
                      <span class="text-xs font-bold text-slate-800 dark:text-slate-100">{item.name}</span>
                      <span class="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        {item.category}
                      </span>
                    </div>

                    <div class="flex items-center gap-4 text-xs font-mono">
                      <span class="text-slate-500">DM: {itemDM} kg</span>
                      <span class="text-slate-500">CP: {item.cpPercent}%</span>
                      <span class="font-bold text-slate-800 dark:text-slate-200">₹{itemCost}/d</span>
                    </div>
                  </div>

                  <div class="flex items-center gap-4">
                    <input
                      type="range"
                      min="0"
                      max={item.category === "green" ? 40 : item.category === "supplement" ? 1 : 12}
                      step={item.category === "supplement" ? 0.05 : 0.5}
                      value={item.defaultAmount}
                      onInput={e => handleAmountChange(item.id, +e.currentTarget.value)}
                      class="w-full accent-brand-600 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
                    />
                    <div class="flex items-center gap-1 min-w-[72px] justify-end">
                      <input
                        type="number"
                        min="0"
                        step={item.category === "supplement" ? 0.05 : 0.5}
                        value={item.defaultAmount}
                        onInput={e => handleAmountChange(item.id, +e.currentTarget.value || 0)}
                        class="w-16 text-center text-xs font-bold py-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white"
                      />
                      <span class="text-xs text-slate-500">{item.unit}</span>
                    </div>
                  </div>
                </div>
              );
            }}
          </For>
        </div>
      </div>

      {/* RATION FEEDING ADVISORY & QUICK LINKS */}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60">
          <div class="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-bold text-xs mb-1.5">
            <span class="material-symbols-outlined text-base">warning</span>
            Acidosis Prevention Tip
          </div>
          <p class="text-xs text-amber-700 dark:text-amber-400 leading-relaxed">
            Ensure adequate wheat straw (minimum 4-5 kg/day) to stimulate rumination and cud chewing. Do not exceed concentrate proportion above 60% of total dry matter.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60">
          <div class="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-xs mb-1.5">
            <span class="material-symbols-outlined text-base">verified</span>
            Bypass Fat Advantage
          </div>
          <p class="text-xs text-emerald-700 dark:text-emerald-400 leading-relaxed">
            Adding 150g of Calcium soap bypass fat increases milk fat percentage by 0.3 - 0.5% without disrupting rumen fiber fermentation bacteria.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-bold text-xs mb-1.5">
              <span class="material-symbols-outlined text-base text-brand-500">shopping_bag</span>
              Procure Concentrates
            </div>
            <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Order bulk binola khal, mineral mixtures, and silage bales directly from verified sellers.
            </p>
          </div>
          <A
            href="/marketplace"
            class="mt-3 inline-flex items-center justify-between text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline"
          >
            <span>Browse Feed Listings</span>
            <span class="material-symbols-outlined text-sm">arrow_forward</span>
          </A>
        </div>
      </div>
    </div>
  );
};
