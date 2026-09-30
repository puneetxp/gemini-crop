# CropSense AI — Master Task & Page Execution Roadmap

> **Standard Execution Protocol**:
> For each page in this roadmap:
> 1. **Design in Stitch**: Generate both **Desktop Variant** (wide-screen, multi-column, sidebar) and **Mobile Variant** (compact, touch-friendly, bottom nav).
> 2. **Connect & Cross-link**: Link the screen in the master showcase (`index.html`) and wire anchor links to/from other pages.
> 3. **Implement Full-Stack**:
>    - **Backend (`python/app/`)**: Verify FastAPI router, schemas, DB query, and ownership rules.
>    - **Frontend (`solidjs/src/`)**: Implement SolidJS page component, reactive store, and `apiClient` integration.
> 4. **Verify**: Check responsiveness across Mobile (390px), Tablet (768px), and Desktop (1440px), then mark the task `[x] Complete`.

---

## Progress Overview
- **Total Primary Routes**: 45 Routes across 4 Domains + Foundation
- **Completed Stitch Prototypes**: 12 Screens (Full Responsive screens + legacy prototypes for all 6 core domains)
- **Current Active Milestone**: Batch 0 (Database Model Scaffolding via `puneetxp/compile-php`) & Batch 1 Implementation

---

## Batch 0: Foundation & Core Scaffolding

- [x] **T0.1: Architecture & Data Model Baseline**
  - References: `ARCHITECTURE-v2.md`, `BACKEND-v2.md`, `DATA_MODEL-v2.md`, `FRONTEND-v2.md`
  - Deliverable: Integrated architecture specification & single source of truth.
- [x] **T0.2: Design System & Tokens**
  - Reference: `DESIGN.md` ("AgriSense Premier" design system)
  - Deliverable: Palette tokens (Emerald `#065f46`, Amber `#d97706`, Mint `#10b981`), Plus Jakarta Sans typography, container query rules.
- [x] **T0.3: Master Interactive Multi-Device Showcase**
  - File: `index.html` (Local preview server on port 4321)
  - Deliverable: Live viewport switcher (Mobile 390px, Tablet 768px, Desktop 1440px, Fluid 100%), route tabs, and specs drawer.
- [x] **T0.4: Database JSON Models & Schema Generator Integrated**
  - Toolchain: `setup.php` & `vendor/puneetxp/compile-php` in project root
  - Verified outputs: `database/structure.sql` (PostgreSQL DDL), `python/app/models/*.py` (Pydantic), `python/app/orm/*.py`, `python/app/api/*.py`, `solidjs/src/shared/Interface/Model/*.ts`.
- [x] **T0.5: Backend Core Scaffolding (`python/app/core/`)**
  - Path: `python/app/core/` (`db.py`, `model.py`, `crud_service.py`, `ownership.py`, `auth.py`, `rate_limiter.py`, `dependencies.py`, `config.py`)
  - Target: Connection pool with `psycopg3`, row-level ownership security, Firebase JWT validation & E2E mock token support.
- [x] **T0.6: Frontend Core Shell Scaffolding (`solidjs/`)**
  - Path: `solidjs/src/` (`lib/api-client.ts`, `stores/auth.store.ts`, `stores/i18n.store.ts`, `shared/Service/Service.ts`, `App.tsx`, `index.tsx`)
  - Target: SolidJS router setup, 5-minute GET cache, offline support via Service Worker & full Vite build verification.

---

## Batch 1: Core Shell, Authentication & Account (11 Routes)

| ID | Route | SolidJS Page | Backend Endpoints | Stitch Designs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **T1.1** | `/` | `pages/Home.tsx` | `GET /analytics/profile-status` | Desktop / Mobile | `[x]` |
| **T1.2** | `/auth/signin` | `pages/auth/SignIn.tsx` | `POST /auth/google`, `POST /auth/login` | Desktop / Mobile | `[x]` |
| **T1.3** | `/auth/signup` | `pages/auth/SignUp.tsx` | `POST /auth/signup`, `GET /address/pincode/{pin}` | Desktop / Mobile | `[x]` |
| **T1.4** | `/dashboard` | `pages/Dashboard.tsx` | `GET /analytics/profile-status`, `GET /satellite/farm/{id}` | `stitch/screens/screen_desktop_dashboard.html`<br>`stitch/screens/screen1_dashboard.html` | `[x]` |
| **T1.5** | `/assistant` | `pages/Assistant.tsx` | `POST /voice/assist`, `POST /voice/query` | Desktop / Mobile | `[x]` |
| **T1.6** | `/menu` | `pages/AllServices.tsx` | Local services grid | `stitch/screens/screen_desktop_menu.html` | `[x]` |
| **T1.7** | `/settings` | `pages/Configuration.tsx` | `localStorage.app_config` | Desktop / Mobile | `[x]` |
| **T1.8** | `/users/profile` | `pages/users/Profile.tsx` | `GET /users/profile`, `PUT /users/profile` | Desktop / Mobile | `[x]` |
| **T1.9** | `/users/security` | `pages/users/Security.tsx` | `POST /users/change-password`, `MFA` | `stitch/screens/screen_desktop_security.html` | `[x]` |
| **T1.10**| `/notifications`| `pages/notifications/Notifications.tsx`| `GET /islogin/user_notification/` | Desktop / Mobile | `[x]` |
| **T1.11**| `/quota/history`| `pages/quota/QuotaHistory.tsx`| `GET /ai-quota/status/{user.id}` | `stitch/screens/screen_desktop_quota.html` | `[x]` |

