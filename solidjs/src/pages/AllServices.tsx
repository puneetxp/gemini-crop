import { Component, createSignal, createMemo, For } from "solid-js";
import { A } from "@solidjs/router";

interface AgriService {
  id: string;
  title: string;
  category: "crops" | "soil" | "livestock" | "market" | "finance" | "community";
  icon: string;
  tag: string;
  tagColor: string;
  description: string;
  route: string;
  actionText: string;
  isExternal?: boolean;
}

const SERVICES: AgriService[] = [
  {
    id: "farm-plots",
    title: "Field & Crop Management",
    category: "crops",
    icon: "agriculture",
    tag: "Geo-Tagged",
    tagColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
    description: "Cadastral plot boundaries, GPS soil tagging, sowing timeline tracker, and acreage analytics.",
    route: "/farm",
    actionText: "Open Plots"
  },
  {
    id: "crop-doctor",
    title: "AI Crop Diagnosis",
    category: "crops",
    icon: "psychiatry",
    tag: "Vision AI",
    tagColor: "bg-purple-50 text-purple-800 border-purple-200",
    description: "Instant foliar disease scanning with Vision AI, lesion segmentation, and ICAR treatment plans.",
    route: "/diagnose",
    actionText: "Launch Scanner"
  },
  {
    id: "satellite-ndvi",
    title: "Satellite NDVI Health",
    category: "soil",
    icon: "satellite_alt",
    tag: "10m Spatial",
    tagColor: "bg-blue-50 text-blue-800 border-blue-200",
    description: "Sentinel-2 multispectral NDVI/NDMI vegetation indices, moisture gradients, and drone imagery sync.",
    route: "/soil/hub",
    actionText: "View Satellite"
  },
  {
    id: "soil-fertigation",
    title: "Soil Moisture & Fertilizer Hub",
    category: "soil",
    icon: "water_drop",
    tag: "LoRaWAN Live",
    tagColor: "bg-teal-50 text-teal-800 border-teal-200",
    description: "Dual-depth capacitive probe data, certified NPK soil health card matrix, and drip fertigation scheduler.",
    route: "/soil/hub",
    actionText: "Soil Telemetry"
  },
  {
    id: "pashu-hub",
    title: "Pashu Care Livestock",
    category: "livestock",
    icon: "pets",
    tag: "RFID Tagged",
    tagColor: "bg-amber-50 text-amber-900 border-amber-200",
    description: "IoT smart collar telemetry, lactation pacing, ICAR diet formulation, and FMD vaccination tracking.",
    route: "/livestock",
    actionText: "Open Pashu Hub"
  },
  {
    id: "equipment-booking",
    title: "Agri-Equipment & Drone Booking",
    category: "market",
    icon: "precision_manufacturing",
    tag: "CHC Subsidized",
    tagColor: "bg-orange-50 text-orange-800 border-orange-200",
    description: "Custom hiring center (CHC) booking for tractors, combine harvesters, and autonomous drone spraying.",
    route: "/marketplace",
    actionText: "Book Machinery"
  },
  {
    id: "harvest-transport",
    title: "Harvest Logistics & Transport",
    category: "market",
    icon: "local_shipping",
    tag: "Cold Chain",
    tagColor: "bg-indigo-50 text-indigo-800 border-indigo-200",
    description: "GPS-tracked farm-to-mandi transport, 10-ton reefer trucks, e-way bill generation, and slot booking.",
    route: "/marketplace",
    actionText: "Book Transport"
  },
  {
    id: "mandi-rates",
    title: "Live Mandi Commodity Rates",
    category: "market",
    icon: "storefront",
    tag: "APMC Realtime",
    tagColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
    description: "Live spot rates across Nashik, Vashi, and Pune mandis with 7-day MSP price rally forecasts.",
    route: "/marketplace",
    actionText: "Track Rates"
  },
  {
    id: "weather-radar",
    title: "Hyperlocal Weather & Spray Advisory",
    category: "crops",
    icon: "partly_cloudy_day",
    tag: "IMD Radar",
    tagColor: "bg-sky-50 text-sky-800 border-sky-200",
    description: "Microclimate forecasting, 48-hour rainfall radar alerts, and pesticide spray window recommendations.",
    route: "/dashboard",
    actionText: "View Weather"
  },
  {
    id: "voice-assistant",
    title: "Voice Agro Assistant",
    category: "community",
    icon: "mic",
    tag: "Multilingual",
    tagColor: "bg-rose-50 text-rose-800 border-rose-200",
    description: "Hands-free voice consultation in Hindi, Marathi, and English for low-literacy field queries.",
    route: "/assistant",
    actionText: "Talk to Assistant"
  },
  {
    id: "community-forum",
    title: "Kisan Community Forum",
    category: "community",
    icon: "forum",
    tag: "KVK Verified",
    tagColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
    description: "Direct Q&A with agricultural scientists, Krishi Vigyan Kendra agronomists, and local peer farmers.",
    route: "/assistant",
    actionText: "Join Community"
  },
  {
    id: "pm-kisan-schemes",
    title: "PM-KISAN & Govt Subsidies",
    category: "finance",
    icon: "account_balance",
    tag: "Direct DBT",
    tagColor: "bg-amber-50 text-amber-900 border-amber-200",
    description: "Kisan Credit Card (KCC) assistance, drip irrigation subsidies, and PMFBY crop insurance filing.",
    route: "/settings",
    actionText: "View Schemes"
  },
  {
    id: "quota-tracker",
    title: "AI Token & Quota Tracker",
    category: "finance",
    icon: "bolt",
    tag: "Active Plan",
    tagColor: "bg-violet-50 text-violet-800 border-violet-200",
    description: "Daily and seasonal multimodal vision and agronomic inference quota monitor with recharge options.",
    route: "/quota/history",
    actionText: "Manage Quota"
  },
  {
    id: "emergency-helpline",
    title: "24x7 Emergency Agro Helpline",
    category: "community",
    icon: "phone_in_talk",
    tag: "Toll-Free",
    tagColor: "bg-red-50 text-red-800 border-red-200",
    description: "Direct one-touch phone bridge to KVK veterinary surgeons, crop doctors, and government helplines.",
    route: "tel:18001801551",
    actionText: "Call 1800-180-1551",
    isExternal: true
  }
];

