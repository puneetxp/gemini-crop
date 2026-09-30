import { Component, createSignal, For } from "solid-js";
import { A } from "@solidjs/router";

interface LivestockListing {
  id: string;
  tagNumber: string;
  title: string;
  species: "Murrah Buffalo" | "Gir Cow" | "Sahiwal Cow" | "Breeding Goat";
  cluster: string;
  lactation: string;
  dailyMilkYieldL: number;
  snfPercent: number;
  ageYears: number;
  weightKg: number;
  calfStatus: string;
  healthPassportVerified: boolean;
  passportDate: string;
  priceReserveInr: number;
  badge: string;
  badgeColor: string;
}

export const LivestockMarketplaceBrowse: Component = () => {
  const [selectedSpecies, setSelectedSpecies] = createSignal<string>("All");
  const [searchQuery, setSearchQuery] = createSignal("");
  const [bookingModalOpen, setBookingModalOpen] = createSignal(false);
  const [selectedAnimal, setSelectedAnimal] = createSignal<LivestockListing | null>(null);
  const [bookingSuccess, setBookingSuccess] = createSignal(false);

  const [animals] = createSignal<LivestockListing[]>([
    {
      id: "mb-1",
      tagNumber: "IN-MH-8402",
      title: "Murrah Buffalo (Lactating Elite)",
      species: "Murrah Buffalo",
      cluster: "Junnar Dairy Cluster",
      lactation: "2nd Lactation",
      dailyMilkYieldL: 22.0,
      snfPercent: 7.8,
      ageYears: 4.5,
      weightKg: 580,
      calfStatus: "Heifer at foot (21 days)",
      healthPassportVerified: true,
      passportDate: "18 Sep 2026",
      priceReserveInr: 125000,
      badge: "Verified Elite",
      badgeColor: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300",
    },
    {
      id: "gc-1",
      tagNumber: "IN-MH-4190",
      title: "Pure Gir Cow (Swarna Kapila)",
      species: "Gir Cow",
      cluster: "Baramati Agro Kendra",
      lactation: "3rd Lactation",
      dailyMilkYieldL: 16.5,
      snfPercent: 8.5,
      ageYears: 5.2,
      weightKg: 420,
      calfStatus: "Gentle Hand-Milked",
      healthPassportVerified: true,
      passportDate: "15 Sep 2026",
      priceReserveInr: 85000,
      badge: "A2 Vedic Certified",
      badgeColor: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300",
    },
    {
      id: "sw-1",
      tagNumber: "IN-MH-1082",
      title: "Sahiwal Dairy Cow (Tropical)",
      species: "Sahiwal Cow",
      cluster: "Niphad Cooperative Yard",
      lactation: "1st Lactation",
      dailyMilkYieldL: 18.0,
      snfPercent: 8.1,
      ageYears: 3.8,
      weightKg: 440,
      calfStatus: "Bull Calf (14 Days)",
      healthPassportVerified: true,
      passportDate: "20 Sep 2026",
      priceReserveInr: 92000,
      badge: "High Resistance",
      badgeColor: "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300",
    },
    {
      id: "jg-1",
      tagNumber: "IN-MH-5512",
      title: "Jamnapari Pure Breeding Doe",
      species: "Breeding Goat",
      cluster: "Sangamner Meat Cluster",
      lactation: "Twin Kidding Record",
      dailyMilkYieldL: 3.5,
      snfPercent: 9.0,
      ageYears: 2.1,
      weightKg: 68,
      calfStatus: "Twin Kids (Active)",
      healthPassportVerified: true,
      passportDate: "22 Sep 2026",
      priceReserveInr: 28000,
      badge: "High Prolificacy",
      badgeColor: "bg-purple-100 dark:bg-purple-950/60 text-purple-800 dark:text-purple-300",
    },
  ]);

  const filteredAnimals = () => {
    return animals().filter((a) => {
      const matchSpecies =
        selectedSpecies() === "All" ||
        (selectedSpecies() === "Murrah Buffalo" && a.species === "Murrah Buffalo") ||
        (selectedSpecies() === "Gir Cow" && a.species === "Gir Cow") ||
        (selectedSpecies() === "Sahiwal Cow" && a.species === "Sahiwal Cow") ||
        (selectedSpecies() === "Breeding Goat" && a.species === "Breeding Goat");

      const matchQuery =
        searchQuery() === "" ||
        a.title.toLowerCase().includes(searchQuery().toLowerCase()) ||
        a.tagNumber.toLowerCase().includes(searchQuery().toLowerCase()) ||
        a.cluster.toLowerCase().includes(searchQuery().toLowerCase());

      return matchSpecies && matchQuery;
    });
  };

  const handleOpenBooking = (animal: LivestockListing) => {
    setSelectedAnimal(animal);
    setBookingModalOpen(true);
    setBookingSuccess(false);
  };

  const handleConfirmEscrow = (e: Event) => {
    e.preventDefault();
    setBookingSuccess(true);
    setTimeout(() => {
      setBookingSuccess(false);
      setBookingModalOpen(false);
    }, 2000);
  };

  return (
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Top Header */}
      <header class="bg-[#064e3b] text-white border-b border-emerald-800/60 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex items-center justify-between h-16">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-400/30">
                <span class="material-symbols-outlined text-emerald-300 text-2xl">pets</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-base tracking-tight">CropSense AI</span>
                  <span class="text-[10px] uppercase font-bold tracking-widest bg-emerald-400/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-400/30">
                    Pashu Dhan
                  </span>
                </div>
                <p class="text-[11px] text-emerald-200/80">Livestock Trading &amp; Veterinary Escrow Exchange</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <A
                href="/livestock/hub"
                class="px-3 py-1.5 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">health_and_safety</span>
                <span>Health Radar</span>
              </A>
              <A
                href="/marketplace/bookings"
                class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <span class="material-symbols-outlined text-sm">lock_clock</span>
                <span>Escrow Bookings</span>
              </A>
            </div>
          </div>
        </div>
      </header>

      <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Breadcrumb & Action Banner */}
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div>
            <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mb-1">
              <A href="/" class="hover:text-emerald-600 transition-colors">Home</A>
              <span>/</span>
              <A href="/livestock" class="hover:text-emerald-600 transition-colors">Livestock</A>
              <span>/</span>
              <span class="font-medium text-slate-700 dark:text-slate-300">Pashu Dhan Marketplace</span>
            </div>
            <h1 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Verified Livestock &amp; Dairy Breeding Marketplace
            </h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Government e-PashuHaat certified cattle with INAHIS RFID passports and 7-day milk yield escrow warranty
            </p>
          </div>

          <div class="flex items-center gap-2">
            <A
              href="/marketplace/bookings"
              class="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-base">add_circle</span>
              <span>List Animal for Sale</span>
            </A>
          </div>
        </div>

        {/* 4 Summary KPI Ribbon */}
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Active Listings</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">pets</span>
            </div>
            <div class="text-2xl font-black text-slate-900 dark:text-white">842 Animals</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">100% INAHIS RFID Tagged</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Average Milk Yield</span>
              <span class="material-symbols-outlined text-blue-600 text-lg">water_drop</span>
            </div>
            <div class="text-2xl font-black text-blue-700 dark:text-blue-400">16.4 L/Day</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">Certified 3-Day Milking Test</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Escrow Value Protected</span>
              <span class="material-symbols-outlined text-emerald-600 text-lg">verified_user</span>
            </div>
            <div class="text-2xl font-black text-emerald-800 dark:text-emerald-300">₹1.48 Cr</div>
            <div class="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold">Zero Default Escrow Guarantee</div>
          </div>

          <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400">Vet Clearance Rate</span>
              <span class="material-symbols-outlined text-purple-600 text-lg">medical_services</span>
            </div>
            <div class="text-2xl font-black text-purple-700 dark:text-purple-400">99.4%</div>
            <div class="text-[11px] text-slate-500 dark:text-slate-400">FMD &amp; Brucellosis Tested</div>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div class="flex flex-wrap items-center gap-2 text-xs">
            {["All", "Murrah Buffalo", "Gir Cow", "Sahiwal Cow", "Breeding Goat"].map((species) => (
              <button
                onClick={() => setSelectedSpecies(species)}
                class={`px-3.5 py-1.5 rounded-xl font-bold transition-all ${
                  selectedSpecies() === species
                    ? "bg-emerald-700 text-white shadow-sm"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                {species === "All" ? "All Species (842)" : species}
              </button>
            ))}
          </div>

          <div class="flex items-center gap-2">
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-sm">search</span>
              <input
                type="text"
                value={searchQuery()}
                onInput={(e) => setSearchQuery(e.currentTarget.value)}
                placeholder="Search Tag ID, Breed, or Mandi..."
                class="pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-emerald-600 w-56"
              />
            </div>
          </div>
        </div>

        {/* Animal Listings Grid */}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <For each={filteredAnimals()}>
            {(animal) => (
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 overflow-hidden shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
                <div class="p-5 space-y-4">
                  <div class="flex items-start justify-between">
                    <div>
                      <div class="flex items-center gap-1.5">
                        <span class={`px-2 py-0.5 rounded-full text-[10px] font-bold ${animal.badgeColor}`}>
                          {animal.badge}
                        </span>
                        <span class="text-[10px] text-slate-400 font-mono">TAG #{animal.tagNumber}</span>
                      </div>
                      <h3 class="font-black text-lg text-slate-900 dark:text-white mt-1">{animal.title}</h3>
                      <p class="text-xs text-slate-500 dark:text-slate-400">{animal.cluster} • {animal.lactation}</p>
                    </div>
                    <div class="text-right">
                      <div class="text-xl font-black text-emerald-700 dark:text-emerald-400">
                        ₹{animal.priceReserveInr.toLocaleString("en-IN")}
                      </div>
                      <div class="text-[10px] text-slate-400">Escrow Reserve</div>
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-2 text-xs py-2 bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                    <div>
                      <span class="text-slate-400 text-[10px] block">Daily Milk Yield:</span>
                      <span class="font-bold text-slate-800 dark:text-slate-200">{animal.dailyMilkYieldL} L/Day</span>
                    </div>
                    <div>
                      <span class="text-slate-400 text-[10px] block">Fat Content:</span>
                      <span class="font-bold text-slate-800 dark:text-slate-200">{animal.snfPercent}% SNF</span>
                    </div>
                    <div>
                      <span class="text-slate-400 text-[10px] block">Age &amp; Weight:</span>
                      <span class="font-bold text-slate-800 dark:text-slate-200">{animal.ageYears} Yrs • {animal.weightKg} Kg</span>
                    </div>
                    <div>
                      <span class="text-slate-400 text-[10px] block">Calf Status:</span>
                      <span class="font-bold text-emerald-700 dark:text-emerald-400">{animal.calfStatus}</span>
                    </div>
                  </div>

                  <div class="flex items-center gap-2 text-[11px] text-emerald-800 dark:text-emerald-300 bg-emerald-50/60 dark:bg-emerald-950/40 p-2.5 rounded-xl border border-emerald-100 dark:border-emerald-800">
                    <span class="material-symbols-outlined text-emerald-600 text-base">verified</span>
                    <span>INAHIS RFID passport &amp; FMD booster verified on {animal.passportDate}</span>
                  </div>
                </div>

                <div class="p-4 bg-slate-50/80 dark:bg-slate-800/80 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
                  <button
                    onClick={() => handleOpenBooking(animal)}
                    class="flex-1 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow transition-all flex items-center justify-center gap-1.5"
                  >
                    <span class="material-symbols-outlined text-sm">lock</span>
                    <span>Lock Animal Escrow</span>
                  </button>
                  <A
                    href="/livestock/doctors"
                    class="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 text-xs font-bold"
                    title="Request Vet Inspection"
                  >
                    <span class="material-symbols-outlined text-sm">stethoscope</span>
                  </A>
                </div>
              </div>
            )}
          </For>
        </div>
      </main>

      {/* Escrow Booking Modal */}
      {bookingModalOpen() && selectedAnimal() && (
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-emerald-600">lock</span>
                <h3 class="font-black text-lg text-slate-900 dark:text-white">Escrow Purchase Guarantee</h3>
              </div>
              <button
                onClick={() => setBookingModalOpen(false)}
                class="text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            {bookingSuccess() ? (
              <div class="p-6 text-center space-y-2">
                <span class="material-symbols-outlined text-emerald-500 text-4xl">check_circle</span>
                <h4 class="font-bold text-slate-900 dark:text-white text-base">Escrow Lock Confirmed!</h4>
                <p class="text-xs text-slate-500">
                  Animal #{selectedAnimal()?.tagNumber} reserved. A certified ICAR veterinary officer will inspect within 48 hours before fund release.
                </p>
              </div>
            ) : (
              <form onSubmit={handleConfirmEscrow} class="space-y-4 text-xs">
                <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl space-y-1 border border-slate-200 dark:border-slate-700">
                  <div class="font-bold text-slate-900 dark:text-white text-sm">{selectedAnimal()?.title}</div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400">
                    Tag: {selectedAnimal()?.tagNumber} • {selectedAnimal()?.cluster}
                  </div>
                  <div class="text-base font-black text-emerald-700 dark:text-emerald-400 pt-1">
                    Total Amount: ₹{selectedAnimal()?.priceReserveInr.toLocaleString("en-IN")}
                  </div>
                </div>

                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Escrow Booking Deposit (10% Required)
                  </label>
                  <input
                    type="text"
                    disabled
                    value={`₹${((selectedAnimal()?.priceReserveInr || 0) * 0.1).toLocaleString("en-IN")}`}
                    class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-mono font-bold"
                  />
                </div>

                <div>
                  <label class="block font-bold text-slate-700 dark:text-slate-300 mb-1">Delivery / Mandi Pickup Point</label>
                  <select class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white">
                    <option>On-Farm Inspection &amp; Direct Transport (Junnar)</option>
                    <option>Pune Gultekdi Livestock Transit Yard</option>
                    <option>Baramati Animal Fairground Hub</option>
                  </select>
                </div>

                <div class="p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-200 dark:border-emerald-800 text-[11px] text-emerald-800 dark:text-emerald-300">
                  🛡️ <strong>7-Day Milk Warranty</strong>: If average daily milk yield falls &gt;15% below certified 22L/day during the 7-day observation period, full escrow deposit is automatically refunded.
                </div>

                <div class="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setBookingModalOpen(false)}
                    class="px-4 py-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="px-5 py-2 bg-emerald-700 hover:bg-emerald-600 text-white font-bold rounded-xl shadow"
                  >
                    Deposit Escrow &amp; Lock
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
export default LivestockMarketplaceBrowse;
