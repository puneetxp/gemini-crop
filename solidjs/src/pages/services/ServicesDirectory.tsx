import { Component, createSignal, For, Show } from "solid-js";
import { A } from "@solidjs/router";

interface ServiceItem {
  id: string;
  name: string;
  category: "drone" | "machinery" | "soil" | "storage" | "scheme";
  provider: string;
  location: string;
  rating: number;
  reviewCount: number;
  rate: string;
  unit: string;
  subsidyEligible: boolean;
  subsidyAmount?: string;
  availability: string;
  specs: string[];
  imageUrl: string;
}

export const ServicesDirectory: Component = () => {
  const [activeCategory, setActiveCategory] = createSignal<string>("all");
  const [searchQuery, setSearchQuery] = createSignal("");
  const [selectedServiceForBooking, setSelectedServiceForBooking] = createSignal<ServiceItem | null>(null);
  const [bookingSuccess, setBookingSuccess] = createSignal(false);

  // Booking Form State
  const [targetPlot, setTargetPlot] = createSignal("Krishna Valley Plot A (4.2 Acres Grapes)");
  const [acresToServe, setAcresToServe] = createSignal(4.2);
  const [preferredSlot, setPreferredSlot] = createSignal("Tomorrow Morning (06:30 AM - 09:30 AM)");

  const services: ServiceItem[] = [
    {
      id: "srv-drone-1",
      name: "Garuda Kisan Drone Spraying (Fungicide / Nano-Urea)",
      category: "drone",
      provider: "Garuda Aerospace & Sahyadri FPO",
      location: "Pimpalgaon Hub (3.5 km)",
      rating: 4.9,
      reviewCount: 164,
      rate: "₹350",
      unit: "per acre",
      subsidyEligible: true,
      subsidyAmount: "50% SMAM Subsidy (Net ₹175/ac)",
      availability: "Available Tomorrow",
      specs: ["DGCA Certified Pilot #DGCA-AG-8091", "10-Liter Precision Tank", "Ultra-fine Centrifugal Atomizer", "Centimeter-accurate RTK GPS"],
      imageUrl: "https://images.unsplash.com/photo-1527977966376-1c8408f9f108?w=300&auto=format&fit=crop&q=80"
    },
    {
      id: "srv-harvester-1",
      name: "Preet 987 Track Combine Harvester with SMS",
      category: "machinery",
      provider: "Kisan Custom Hiring Center (CHC)",
      location: "Niphad Mandi (6.2 km)",
      rating: 4.85,
      reviewCount: 92,
      rate: "₹1,800",
      unit: "per hour (Diesel & Operator incl.)",
      subsidyEligible: true,
      subsidyAmount: "CHC Subsidized Rate",
      availability: "2 Units Ready",
      specs: ["Fitted with Straw Management System (SMS)", "Paddy, Wheat & Soybean Capable", "Rubber Track for Wet Soil Transit", "Fuel & Skilled Driver Included"],
      imageUrl: "https://images.unsplash.com/photo-1589923188900-85dae523342b?w=300&auto=format&fit=crop&q=80"
    },
    {
      id: "srv-laser-1",
      name: "Trimble GPS Guided Laser Land Leveler",
      category: "machinery",
      provider: "AgroTech Precision Engineering",
      location: "Nashik Rural (9.8 km)",
      rating: 4.92,
      reviewCount: 78,
      rate: "₹900",
      unit: "per acre",
      subsidyEligible: false,
      availability: "Booking Open (2 Days Advance)",
      specs: ["8-foot Dual Hydraulic Blade", "Saves 25-30% Irrigation Water", "Increases Fertilizer Uniformity by 18%", "Twin Transmitter System"],
      imageUrl: "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=300&auto=format&fit=crop&q=80"
    },
    {
      id: "srv-soil-1",
      name: "Mobile Soil Testing Van & ICAR Soil Health Card",
      category: "soil",
      provider: "ICAR KVK Mobile Soil Laboratory",
      location: "Doorstep Farmgate Service",
      rating: 4.95,
      reviewCount: 310,
      rate: "₹250",
      unit: "per soil sample",
      subsidyEligible: true,
      subsidyAmount: "Govt Soil Health Scheme",
      availability: "Same-Day Testing",
      specs: ["12 Parameters (N, P, K, pH, EC, OC, Zn, Fe, Cu, Mn, B, S)", "Spectrophotometer Analysis in Van", "Digital Report Delivered in 2 Hours", "Custom Fertilizer Dose Calculation"],
      imageUrl: "https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=300&auto=format&fit=crop&q=80"
    },
    {
      id: "srv-storage-1",
      name: "Reefer Solar Cold Storage Chamber (2°C to 8°C)",
      category: "storage",
      provider: "Pimpalgaon APMC Cold Chain Ltd",
      location: "Pimpalgaon Baswant (4.0 km)",
      rating: 4.88,
      reviewCount: 120,
      rate: "₹1.20",
      unit: "per kg / month",
      subsidyEligible: false,
      availability: "10 MT Chamber Space Open",
      specs: ["Solar PV Powered + Diesel Generator Backup", "Ethylene Scrubber for Grapes & Pomegranates", "Humidity Regulated at 90-95% RH", "Warehouse Receipt Loan Eligible"],
      imageUrl: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=300&auto=format&fit=crop&q=80"
    },
    {
      id: "srv-drone-bat-1",
      name: "Fast-Charge Drone Battery Rental & Generator Kit",
      category: "drone",
      provider: "Kisan Drone Hub Niphad",
      location: "Niphad (5.5 km)",
      rating: 4.75,
      reviewCount: 45,
      rate: "₹450",
      unit: "per day",
      subsidyEligible: false,
      availability: "In Stock (6 Sets)",
      specs: ["3x 16,000 mAh 6S Smart LiPo Batteries", "2400W Fast Field Charger", "20-minute Full Charge Cycle", "Heavy-Duty Weatherproof Case"],
      imageUrl: "https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=300&auto=format&fit=crop&q=80"
    }
  ];

  const filteredServices = () => {
    return services.filter(srv => {
      const matchesSearch =
        srv.name.toLowerCase().includes(searchQuery().toLowerCase()) ||
        srv.provider.toLowerCase().includes(searchQuery().toLowerCase()) ||
        srv.location.toLowerCase().includes(searchQuery().toLowerCase());

      const matchesCat = activeCategory() === "all" || srv.category === activeCategory();

      return matchesSearch && matchesCat;
    });
  };

  const handleBookingSubmit = (e: Event) => {
    e.preventDefault();
    setBookingSuccess(true);
    setTimeout(() => {
      setBookingSuccess(false);
      setSelectedServiceForBooking(null);
    }, 2800);
  };

  return (
    <div class="space-y-6">
      {/* Header & Breadcrumb */}
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
            <A href="/dashboard" class="hover:underline">Home</A>
            <span>/</span>
            <A href="/menu" class="hover:underline">All Services</A>
            <span>/</span>
            <span class="text-brand-600 dark:text-brand-400 font-medium">Services Directory</span>
          </div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <span class="material-symbols-outlined text-brand-600 text-3xl">precision_manufacturing</span>
            Agricultural Services &amp; Machinery Rental Hub
          </h1>
          <p class="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
            Custom Hiring Center (CHC) equipment, DGCA certified drone spraying, soil testing vans, and DBT government subsidy booking.
          </p>
        </div>

        {/* Quick Stats Pill */}
        <div class="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 px-3.5 py-2 rounded-xl text-emerald-800 dark:text-emerald-300 text-xs font-semibold">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>28 Machinery Units Available in 10 km</span>
        </div>
      </div>

      {/* PROMINENT GOVERNMENT SUBSIDY & SCHEME ASSISTANT BANNER */}
      <div class="rounded-2xl bg-gradient-to-r from-emerald-800 via-teal-800 to-slate-900 text-white p-5 shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4 border border-emerald-700/40">
        <div class="relative z-10 flex items-start gap-3.5">
          <div class="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/30">
            <span class="material-symbols-outlined text-2xl text-emerald-300">account_balance</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-black uppercase tracking-wider bg-emerald-500/30 px-2 py-0.5 rounded-full border border-emerald-400/30">
                DBT Govt Linked #SMAM-MH-2024
              </span>
              <span class="text-xs font-medium text-emerald-200">Sub-Mission on Agricultural Mechanization</span>
            </div>
            <h3 class="text-lg font-black mt-1">Up to 50% Direct Subsidy on Drone Spraying &amp; CHC Rentals</h3>
            <p class="text-xs text-emerald-100/90 mt-0.5 max-w-2xl leading-relaxed">
              Eligible small &amp; marginal farmers and women farmers receive 50% instant reimbursement credited directly to their Aadhaar-linked bank account.
            </p>
          </div>
        </div>

        <div class="relative z-10 flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => alert("Checking PM-KISAN Aadhaar DBT eligibility for User #MH-LIV-409...")}
            class="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs shadow-md transition-all flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-base">verified</span>
            Check Subsidy Eligibility
          </button>
        </div>
      </div>

      {/* SEARCH & CATEGORY FILTERS */}
      <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
        <div class="flex flex-col md:flex-row md:items-center gap-3">
          <div class="relative flex-1">
            <span class="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-lg">search</span>
            <input
              type="text"
              placeholder="Search machinery (Harvester, Laser Leveler, Drone, Soil Van...)"
              value={searchQuery()}
              onInput={e => setSearchQuery(e.currentTarget.value)}
              class="w-full text-xs pl-9 pr-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div class="flex items-center gap-2 text-xs text-slate-500 shrink-0">
            <span class="material-symbols-outlined text-base">near_me</span>
            <span>Radius: <strong>Within 15 km</strong></span>
          </div>
        </div>

        {/* Filter Pills */}
        <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <button
            onClick={() => setActiveCategory("all")}
            class={`px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap transition-all ${
              activeCategory() === "all"
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
            }`}
          >
            All Services ({services.length})
          </button>
          <button
            onClick={() => setActiveCategory("drone")}
            class={`px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap transition-all ${
              activeCategory() === "drone"
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
            }`}
          >
            Drone Spraying (DGCA)
          </button>
          <button
            onClick={() => setActiveCategory("machinery")}
            class={`px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap transition-all ${
              activeCategory() === "machinery"
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
            }`}
          >
            Heavy Machinery &amp; CHC
          </button>
          <button
            onClick={() => setActiveCategory("soil")}
            class={`px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap transition-all ${
              activeCategory() === "soil"
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
            }`}
          >
            Mobile Soil Lab
          </button>
          <button
            onClick={() => setActiveCategory("storage")}
            class={`px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap transition-all ${
              activeCategory() === "storage"
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
            }`}
          >
            Cold Storage
          </button>
        </div>
      </div>

      {/* SERVICES GRID */}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <For each={filteredServices()}>
          {srv => (
            <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
              <div>
                {/* Image Banner */}
                <div class="relative h-44 w-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <img
                    src={srv.imageUrl}
                    alt={srv.name}
                    class="w-full h-full object-cover group-hover:scale-105 transition-all"
                  />
                  <div class="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent" />
                  <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white">
                    <span class="text-xs font-bold drop-shadow-md">{srv.provider}</span>
                    <span class="text-[10px] font-semibold bg-slate-900/80 backdrop-blur-md px-2 py-0.5 rounded-full border border-white/20">
                      {srv.location}
                    </span>
                  </div>
                  {srv.subsidyEligible && (
                    <span class="absolute top-3 left-3 text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-amber-500 text-white shadow-sm">
                      Govt Subsidized
                    </span>
                  )}
                </div>

                {/* Card Content */}
                <div class="p-4 space-y-3">
                  <div class="flex items-start justify-between gap-2">
                    <h3 class="text-sm font-black text-slate-900 dark:text-white">{srv.name}</h3>
                    <div class="flex items-center gap-0.5 text-xs text-amber-500 font-bold shrink-0">
                      <span class="material-symbols-outlined text-xs">star</span>
                      <span>{srv.rating}</span>
                      <span class="text-[10px] text-slate-400 font-normal">({srv.reviewCount})</span>
                    </div>
                  </div>

                  {/* Specs List */}
                  <ul class="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                    <For each={srv.specs}>
                      {spec => (
                        <li class="flex items-center gap-1.5">
                          <span class="material-symbols-outlined text-emerald-500 text-sm">check</span>
                          <span class="truncate">{spec}</span>
                        </li>
                      )}
                    </For>
                  </ul>

                  {/* Pricing & Availability */}
                  <div class="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
                    <div>
                      <span class="text-[10px] text-slate-400 uppercase font-semibold block">Rental Rate</span>
                      <span class="text-base font-black text-slate-900 dark:text-white">{srv.rate}</span>
                      <span class="text-[10px] text-slate-500 ml-1">{srv.unit}</span>
                    </div>
                    <span class="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                      {srv.availability}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div class="p-4 pt-0">
                <button
                  onClick={() => setSelectedServiceForBooking(srv)}
                  class="w-full py-2.5 rounded-xl text-xs font-black bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-all flex items-center justify-center gap-1.5"
                >
                  <span class="material-symbols-outlined text-sm">calendar_month</span>
                  Book Service Now
                </button>
              </div>
            </div>
          )}
        </For>
      </div>

      {/* BOOKING MODAL */}
      <Show when={selectedServiceForBooking()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm">
          <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 class="text-base font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-brand-600">calendar_month</span>
                  Book Equipment / Service
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">{selectedServiceForBooking()?.name}</p>
              </div>
              <button
                onClick={() => setSelectedServiceForBooking(null)}
                class="p-1 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            {bookingSuccess() ? (
              <div class="py-8 text-center space-y-2">
                <span class="material-symbols-outlined text-5xl text-emerald-500 animate-bounce">check_circle</span>
                <h4 class="text-base font-black text-slate-900 dark:text-white">Booking Confirmed!</h4>
                <p class="text-xs text-slate-500">
                  CHC Hub operator dispatched. Direct token sent via SMS &amp; WhatsApp.
                </p>
              </div>
            ) : (
              <form onSubmit={handleBookingSubmit} class="space-y-4 text-xs">
                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Target Farm Plot</label>
                  <select
                    value={targetPlot()}
                    onChange={e => setTargetPlot(e.currentTarget.value)}
                    class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="Krishna Valley Plot A (4.2 Acres Grapes)">Krishna Valley Plot A (4.2 Acres Grapes)</option>
                    <option value="Niphad Onion Farm Plot B (6.0 Acres)">Niphad Onion Farm Plot B (6.0 Acres)</option>
                    <option value="Karnal Basmati Plot C (8.5 Acres)">Karnal Basmati Plot C (8.5 Acres)</option>
                  </select>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Acreage / Quantity</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      step="0.5"
                      value={acresToServe()}
                      onInput={e => setAcresToServe(+e.currentTarget.value || 1)}
                      class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <div>
                    <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Time Slot</label>
                    <select
                      value={preferredSlot()}
                      onChange={e => setPreferredSlot(e.currentTarget.value)}
                      class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="Tomorrow Morning (06:30 AM - 09:30 AM)">Tomorrow Morning (06:30 AM)</option>
                      <option value="Tomorrow Afternoon (03:30 PM - 06:30 PM)">Tomorrow Afternoon (03:30 PM)</option>
                      <option value="Day After Tomorrow Morning">Day After Tomorrow Morning</option>
                    </select>
                  </div>
                </div>

                {/* Escrow Guarantee Note */}
                <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1">
                  <div class="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-bold">
                    <span class="material-symbols-outlined text-sm">lock</span>
                    CropSense Escrow Protection
                  </div>
                  <p class="text-[11px] text-slate-500 leading-relaxed">
                    Advance is held securely in escrow and released to the CHC hub only upon GPS verification of completed field service.
                  </p>
                </div>

                <div class="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                  <div>
                    <span class="text-[10px] text-slate-400 uppercase font-semibold block">Total Estimated</span>
                    <strong class="text-sm text-slate-900 dark:text-white">
                      ₹{(acresToServe() * 350).toLocaleString("en-IN")}
                    </strong>
                  </div>

                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedServiceForBooking(null)}
                      class="px-3 py-2 rounded-xl text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      class="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-black shadow-sm transition-all"
                    >
                      Confirm Booking
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      </Show>
    </div>
  );
};
