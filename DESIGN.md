# CropSense AI — Design System & UI Specification

## 1. Product Vision & Brand Architecture
CropSense AI is a next-generation mobile-first digital public infrastructure platform empowering Indian smallholder farmers, buyers, agricultural officers, and service providers. The interface combines high accessibility, intuitive visual cues, and resilient outdoor sunlight contrast with state-of-the-art AI interactions (Gemini Vision disease diagnosis, satellite crop health maps, multimodal voice assistant in Indian regional languages, and pre-harvest advance booking contracts).

---

## 2. Color Palette & Semantic Tokens

### 2.1 Brand & Primary Colors
* **Primary Emerald (Growth & Agriculture)**:
  * `primary-900`: `#064e3b` (Deep forest headers)
  * `primary-800`: `#065f46` (Primary action dark)
  * `primary-700`: `#047857` (Primary brand buttons, active navigation)
  * `primary-600`: `#059669` (Interactive accents)
  * `primary-500`: `#10b981` (Vibrant badges, success highlights)
  * `primary-100`: `#d1fae5` (Soft tinted card backgrounds)
  * `primary-50`: `#ecfdf5` (Surface fill, selected list items)

* **Harvest Gold (Grain, Yield & Prosperity)**:
  * `accent-700`: `#b45309` (Amber tags, contract alerts)
  * `accent-500`: `#f59e0b` (Price trends, opportunity score)
  * `accent-100`: `#fef3c7` (Highlight pill backgrounds)

* **Telemetry Cyan (Satellite & AI Intelligence)**:
  * `ai-600`: `#0891b2` (Gemini assistant glow, satellite telemetry)
  * `ai-500`: `#06b6d4` (Active AI processing, voice visualizer)
  * `ai-50`: `#ecfeff` (AI recommendation card backgrounds)

### 2.2 Semantic & Telemetry Status Colors
* **Optimal / Healthy Crop / Normal**: `#10b981` (`emerald-500`)
* **Watchlist / Moderate Alert / Warning**: `#f59e0b` (`amber-500`)
* **Urgent / Disease Detected / Severe**: `#ef4444` (`red-500`)
* **Moisture / Weather / Irrigation**: `#0284c7` (`sky-600`)
* **Soil Organic / Fertilizer**: `#854d0e` (`yellow-800`)

### 2.3 Surface & Neutral Shades
* **Canvas Light**: `#f8fafc` (Ultra-clean daylight canvas)
* **Surface White**: `#ffffff` (Elevated cards and modal dialogs)
* **Card Border**: `#e2e8f0` (Subtle 1px boundary)
* **Text Primary**: `#0f172a` (Slate 900, crisp high-contrast readability)
* **Text Secondary**: `#475569` (Slate 600, labels and supporting metadata)
* **Text Muted**: `#94a3b8` (Slate 400, timestamps, placeholders)

---

## 3. Typography & Hierarchy