export const AllServices: Component = () => {
  const [searchQuery, setSearchQuery] = createSignal("");
  const [selectedCategory, setSelectedCategory] = createSignal<string>("all");

  const categories = [
    { id: "all", label: "All Services (14)" },
    { id: "crops", label: "Crop Health & AI (3)" },
    { id: "soil", label: "Soil & Satellite (2)" },
    { id: "livestock", label: "Livestock & Pashu (1)" },
    { id: "market", label: "Marketplace & Transport (3)" },
    { id: "finance", label: "Govt & Finance (2)" },
    { id: "community", label: "Community & Helpline (3)" }
  ];

  const filteredServices = createMemo(() => {
    const q = searchQuery().toLowerCase().trim();
    const cat = selectedCategory();

    return SERVICES.filter((service) => {
      const matchesCat = cat === "all" || service.category === cat;
      const matchesQuery =
        q === "" ||
        service.title.toLowerCase().includes(q) ||
        service.description.toLowerCase().includes(q) ||
        service.tag.toLowerCase().includes(q);
      return matchesCat && matchesQuery;
    });
  });

  return (
    <div class="space-y-6">
      {/* Header and Search */}
      <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-1">
            <span class="material-symbols-outlined text-base">apps</span>
            <span>Agricultural Directory</span>
          </div>
          <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">
            Agri-Services &amp; Intelligence Hub
          </h1>
          <p class="text-xs text-slate-500 mt-1 max-w-xl">
            Access ICAR-compliant telemetric tools, multimodal AI diagnostics, and precision farming utilities.
          </p>
        </div>

        {/* Live Search Input */}
        <div class="relative w-full md:w-80">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">
            search
          </span>
          <input
            type="text"
            value={searchQuery()}
            onInput={(e) => setSearchQuery(e.currentTarget.value)}
            placeholder="Search tools, equipment, mandi..."
            class="w-full pl-9 pr-16 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-forest focus:ring-2 focus:ring-forest/20 transition-all"
          />
          {searchQuery() && (
            <button
              onClick={() => setSearchQuery("")}
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Telemetry Summary Banner */}
      <section class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <div class="p-4 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">Plots Monitored</span>
            <span class="w-8 h-8 rounded-xl bg-emerald-50 text-forest flex items-center justify-center">
              <span class="material-symbols-outlined text-base">grid_view</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-forest">3 Active Plots</span>
            <p class="text-[11px] text-slate-400 mt-0.5">18.5 Acres Total</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">Satellite Overpass</span>
            <span class="w-8 h-8 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">satellite_alt</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-sky-900">In 18 hrs</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Sentinel-2 Multispectral</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-white border border-emerald-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-500">AI Daily Quota</span>
            <span class="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">neurology</span>
            </span>
          </div>
          <div>
            <span class="text-xl font-extrabold text-purple-900">42/50 Remaining</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Multimodal Vision AI</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-white border border-amber-200/80 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-amber-700">KVK Agro Advisory</span>
            <span class="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
              <span class="material-symbols-outlined text-base">warning</span>
            </span>
          </div>
          <div>
            <span class="text-base font-extrabold text-amber-900">Fall Armyworm Watch</span>
            <p class="text-[11px] text-amber-700 mt-0.5">&lt;5km radius active alert</p>
          </div>
        </div>
      </section>

      {/* Category Filter Chips */}
      <div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <For each={categories}>
          {(cat) => (
            <button
              onClick={() => setSelectedCategory(cat.id)}
              class={`px-3.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${
                selectedCategory() === cat.id
                  ? "bg-forest text-white border-forest shadow-sm"
                  : "bg-white text-slate-600 border-slate-200 hover:border-forest/40 hover:text-forest"
              }`}
            >
              {cat.label}
            </button>
          )}
        </For>
      </div>

      {/* Services Grid (14 Cards) */}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <For each={filteredServices()}>
          {(service) => (
            <div class="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-forest/30 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group">
              <div>
                <div class="flex items-start justify-between gap-3 mb-3">
                  <div class="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center text-forest group-hover:bg-emerald-50 transition-colors">
                    <span class="material-symbols-outlined text-xl">{service.icon}</span>
                  </div>
                  <span class={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${service.tagColor}`}>
                    {service.tag}
                  </span>
                </div>

                <h3 class="text-sm font-bold text-slate-900 group-hover:text-forest transition-colors">
                  {service.title}
                </h3>
                <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                  {service.description}
                </p>
              </div>

              <div class="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
                {service.isExternal ? (
                  <a
                    href={service.route}
                    class="w-full text-center px-3 py-2 bg-red-50 hover:bg-red-100 text-red-800 border border-red-200 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                  >
                    <span class="material-symbols-outlined text-sm">call</span>
                    <span>{service.actionText}</span>
                  </a>
                ) : (
                  <A
                    href={service.route}
                    class="w-full text-center px-3 py-2 bg-slate-50 hover:bg-forest hover:text-white text-slate-700 border border-slate-200 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 group-hover:border-forest"
                  >
                    <span>{service.actionText}</span>
                    <span class="material-symbols-outlined text-xs">arrow_forward</span>
                  </A>
                )}
              </div>
            </div>
          )}
        </For>
      </div>

      {filteredServices().length === 0 && (
        <div class="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-300">
          <span class="material-symbols-outlined text-4xl text-slate-300 mb-2">search_off</span>
          <p class="text-sm font-bold text-slate-700">No matching services found</p>
          <p class="text-xs text-slate-400 mt-1">Try searching for keywords like &ldquo;drone&rdquo;, &ldquo;soil&rdquo;, or &ldquo;mandi&rdquo;</p>
          <button
            onClick={() => {
              setSearchQuery("");
              setSelectedCategory("all");
            }}
            class="mt-4 px-4 py-1.5 bg-forest text-white rounded-xl text-xs font-bold shadow-sm"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
};