---

## Batch 2: Farm, Plot, Crop & Strategic Planning (12 Routes)

| ID | Route | SolidJS Page | Backend Endpoints | Stitch Designs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **T2.1** | `/farm` | `pages/farm/Index.tsx` | `GET /farms` (`FarmService.getFarms()`) | Desktop / Mobile | `[x]` |
| **T2.2** | `/farm/register` | `pages/farm/Register.tsx` | `POST /farms`, `GET /farms/location-lookup` | `stitch/screens/screen_desktop_farm_register.html` | `[x]` |
| **T2.3** | `/farm/:id` | `pages/farm/FarmDashboard.tsx` | `GET /farms/{id}`, `GET /satellite/farm/{id}` | `stitch/screens/screen_desktop_farm_detail.html` | `[x]` |
| **T2.4** | `/analytics/farm/:id`| `pages/farm/FarmAnalytics.tsx`| `GET /analytics/farm/{id}`, expenses | `stitch/screens/screen_desktop_farm_analytics.html` | `[x]` |
| **T2.5** | `/plots/create` | `pages/plots/Create.tsx` | `POST /farms/{farm_id}/plots` | `stitch/screens/screen_desktop_plot_create.html` | `[x]` |
| **T2.6** | `/crops/plant` | `pages/crops/PlantCrop.tsx` | `POST /crops/quick-plant` | `stitch/screens/screen_desktop_plant_crop.html` | `[x]` |
| **T2.7** | `/crops/my-crops` | `pages/crops/MyCrops.tsx` | `GET /crops/my-crops` | `stitch/screens/screen_desktop_my_crops.html` | `[x]` |
| **T2.8** | `/crops/annual-strategy/:id` | `pages/crops/AnnualStrategyDetail.tsx`| `GET /annual-strategy/{id}` | `stitch/screens/screen_desktop_strategy.html` | `[x]` |
| **T2.9** | `/diagnose` | `pages/crops/Diagnose.tsx` | `POST /vision/diagnose-crop` | `stitch/screens/screen_desktop_diagnose.html`<br>`stitch/screens/screen2_diagnose.html` | `[x]` |
| **T2.10**| `/strategy/select-farm`| `pages/strategy/SelectFarm.tsx`| `GET /farms` | `stitch/screens/screen_desktop_strategy_select.html` | `[x]` |
| **T2.11**| `/strategy/request`| `pages/strategy/Request.tsx` | `POST /annual-strategy` | `stitch/screens/screen_desktop_strategy_request.html` | `[x]` |
| **T2.12**| `/strategy/results`| `pages/strategy/Results.tsx` | `GET /annual-strategy/list` | `stitch/screens/screen_desktop_strategy.html` | `[x]` |

---

## Batch 3: Livestock, Climate, Soil & Health Services (8 Routes)

| ID | Route | SolidJS Page | Backend Endpoints | Stitch Designs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **T3.1** | `/livestock` | `pages/livestock/PashuHome.tsx` | `GET /islogin/livestock/`, milk summary | `stitch/screens/screen_desktop_livestock.html`<br>`stitch/screens/screen4_livestock.html` | `[x]` |
| **T3.2** | `/livestock/hub` | `pages/livestock/LivestockHub.tsx`| `GET /vaccination-reminders` | `stitch/screens/screen_desktop_livestock_hub.html` | `[x]` |
| **T3.3** | `/livestock/diet-plan`| `pages/livestock/DietPlan.tsx`| Browser math via `dietPlan` service | `stitch/screens/screen_desktop_diet_plan.html` | `[x]` |
| **T3.4** | `/livestock/doctors` | `pages/livestock/VeterinaryDoctors.tsx`| `GET /veterinary/doctors` | `stitch/screens/screen_desktop_veterinary_doctors.html` | `[x]` |
| **T3.5** | `/climate/hub` | `pages/climate/ClimateHub.tsx` | `GET /weather/forecast`, alerts | `stitch/screens/screen_desktop_climate_hub.html` | `[x]` |
| **T3.6** | `/soil/hub` | `pages/soil/SoilFertilizerHub.tsx`| `GET /soil/health/plot/{id}`, NPK | `stitch/screens/screen_desktop_soil_satellite.html`<br>`stitch/screens/screen5_soil_satellite.html` | `[x]` |
| **T3.7** | `/pest-disease/hub`| `pages/pest-disease/PestDiseaseHub.tsx`| `POST /pest-disease/identify` | `stitch/screens/screen_desktop_pest_disease.html` | `[x]` |
| **T3.8** | `/services` | `pages/services/ServicesDirectory.tsx`| `GET /islogin/service/` | `stitch/screens/screen_desktop_services_directory.html` | `[x]` |

