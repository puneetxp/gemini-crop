import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface Waypoint {
  step: number;
  title: string;
  subtitle: string;
  status: "completed" | "current" | "pending";
}

interface ShipmentTracking {
  id: string;
  vehicleNumber: string;
  vehicleType: string;
  cargo: string;
  route: string;
  eta: string;
  driverName: string;
  driverPhone: string;
  reeferTempC: number;
  targetTempC: number;
  tempStatus: "optimal" | "warning" | "ambient";
  humidityPercent: number;
  sealNumber: string;
  sealStatus: "LOCKED" | "BREACH_ALERT";
  fuelPercent: number;
  speedKmH: number;
  waypoints: Waypoint[];
}

export const TransportTracking: Component = () => {
  const [activeTab, setActiveTab] = createSignal<"all" | "reefer" | "dry">("all");
  const [selectedShipmentId, setSelectedShipmentId] = createSignal<string>("CC-8105");
  const [alertDismissed, setAlertDismissed] = createSignal(false);

  const [shipments] = createSignal<ShipmentTracking[]>([
    {
      id: "CC-8105",
      vehicleNumber: "MH-14-GH-4190",
      vehicleType: "Reefer Multi-Axle (16 Ton)",
      cargo: "12 MT Export Bhagwa Pomegranate",
      route: "Junnar Packhouse ➔ JNPT Cold Port Terminal",
      eta: "2h 45m (14:30 IST)",
      driverName: "Anand P.",
      driverPhone: "+91 98230 44910",
      reeferTempC: 3.8,
      targetTempC: 4.0,
      tempStatus: "optimal",
      humidityPercent: 92,
      sealNumber: "TS-4491",
      sealStatus: "LOCKED",
      fuelPercent: 84,
      speedKmH: 58,
      waypoints: [
        { step: 1, title: "Packhouse Loaded", subtitle: "08:15 IST (2.8°C Pre-cool)", status: "completed" },
        { step: 2, title: "Weighbridge #1", subtitle: "Gross: 24,120 Kg", status: "completed" },
        { step: 3, title: "Ghat Expressway", subtitle: "GPS Speed: 58 Km/h", status: "completed" },
        { step: 4, title: "Navi Mumbai Toll", subtitle: "Current Location (12 Km to gate)", status: "current" },
        { step: 5, title: "JNPT In-Gate", subtitle: "Scheduled 14:30 IST", status: "pending" },
      ],
    },
    {
      id: "CC-9402",
      vehicleNumber: "MH-12-AQ-8821",
      vehicleType: "Tarpaulin Multi-Axle (20 Ton)",
      cargo: "20 MT Sharbati Milling Wheat",
      route: "Baramati Farmers FPO ➔ Vashi APMC Yard 4",
      eta: "1h 15m (13:00 IST)",
      driverName: "Ramesh K.",
      driverPhone: "+91 98230 11234",
      reeferTempC: 18.2,
      targetTempC: 22.0,
      tempStatus: "ambient",
      humidityPercent: 62,
      sealNumber: "TS-8820",
      sealStatus: "LOCKED",
      fuelPercent: 71,
      speedKmH: 45,
      waypoints: [
        { step: 1, title: "FPO Silo Dispatched", subtitle: "07:30 IST", status: "completed" },
        { step: 2, title: "Weighbridge Tare Check", subtitle: "Net Grain: 20,050 Kg", status: "completed" },
        { step: 3, title: "Pune Bypass Corridors", subtitle: "NH-48 Dedicated Lane", status: "completed" },
        { step: 4, title: "Panvel Ingate Check", subtitle: "Current Location (4 Km)", status: "current" },
        { step: 5, title: "Vashi Yard 4 Unload", subtitle: "Scheduled 13:00 IST", status: "pending" },
      ],
    },
    {
      id: "CC-6208",
      vehicleNumber: "MH-15-BT-6208",
      vehicleType: "Insulated Milk Tanker (10 KL)",
      cargo: "8,000 L Pure A2 Chilled Milk",
      route: "Niphad Dairy Coop ➔ Pune Urban Processing Depot",
      eta: "45m (12:30 IST)",
      driverName: "Santosh M.",
      driverPhone: "+91 97654 32109",
      reeferTempC: 4.1,
      targetTempC: 4.0,
      tempStatus: "optimal",
      humidityPercent: 88,
      sealNumber: "TS-6208",
      sealStatus: "LOCKED",
      fuelPercent: 90,
      speedKmH: 52,
      waypoints: [
        { step: 1, title: "Chilling Plant Ingate", subtitle: "06:00 IST (3.5°C)", status: "completed" },
        { step: 2, title: "Agitator Testing", subtitle: "Butterfat 4.2% Passed", status: "completed" },
        { step: 3, title: "Nashik Highway Toll", subtitle: "RFID Tag Scanned", status: "completed" },
        { step: 4, title: "Chakan Outer Ring", subtitle: "Current Location", status: "current" },
        { step: 5, title: "Pune Mother Dairy", subtitle: "Scheduled 12:30 IST", status: "pending" },
      ],
    },
  ]);

  const currentShipment = () =>
    shipments().find((s) => s.id === selectedShipmentId()) || shipments()[0];

  return (
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Top Header */}
      <header class="bg-[#064e3b] text-white border-b border-emerald-800/60 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex items-center justify-between h-16">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-400/30">
                <span class="material-symbols-outlined text-emerald-300 text-2xl">local_shipping</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-base tracking-tight">CropSense AI</span>
                  <span class="text-[10px] uppercase font-bold tracking-widest bg-emerald-400/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-400/30">
                    Logistics
                  </span>
                </div>
                <p class="text-[11px] text-emerald-200/80">Cold Chain Reefer Fleet &amp; Live Waypoint Telemetry</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <A
                href="/marketplace/bookings"
                class="px-3 py-1.5 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">lock_clock</span>
                <span>Escrow Orders</span>
              </A>
              <A
                href="/marketplace/buyer-dashboard"
                class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">storefront</span>
                <span>Buyer Console</span>
              </A>
            </div>
          </div>
        </div>
      </header>

      <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Breadcrumb & Title */}
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div>
            <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <A href="/" class="hover:text-emerald-600 transition-colors">Home</A>
              <span>/</span>
              <A href="/marketplace" class="hover:text-emerald-600 transition-colors">Marketplace</A>
              <span>/</span>
              <span class="font-medium text-slate-700 dark:text-slate-300">Fleet Telemetry</span>
            </div>
            <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Live Reefer Telemetry &amp; Mandi In-Transit Dispatch
            </h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Real-time cold compartment temperature sensors, electronic RFID tamper seal logs, and automated weighbridge clearance
            </p>
          </div>

          <div class="flex items-center gap-2">
            <A
              href="/marketplace/bookings"
              class="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-base">add_road</span>
              <span>Book Reefer Vehicle</span>
            </A>
          </div>
        </div>

        {/* 4 Summary KPI Metrics */}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Fleet Active In-Transit</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">local_shipping</span>
            </div>
            <div class="text-2xl font-black text-slate-900 dark:text-white">18 Vehicles</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">14 Reefer • 4 Dry Cargo</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Cold Integrity Score</span>
              <span class="material-symbols-outlined text-blue-600 text-lg">ac_unit</span>
            </div>
            <div class="text-2xl font-black text-blue-700 dark:text-blue-400">3.9°C Mean</div>
            <div class="text-[11px] text-blue-600 dark:text-blue-400 font-semibold">0 Temperature Excursions</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Tamper RFID Seals</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">verified_user</span>
            </div>
            <div class="text-2xl font-black text-emerald-800 dark:text-emerald-300">100% Intact</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">Zero Breach Incident Logged</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Weighbridge On-Time SLA</span>
              <span class="material-symbols-outlined text-purple-600 text-lg">schedule</span>
            </div>
            <div class="text-2xl font-black text-purple-700 dark:text-purple-400">98.6%</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">Avg Ingate Dwell: 14 Mins</div>
          </div>
        </div>

        {/* Selected Consignment Details Card */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-6">
          {/* Header Info */}
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold">
                <span class="material-symbols-outlined text-2xl">
                  {currentShipment().tempStatus === "ambient" ? "grain" : "ac_unit"}
                </span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-black text-lg text-slate-900 dark:text-white">
                    Shipment #{currentShipment().id} ({currentShipment().vehicleNumber})
                  </span>
                  <span
                    class={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      currentShipment().tempStatus === "optimal"
                        ? "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300"
                        : "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300"
                    }`}
                  >
                    {currentShipment().tempStatus === "optimal" ? "Cold Chain Active" : "Ambient Grain"}
                  </span>
                </div>
                <div class="text-xs text-slate-500 dark:text-slate-400">
                  {currentShipment().cargo} • {currentShipment().route}
                </div>
              </div>
            </div>

            <div class="text-right">
              <div class="text-sm font-black text-emerald-700 dark:text-emerald-400">
                ETA: {currentShipment().eta}
              </div>
              <div class="text-[11px] text-slate-400">
                Driver: {currentShipment().driverName} ({currentShipment().driverPhone})
              </div>
            </div>
          </div>

          {/* Waypoint Progress Stepper */}
          <div class="grid grid-cols-2 md:grid-cols-5 gap-3 text-center text-xs py-2">
            <For each={currentShipment().waypoints}>
              {(wp) => (
                <div
                  class={`p-3 rounded-xl border transition-all ${
                    wp.status === "completed"
                      ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800"
                      : wp.status === "current"
                      ? "bg-blue-50/50 dark:bg-blue-950/20 border-blue-300 dark:border-blue-700 ring-2 ring-blue-500/20"
                      : "bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800 opacity-60"
                  }`}
                >
                  <div
                    class={`w-7 h-7 mx-auto rounded-full flex items-center justify-center text-xs font-bold mb-1.5 ${
                      wp.status === "completed"
                        ? "bg-emerald-600 text-white"
                        : wp.status === "current"
                        ? "bg-blue-600 text-white animate-pulse"
                        : "bg-slate-200 dark:bg-slate-700 text-slate-500"
                    }`}
                  >
                    {wp.status === "completed" ? "✓" : wp.step}
                  </div>
                  <div class="font-bold text-slate-900 dark:text-white text-[11px]">{wp.title}</div>
                  <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{wp.subtitle}</div>
                </div>
              )}
            </For>
          </div>

          {/* Telemetry Sensors Ribbon */}
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
            <div>
              <span class="text-slate-400 text-[10px] block">Compartment Temp:</span>
              <span class="font-bold text-blue-700 dark:text-blue-400 text-base">
                {currentShipment().reeferTempC}°C
              </span>
              <span class="text-[10px] text-slate-400 block">(Target: {currentShipment().targetTempC}°C)</span>
            </div>
            <div>
              <span class="text-slate-400 text-[10px] block">Relative Humidity:</span>
              <span class="font-bold text-slate-800 dark:text-slate-200 text-base">
                {currentShipment().humidityPercent}% RH
              </span>
              <span class="text-[10px] text-emerald-600 dark:text-emerald-400 block">Optimum Range</span>
            </div>
            <div>
              <span class="text-slate-400 text-[10px] block">RFID Electronic Seal:</span>
              <span class="font-bold text-emerald-700 dark:text-emerald-400 text-base">
                #{currentShipment().sealNumber}
              </span>
              <span class="text-[10px] text-emerald-600 dark:text-emerald-400 block">LOCKED &amp; VERIFIED</span>
            </div>
            <div>
              <span class="text-slate-400 text-[10px] block">Aux Generator / Speed:</span>
              <span class="font-bold text-slate-800 dark:text-slate-200 text-base">
                {currentShipment().speedKmH} Km/h
              </span>
              <span class="text-[10px] text-slate-400 block">Fuel: {currentShipment().fuelPercent}% Remaining</span>
            </div>
          </div>
        </div>

        {/* Consignment Selector Cards */}
        <div>
          <h3 class="font-bold text-slate-900 dark:text-white text-sm mb-3">All Active Consignments in Fleet</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <For each={shipments()}>
              {(s) => (
                <button
                  onClick={() => setSelectedShipmentId(s.id)}
                  class={`p-4 rounded-2xl border text-left transition-all ${
                    selectedShipmentId() === s.id
                      ? "border-emerald-500 dark:border-emerald-400 ring-2 ring-emerald-500/20 bg-white dark:bg-slate-900 shadow"
                      : "border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 hover:bg-white dark:hover:bg-slate-900"
                  }`}
                >
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-900 dark:text-white text-xs">{s.id}</span>
                    <span class="text-[10px] font-bold text-blue-700 dark:text-blue-400 font-mono">
                      {s.reeferTempC}°C
                    </span>
                  </div>
                  <div class="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-1 truncate">
                    {s.cargo}
                  </div>
                  <div class="text-[10px] text-slate-400 truncate mt-0.5">{s.route}</div>
                  <div class="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 mt-2">
                    ETA: {s.eta}
                  </div>
                </button>
              )}
            </For>
          </div>
        </div>
      </main>
    </div>
  );
};
export default TransportTracking;
