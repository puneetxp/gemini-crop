import { Component, createSignal, createMemo, For } from "solid-js";

interface AuditLogItem {
  id: string;
  timestamp: string;
  model: string;
  category: "vision" | "voice" | "satellite" | "market";
  target: string;
  consumption: string;
  latency: string;
  status: "success" | "cached" | "optimal";
  confidence?: string;
}

const AUDIT_LOGS: AuditLogItem[] = [
  {
    id: "log-1",
    timestamp: "Today, 11:42 AM",
    model: "Gemini 2.0 Flash Vision",
    category: "vision",
    target: "Krishna Valley Plot A (Sharbati Wheat)",
    consumption: "1 Leaf Scan (1,420 tokens)",
    latency: "640ms",
    status: "success",
    confidence: "98.4%"
  },
  {
    id: "log-2",
    timestamp: "Today, 09:15 AM",
    model: "Gemini Live Kisan Audio",
    category: "voice",
    target: "Marathi Voice Query: Onion Downy Mildew",
    consumption: "2.4 Voice Mins (3,800 tokens)",
    latency: "820ms",
    status: "success"
  },
  {
    id: "log-3",
    timestamp: "Today, 08:30 AM",
    model: "Sentinel-2 + Gemini 1.5 Pro",
    category: "satellite",
    target: "Plot B (Table Grapes 8.5 Ac)",
    consumption: "1 Satellite NDVI Pass",
    latency: "1.2s",
    status: "success",
    confidence: "10m Spatial"
  },
  {
    id: "log-4",
    timestamp: "Yesterday, 04:30 PM",
    model: "Gemini Flash Market Forecaster",
    category: "market",
    target: "Nashik APMC Onion Price 7-Day Curve",
    consumption: "850 tokens",
    latency: "410ms",
    status: "cached"
  },
  {
    id: "log-5",
    timestamp: "Yesterday, 02:10 PM",
    model: "Gemini 2.0 Flash Vision",
    category: "vision",
    target: "Krishna Dairy Shed (Gauri Gir Cow)",
    consumption: "1 Biometric Scan (1,150 tokens)",
    latency: "790ms",
    status: "success",
    confidence: "96.2%"
  },
  {
    id: "log-6",
    timestamp: "Sep 27, 10:05 AM",
    model: "Gemini 2.0 Pro Soil Agronomist",
    category: "satellite",
    target: "NPK Certified Soil Card Rebalance",
    consumption: "2,400 tokens",
    latency: "1.1s",
    status: "optimal"
  }
];

