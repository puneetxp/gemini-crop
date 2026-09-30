import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface Bovine {
  tagId: string;
  name: string;
  breed: string;
  category: "Cow" | "Buffalo" | "Bull" | "Calf";
  lactation: string;
  dailyYield: string;
  fatContent?: string;
  status: string;
  statusBadgeColor: string;
  nextVaccine: string;
  nextVaccineDays: number;
  inaphVerified: boolean;
}

interface VaccineEvent {
  id: string;
  disease: string;
  protocol: string;
  dueDate: string;
  daysRemaining: number;
  targetCount: number;
  dispensary: string;
  status: "due" | "completed" | "scheduled";
  verifiedBy?: string;
}

export const LivestockHub: Component = () => {
  const [activeTab, setActiveTab] = createSignal<"registry" | "vaccines" | "reproduction">("registry");
  const [searchFilter, setSearchFilter] = createSignal<string>("");

  const herd: Bovine[] = [
    {
      tagId: "1002-9481-0293",
      name: "Ganga",
      breed: "Pure Gir Cow",
      category: "Cow",
      lactation: "4th Lactation",
      dailyYield: "18.2 L/day",
      fatContent: "4.4% Fat",
      status: "Healthy • Pregnant (Month 4)",
      statusBadgeColor: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
      nextVaccine: "Brucellosis Booster",
      nextVaccineDays: 14,
      inaphVerified: true
    },
    {
      tagId: "1002-8812-4019",
      name: "Lakshmi",
      breed: "Murrah Buffalo",
      category: "Buffalo",
      lactation: "2nd Lactation",
      dailyYield: "14.5 L/day",
      fatContent: "7.2% Fat (High Fat)",
      status: "In Milk • Optimal",
      statusBadgeColor: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
      nextVaccine: "FMD Booster",
      nextVaccineDays: 8,
      inaphVerified: true
    },
    {
      tagId: "1002-7721-9941",
      name: "Gauri",
      breed: "Sahiwal Cow",
      category: "Cow",
      lactation: "1st Lactation Heifer",
      dailyYield: "12.0 L/day",
      fatContent: "4.1% Fat",
      status: "RFID Collar Synced",
      statusBadgeColor: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
      nextVaccine: "FMD Booster",
      nextVaccineDays: 8,
      inaphVerified: true
    },
    {
      tagId: "1002-6632-1102",
      name: "Nandi",
      breed: "Gir Breeding Bull",
      category: "Bull",
      lactation: "Sire Stud",
      dailyYield: "Pedigree Verified",
      status: "Active Stud • Grade A+",
      statusBadgeColor: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
      nextVaccine: "HS Annual",
      nextVaccineDays: 45,
      inaphVerified: true
    }
  ];

  const vaccines: VaccineEvent[] = [
    {
      id: "v-1",
      disease: "Foot & Mouth Disease (FMD) Booster",
      protocol: "ICAR-IVRI National Prophylaxis Cycle",
      dueDate: "06 Oct 2026",
      daysRemaining: 8,
      targetCount: 14,
      dispensary: "Niphad Veterinary Poly-clinic Drive",
      status: "due"
    },
    {
      id: "v-2",
      disease: "Hemorrhagic Septicemia (HS) Annual",
      protocol: "Bivalent Alum Precipitated Vaccine",
      dueDate: "22 Aug 2026",
      daysRemaining: -38,
      targetCount: 18,
      dispensary: "Dr. Sanjay Kulkarni (Cert #HS-2024-91)",
      status: "completed",
      verifiedBy: "Dr. Sanjay Kulkarni (MVSc)"
    },
    {
      id: "v-3",
      disease: "Black Quarter (BQ) Pre-Winter",
      protocol: "Clostridium chauvoei formalised culture",
      dueDate: "15 Nov 2026",
      daysRemaining: 47,
      targetCount: 15,
      dispensary: "KVK Niphad Mobile Animal Clinic",
      status: "scheduled"
    }
  ];

  const filteredHerd = () => {
    const q = searchFilter().toLowerCase().trim();
    if (!q) return herd;
    return herd.filter(
      (b) =>
        b.name.toLowerCase().includes(q) ||
        b.tagId.toLowerCase().includes(q) ||
        b.breed.toLowerCase().includes(q)
    );
  };

  return (
    <div class="space-y-6 pb-20">
      {/* Top Banner & Context Header */}
      <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-6 shadow-sm">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
              <span class="material-symbols-outlined text-sm">pets</span>
              <span>PASHU & LIVESTOCK HEALTH ENGINE</span>
              <span>•</span>
              <span>INAPH SYNCHRONIZED</span>
            </div>
            <h1 class="text-2xl lg:text-3xl font-bold text-on-surface dark:text-white">
              Livestock Management & Vaccination Hub
            </h1>
            <p class="text-sm text-on-surface-variant dark:text-slate-400 mt-1 max-w-2xl">
              Track dairy bovine health, milk lactation yields, automated veterinary vaccination
              compliance, and Bharat Pashudhan registry records.
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <A
              href="/livestock/diet-plan"
              class="px-4 py-2.5 rounded-xl border border-outline-variant/40 bg-surface-container-low dark:bg-slate-800 text-on-surface dark:text-slate-200 text-xs font-bold hover:bg-surface-container transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span class="material-symbols-outlined text-sm">nutrition</span>
              <span>Ration Calculator</span>
            </A>
            <A
              href="/livestock/doctors"
              class="px-4 py-2.5 rounded-xl border border-outline-variant/40 bg-surface-container-low dark:bg-slate-800 text-on-surface dark:text-slate-200 text-xs font-bold hover:bg-surface-container transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span class="material-symbols-outlined text-sm">medical_services</span>
              <span>Consult Vet</span>
            </A>
            <button
              onClick={() => alert("RFID Scanner ready: Scan Pashu Aadhaar ear tag.")}
              class="px-4 py-2.5 rounded-xl bg-primary-container hover:bg-emerald-800 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-transform active:scale-95"
            >
              <span class="material-symbols-outlined text-sm">add_circle</span>
              <span>+ Tag Cattle</span>
            </button>
          </div>
        </div>

        {/* 4 Executive KPI Cards */}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-6">
          <div class="p-4 rounded-xl bg-surface-container-low dark:bg-slate-800 border border-outline-variant/30 space-y-1">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Total Herd
            </span>
            <div class="text-2xl font-bold text-on-surface dark:text-white">18 Bovines</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">
              12 Milking • 3 Dry • 3 Calves
            </div>
          </div>

          <div class="p-4 rounded-xl bg-surface-container-low dark:bg-slate-800 border border-outline-variant/30 space-y-1">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Today's Milk Harvest
            </span>
            <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
              142.5 L
            </div>
            <div class="text-[11px] text-slate-500">
              Fat 4.2% • SNF 8.7 (₹5,415 / day)
            </div>
          </div>

          <div class="p-4 rounded-xl bg-surface-container-low dark:bg-slate-800 border border-outline-variant/30 space-y-1">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Vaccination Compliance
            </span>
            <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">100%</div>
            <div class="text-[11px] text-amber-600 dark:text-amber-400 font-semibold">
              FMD Booster in 8 days
            </div>
          </div>

          <div class="p-4 rounded-xl bg-surface-container-low dark:bg-slate-800 border border-outline-variant/30 space-y-1">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Lactation Phase
            </span>
            <div class="text-2xl font-bold text-on-surface dark:text-white">Phase 2 Peak</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400">
              Avg 14.8 L/cow (+1.2L trend)
            </div>
          </div>
        </div>
      </div>

      {/* Main 12-Column Grid */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 8-Columns: Roster & Vaccine Schedule */}
        <div class="lg:col-span-8 space-y-6">
          {/* Tabs bar */}
          <div class="flex items-center justify-between border-b border-outline-variant/30 pb-2">
            <div class="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("registry")}
                class={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab() === "registry"
                    ? "bg-primary-container text-white shadow-xs"
                    : "bg-surface-container-low text-slate-600 dark:text-slate-300 hover:bg-surface-container"
                }`}
              >
                Herd Roster (18)
              </button>
              <button
                onClick={() => setActiveTab("vaccines")}
                class={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab() === "vaccines"
                    ? "bg-primary-container text-white shadow-xs"
                    : "bg-surface-container-low text-slate-600 dark:text-slate-300 hover:bg-surface-container"
                }`}
              >
                Vaccine Schedule
              </button>
            </div>

            <div class="relative w-48 sm:w-64">
              <span class="material-symbols-outlined absolute left-2.5 top-2 text-slate-400 text-sm">
                search
              </span>
              <input
                type="text"
                placeholder="Search tag, name, breed..."
                value={searchFilter()}
                onInput={(e) => setSearchFilter(e.currentTarget.value)}
                class="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl bg-surface-container-low dark:bg-slate-800 border border-outline-variant/30 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Tab 1: Active Herd Registry */}
          {activeTab() === "registry" && (
            <div class="space-y-3">
              <For each={filteredHerd()}>
                {(bovine) => (
                  <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-4 lg:p-5 shadow-sm hover:border-emerald-500/40 transition-all">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div class="flex items-start gap-3">
                        <div class="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 flex items-center justify-center shrink-0 border border-emerald-200 dark:border-emerald-800/40">
                          <span class="material-symbols-outlined text-2xl">pets</span>
                        </div>
                        <div>
                          <div class="flex items-center gap-2">
                            <h3 class="font-bold text-base text-on-surface dark:text-white">
                              {bovine.name}
                            </h3>
                            <span class={`text-[10px] font-bold px-2 py-0.5 rounded-full ${bovine.statusBadgeColor}`}>
                              {bovine.status}
                            </span>
                          </div>
                          <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex flex-wrap items-center gap-2">
                            <span>Tag #{bovine.tagId}</span>
                            <span>•</span>
                            <span class="font-semibold text-slate-700 dark:text-slate-300">{bovine.breed}</span>
                            <span>•</span>
                            <span>{bovine.lactation}</span>
                          </div>
                        </div>
                      </div>

                      <div class="flex items-center gap-4 text-right">
                        <div>
                          <div class="text-base font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                            {bovine.dailyYield}
                          </div>
                          {bovine.fatContent && (
                            <div class="text-[10px] text-slate-500">{bovine.fatContent}</div>
                          )}
                        </div>

                        <button
                          onClick={() => alert(`Details for ${bovine.name} (Tag #${bovine.tagId}): Temperature 38.5°C, Rumination 440 mins/day.`)}
                          class="p-2 rounded-xl bg-surface-container-low hover:bg-surface-container text-slate-600 dark:text-slate-300 transition-colors"
                          title="View IoT Telemetry"
                        >
                          <span class="material-symbols-outlined text-base">sensors</span>
                        </button>
                      </div>
                    </div>

                    <div class="mt-3 pt-3 border-t border-outline-variant/20 flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div class="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                        <span class="material-symbols-outlined text-sm text-emerald-600">vaccines</span>
                        <span>
                          Next Vaccine: <strong>{bovine.nextVaccine}</strong> (in {bovine.nextVaccineDays} days)
                        </span>
                      </div>

                      <div class="flex items-center gap-2">
                        {bovine.inaphVerified && (
                          <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                            <span class="material-symbols-outlined text-xs">verified</span>
                            <span>INAPH Verified</span>
                          </span>
                        )}
                        <A
                          href="/livestock/doctors"
                          class="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                        >
                          Log Checkup →
                        </A>
                      </div>
                    </div>
                  </div>
                )}
              </For>
            </div>
          )}

          {/* Tab 2: Vaccination Schedule */}
          {activeTab() === "vaccines" && (
            <div class="space-y-4">
              <For each={vaccines}>
                {(vac) => (
                  <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-3">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div class="flex items-center gap-3">
                        <div class={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
                          vac.status === "due"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                            : vac.status === "completed"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                        }`}>
                          <span class="material-symbols-outlined">vaccines</span>
                        </div>
                        <div>
                          <h4 class="font-bold text-sm text-on-surface dark:text-white">
                            {vac.disease}
                          </h4>
                          <span class="text-xs text-slate-500">{vac.protocol}</span>
                        </div>
                      </div>

                      <span class={`px-2.5 py-1 rounded-full text-xs font-bold self-start sm:self-auto ${
                        vac.status === "due"
                          ? "bg-amber-100 text-amber-900 dark:bg-amber-900/60 dark:text-amber-200"
                          : vac.status === "completed"
                          ? "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/60 dark:text-emerald-200"
                          : "bg-blue-100 text-blue-900 dark:bg-blue-900/60 dark:text-blue-200"
                      }`}>
                        {vac.status === "due"
                          ? `Due in ${vac.daysRemaining} days`
                          : vac.status === "completed"
                          ? "✓ Administered & Certified"
                          : `Scheduled for ${vac.dueDate}`}
                      </span>
                    </div>

                    <div class="p-3 rounded-xl bg-surface-container-low dark:bg-slate-800/60 text-xs flex flex-wrap items-center justify-between gap-2">
                      <span class="text-slate-600 dark:text-slate-400">
                        Dispensary: <strong class="text-on-surface dark:text-white">{vac.dispensary}</strong>
                      </span>
                      <span class="text-slate-600 dark:text-slate-400">
                        Target Herd: <strong>{vac.targetCount} Bovines</strong>
                      </span>
                    </div>
                  </div>
                )}
              </For>
            </div>
          )}
        </div>

        {/* Right 4-Columns: Telemetry & Polyclinic Support */}
        <div class="lg:col-span-4 space-y-6">
          {/* INAPH Sync Card */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center gap-2.5 pb-2 border-b border-outline-variant/20">
              <span class="material-symbols-outlined text-emerald-600 text-lg">shield</span>
              <h4 class="font-bold text-xs text-on-surface dark:text-white uppercase tracking-wider">
                National Livestock Registry
              </h4>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">
              Synchronized with <strong>Bharat Pashudhan & INAPH</strong> under the National Animal
              Disease Control Programme (NADCP). 100% of adult animals carry active RFID ear tags.
            </p>
            <div class="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40 text-[11px] text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">qr_code</span>
              <span>PMFBY Livestock Insurance Active (Policy #MH-NSK-2024-81)</span>
            </div>
          </div>

          {/* Smart Bulk Milk Chiller IoT Feed */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-outline-variant/20">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-600 text-lg">ac_unit</span>
                <h4 class="font-bold text-xs text-on-surface dark:text-white uppercase tracking-wider">
                  Bulk Milk Chiller IoT
                </h4>
              </div>
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            </div>

            <div class="grid grid-cols-2 gap-2 text-center text-xs">
              <div class="p-2.5 rounded-xl bg-surface-container-low dark:bg-slate-800">
                <span class="text-[10px] text-slate-500 block">Temperature</span>
                <span class="text-lg font-bold text-blue-600 font-mono">3.8°C</span>
                <span class="text-[9px] text-emerald-600 block">Target &lt;4.0°C</span>
              </div>
              <div class="p-2.5 rounded-xl bg-surface-container-low dark:bg-slate-800">
                <span class="text-[10px] text-slate-500 block">MBRT Test</span>
                <span class="text-lg font-bold text-emerald-600 font-mono">Grade A</span>
                <span class="text-[9px] text-slate-500 block">&gt;5 Hours Active</span>
              </div>
            </div>
          </div>

          {/* Daily Fodder Ration */}
          <div class="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant/30 rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-outline-variant/20">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600 text-lg">grass</span>
                <h4 class="font-bold text-xs text-on-surface dark:text-white uppercase tracking-wider">
                  Daily Fodder Balance
                </h4>
              </div>
              <A href="/livestock/diet-plan" class="text-[11px] font-bold text-emerald-600 hover:underline">
                Rebalance
              </A>
            </div>

            <div class="space-y-2 text-xs">
              <div>
                <div class="flex justify-between text-slate-600 dark:text-slate-300 text-[11px] mb-1">
                  <span>Maize Silage</span>
                  <span class="font-semibold">220 kg (88%)</span>
                </div>
                <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                  <div class="bg-emerald-600 h-full rounded-full" style="width: 88%"></div>
                </div>
              </div>

              <div>
                <div class="flex justify-between text-slate-600 dark:text-slate-300 text-[11px] mb-1">
                  <span>Napier Hybrid Grass</span>
                  <span class="font-semibold">180 kg (100%)</span>
                </div>
                <div class="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden">
                  <div class="bg-emerald-600 h-full rounded-full" style="width: 100%"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Tele-Veterinary Hotline */}
          <div class="bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 rounded-2xl p-5 space-y-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-xl">medical_services</span>
              </div>
              <div>
                <h4 class="font-bold text-xs text-emerald-950 dark:text-emerald-200">
                  Dr. Sanjay Deshmukh
                </h4>
                <p class="text-[11px] text-emerald-800 dark:text-emerald-400">
                  M.V.Sc (Surgery) • In-charge KVK Niphad Polyclinic
                </p>
              </div>
            </div>

            <a
              href="tel:18001801551"
              class="w-full bg-white dark:bg-slate-800 hover:bg-emerald-50 text-emerald-800 dark:text-emerald-300 text-xs font-bold py-2.5 px-4 rounded-xl border border-emerald-300 dark:border-emerald-700/50 flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              <span class="material-symbols-outlined text-sm">call</span>
              <span>Direct Helpline: 1800-180-1551</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