---

## Batch 4: Marketplace, Advance Booking Escrow & Admin (14 Routes)

| ID | Route | SolidJS Page | Backend Endpoints | Stitch Designs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **T4.1** | `/marketplace` | `pages/marketplace/Browse.tsx` | `GET /marketplace/listings` | Desktop / Mobile | `[x]` |
| **T4.2** | `/marketplace/:id`| `pages/marketplace/Detail.tsx`| `GET /marketplace/listings/{id}` | `stitch/screens/screen_desktop_marketplace_detail.html` | `[x]` |
| **T4.3** | `/marketplace/my-listings`| `pages/marketplace/MyListings.tsx`| `GET /marketplace/my-listings` | `stitch/screens/screen_desktop_my_listings.html` | `[x]` |
| **T4.4** | `/marketplace/buyer-dashboard`| `pages/marketplace/BuyerDashboard.tsx`| `POST /supply-requests/`, matches | `stitch/screens/screen_desktop_buyer_dashboard.html` | `[x]` |
| **T4.5** | `/marketplace/bookings`| `pages/marketplace/Bookings.tsx`| `GET /marketplace/advance-bookings` | `stitch/screens/screen_desktop_marketplace_bookings.html` | `[x]` |
| **T4.6** | `/marketplace/bookings/:id`| `pages/marketplace/BookingDetails.tsx`| `POST /advance-bookings/{id}/confirm`, `quality-verify` | `stitch/screens/screen_desktop_booking.html`<br>`stitch/screens/screen3_booking.html` | `[x]` |
| **T4.7** | `/marketplace/intelligence`| `pages/marketplace/MarketIntelligence.tsx`| `GET /market-intelligence/trends/` | `stitch/screens/screen_desktop_market_intelligence.html` | `[x]` |
| **T4.8** | `/marketplace/supply-planning`| `pages/marketplace/SupplyPlanning.tsx`| `GET /predictive-analytics/` | `stitch/screens/screen_desktop_supply_planning.html` | `[x]` |
| **T4.9** | `/livestock-marketplace`| `pages/livestock-marketplace/Browse.tsx`| `GET /livestock-marketplace/` | `stitch/screens/screen_desktop_livestock_marketplace.html` | `[x]` |
| **T4.10**| `/transport/tracking`| `pages/transport/TransportTracking.tsx`| `GET /transport/bookings` | `stitch/screens/screen_desktop_transport_tracking.html` | `[x]` |
| **T4.11**| `/admin/analytics`| `pages/admin/PlatformAnalytics.tsx`| `GET /analytics/platform` | `stitch/screens/screen_desktop_admin_analytics.html` | `[x]` |
| **T4.12**| `/admin/quota` | `pages/admin/QuotaMonitoring.tsx`| `GET /ai-quota/statistics`, resets | `stitch/screens/screen_desktop_admin_quota.html` | `[x]` |

---

## Page Development Checklist (Template for Each Page Agent)

When creating or refining a page:
1. [ ] **Stitch Desktop Screen**: Wide view (`≥ 1024px`) with sidebar and multi-column analytics grid.
2. [ ] **Stitch Mobile Screen**: Compact view (`< 768px`) with docked bottom navigation.
3. [ ] **Cross-Screen Link Wiring**: Wire `href` anchors to parent/child pages and register in `index.html`.
4. [ ] **Backend Router Alignment**: Validate Pydantic schema and FastAPI endpoint path in `BACKEND-v2.md`.
5. [ ] **Database Table Scope**: Verify row-level security rule in `DATA_MODEL-v2.md` (`core/ownership.py`).
6. [ ] **SolidJS Component**: Build reactive view in `solidjs/src/pages/` using `apiClient` or `ModelService`.
7. [ ] **Responsive Verification**: Test at 390px, 768px, and 1440px in `index.html`.
