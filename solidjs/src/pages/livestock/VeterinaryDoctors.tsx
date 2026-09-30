import { Component, createSignal, For, Show } from "solid-js";
import { A } from "@solidjs/router";

interface VetDoctor {
  id: string;
  name: string;
  qualifications: string;
  specialty: string;
  experienceYears: number;
  rating: number;
  reviewCount: number;
  vciRegNumber: string;
  district: string;
  state: string;
  consultationFee: number;
  visitFee: number;
  isAvailableNow: boolean;
  offersHomeVisit: boolean;
  languages: string[];
  avatarUrl: string;
}

interface PrescriptionRecord {
  id: string;
  bovineTag: string;
  animalName: string;
  doctorName: string;
  date: string;
  diagnosis: string;
  medicines: string[];
  withdrawalPeriodDays: number;
  pdfUrl: string;
}

export const VeterinaryDoctors: Component = () => {
  const [searchQuery, setSearchQuery] = createSignal("");
  const [selectedSpecialty, setSelectedSpecialty] = createSignal("all");
  const [availabilityFilter, setAvailabilityFilter] = createSignal<"all" | "online" | "visit">("all");
  const [selectedDoctorForBooking, setSelectedDoctorForBooking] = createSignal<VetDoctor | null>(null);
  const [bookingSuccess, setBookingSuccess] = createSignal(false);
  const [activeTab, setActiveTab] = createSignal<"doctors" | "prescriptions">("doctors");

  // Booking Form State
  const [bovineTagInput, setBovineTagInput] = createSignal("1002-8812-4019 (Lakshmi)");
  const [symptomDescription, setSymptomDescription] = createSignal("");
  const [bookingType, setBookingType] = createSignal<"video" | "visit">("video");
  const [selectedSlot, setSelectedSlot] = createSignal("Today, 02:30 PM");

  const doctors: VetDoctor[] = [
    {
      id: "doc-1",
      name: "Dr. Rajesh Patil",
      qualifications: "MVSc (Animal Reproduction & Gynaecology), NDRI Gold Medalist",
      specialty: "obstetrics",
      experienceYears: 14,
      rating: 4.9,
      reviewCount: 182,
      vciRegNumber: "VCI-MH-2010-0491",
      district: "Nashik / Niphad",
      state: "Maharashtra",
      consultationFee: 300,
      visitFee: 800,
      isAvailableNow: true,
      offersHomeVisit: true,
      languages: ["Marathi", "Hindi", "English"],
      avatarUrl: "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80"
    },
    {
      id: "doc-2",
      name: "Dr. Meenakshi Sundaram",
      qualifications: "BVSc & AH (Ruminant Medicine), IVRI Izatnagar",
      specialty: "medicine",
      experienceYears: 8,
      rating: 4.85,
      reviewCount: 94,
      vciRegNumber: "VCI-TN-2016-1182",
      district: "Pune / Baramati",
      state: "Maharashtra",
      consultationFee: 250,
      visitFee: 700,
      isAvailableNow: true,
      offersHomeVisit: false,
      languages: ["Hindi", "English", "Tamil"],
      avatarUrl: "https://images.unsplash.com/photo-1594824813579-450a866f7f6f?w=150&auto=format&fit=crop&q=80"
    },
    {
      id: "doc-3",
      name: "Dr. Harpreet Singh Dhillon",
      qualifications: "MVSc (Veterinary Surgery & Radiology), GADVASU",
      specialty: "surgery",
      experienceYears: 18,
      rating: 4.95,
      reviewCount: 310,
      vciRegNumber: "VCI-PB-2006-0023",
      district: "Ludhiana / Khanna",
      state: "Punjab",
      consultationFee: 400,
      visitFee: 1200,
      isAvailableNow: false,
      offersHomeVisit: true,
      languages: ["Punjabi", "Hindi", "English"],
      avatarUrl: "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=150&auto=format&fit=crop&q=80"
    },
    {
      id: "doc-4",
      name: "Dr. Anjali Deshmukh",
      qualifications: "PhD (Ruminant Nutrition & Metabolic Health), NDDB Fellow",
      specialty: "nutrition",
      experienceYears: 11,
      rating: 4.88,
      reviewCount: 140,
      vciRegNumber: "VCI-GJ-2013-0874",
      district: "Anand / Kheda",
      state: "Gujarat",
      consultationFee: 350,
      visitFee: 900,
      isAvailableNow: true,
      offersHomeVisit: true,
      languages: ["Gujarati", "Hindi", "English"],
      avatarUrl: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150&auto=format&fit=crop&q=80"
    },
    {
      id: "doc-5",
      name: "Dr. Sanjay Deshmukh",
      qualifications: "BVSc & AH, Head of ICAR-KVK Niphad Polyclinic",
      specialty: "general",
      experienceYears: 22,
      rating: 4.92,
      reviewCount: 420,
      vciRegNumber: "VCI-MH-2002-0118",
      district: "Niphad",
      state: "Maharashtra",
      consultationFee: 0, // Free Govt KVK tele-triage
      visitFee: 300,
      isAvailableNow: true,
      offersHomeVisit: true,
      languages: ["Marathi", "Hindi"],
      avatarUrl: "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=150&auto=format&fit=crop&q=80"
    }
  ];

  const prescriptions: PrescriptionRecord[] = [
    {
      id: "rx-9021",
      bovineTag: "1002-8812-4019",
      animalName: "Lakshmi (Murrah Buffalo)",
      doctorName: "Dr. Rajesh Patil",
      date: "24 Sep 2026",
      diagnosis: "Sub-clinical Mastitis (Right Hind Quarter)",
      medicines: [
        "Intramammary Cefquinome Infusion (1 syringe q24h for 3 days)",
        "Meloxicam 15ml IM OD for 3 days",
        "Trisodium Citrate oral powder (30g daily for 7 days)"
      ],
      withdrawalPeriodDays: 3,
      pdfUrl: "#"
    },
    {
      id: "rx-8834",
      bovineTag: "1002-9481-0293",
      animalName: "Ganga (Gir Cow)",
      doctorName: "Dr. Sanjay Deshmukh",
      date: "12 Sep 2026",
      diagnosis: "Post-Partum Hypocalcemia (Milk Fever Prophylaxis)",
      medicines: [
        "Calcium Borogluconate 450ml IV Slow Infusion",
        "Oral Ionic Calcium Gel (300g post-calving)"
      ],
      withdrawalPeriodDays: 0,
      pdfUrl: "#"
    }
  ];

  const filteredDoctors = () => {
    return doctors.filter(doc => {
      const matchesSearch =
        doc.name.toLowerCase().includes(searchQuery().toLowerCase()) ||
        doc.district.toLowerCase().includes(searchQuery().toLowerCase()) ||
        doc.qualifications.toLowerCase().includes(searchQuery().toLowerCase());

      const matchesSpecialty =
        selectedSpecialty() === "all" || doc.specialty === selectedSpecialty();

      const matchesAvailability =
        availabilityFilter() === "all" ||
        (availabilityFilter() === "online" && doc.isAvailableNow) ||
        (availabilityFilter() === "visit" && doc.offersHomeVisit);

      return matchesSearch && matchesSpecialty && matchesAvailability;
    });
  };

  const handleBookSubmit = (e: Event) => {
    e.preventDefault();
    setBookingSuccess(true);
    setTimeout(() => {
      setBookingSuccess(false);
      setSelectedDoctorForBooking(null);
    }, 2800);
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
            <span class="text-brand-600 dark:text-brand-400 font-medium">Veterinary Doctors</span>
          </div>
          <h1 class="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <span class="material-symbols-outlined text-brand-600 text-3xl">medical_services</span>
            Tele-Veterinary &amp; Doctor Booking
          </h1>
          <p class="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
            VCI-certified veterinary officers, ruminant surgeons, and animal nutritionists for instant tele-consultation and on-farm visits.
          </p>
        </div>

        {/* Tab Switcher */}
        <div class="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab("doctors")}
            class={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab() === "doctors"
                ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <span class="material-symbols-outlined text-base">stethoscope</span>
            <span>Doctors Directory</span>
          </button>
          <button
            onClick={() => setActiveTab("prescriptions")}
            class={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab() === "prescriptions"
                ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <span class="material-symbols-outlined text-base">prescriptions</span>
            <span>e-Prescriptions ({prescriptions.length})</span>
          </button>
        </div>
      </div>

      {/* 24/7 EMERGENCY SOS SPEED DIAL BANNER */}
      <div class="rounded-2xl bg-gradient-to-r from-red-600 to-amber-600 text-white p-5 shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="relative z-10 flex items-start gap-3.5">
          <div class="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/30">
            <span class="material-symbols-outlined text-2xl text-white animate-pulse">emergency</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-black uppercase tracking-wider bg-white/25 px-2 py-0.5 rounded-full">24x7 Critical Care</span>
              <span class="text-xs font-medium text-red-100">Dystocia • Bloat • Milk Fever • Trauma</span>
            </div>
            <h3 class="text-lg font-black mt-1">National Animal Emergency Helpline &amp; Mobile Ambulance</h3>
            <p class="text-xs text-red-100 mt-0.5 max-w-xl">
              Free Government 1962 Pashu Ambulance with onboard field surgery kit, oxygen, and emergency tele-triage.
            </p>
          </div>
        </div>

        <div class="relative z-10 flex items-center gap-2.5 shrink-0">
          <a
            href="tel:1962"
            class="px-4 py-2.5 rounded-xl bg-white text-red-700 hover:bg-red-50 text-xs font-black shadow-md transition-all flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-lg">call</span>
            Dial 1962 (Toll-Free)
          </a>
          <button
            onClick={() => {
              setSelectedDoctorForBooking(doctors[0]);
              setBookingType("video");
            }}
            class="px-4 py-2.5 rounded-xl bg-red-900/60 hover:bg-red-900/80 text-white text-xs font-semibold backdrop-blur-md border border-white/20 transition-all flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-lg">videocam</span>
            Instant Video Triage
          </button>
        </div>
      </div>

      <Show when={activeTab() === "doctors"}>
        {/* SEARCH & FILTERS BAR */}
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
          <div class="flex flex-col md:flex-row md:items-center gap-3">
            {/* Search Input */}
            <div class="relative flex-1">
              <span class="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-lg">search</span>
              <input
                type="text"
                placeholder="Search by doctor name, district (Niphad, Pune, Anand...), or specialty..."
                value={searchQuery()}
                onInput={e => setSearchQuery(e.currentTarget.value)}
                class="w-full text-xs pl-9 pr-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Availability Mode Toggle */}
            <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
              <button
                onClick={() => setAvailabilityFilter("all")}
                class={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  availabilityFilter() === "all"
                    ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                All Modes
              </button>
              <button
                onClick={() => setAvailabilityFilter("online")}
                class={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
                  availabilityFilter() === "online"
                    ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Available Now
              </button>
              <button
                onClick={() => setAvailabilityFilter("visit")}
                class={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
                  availabilityFilter() === "visit"
                    ? "bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <span class="material-symbols-outlined text-sm">home_pin</span>
                Farm Visit
              </button>
            </div>
          </div>

          {/* Specialty Filter Chips */}
          <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => setSelectedSpecialty("all")}
              class={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                selectedSpecialty() === "all"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
              }`}
            >
              All Specialties ({doctors.length})
            </button>
            <button
              onClick={() => setSelectedSpecialty("obstetrics")}
              class={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                selectedSpecialty() === "obstetrics"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
              }`}
            >
              Bovine Obstetrics &amp; AI
            </button>
            <button
              onClick={() => setSelectedSpecialty("nutrition")}
              class={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                selectedSpecialty() === "nutrition"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
              }`}
            >
              Ruminant Nutrition &amp; TMR
            </button>
            <button
              onClick={() => setSelectedSpecialty("surgery")}
              class={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                selectedSpecialty() === "surgery"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
              }`}
            >
              Surgery &amp; Teat Disorders
            </button>
            <button
              onClick={() => setSelectedSpecialty("medicine")}
              class={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                selectedSpecialty() === "medicine"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
              }`}
            >
              Internal Medicine &amp; Infections
            </button>
            <button
              onClick={() => setSelectedSpecialty("general")}
              class={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-all ${
                selectedSpecialty() === "general"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
              }`}
            >
              KVK Govt Polyclinic
            </button>
          </div>
        </div>

        {/* DOCTORS GRID */}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <For each={filteredDoctors()}>
            {doc => (
              <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                <div>
                  {/* Doctor Profile Top */}
                  <div class="flex items-start gap-3.5 mb-3">
                    <img
                      src={doc.avatarUrl}
                      alt={doc.name}
                      class="w-14 h-14 rounded-2xl object-cover border-2 border-brand-500/20 shadow-sm shrink-0"
                    />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-1.5">
                        <h3 class="text-sm font-black text-slate-900 dark:text-white truncate">{doc.name}</h3>
                        <span class="material-symbols-outlined text-sm text-brand-600" title="VCI Verified">verified</span>
                      </div>
                      <p class="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1 mt-0.5">{doc.qualifications}</p>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                          {doc.vciRegNumber}
                        </span>
                        <div class="flex items-center gap-0.5 text-xs text-amber-500 font-bold">
                          <span class="material-symbols-outlined text-xs">star</span>
                          <span>{doc.rating}</span>
                          <span class="text-[10px] text-slate-400 font-normal">({doc.reviewCount})</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Badges & Location */}
                  <div class="space-y-2 py-2 border-y border-slate-100 dark:border-slate-800/80 my-3 text-xs text-slate-600 dark:text-slate-400">
                    <div class="flex items-center justify-between">
                      <span class="flex items-center gap-1 text-[11px]">
                        <span class="material-symbols-outlined text-sm text-slate-400">location_on</span>
                        {doc.district}, {doc.state}
                      </span>
                      <span class="text-[11px] font-medium text-slate-500">{doc.experienceYears} yrs experience</span>
                    </div>

                    <div class="flex items-center justify-between">
                      <span class="text-[11px] text-slate-500">Languages:</span>
                      <span class="text-[11px] font-medium text-slate-700 dark:text-slate-300">{doc.languages.join(", ")}</span>
                    </div>

                    <div class="flex items-center justify-between">
                      <span class="text-[11px] text-slate-500">Live Status:</span>
                      {doc.isAvailableNow ? (
                        <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                          Ready for Video Call (15m)
                        </span>
                      ) : (
                        <span class="text-[11px] text-slate-400">Next Slot at 04:00 PM</span>
                      )}
                    </div>
                  </div>

                  {/* Consultation Pricing */}
                  <div class="flex items-center justify-between text-xs mb-4">
                    <div>
                      <span class="text-[10px] text-slate-400 uppercase font-semibold">Video Consult</span>
                      <div class="text-sm font-black text-slate-900 dark:text-white">
                        {doc.consultationFee === 0 ? "FREE (KVK)" : `₹${doc.consultationFee}`}
                      </div>
                    </div>
                    {doc.offersHomeVisit && (
                      <div class="text-right">
                        <span class="text-[10px] text-slate-400 uppercase font-semibold">Farm Visit</span>
                        <div class="text-sm font-black text-slate-900 dark:text-white">₹{doc.visitFee}</div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div class="grid grid-cols-2 gap-2 pt-2">
                  <button
                    onClick={() => {
                      setSelectedDoctorForBooking(doc);
                      setBookingType("video");
                    }}
                    class="w-full py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-all flex items-center justify-center gap-1"
                  >
                    <span class="material-symbols-outlined text-sm">videocam</span>
                    Video Consult
                  </button>

                  <button
                    onClick={() => {
                      setSelectedDoctorForBooking(doc);
                      setBookingType("visit");
                    }}
                    disabled={!doc.offersHomeVisit}
                    class="w-full py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-all flex items-center justify-center gap-1 disabled:opacity-50"
                  >
                    <span class="material-symbols-outlined text-sm">home_pin</span>
                    Book Visit
                  </button>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>

      {/* PRESCRIPTIONS & TREATMENT HISTORY TAB */}
      <Show when={activeTab() === "prescriptions"}>
        <div class="space-y-4">
          <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
            <h2 class="text-sm font-black text-slate-900 dark:text-white mb-1 flex items-center gap-2">
              <span class="material-symbols-outlined text-brand-600">prescriptions</span>
              Digital e-Prescription &amp; Medicine Withdrawal Registry
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">
              All prescriptions are signed with the doctor's VCI digital seal and track milk/meat antibiotic withdrawal withholding periods.
            </p>

            <div class="space-y-4">
              <For each={prescriptions}>
                {rx => (
                  <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 space-y-3">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 dark:border-slate-700/60 pb-3">
                      <div>
                        <div class="flex items-center gap-2">
                          <span class="text-xs font-bold text-slate-900 dark:text-white">{rx.diagnosis}</span>
                          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-semibold">
                            {rx.id}
                          </span>
                        </div>
                        <p class="text-xs text-slate-500 mt-0.5">
                          Patient: <span class="font-medium text-slate-700 dark:text-slate-300">{rx.animalName}</span> ({rx.bovineTag}) • Prescribed by {rx.doctorName} on {rx.date}
                        </p>
                      </div>

                      <div class="flex items-center gap-2">
                        {rx.withdrawalPeriodDays > 0 ? (
                          <span class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">hourglass_top</span>
                            {rx.withdrawalPeriodDays}d Milk Withholding
                          </span>
                        ) : (
                          <span class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                            0d Withdrawal (Safe)
                          </span>
                        )}
                        <button
                          onClick={() => alert(`Downloading official VCI verified PDF for ${rx.id}`)}
                          class="px-3 py-1 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 flex items-center gap-1"
                        >
                          <span class="material-symbols-outlined text-sm">download</span>
                          PDF
                        </button>
                      </div>
                    </div>

                    <div>
                      <span class="text-[11px] font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider block mb-1">
                        Prescribed Course &amp; Dosage:
                      </span>
                      <ul class="list-disc list-inside text-xs text-slate-800 dark:text-slate-200 space-y-1">
                        <For each={rx.medicines}>{med => <li>{med}</li>}</For>
                      </ul>
                    </div>
                  </div>
                )}
              </For>
            </div>
          </div>
        </div>
      </Show>

      {/* BOOKING MODAL */}
      <Show when={selectedDoctorForBooking()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm">
          <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 class="text-base font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-brand-600">event_available</span>
                  Book {bookingType() === "video" ? "Tele-Video Call" : "On-Farm Visit"}
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">With {selectedDoctorForBooking()?.name}</p>
              </div>
              <button
                onClick={() => setSelectedDoctorForBooking(null)}
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
                  Appointment link sent via SMS/WhatsApp. Doctor will connect at {selectedSlot()}.
                </p>
              </div>
            ) : (
              <form onSubmit={handleBookSubmit} class="space-y-4 text-xs">
                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Select Animal / Bovine</label>
                  <select
                    value={bovineTagInput()}
                    onChange={e => setBovineTagInput(e.currentTarget.value)}
                    class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="1002-8812-4019">Lakshmi (Murrah Buffalo #1002-8812-4019)</option>
                    <option value="1002-9481-0293">Ganga (Gir Cow #1002-9481-0293)</option>
                    <option value="1002-5519-3321">Heifer Calf #1002-5519-3321</option>
                  </select>
                </div>

                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Consultation Mode</label>
                  <div class="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setBookingType("video")}
                      class={`p-2.5 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition-all ${
                        bookingType() === "video"
                          ? "border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300"
                          : "border-slate-200 dark:border-slate-700 text-slate-600"
                      }`}
                    >
                      <span class="material-symbols-outlined text-base">videocam</span>
                      <span>Video Call (₹{selectedDoctorForBooking()?.consultationFee})</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setBookingType("visit")}
                      disabled={!selectedDoctorForBooking()?.offersHomeVisit}
                      class={`p-2.5 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition-all ${
                        bookingType() === "visit"
                          ? "border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300"
                          : "border-slate-200 dark:border-slate-700 text-slate-600 disabled:opacity-40"
                      }`}
                    >
                      <span class="material-symbols-outlined text-base">home_pin</span>
                      <span>Farm Visit (₹{selectedDoctorForBooking()?.visitFee})</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Preferred Time Slot</label>
                  <select
                    value={selectedSlot()}
                    onChange={e => setSelectedSlot(e.currentTarget.value)}
                    class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="Today, 02:30 PM">Today, 02:30 PM (Earliest Slot)</option>
                    <option value="Today, 04:00 PM">Today, 04:00 PM</option>
                    <option value="Tomorrow, 10:00 AM">Tomorrow Morning, 10:00 AM</option>
                    <option value="Tomorrow, 03:00 PM">Tomorrow Afternoon, 03:00 PM</option>
                  </select>
                </div>

                <div>
                  <label class="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Symptoms / Issue Description</label>
                  <textarea
                    rows="3"
                    placeholder="E.g. Animal is off-feed since morning, mild swelling on left hind quarter, temperature 103.5°F..."
                    value={symptomDescription()}
                    onInput={e => setSymptomDescription(e.currentTarget.value)}
                    class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                <div class="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                  <span class="text-slate-500">
                    Payable Amount: <strong class="text-slate-900 dark:text-white">₹{bookingType() === "video" ? selectedDoctorForBooking()?.consultationFee : selectedDoctorForBooking()?.visitFee}</strong>
                  </span>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedDoctorForBooking(null)}
                      class="px-3 py-2 rounded-xl text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      class="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold shadow-sm transition-all"
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
