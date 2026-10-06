import { Component, createSignal, For, Show, onMount } from "solid-js";
import { A, useParams } from "@solidjs/router";
import { apiClient } from "../../lib/api-client";

interface PlotLedgerItem {
  id: string;
  plotName: string;
  gatNo: string;
  crop: string;
  acres: number;
  yieldPerAc: string;
  projectedRevenue: string;
  operatingCost: string;
  marginPercent: string;
  contractStatus: string;
  statusColor: string;
}

export const FarmAnalytics: Component = () => {
  const params = useParams();
  const farmId = () => params.id || "1";

  const [loading, setLoading] = createSignal(false);
  const [selectedSeason, setSelectedSeason] = createSignal("rabi_2024_25");
  const [showExpenseModal, setShowExpenseModal] = createSignal(false);

  // Financial summary state
  const [financeMetrics, setFinanceMetrics] = createSignal({
    farmName: "Krishna Valley Farm",
    icarId: "MH-NSK-2024-8841",
    location: "Nashik, Maharashtra",
    netProfit: "₹2,88,000",
    profitMargin: "68%",
    totalOpex: "₹1,24,000",
    budgetOpex: "₹1,40,000",
    opexSavings: "11.4%",
    grossHarvest: "₹4,12,000",
    escrowLocked: "₹2,65,000",
    carbonCreditsValuation: "₹36,500",
    carbonSequesteredTonnes: "14.2 T",
    socPercent: "0.62%",
    socIncrease: "+0.14%",
    kccLimit: "₹3,00,000",
    kccDrawn: "₹1,15,000",
    kccAvailable: "₹1,85,000",
    pmksySubsidy: "₹64,800",
  });

  const monthlyCashflow = [
    { month: "Oct 24", actual: 28000, projected: 32000 },
    { month: "Nov 24", actual: 34000, projected: 36000 },
    { month: "Dec 24", actual: 26000, projected: 30000 },
    { month: "Jan 25", actual: 18000, projected: 22000 },
    { month: "Feb 25", actual: 12000, projected: 14000 },
    { month: "Mar 25", actual: 6000, projected: 6000 },
  ];

  const plotLedger: PlotLedgerItem[] = [
    {
      id: "plot-a",
      plotName: "Plot A • North Orchard",
      gatNo: "Gat #142/2A",
      crop: "Table Grapes (Thomson Seedless)",
      acres: 5.2,
      yieldPerAc: "14.8 Tonnes/Ac",
      projectedRevenue: "₹2,45,000",
      operatingCost: "₹72,000",
      marginPercent: "+70.6%",
      contractStatus: "Escrow Contract #BK-8924 Active",
      statusColor: "text-emerald-700 bg-emerald-50 border-emerald-200",
    },
    {
      id: "plot-b",
      plotName: "Plot B • Central Parcel",
      gatNo: "Gat #142/2B",
      crop: "Sharbati Durum Wheat",
      acres: 4.8,
      yieldPerAc: "22 Qtl/Ac",
      projectedRevenue: "₹98,000",
      operatingCost: "₹31,000",
      marginPercent: "+68.3%",
      contractStatus: "NABL Grade A+ Certified",
      statusColor: "text-blue-700 bg-blue-50 border-blue-200",
    },
    {
      id: "plot-c",
      plotName: "Plot C • South Terrace",
      gatNo: "Gat #143/1",
      crop: "Bhagwa Pomegranate",
      acres: 3.5,
      yieldPerAc: "8.4 Tonnes/Ac",
      projectedRevenue: "₹69,000",
      operatingCost: "₹21,000",
      marginPercent: "+69.5%",
      contractStatus: "Pre-flowering Canopy",
      statusColor: "text-amber-700 bg-amber-50 border-amber-200",
    },
    {
      id: "plot-d",
      plotName: "Plot D • Lower Basin",
      gatNo: "Gat #143/2",
      crop: "Dhaincha Green Manure",
      acres: 5.0,
      yieldPerAc: "Soil Biomass (+35kg N/Ac)",
      projectedRevenue: "₹14,200 (Fertilizer Offset)",
      operatingCost: "₹0 (PM-PRANAM)",
      marginPercent: "+100%",
      contractStatus: "Soil Reconditioning",
      statusColor: "text-purple-700 bg-purple-50 border-purple-200",
    },
  ];

  onMount(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<any>(`/analytics/farm/${farmId()}`);
      if (res) {
        setFinanceMetrics((prev) => ({
          ...prev,
          netProfit: res.net_profit || prev.netProfit,
          totalOpex: res.total_opex || prev.totalOpex,
          grossHarvest: res.gross_harvest || prev.grossHarvest,
        }));
      }
    } catch {
      // Graceful offline mock fallback
    } finally {
      setLoading(false);
    }
  });

  return (
    <div class="space-y-6 max-w-7xl mx-auto pb-24">
      {/* CONTEXTUAL TOP HEADER & CONTROLS */}
      <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          {/* Breadcrumbs */}
          <div class="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <A href="/dashboard" class="hover:text-emerald-700">Home</A>
            <span>/</span>
            <A href="/farm" class="hover:text-emerald-700">My Farms & Plots</A>
            <span>/</span>
            <A href={`/farm/${farmId()}`} class="hover:text-emerald-700">{financeMetrics().farmName}</A>
            <span>/</span>
            <span class="text-slate-900 font-semibold">Financial & Yield Analytics</span>
          </div>

          <div class="flex flex-wrap items-center gap-2.5 mt-1.5">
            <h1 class="text-xl md:text-2xl font-black text-slate-900 tracking-tight">
              {financeMetrics().farmName} Financial Intelligence & Carbon Ledger
            </h1>
            <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              ICAR & NABARD Certified
            </span>
            <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-300">
              Verra Carbon VM0042
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">
            {financeMetrics().location} • 18.5 Acres Holding • e-NAM APMC Linked Ledger
          </p>
        </div>

        {/* Season Filter & Action Buttons */}
        <div class="flex flex-wrap items-center gap-2.5">
          <select
            value={selectedSeason()}
            onChange={(e) => setSelectedSeason(e.currentTarget.value)}
            class="bg-slate-50 border border-slate-200 text-slate-800 font-bold text-xs rounded-xl px-3 py-2 focus:outline-none focus:border-emerald-600"
          >
            <option value="rabi_2024_25">Rabi Season 2024–25 (Active)</option>
            <option value="kharif_2024">Kharif Season 2024 (Harvested)</option>
            <option value="annual_2023_24">Annual 2023–24 Consolidated</option>
          </select>

          <button
            type="button"
            class="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition-colors"
          >
            <span class="material-symbols-outlined text-sm">picture_as_pdf</span>
            <span>Audit PDF</span>
          </button>

          <button
            type="button"
            onClick={() => setShowExpenseModal(true)}
            class="px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all active:scale-98"
          >
            <span class="material-symbols-outlined text-sm">add_circle</span>
            <span>+ Log Expense</span>
          </button>
        </div>
      </div>

      {/* 4 HIGH-IMPACT FINANCIAL STAT CARDS */}
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* KPI 1: Net Operating Profit */}
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-bold">Net Farm Profit</span>
            <span class="material-symbols-outlined text-emerald-700 text-base">payments</span>
          </div>
          <p class="text-2xl font-black text-slate-900 tracking-tight">{financeMetrics().netProfit}</p>
          <div class="flex items-center gap-1 text-[11px] font-bold text-emerald-700">
            <span class="material-symbols-outlined text-xs">trending_up</span>
            <span>+{financeMetrics().profitMargin} Margin (Realized Net)</span>
          </div>
        </div>

        {/* KPI 2: Total OpEx & Savings */}
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-bold">Total OpEx & Inputs</span>
            <span class="material-symbols-outlined text-amber-600 text-base">receipt_long</span>
          </div>
          <p class="text-2xl font-black text-slate-900 tracking-tight">{financeMetrics().totalOpex}</p>
          <p class="text-[11px] text-emerald-700 font-bold">
            {financeMetrics().opexSavings} below budget via Precision Drip
          </p>
        </div>

        {/* KPI 3: Gross Harvest Realization */}
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-bold">Gross Harvest Forecast</span>
            <span class="material-symbols-outlined text-blue-600 text-base">storefront</span>
          </div>
          <p class="text-2xl font-black text-slate-900 tracking-tight">{financeMetrics().grossHarvest}</p>
          <p class="text-[11px] text-blue-700 font-medium">
            {financeMetrics().escrowLocked} Locked in APMC Escrow
          </p>
        </div>

        {/* KPI 4: Verified Soil Carbon (SOC) */}
        <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-500">
            <span class="font-bold">Verified Carbon Credits</span>
            <span class="material-symbols-outlined text-emerald-600 text-base">eco</span>
          </div>
          <p class="text-2xl font-black text-emerald-800 tracking-tight">{financeMetrics().carbonCreditsValuation}</p>
          <p class="text-[11px] text-emerald-700 font-bold">
            {financeMetrics().carbonSequesteredTonnes} CO2e @ $31/T (Verra VM0042)
          </p>
        </div>
      </div>

      {/* MAIN TWO-COLUMN ANALYSIS GRID */}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: CASHFLOW, EXPENSES & PLOT-BY-PLOT ROI (7 cols on Desktop) */}
        <div class="lg:col-span-8 space-y-6">
          {/* Card 1: Seasonal Cashflow & Expense Breakdown */}
          <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4">
            <div class="flex flex-wrap items-center justify-between pb-3 border-b border-slate-100 gap-2">
              <div>
                <h3 class="font-black text-base text-slate-900">Seasonal Burn & Cashflow Matrix</h3>
                <p class="text-xs text-slate-500">Actual expenses vs projected budget allocation</p>
              </div>
              <div class="text-right">
                <span class="text-xs text-slate-400 block font-medium">Input Spend Efficiency</span>
                <span class="text-xs font-black text-emerald-700">₹6,702 / Acre <span class="text-slate-400 font-normal">(Avg: ₹8,950)</span></span>
              </div>
            </div>

            {/* Monthly Bar Chart Visualizer */}
            <div class="grid grid-cols-6 gap-2 text-center text-xs pt-2">
              <For each={monthlyCashflow}>
                {(item) => (
                  <div class="space-y-1.5 flex flex-col items-center">
                    <div class="h-32 w-full bg-slate-50 rounded-xl flex items-end justify-center p-1 relative border border-slate-100">
                      {/* Projected Goal bar */}
                      <div
                        class="w-3 bg-slate-200 rounded-t-sm absolute"
                        style={{ height: `${(item.projected / 40000) * 100}%`, left: "30%" }}
                        title={`Projected: ₹${item.projected}`}
                      ></div>
                      {/* Actual Burn bar */}
                      <div
                        class="w-3 bg-emerald-600 rounded-t-sm absolute"
                        style={{ height: `${(item.actual / 40000) * 100}%`, right: "30%" }}
                        title={`Actual: ₹${item.actual}`}
                      ></div>
                    </div>
                    <span class="font-bold text-[11px] text-slate-700">{item.month}</span>
                    <span class="text-[10px] text-slate-400 font-mono">₹{(item.actual / 1000).toFixed(0)}k</span>
                  </div>
                )}
              </For>
            </div>

            {/* Expense Categories Breakdown Bar */}
            <div class="pt-3 border-t border-slate-100 space-y-2">
              <span class="text-xs font-bold text-slate-700 block">OpEx Allocation by Component</span>
              <div class="w-full h-3 rounded-full overflow-hidden flex bg-slate-100">
                <div class="bg-emerald-600 h-full" style={{ width: "38%" }} title="Fertilizers & Nutrients 38%"></div>
                <div class="bg-blue-600 h-full" style={{ width: "26%" }} title="Labor & Harvesting 26%"></div>
                <div class="bg-amber-500 h-full" style={{ width: "24%" }} title="Solar Power & Drip 24%"></div>
                <div class="bg-purple-500 h-full" style={{ width: "12%" }} title="Bio-Crop Protection 12%"></div>
              </div>
              <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-600 font-medium pt-1">
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
                  <span>Nutrients ₹47,120 (38%)</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-blue-600"></span>
                  <span>Labor ₹32,240 (26%)</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                  <span>Drip & Power ₹29,760 (24%)</span>
                </span>
                <span class="flex items-center gap-1">
                  <span class="w-2 h-2 rounded-full bg-purple-500"></span>
                  <span>Bio-Agents ₹14,880 (12%)</span>
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Plot-by-Plot ROI & Yield Performance Ledger Table */}
          <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 class="font-black text-base text-slate-900">Plot-by-Plot Yield, Revenue & ROI Ledger</h3>
                <p class="text-xs text-slate-500">Audited unit economics across 4 registered cadastral parcels</p>
              </div>
              <button
                type="button"
                class="px-2.5 py-1 text-xs font-bold text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors"
              >
                Export GSTR-2 Agri
              </button>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs border-collapse">
                <thead>
                  <tr class="border-b border-slate-200 text-slate-400 uppercase text-[10px] font-bold tracking-wider">
                    <th class="pb-2">Plot / Parcel</th>
                    <th class="pb-2">Crop & Variety</th>
                    <th class="pb-2 text-right">Yield</th>
                    <th class="pb-2 text-right">Projected Rev</th>
                    <th class="pb-2 text-right">OpEx</th>
                    <th class="pb-2 text-right">Margin</th>
                    <th class="pb-2 text-right">Escrow Status</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <For each={plotLedger}>
                    {(item) => (
                      <tr class="hover:bg-slate-50/80 transition-colors">
                        <td class="py-3">
                          <span class="font-bold text-slate-900 block">{item.plotName}</span>
                          <span class="text-[10px] text-slate-400 font-mono">{item.gatNo} • {item.acres} Ac</span>
                        </td>
                        <td class="py-3 font-semibold text-slate-700">{item.crop}</td>
                        <td class="py-3 text-right font-bold text-slate-900">{item.yieldPerAc}</td>
                        <td class="py-3 text-right font-black text-emerald-700">{item.projectedRevenue}</td>
                        <td class="py-3 text-right text-slate-600 font-medium">{item.operatingCost}</td>
                        <td class="py-3 text-right font-black text-emerald-800">{item.marginPercent}</td>
                        <td class="py-3 text-right">
                          <span class={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${item.statusColor}`}>
                            {item.contractStatus}
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

        {/* RIGHT COLUMN: CARBON LEDGER, DBT SUBSIDIES & AI CFO (4 cols on Desktop) */}
        <div class="lg:col-span-4 space-y-6">
          {/* Card 1: Verra Carbon Credit Ledger */}
          <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                  <span class="material-symbols-outlined text-base">eco</span>
                </div>
                <div>
                  <h3 class="font-bold text-sm text-slate-900">Verra Carbon Credit Ledger</h3>
                  <p class="text-[11px] text-slate-500">Methodology VM0042 Verified</p>
                </div>
              </div>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                Gold Standard
              </span>
            </div>

            <div class="space-y-3 text-xs">
              <div class="p-3 bg-emerald-50/50 rounded-xl border border-emerald-200 space-y-1">
                <span class="text-[10px] text-emerald-800 font-bold uppercase tracking-wider block">
                  Soil Organic Carbon (SOC) Stock
                </span>
                <p class="text-xl font-black text-emerald-950">
                  {financeMetrics().socPercent}{" "}
                  <span class="text-xs text-emerald-700 font-bold">({financeMetrics().socIncrease} YoY Increase)</span>
                </p>
                <p class="text-[11px] text-emerald-800">
                  Total Sequestered: <strong>14.2 Metric Tonnes CO2e</strong>
                </p>
              </div>

              <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <span class="text-slate-500">Agri-Carbon Exchange Price:</span>
                <span class="font-black text-slate-900">₹2,570 / Tonne ($31.00)</span>
              </div>

              <button
                type="button"
                class="w-full py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs"
              >
                <span class="material-symbols-outlined text-sm">account_balance</span>
                <span>Liquidate ₹36,500 to KCC Account</span>
              </button>
            </div>
          </div>

          {/* Card 2: Government DBT Subsidies & KCC Loan Facility */}
          <div class="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-3 text-xs">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-700">account_balance</span>
                <h3 class="font-bold text-sm text-slate-900">KCC Loan & Govt DBT Tracker</h3>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-800">
                SBI KCC Active
              </span>
            </div>

            {/* KCC Facility */}
            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
              <div class="flex justify-between items-center font-bold">
                <span class="text-slate-900">Kisan Credit Card (KCC)</span>
                <span class="text-emerald-700">4% p.a. Subvention</span>
              </div>
              <div class="flex justify-between text-[11px] text-slate-500">
                <span>Drawn: {financeMetrics().kccDrawn}</span>
                <span>Limit: {financeMetrics().kccLimit}</span>
              </div>
              <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                <div class="bg-blue-600 h-full rounded-full" style={{ width: "38%" }}></div>
              </div>
              <span class="text-[10px] text-slate-500 block pt-0.5">
                Available Credit Balance: <strong class="text-slate-800">{financeMetrics().kccAvailable}</strong>
              </span>
            </div>

            {/* Subsidies List */}
            <div class="space-y-1.5 pt-1">
              <div class="flex items-center justify-between p-2 rounded-lg bg-emerald-50/70 border border-emerald-200">
                <div>
                  <span class="font-bold text-emerald-950 block">PMKSY Drip Subsidy (80%)</span>
                  <span class="text-[10px] text-emerald-700">Ref #DBT-99214 • Credited</span>
                </div>
                <span class="font-black text-emerald-800">{financeMetrics().pmksySubsidy}</span>
              </div>

              <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
                <div>
                  <span class="font-bold text-slate-800 block">PM-KISAN 18th Installment</span>
                  <span class="text-[10px] text-slate-500">Aadhaar Linked Account</span>
                </div>
                <span class="font-black text-slate-900">₹2,000</span>
              </div>
            </div>
          </div>

          {/* Card 3: Agri-CFO Intelligence Recommendation */}
          <div class="bg-gradient-to-br from-emerald-900 to-emerald-950 text-white rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5 text-emerald-300 font-bold text-xs">
                <span class="material-symbols-outlined text-base">auto_awesome</span>
                <span>Agri-CFO Intelligence</span>
              </div>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-800 text-emerald-100">
                94% Confidence
              </span>
            </div>

            <p class="text-xs text-emerald-100 leading-relaxed font-medium">
              "Pre-sell <strong class="text-white font-bold">40% of Plot B Durum Wheat</strong> now to lock in the <strong class="text-white font-bold">₹2,650/Qtl</strong> APMC forward contract. Satellite yield maps from Madhya Pradesh signal an 18% post-harvest supply surge arriving late February."
            </p>

            <div class="flex items-center gap-2 pt-2 border-t border-emerald-800/80">
              <button
                type="button"
                class="flex-1 py-1.5 px-3 rounded-lg bg-emerald-800/60 hover:bg-emerald-800 text-emerald-200 text-xs font-semibold flex items-center justify-center gap-1 transition-colors"
              >
                <span class="material-symbols-outlined text-sm">volume_up</span>
                <span>Listen in मराठी</span>
              </button>
              <A
                href="/marketplace"
                class="py-1.5 px-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-emerald-950 text-xs font-bold transition-colors"
              >
                Lock Contract
              </A>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
