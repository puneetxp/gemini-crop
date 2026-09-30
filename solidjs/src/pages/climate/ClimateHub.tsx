import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface DayAdvisory {
  day: string;
  date: string;
  condition: string;
  icon: string;
  tempMax: number;
  tempMin: number;
  rainMm: number;
  rainProb: number;
  windSpeed: number;
  et0: number; // Evapotranspiration in mm/day
  prescription: string;
  spraySuitability: "optimal" | "caution" | "forbidden";
}

interface HourlyForecast {
  time: string;
  temp: number;
  rainProb: number;
  windSpeed: number;
  suitability: "optimal" | "caution" | "forbidden";
  label: string;
}

export const ClimateHub: Component = () => {
  const [selectedFarm, setSelectedFarm] = createSignal("baramati");
  const [radarLayer, setRadarLayer] = createSignal<"reflectivity" | "clouds" | "wind">("reflectivity");
  const [radarTimeOffset, setRadarTimeOffset] = createSignal<number>(0);
  const [alertDismissed, setAlertDismissed] = createSignal(false);

  const hourlyData: HourlyForecast[] = [
    { time: "06:00", temp: 22, rainProb: 0, windSpeed: 6, suitability: "optimal", label: "Ideal Spray" },
    { time: "08:00", temp: 25, rainProb: 0, windSpeed: 8, suitability: "optimal", label: "Ideal Spray" },
    { time: "10:00", temp: 28, rainProb: 5, windSpeed: 10, suitability: "optimal", label: "Safe Drone Run" },
    { time: "12:00", temp: 33, rainProb: 10, windSpeed: 16, suitability: "caution", label: "Wind Drift Risk" },
    { time: "14:00", temp: 36, rainProb: 15, windSpeed: 19, suitability: "caution", label: "Heatwave Peak" },
    { time: "16:00", temp: 34, rainProb: 25, windSpeed: 14, suitability: "caution", label: "Moderate Wind" },
    { time: "18:00", temp: 30, rainProb: 65, windSpeed: 12, suitability: "forbidden", label: "Rain Showers" },
    { time: "20:00", temp: 27, rainProb: 75, windSpeed: 15, suitability: "forbidden", label: "Heavy Rain" },
    { time: "22:00", temp: 25, rainProb: 30, windSpeed: 8, suitability: "caution", label: "Wet Leaf Foliage" }
  ];

  const weekForecast: DayAdvisory[] = [
    {
      day: "Today",
      date: "30 Sep",
      condition: "Partly Cloudy • Evening Thunderstorm",
      icon: "thunderstorm",
      tempMax: 36.5,
      tempMin: 21.0,
      rainMm: 14.2,
      rainProb: 75,
      windSpeed: 14,
      et0: 5.8,
      prescription: "Complete systemic fungicide (Mancozeb) spray before 10:30 AM. Halt irrigation.",
      spraySuitability: "caution"
    },
    {
      day: "Thursday",
      date: "01 Oct",
      condition: "Clear Sky • High Sunlight",
      icon: "wb_sunny",
      tempMax: 38.0,
      tempMin: 22.0,
      rainMm: 0.0,
      rainProb: 5,
      windSpeed: 9,
      et0: 6.4,
      prescription: "Apply 4-hour deep drip fertigation with 12:61:00 (Mono Ammonium Phosphate).",
      spraySuitability: "optimal"
    },
    {
      day: "Friday",
      date: "02 Oct",
      condition: "Severe Heatwave Warning",
      icon: "local_fire_department",
      tempMax: 41.5,
      tempMin: 24.5,
      rainMm: 0.0,
      rainProb: 0,
      windSpeed: 18,
      et0: 7.6,
      prescription: "Deploy shade nets and schedule 35-min sprinkler canopy misting at 1:30 PM.",
      spraySuitability: "caution"
    },
    {
      day: "Saturday",
      date: "03 Oct",
      condition: "Hot & Dry Winds",
      icon: "air",
      tempMax: 40.0,
      tempMin: 23.5,
      rainMm: 0.0,
      rainProb: 10,
      windSpeed: 21,
      et0: 7.1,
      prescription: "Avoid foliar pesticide spraying due to extreme drift. Inspect drip line pressure.",
      spraySuitability: "forbidden"
    },
    {
      day: "Sunday",
      date: "04 Oct",
      condition: "Passing Clouds",
      icon: "cloud",
      tempMax: 35.0,
      tempMin: 21.5,
      rainMm: 2.5,
      rainProb: 30,
      windSpeed: 11,
      et0: 5.2,
      prescription: "Optimal window for shoot pinching and sub-lateral canopy thinning.",
      spraySuitability: "optimal"
    },
    {
      day: "Monday",
      date: "05 Oct",
      condition: "Moderate Rain Showers",
      icon: "rainy",
      tempMax: 32.0,
      tempMin: 20.0,
      rainMm: 22.0,
      rainProb: 85,
      windSpeed: 15,
      et0: 3.9,
      prescription: "Drain excess surface water from furrows to prevent root phytophthora rot.",
      spraySuitability: "forbidden"
    },
    {
      day: "Tuesday",
      date: "06 Oct",
      condition: "Sunny & Mild",
      icon: "sunny",
      tempMax: 33.5,
      tempMin: 19.5,
      rainMm: 0.0,
      rainProb: 10,
      windSpeed: 8,
      et0: 4.8,
      prescription: "Post-rain prophylactic bio-fungicide (Trichoderma viride) soil drenching.",
      spraySuitability: "optimal"
    }
  ];

  return (
    <div class="space-y-6">
      {/* Header & Location Selector */}
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
            <A href="/dashboard" class="hover:underline">Home</A>
            <span>/</span>
            <span class="text-brand-600 dark:text-brand-400 font-medium">Climate &amp; Weather Hub</span>
          </div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <span class="material-symbols-outlined text-brand-600 text-3xl">thermostat</span>
            Micro-Climate &amp; Hyperlocal Weather Advisory
          </h1>
          <p class="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
            Real-time Doppler precipitation radar, IoT sensor telemetry, and IMD-CRIDA precision agro-meteorological advisories.
          </p>
        </div>

        {/* Farm Context Selector */}
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 shadow-sm">
            <span class="material-symbols-outlined text-brand-600 text-lg">location_on</span>
            <select
              value={selectedFarm()}
              onChange={e => setSelectedFarm(e.currentTarget.value)}
              class="text-xs font-bold bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="baramati">Baramati Grape Vineyard (Plot A - 4.2 Acres)</option>
              <option value="niphad">Niphad Onion &amp; Pomegranate (Plot B - 6.0 Acres)</option>
              <option value="karnal">Karnal Basmati Paddy (Plot C - 8.5 Acres)</option>
            </select>
          </div>

          <div class="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-semibold">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>IMD Verified</span>
          </div>
        </div>
      </div>

      {/* EXTREME WEATHER ORANGE ALERT BANNER */}
      {!alertDismissed() && (
        <div class="rounded-2xl bg-gradient-to-r from-amber-600 via-orange-600 to-amber-700 text-white p-5 shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="relative z-10 flex items-start gap-3.5">
            <div class="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/30">
              <span class="material-symbols-outlined text-2xl text-white animate-pulse">warning</span>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-black uppercase tracking-wider bg-white/25 px-2 py-0.5 rounded-full">
                  IMD Orange Warning • Heatwave Advisory
                </span>
                <span class="text-xs font-medium text-amber-100">Peak Friday • 41.5°C Expected</span>
              </div>
              <h3 class="text-lg font-black mt-1">Sun Scald &amp; Severe Berry Desiccation Hazard</h3>
              <p class="text-xs text-amber-100 mt-0.5 max-w-2xl leading-relaxed">
                Daytime temperatures will peak 4.5°C above seasonal normal. Apply straw mulching across vine rows and run 35-minute overhead misting between 1:00 PM and 3:00 PM to protect tender grape bunches.
              </p>
            </div>
          </div>

          <div class="relative z-10 flex items-center gap-2 shrink-0">
            <button
              onClick={() => alert("Mitigation checklist dispatched to WhatsApp group #BaramatiFarmWorkers")}
              class="px-4 py-2.5 rounded-xl bg-white text-orange-700 hover:bg-orange-50 text-xs font-black shadow-md transition-all flex items-center gap-2"
            >
              <span class="material-symbols-outlined text-base">share</span>
              Dispatch to Workers
            </button>
            <button
              onClick={() => setAlertDismissed(true)}
              class="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors"
              title="Dismiss"
            >
              <span class="material-symbols-outlined text-lg">close</span>
            </button>
          </div>
        </div>
      )}

      {/* 4 LIVE TELEMETRY SCORECARDS */}
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Ambient Temperature */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-bold uppercase tracking-wider">Air Temperature</span>
              <span class="material-symbols-outlined text-brand-600 text-lg">device_thermostat</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl font-black text-slate-900 dark:text-white">31.4°C</span>
              <span class="text-xs text-slate-500 font-medium">Feels 34.2°C</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
            <span>High: 36.5°C • Low: 21.0°C</span>
            <span class="text-amber-600 dark:text-amber-400 font-semibold">+1.8° vs avg</span>
          </div>
        </div>

        {/* Card 2: Relative Humidity */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-bold uppercase tracking-wider">Relative Humidity</span>
              <span class="material-symbols-outlined text-blue-600 text-lg">humidity_percentage</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl font-black text-slate-900 dark:text-white">68%</span>
              <span class="text-xs text-slate-500 font-medium">Dew Pt: 24.2°C</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
            <span class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 font-bold text-[10px]">
              High Spore Risk
            </span>
            <span class="text-slate-400 text-[11px]">Downy Mildew</span>
          </div>
        </div>

        {/* Card 3: Wind Velocity & Direction */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-bold uppercase tracking-wider">Wind &amp; Gusts</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">air</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl font-black text-slate-900 dark:text-white">12</span>
              <span class="text-xs text-slate-500 font-medium">km/h NE</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
            <span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-bold text-[10px]">
              Drone Safe
            </span>
            <span class="text-slate-400 text-[11px]">Until 11:00 AM</span>
          </div>
        </div>

        {/* Card 4: Subsoil Moisture & Rootzone */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span class="font-bold uppercase tracking-wider">Soil Moisture (15cm)</span>
              <span class="material-symbols-outlined text-teal-600 text-lg">grass</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl font-black text-slate-900 dark:text-white">32.4%</span>
              <span class="text-xs text-slate-500 font-medium">VWC Optimal</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
            <span>Soil Temp: 23.5°C</span>
            <span class="text-emerald-600 dark:text-emerald-400 font-bold">Field Capacity</span>
          </div>
        </div>
      </div>

      {/* TWO COLUMN GRID: DOPPLER RADAR (LEFT) & IOT TELEMETRY STATION (RIGHT) */}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Doppler Precipitation Radar & 24h Spray Windows (2 cols) */}
        <div class="lg:col-span-2 space-y-6">
          {/* Doppler Radar Frame */}
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-brand-600">radar</span>
                  IMD Doppler Weather Radar &amp; Precipitation Trajectory
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Composite reflectivity from Mumbai &amp; Goa radar stations (Range 250km)</p>
              </div>

              {/* Layer Toggles */}
              <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs">
                <button
                  onClick={() => setRadarLayer("reflectivity")}
                  class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    radarLayer() === "reflectivity"
                      ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                      : "text-slate-500 hover:text-slate-900"
                  }`}
                >
                  Reflectivity (dBZ)
                </button>
                <button
                  onClick={() => setRadarLayer("clouds")}
                  class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    radarLayer() === "clouds"
                      ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                      : "text-slate-500 hover:text-slate-900"
                  }`}
                >
                  Cloud Tops IR
                </button>
                <button
                  onClick={() => setRadarLayer("wind")}
                  class={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    radarLayer() === "wind"
                      ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                      : "text-slate-500 hover:text-slate-900"
                  }`}
                >
                  Wind Vectors
                </button>
              </div>
            </div>

            {/* Radar Simulated Map Canvas */}
            <div class="relative h-72 rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center">
              {/* Concentric Radar Rings */}
              <div class="absolute w-48 h-48 rounded-full border border-emerald-500/20" />
              <div class="absolute w-96 h-96 rounded-full border border-emerald-500/15" />
              <div class="absolute w-[500px] h-[500px] rounded-full border border-emerald-500/10" />

              {/* Crosshair Lines */}
              <div class="absolute inset-x-0 top-1/2 h-px bg-emerald-500/15" />
              <div class="absolute inset-y-0 left-1/2 w-px bg-emerald-500/15" />

              {/* Rain Clouds / Echo Simulation */}
              <div class="absolute top-1/4 right-1/4 w-36 h-28 rounded-full bg-gradient-to-br from-emerald-500/40 via-yellow-500/50 to-red-500/60 filter blur-xl animate-pulse" />
              <div class="absolute bottom-1/3 left-1/3 w-28 h-20 rounded-full bg-gradient-to-tr from-cyan-500/30 to-blue-500/40 filter blur-lg" />

              {/* Farm Pin Landmark */}
              <div class="relative z-10 flex flex-col items-center">
                <div class="w-4 h-4 rounded-full bg-brand-500 border-2 border-white shadow-lg animate-ping absolute" />
                <div class="w-3.5 h-3.5 rounded-full bg-brand-500 border-2 border-white shadow-lg relative" />
                <span class="mt-2 text-[10px] font-black uppercase tracking-wider bg-slate-900/90 text-white px-2 py-0.5 rounded-md border border-slate-700 shadow-md">
                  Baramati Plot A (You)
                </span>
              </div>

              {/* Range & dBZ Legend Overlay */}
              <div class="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-xl p-2 text-[10px] text-slate-300 space-y-1">
                <span class="font-bold block text-slate-400">Precipitation Intensity (dBZ)</span>
                <div class="flex items-center gap-1">
                  <span class="w-3 h-2 rounded bg-cyan-400" title="15 dBZ Light Drizzle" />
                  <span class="w-3 h-2 rounded bg-emerald-500" title="30 dBZ Moderate" />
                  <span class="w-3 h-2 rounded bg-amber-400" title="45 dBZ Heavy" />
                  <span class="w-3 h-2 rounded bg-red-600" title="60 dBZ Severe Hail" />
                  <span class="ml-1 text-slate-400">10 → 65 dBZ</span>
                </div>
              </div>

              {/* Time Scrub Controls */}
              <div class="absolute bottom-3 right-3 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white">
                <button
                  onClick={() => setRadarTimeOffset(-1)}
                  class={`px-2 py-0.5 rounded font-mono text-[11px] ${radarTimeOffset() === -1 ? "bg-brand-600" : "hover:bg-slate-800"}`}
                >
                  -1h
                </button>
                <button
                  onClick={() => setRadarTimeOffset(0)}
                  class={`px-2 py-0.5 rounded font-mono text-[11px] ${radarTimeOffset() === 0 ? "bg-brand-600 font-bold" : "hover:bg-slate-800"}`}
                >
                  Live
                </button>
                <button
                  onClick={() => setRadarTimeOffset(1)}
                  class={`px-2 py-0.5 rounded font-mono text-[11px] ${radarTimeOffset() === 1 ? "bg-brand-600" : "hover:bg-slate-800"}`}
                >
                  +1h
                </button>
                <button
                  onClick={() => setRadarTimeOffset(2)}
                  class={`px-2 py-0.5 rounded font-mono text-[11px] ${radarTimeOffset() === 2 ? "bg-brand-600" : "hover:bg-slate-800"}`}
                >
                  +2h
                </button>
              </div>
            </div>
          </div>

          {/* 24-Hour Spray Suitability & Rain Forecast Matrix */}
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-base text-brand-600">pest_control</span>
                  24-Hour Agricultural Spray Suitability Timeline
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">Automated assessment based on wind gusts, relative humidity, and precipitation probability</p>
              </div>
              <div class="flex items-center gap-3 text-xs">
                <span class="flex items-center gap-1 text-emerald-600 font-semibold">
                  <span class="w-2 h-2 rounded-full bg-emerald-500" /> Optimal
                </span>
                <span class="flex items-center gap-1 text-amber-600 font-semibold">
                  <span class="w-2 h-2 rounded-full bg-amber-500" /> Caution
                </span>
                <span class="flex items-center gap-1 text-red-600 font-semibold">
                  <span class="w-2 h-2 rounded-full bg-red-500" /> No Spray
                </span>
              </div>
            </div>

            <div class="grid grid-cols-3 sm:grid-cols-9 gap-2">
              <For each={hourlyData}>
                {hour => (
                  <div
                    class={`p-2.5 rounded-xl border text-center space-y-1 transition-all ${
                      hour.suitability === "optimal"
                        ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-800 dark:bg-emerald-950/40"
                        : hour.suitability === "caution"
                        ? "border-amber-200 bg-amber-50/70 dark:border-amber-800 dark:bg-amber-950/40"
                        : "border-red-200 bg-red-50/70 dark:border-red-800 dark:bg-red-950/40"
                    }`}
                  >
                    <span class="text-[11px] font-mono font-bold text-slate-700 dark:text-slate-300 block">{hour.time}</span>
                    <span class="text-xs font-black text-slate-900 dark:text-white block">{hour.temp}°C</span>
                    <div class="text-[10px] text-slate-500">
                      <span>{hour.rainProb}% rain</span>
                    </div>
                    <span
                      class={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded-md block truncate ${
                        hour.suitability === "optimal"
                          ? "bg-emerald-200 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200"
                          : hour.suitability === "caution"
                          ? "bg-amber-200 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                          : "bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200"
                      }`}
                    >
                      {hour.label}
                    </span>
                  </div>
                )}
              </For>
            </div>
          </div>
        </div>

        {/* Right Column: IoT Telemetry Station & Voice Bulletin (1 col) */}
        <div class="space-y-6">
          {/* IoT Telemetry Station Health */}
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-base text-brand-600">sensors</span>
                IoT Station #CS-BAR-04
              </h3>
              <span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 text-[10px] font-black uppercase">
                Online
              </span>
            </div>

            <div class="space-y-2.5 text-xs text-slate-600 dark:text-slate-400">
              <div class="flex items-center justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span>Solar PV Charging:</span>
                <span class="font-bold text-slate-900 dark:text-white">14.2 V (Optimal)</span>
              </div>
              <div class="flex items-center justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span>Internal Battery:</span>
                <span class="font-bold text-emerald-600 dark:text-emerald-400">94%</span>
              </div>
              <div class="flex items-center justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span>LoRa Mesh Signal:</span>
                <span class="font-mono text-slate-900 dark:text-white">+9.2 dB SNR (Strong)</span>
              </div>
              <div class="flex items-center justify-between py-1">
                <span>Telemetry Sync:</span>
                <span class="text-slate-500">4 minutes ago</span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2 pt-2">
              <button
                onClick={() => alert("Sensor calibration packet sent to Station #CS-BAR-04 via LoRaWAN")}
                class="py-2 px-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors flex items-center justify-center gap-1"
              >
                <span class="material-symbols-outlined text-sm">tune</span>
                Calibrate
              </button>
              <button
                onClick={() => alert("Exporting 30-day hourly microclimate CSV dataset")}
                class="py-2 px-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors flex items-center justify-center gap-1"
              >
                <span class="material-symbols-outlined text-sm">download</span>
                Export CSV
              </button>
            </div>
          </div>

          {/* IMD Voice Agromet Bulletin */}
          <div class="bg-gradient-to-br from-emerald-900 to-teal-950 text-white rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-emerald-400">graphic_eq</span>
              <span class="text-xs font-black uppercase tracking-wider text-emerald-300">Daily Agro-Met Audio Bulletin</span>
            </div>
            <h4 class="text-sm font-bold">Listen to Today's Advisory (Marathi &amp; Hindi)</h4>
            <p class="text-xs text-emerald-100/80 leading-relaxed">
              Curated by ICAR-CRIDA agrometeorologists for grape vine pruning, powdery mildew spray timing, and drip schedules.
            </p>

            <div class="flex items-center gap-3 pt-2">
              <button
                onClick={() => alert("Playing IMD Regional Marathi Audio Bulletin")}
                class="w-10 h-10 rounded-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 flex items-center justify-center shadow-md transition-all shrink-0"
              >
                <span class="material-symbols-outlined text-xl">play_arrow</span>
              </button>
              <div class="flex-1">
                <div class="w-full bg-white/20 h-1.5 rounded-full overflow-hidden">
                  <div class="bg-emerald-400 h-full w-1/3 rounded-full" />
                </div>
                <div class="flex justify-between text-[10px] text-emerald-200/70 mt-1">
                  <span>0:35</span>
                  <span>1:45</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Helpline Card */}
          <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2">
            <div class="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
              <span class="material-symbols-outlined text-brand-600">support_agent</span>
              IMD Kisan Weather Helpline
            </div>
            <p class="text-xs text-slate-500">Free telephonic advisory from agrometeorological field officers.</p>
            <a
              href="tel:18001801551"
              class="inline-flex items-center gap-1.5 text-xs font-bold text-brand-600 dark:text-brand-400 hover:underline pt-1"
            >
              <span class="material-symbols-outlined text-sm">call</span>
              1800-180-1551 (Toll-Free)
            </a>
          </div>
        </div>
      </div>

      {/* 7-DAY AGROMETEOROLOGICAL ADVISORY TABLE */}
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 class="text-sm font-black text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-brand-600">calendar_month</span>
              7-Day Crop Agro-Meteorological Forecast &amp; Prescriptions
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">Calculated using ECMWF 0.1° and IMD WRF numerical weather models</p>
          </div>

          <button
            onClick={() => alert("Downloading official IMD Agromet Bulletin PDF")}
            class="px-3.5 py-2 rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors flex items-center gap-1.5 shrink-0"
          >
            <span class="material-symbols-outlined text-base">picture_as_pdf</span>
            Download Official Bulletin
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-y border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <tr>
                <th class="p-3">Day / Date</th>
                <th class="p-3">Condition</th>
                <th class="p-3">Temp (Max/Min)</th>
                <th class="p-3">Rainfall</th>
                <th class="p-3">ET₀ (mm/d)</th>
                <th class="p-3">Spray Suitability</th>
                <th class="p-3">Agronomic Action Plan</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              <For each={weekForecast}>
                {day => (
                  <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                    <td class="p-3 font-bold text-slate-900 dark:text-white whitespace-nowrap">
                      {day.day}
                      <span class="block text-[11px] font-normal text-slate-400">{day.date}</span>
                    </td>
                    <td class="p-3 whitespace-nowrap">
                      <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-slate-500">{day.icon}</span>
                        <span class="text-slate-700 dark:text-slate-300">{day.condition}</span>
                      </div>
                    </td>
                    <td class="p-3 font-mono font-bold text-slate-800 dark:text-slate-200 whitespace-nowrap">
                      {day.tempMax}° / {day.tempMin}°C
                    </td>
                    <td class="p-3 whitespace-nowrap">
                      <span class="font-bold text-slate-900 dark:text-white">{day.rainMm} mm</span>
                      <span class="text-slate-400 text-[11px] ml-1">({day.rainProb}%)</span>
                    </td>
                    <td class="p-3 font-mono text-slate-700 dark:text-slate-300 whitespace-nowrap">
                      {day.et0} mm
                    </td>
                    <td class="p-3 whitespace-nowrap">
                      <span
                        class={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
                          day.spraySuitability === "optimal"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                            : day.spraySuitability === "caution"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                            : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                        }`}
                      >
                        {day.spraySuitability}
                      </span>
                    </td>
                    <td class="p-3 text-slate-700 dark:text-slate-300 font-medium">
                      {day.prescription}
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