export const QuotaHistory: Component = () => {
  const [selectedFilter, setSelectedFilter] = createSignal<string>("all");
  const [searchQuery, setSearchQuery] = createSignal("");
  const [topUpSuccess, setTopUpSuccess] = createSignal<string | null>(null);

  const filters = [
    { id: "all", label: "All AI Events (34)" },
    { id: "vision", label: "Leaf Diagnostics (18)" },
    { id: "voice", label: "Voice Consultations (7)" },
    { id: "satellite", label: "Satellite NDVI (5)" },
    { id: "market", label: "Market Forecasts (4)" }
  ];

  const filteredLogs = createMemo(() => {
    const f = selectedFilter();
    const q = searchQuery().toLowerCase().trim();

    return AUDIT_LOGS.filter((item) => {
      const matchesFilter = f === "all" || item.category === f;
      const matchesQuery =
        q === "" ||
        item.model.toLowerCase().includes(q) ||
        item.target.toLowerCase().includes(q) ||
        item.consumption.toLowerCase().includes(q);
      return matchesFilter && matchesQuery;
    });
  });

  const handleTopUp = (packName: string) => {
    setTopUpSuccess(`Successfully activated ${packName}! Quota updated.`);
    setTimeout(() => setTopUpSuccess(null), 4000);
  };

  return (
    <div class="space-y-6">
      {/* Top Header */}
      <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-1">
            <span class="material-symbols-outlined text-base">neurology</span>
            <span>Gemini 2.0 AI Telemetry</span>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">
            AI Quota &amp; Telemetry Usage History
          </h1>
          <p class="text-xs text-slate-500 mt-1 max-w-xl">
            Monitor real-time vision inferences, spoken audio minutes, satellite spectral compute, and historical ICAR-compliant audit trails.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-forest border border-emerald-200 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Gemini Multimodal TPU Engine Online</span>
          </span>
        </div>
      </div>

      {/* Quota Telemetry Banner (4 Metric Cards) */}
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Vision Scans */}
        <div class="p-5 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-slate-500">Daily Leaf Vision Scans</span>
            <span class="w-8 h-8 rounded-xl bg-emerald-50 text-forest flex items-center justify-center">
              <span class="material-symbols-outlined text-base">psychiatry</span>
            </span>
          </div>
          <div>
            <div class="flex items-baseline gap-1.5">
              <span class="text-2xl font-extrabold text-forest">42 / 50</span>
              <span class="text-xs font-bold text-emerald-600">Remaining</span>
            </div>
            <div class="w-full bg-slate-100 h-2 rounded-full mt-2.5 overflow-hidden">
              <div class="h-full bg-emerald-500 rounded-full w-[84%]" />
            </div>
            <p class="text-[11px] text-slate-400 mt-2">
              Resets in 6h 24m &bull; Gemini 2.0 Flash
            </p>
          </div>
        </div>

        {/* Metric 2: LLM Tokens */}
        <div class="p-5 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-slate-500">Inference Tokens</span>
            <span class="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">token</span>
            </span>
          </div>
          <div>
            <div class="flex items-baseline gap-1.5">
              <span class="text-2xl font-extrabold text-purple-900">184.2k</span>
              <span class="text-xs font-bold text-slate-400">/ 250k used</span>
            </div>
            <div class="w-full bg-slate-100 h-2 rounded-full mt-2.5 overflow-hidden">
              <div class="h-full bg-purple-600 rounded-full w-[73.6%]" />
            </div>
            <p class="text-[11px] text-slate-400 mt-2">
              65,800 tokens buffer available
            </p>
          </div>
        </div>

        {/* Metric 3: Voice Minutes */}
        <div class="p-5 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-slate-500">Kisan Voice Minutes</span>
            <span class="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">mic</span>
            </span>
          </div>
          <div>
            <div class="flex items-baseline gap-1.5">
              <span class="text-2xl font-extrabold text-amber-900">48 / 60</span>
              <span class="text-xs font-bold text-slate-400">Mins used</span>
            </div>
            <div class="w-full bg-slate-100 h-2 rounded-full mt-2.5 overflow-hidden">
              <div class="h-full bg-amber-500 rounded-full w-[80%]" />
            </div>
            <p class="text-[11px] text-slate-400 mt-2">
              12 mins buffer &bull; Marathi/Hindi ASR
            </p>
          </div>
        </div>

        {/* Metric 4: Satellite NDVI Passes */}
        <div class="p-5 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-slate-500">Sentinel-2 NDVI Passes</span>
            <span class="w-8 h-8 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">satellite_alt</span>
            </span>
          </div>
          <div>
            <div class="flex items-baseline gap-1.5">
              <span class="text-2xl font-extrabold text-sky-900">12 / 20</span>
              <span class="text-xs font-bold text-slate-400">Passes used</span>
            </div>
            <div class="w-full bg-slate-100 h-2 rounded-full mt-2.5 overflow-hidden">
              <div class="h-full bg-sky-500 rounded-full w-[60%]" />
            </div>
            <p class="text-[11px] text-slate-400 mt-2">
              Next pass tomorrow 10:42 AM IST
            </p>
          </div>
        </div>
      </section>

      {/* Subscription Tier & Quick Top-Up Packs */}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Plan Card */}
        <div class="p-6 rounded-2xl bg-gradient-to-br from-forest to-emerald-900 text-white shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-400/20 text-emerald-200 border border-emerald-400/30">
                Active Plan
              </span>
              <span class="text-xs font-mono text-emerald-200">ICAR-GOV-SUB</span>
            </div>
            <h3 class="text-xl font-bold">Kisan Pro Tier</h3>
            <p class="text-xs text-emerald-200 mt-1">
              100% Subsidized under PM-KISAN Digital Agriculture Mission
            </p>

            <ul class="mt-4 space-y-2 text-xs text-emerald-100">
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-sm text-emerald-300">check_circle</span>
                <span>Priority Gemini 2.0 Flash TPU Queuing</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-sm text-emerald-300">check_circle</span>
                <span>Offline SMS Failover for 2G Rural Zones</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-sm text-emerald-300">check_circle</span>
                <span>NABL-Accredited Pathology Diagnostics</span>
              </li>
            </ul>
          </div>

          <div class="mt-6 pt-4 border-t border-emerald-800/80 flex items-center justify-between text-xs">
            <span>Renewed Monthly</span>
            <span class="font-extrabold text-base text-white">&#8377;0 / month</span>
          </div>
        </div>

        {/* Top-Up Packs (2 cols) */}
        <div class="lg:col-span-2 p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-bold text-slate-900">Instant Quota Top-Up</h3>
              <p class="text-xs text-slate-500">Need emergency scans before tomorrow&apos;s reset? Top up via UPI instantly.</p>
            </div>
          </div>

          {topUpSuccess() && (
            <div class="p-3 rounded-xl bg-emerald-50 text-forest text-xs font-bold border border-emerald-200 flex items-center gap-2">
              <span class="material-symbols-outlined text-sm">verified</span>
              <span>{topUpSuccess()}</span>
            </div>
          )}

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between">
              <div>
                <span class="text-xs font-bold text-slate-600">+25 Leaf Scans</span>
                <p class="text-[11px] text-slate-400 mt-1">Instant Gemini Vision pack</p>
                <div class="text-lg font-extrabold text-forest mt-2">&#8377;49</div>
              </div>
              <button
                onClick={() => handleTopUp("+25 Leaf Scans")}
                class="mt-3 w-full py-1.5 px-3 bg-white hover:bg-forest hover:text-white text-forest border border-forest/30 font-bold rounded-lg text-xs transition-colors"
              >
                Add Pack
              </button>
            </div>

            <div class="p-4 rounded-xl bg-purple-50/50 border border-purple-200/80 flex flex-col justify-between">
              <div>
                <span class="text-xs font-bold text-purple-900">+100k Tokens</span>
                <p class="text-[11px] text-purple-600 mt-1">Multi-season agronomic chat</p>
                <div class="text-lg font-extrabold text-purple-900 mt-2">&#8377;99</div>
              </div>
              <button
                onClick={() => handleTopUp("+100k Tokens")}
                class="mt-3 w-full py-1.5 px-3 bg-purple-700 hover:bg-purple-800 text-white font-bold rounded-lg text-xs transition-colors"
              >
                Add Pack
              </button>
            </div>

            <div class="p-4 rounded-xl bg-amber-50/50 border border-amber-200/80 flex flex-col justify-between">
              <div>
                <span class="text-xs font-bold text-amber-900">+30 Voice Mins</span>
                <p class="text-[11px] text-amber-700 mt-1">Marathi/Hindi audio advisory</p>
                <div class="text-lg font-extrabold text-amber-900 mt-2">&#8377;39</div>
              </div>
              <button
                onClick={() => handleTopUp("+30 Voice Mins")}
                class="mt-3 w-full py-1.5 px-3 bg-white hover:bg-amber-600 hover:text-white text-amber-800 border border-amber-300 font-bold rounded-lg text-xs transition-colors"
              >
                Add Pack
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Live Inference Audit Trail Table */}
      <div class="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-4">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 class="text-base font-bold text-slate-900">Inference Audit Trail</h3>
            <p class="text-xs text-slate-500">Cryptographically verifiable log of all multimodal API calls</p>
          </div>

          <div class="flex items-center gap-2">
            <div class="relative">
              <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
                search
              </span>
              <input
                type="text"
                value={searchQuery()}
                onInput={(e) => setSearchQuery(e.currentTarget.value)}
                placeholder="Search audit trail..."
                class="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-forest"
              />
            </div>

            <button
              onClick={() => alert("Exporting Audit Log as CSV / ICAR Audit PDF...")}
              class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <span class="material-symbols-outlined text-sm">file_download</span>
              <span>Export Log</span>
            </button>
          </div>
        </div>

        {/* Filter Chips */}
        <div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <For each={filters}>
            {(f) => (
              <button
                onClick={() => setSelectedFilter(f.id)}
                class={`px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${
                  selectedFilter() === f.id
                    ? "bg-forest text-white border-forest shadow-sm"
                    : "bg-white text-slate-600 border-slate-200 hover:border-forest/40 hover:text-forest"
                }`}
              >
                {f.label}
              </button>
            )}
          </For>
        </div>

        {/* Audit Table */}
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-slate-200 text-slate-500 font-bold">
                <th class="py-2.5 px-3">Timestamp</th>
                <th class="py-2.5 px-3">Model / Capability</th>
                <th class="py-2.5 px-3">Plot / Target</th>
                <th class="py-2.5 px-3">Quota Consumed</th>
                <th class="py-2.5 px-3">Latency</th>
                <th class="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <For each={filteredLogs()}>
                {(item) => (
                  <tr class="hover:bg-slate-50/80 transition-colors">
                    <td class="py-3 px-3 font-mono text-slate-500 text-[11px] whitespace-nowrap">
                      {item.timestamp}
                    </td>
                    <td class="py-3 px-3">
                      <span class="font-bold text-slate-900">{item.model}</span>
                    </td>
                    <td class="py-3 px-3 text-slate-600">
                      {item.target}
                    </td>
                    <td class="py-3 px-3 font-mono font-medium text-slate-700 whitespace-nowrap">
                      {item.consumption}
                    </td>
                    <td class="py-3 px-3 font-mono text-slate-500 text-[11px]">
                      {item.latency}
                    </td>
                    <td class="py-3 px-3">
                      <span
                        class={`px-2 py-0.5 rounded-full text-[10px] font-bold border inline-flex items-center gap-1 ${
                          item.status === "success"
                            ? "bg-emerald-50 text-forest border-emerald-200"
                            : item.status === "cached"
                            ? "bg-slate-100 text-slate-700 border-slate-200"
                            : "bg-blue-50 text-blue-700 border-blue-200"
                        }`}
                      >
                        <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                        <span>{item.status.toUpperCase()}</span>
                        {item.confidence && <span class="text-slate-400 font-mono">({item.confidence})</span>}
                      </span>
                    </td>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