* **Font Family**:
  * Primary: `'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
  * Regional & Multilingual: Supported with clean unicode rendering for Hindi (हिंदी), Marathi (मराठी), and Punjabi (ਪੰਜਾਬੀ).
  * Monospace / Data: `'JetBrains Mono', 'Fira Code', monospace` (for satellite coordinates, sensor readings, transaction hashes)

* **Scale**:
  * **Display Title**: `32px` / Line Height `1.2` / Weight `700`
  * **Screen Header (H1)**: `24px` / Line Height `1.3` / Weight `700`
  * **Section Heading (H2)**: `20px` / Line Height `1.35` / Weight `600`
  * **Subheading (H3)**: `16px` / Line Height `1.4` / Weight `600`
  * **Body Primary**: `15px` / Line Height `1.5` / Weight `400` & `500`
  * **Body Small / Captions**: `13px` / Line Height `1.4` / Weight `400` & `500`
  * **Micro / Badges**: `11px` / Line Height `1.2` / Weight `600` (Uppercase tracked)

---

## 4. Layout, Spacing & Elevation

* **Mobile-First Layout**:
  * Max container width: `480px` on mobile screens, fluid centered on tablets/desktops (`max-w-7xl`).
  * Padding: `16px` (`p-4`) on mobile, `24px` (`p-6`) on desktop.
* **Component Corner Radii**:
  * Small badges / Pills: `9999px` (Full rounded)
  * Inputs & Action buttons: `12px` (`rounded-xl`)
  * Feature cards & Content containers: `16px` (`rounded-2xl`)
  * Bottom sheets & Dialogs: `24px 24px 0 0` (`rounded-t-3xl`)
* **Shadows & Glassmorphism**:
  * Card shadow: `0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)`
  * Floating action button shadow: `0 10px 25px -5px rgba(5, 150, 105, 0.35)`
  * Glass blur effect: `backdrop-filter: blur(12px); background: rgba(255, 255, 255, 0.85);`

---

## 5. Core Screens & UX Patterns

### Screen 1: Farmer Smart Dashboard (`/dashboard`)
* **Weather & Early Warning Bar**: Real-time temperature, IMD rainfall forecast, humidity, and severe frost/pest risk badge.
* **Farm Snapshot & Satellite Telemetry**: Active acreage, Sentinel-2 NDVI vegetative health indicator (e.g. `NDVI 0.78 - Vigorous Growth`), soil moisture gauge.
* **Current Seasonal Plan (Kharif / Rabi)**: Crop stage tracker (Sowing, Flowering, Harvest countdown), expected yield vs market demand.
* **Quick Action Grid**:
  1. *AI Crop Doctor* (Instant photo diagnosis)
  2. *Soil & Fertilizer Hub* (Soil Health Card recommendations)
  3. *Pashu / Livestock Hub* (Milk tracking & vet care)
  4. *Mandi Market Prices & Advance Bookings*
* **Persistent Bottom Navigation**: Home, Farms, Diagnostics, Market, Pashu.
* **Floating Multilingual Voice AI Button**: "Tap to talk in Hindi, Marathi, Punjabi, or English".

### Screen 2: Gemini Vision AI Crop Diagnostic (`/diagnose`)
* **Photo Capture & Upload Viewport**: High-res viewfinder with guidance frame ("Align leaf within frame").
* **Instant Diagnostic Card**:
  * Detected Issue: e.g. *Early Blight (Alternaria solani)*
  * Confidence: `94% AI Confidence`
  * Urgency Tag: `High Urgency — Treat within 48h`
* **Tailored Treatment Action Plan**:
  * Organic remedy: Neem oil spray + Trichoderma viride formulation
  * Chemical remedy: Mancozeb 75% WP @ 2g/L
  * Safety guardrails & protective equipment warnings
* **One-Click Actions**: Book Krishi Vigyan Kendra (KVK) Agronomist Call, Order Supplies, Save to Farm History.

### Screen 3: Marketplace Advance Booking & Escrow Workflow (`/marketplace/bookings/:id`)
* **Contract Overview**: Crop type, certified variety, quantity (e.g. 100 Quintals Sharbati Wheat), agreed floor price per quintal.
* **Visual Escrow Milestone Tracker**:
  1. Buyer Match Accepted (Completed)
  2. Farmer Confirmation (Completed)
  3. Quality & Moisture Verification (Active — Passed Grade A, 11.2% moisture)
  4. Escrow Advance Release & Final Settlement
* **Digital Quality Certificate**: Photo evidence, spectrometer reading, inspector signature.
* **Interactive Controls**: "Approve & Release Milestone Payment", "Request Re-inspection", "Download Legal Agreement".

### Screen 4: Livestock & Pashu Health Intelligence (`/livestock`)
* **Herd Portfolio Overview**: Cattle & Buffalo cards, tagging ID, lactation phase, daily milk production graph.
* **Vaccination & Breeding Schedule**: Interactive calendar for FMD, Brucellosis, Deworming with push alert reminders.
* **AI Diet & Ration Balancing Calculator**: Feed ratio optimization (Green fodder, Dry roughage, Mineral mixture) calculated against live milk yield.
* **Veterinary Teleconsultation**: Verified local veterinarians with instant call / clinic appointment booking.

### Screen 5: Satellite Health Map & Soil Health Card (`/farm/:id` / `/soil/hub`)
* **Field Boundary Polygon**: High-resolution true-color satellite overlay + interactive NDVI false-color heatmap.
* **Soil Health Parameters**: N-P-K nutrient radar chart, soil pH (6.8 Optimal), electrical conductivity, and micronutrient status (Zinc, Iron, Boron).
* **Automated Prescription**: Plot-specific fertilizer schedule synchronized with local weather forecast to prevent nutrient leaching.
