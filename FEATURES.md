# CropSense AI: feature list

This file is separate from `README.md`. It lists what the app does today, checked against the running local stack
(`backend-rec` :8001, `frontend-rec` :3002) on 2 Oct 2026. The only app change was removing stray `/* Assistant Turn Message */` text shown above assistant replies (`solidjs/src/pages/Assistant.tsx`). The demo video is built with `python3 scripts/build_video.py`
(clips from `scripts/record_demo.cjs`, slides from the pitch deck PDF, captions in `artifacts/video/cropsense-demo.srt`).

Status key: **Live** means the screen calls the real backend and shows real results. **Prototype** means the screen
is designed and routed, but it shows sample data (its backend API may already exist).

## 1. Live features (shown in the demo video)

| # | Feature | What the farmer does | Under the hood | Video |
|---|---|---|---|---|
| 1 | Landing page | Sees what CropSense does, then opens the demo | SolidJS PWA, AgriSense Premier design tokens | 02 |
| 2 | Sign-in and demo account | Signs in with email, or taps "Try the demo farmer account" (temporary account, deleted after 24 h) | Firebase Auth; `POST /auth/demo` | 03 |
| 3 | Language switch | Switches the menus to हिंदी, मराठी or ਪੰਜਾਬੀ | `stores/i18n.store.ts` (only the menus are translated so far) | 03 |
| 4 | Register a farm by pincode | Types a name and pincode 313001; state, district and village fill in | `GET /address/pincode/{pin}` (India Post), `POST /farms` | 04 |
| 5 | My farms / my crops | Sees their own farms and crops, or an empty state | `GET /farms`, `GET /crops/my-crops`, row-level ownership | 04 |
| 6 | 365-day crop plan | Picks a farm, sets a budget, gets a kharif / rabi / zaid rotation | `POST /annual-strategy` → **Gemini 3.8 Flash** on Vertex AI (JSON mode), using soil profile and weather forecast | 05 |
| 6a | Regenerative practices | Each practice is tied to the farm data behind it ("Based on: pH 8.2, low organic carbon") | Same Gemini call | 05 |
| 6b | Honest fallback | If Gemini doesn't answer, the plan is labelled as a fallback | `is_fallback` in the response | — |
| 7 | Ask CropSense (chat and voice) | Asks "Is rabi mein kaunsi fasal lagaun?" and gets a Hinglish answer with a crop/variety/sowing table, quick-reply chips and links | `POST /voice/assist` → **Gemini 3.5 Flash-Lite**, with the farmer's own farms, crops and animals as context | 07 |
| 7a | One-question-at-a-time forms | The assistant asks one question at a time to add an animal or crop, then shows a preview to approve | `voice_assist_service.py` | — |
| 7b | Read aloud | "Listen" reads the reply in an Indian voice | `lib/fluent-tts.ts` | 07 |
| 8 | Photo diagnosis | Uploads a leaf photo and gets the disease, severity and treatment ("Brown Rust (Leaf Rust), severe, 95%"); banned pesticides are removed and a CIBRC label note is added | `POST /vision/diagnose-crop` → **Gemini 3.8 Flash** (multimodal) | 06 |
| 9 | Plant a crop / create a plot / farm analytics | Adds records to a farm | Farm, plot and crop APIs | — |
| 10 | Installable PWA | Installs to the home screen; works offline on low bandwidth | `public/manifest.json`, `public/sw.js` | — |

## 2. Prototype screens (sample data, backend API exists)

| Area | Screens | Backend already there |
|---|---|---|
| Climate and alerts | Climate hub | `weather.py`, `severe_weather.py`, `weather_recommendations.py` |
| Marketplace | Browse, detail, my listings, buyer dashboard, bookings, market intelligence, supply planning | `marketplace.py`, `market_data.py`, `market_intelligence.py`, `supply_requests.py`, `advance_booking.py` |
| Livestock (Pashu) | Pashu home, livestock hub, diet plan, vets, livestock marketplace | `livestock*.py`, `veterinary.py`, `vaccination_reminders.py` |
| Soil and pests | Soil & fertilizer hub, pest & disease hub | `soil*.py`, `slusi.py`, `fertilizer_*.py`, `pest_disease.py` |
| Logistics | Transport tracking | `transport.py` |
| Account | Profile, security, notifications, quota history, settings | `users.py`, `notifications.py`, `ai_quota.py` |
| Admin | Platform analytics, quota monitoring | `analytics.py`, `ai_quota.py` |

## 3. Platform

- **Google Cloud:** Vertex AI (Gemini 3.8 Flash, 3.5 Flash-Lite, 2.5 Flash fallback), Cloud Run, Cloud SQL, Firebase
  Auth, Secret Manager, BigQuery. Deployed with `./deploy-gcp.sh` / `terraform/gcp/`.
- **Schema-first:** `database/Model/*.json` → SQL, Pydantic, ORM and TypeScript via `setup.php`.
- **Security:** row-level ownership checks on 39 tables (`python/app/core/ownership.py`), rate limiting.
- **Design:** 39 Stitch screens in `stitch/screens/`, showcase viewer `index.html`.

## 4. Known issues seen while recording

- The crop-plan zaid card can come back without sowing dates or cost ("Sow — • Harvest —").
- The dashboard body is English sample data, even after switching language.

## 5. Credits

- Leaf photo in segment 06 (`artifacts/video/leaf.jpg`): "Wheat leaf rust on wheat" by James Kolmer, USDA ARS, public domain, via Wikimedia Commons.
- Build captures in segments 01b–01d: your 28 Sep 2026 screen recordings (Gemini Deep Research, export to NotebookLM, Antigravity + Stitch MCP), cropped to 16:9 without the browser tab bar.
