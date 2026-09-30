# CropSense AI

**AI farm advice for India's small and marginal farmers, for their own field and in their own language.**

Built for *Build with AI: Code for Communities* (2nd edition), **Track 04: Agricultural Intelligence**.

- **Live app:** https://cropsense-frontend-ttmistutza-uc.a.run.app
- **API docs (OpenAPI):** https://cropsense-backend-ttmistutza-uc.a.run.app/docs
- **Try it without signing up:** *Try the demo farmer account* on the sign-in page (or *Instant Demo Access* on the
  home page) opens your own temporary account with a sample farm near Udaipur. It stays signed in for your visit
  and is deleted, with everything you added, after 24 hours.

A farmer registers a farm with a pincode. CropSense then places the farm in its district and uses the farm's soil
test, the district weather forecast and satellite readings to build a regenerative, three-season crop plan with
Gemini. The same app diagnoses crop disease from a leaf photo, and answers spoken or typed questions in Hindi,
Marathi, Punjabi or English.

## What works today

| Flow | What happens | Google AI |
|---|---|---|
| **Register a farm** | Pincode → state, district and villages (India Post), soil type, irrigation, area | — |
| **Crop plan** | Kharif / rabi / zaid crops and varieties, sowing and harvest dates, cost and profit per acre, month-by-month actions, and 3–6 **regenerative practices** (legume rotation, green manure, residue incorporation instead of burning, reduced tillage, organic inputs), each tied to the farm data it responds to | Gemini 3.8 Flash on Vertex AI (JSON mode) |
| **Photo diagnosis** | Leaf photo → disease, severity, organic / cultural / chemical treatment. A safety check removes pesticides banned in India and adds the CIBRC label note | Gemini 3.8 Flash multimodal |
| **Voice & chat assistant** | Speak or type in the farmer's language; answers use the farmer's own farms, crops and animals, can open the right screen, and can draft records the farmer approves | Gemini 3.5 Flash-Lite (audio in); replies read aloud in the browser |
| **My farms / my crops** | The farmer's own records, per account | — |

If Gemini is unavailable, the crop plan says so (`is_fallback`) instead of presenting a generic plan as advice.

**Prototype screens.** Marketplace, livestock, climate, soil hub and admin pages are UI prototypes that still show
sample data. Their backend APIs exist (see `/docs`), but they are not yet connected to those screens.

## How the crop plan is grounded

Gemini receives the farm profile and live context, then returns structured JSON:

| Input | Source |
|---|---|
| State, district, village | Pincode lookup (India Post) |
| Soil N, P, K, pH, organic carbon | The farmer's soil-test values, else a typical profile for the district (`services/soil_mapping.py`) |
| Soil type, irrigation, area, budget per acre | Farm record and the request |
| 5-day weather forecast | OpenWeather, at the farm's GPS point or the district's coordinates |
| Crop vigour and water stress | Sentinel-2 NDVI / NDMI via Microsoft Planetary Computer (farms with a GPS point) |
| District soil moisture | data.gov.in (when ingested) |

Code: `python/app/api/v1/annual_strategy.py` (context), `python/app/services/bedrock_service.py`
(`get_annual_crop_strategy`, the Gemini prompt; the file name is historical).

## Google Cloud and Gemini

| Service | Used for |
|---|---|
| **Gemini 3.8 Flash** (Vertex AI) | Crop plans, photo diagnosis |
| **Gemini 3.5 Flash-Lite** (Vertex AI) | Voice / text assistant (audio understanding, intent, form filling) |
| Gemini 2.5 Flash | Fallback when the models above don't answer |
| Cloud Run | Frontend (nginx) and backend (FastAPI) |
| Cloud SQL (PostgreSQL) | Farms, crops, diagnoses, plans |
| Firebase Authentication | Email / password accounts |
| Secret Manager, Cloud Build, Artifact Registry | Secrets and image builds |
| BigQuery, Firestore | Analytics dataset (`cropsense_analytics`), app data |

Model ids and the Vertex AI endpoint are set in `python/app/core/config.py` (`GEMINI_MODEL`,
`GEMINI_ASSIST_MODEL`, `GEMINI_FALLBACK_MODEL`, `GEMINI_LOCATION=global`).

## Built for all of India

- **Any state, any district.** Farms are keyed by pincode, so location, soil and weather context follow for any
  district. Nothing is hard-coded to one region.
- **Languages.** The UI ships in English, Hindi, Marathi and Punjabi (`solidjs/src/i18n/`); the assistant and
  diagnosis answer in the selected language.
- **Low bandwidth.** An installable PWA with offline caching (`solidjs/public/sw.js`).
- **Interoperable.** A schema-first data model (`database/Model/*.json`, 58 tables) generates the SQL, API models
  and TypeScript types, and every endpoint is documented in OpenAPI at `/docs`.
- **Deploy per state.** `./deploy-gcp.sh` and `terraform/gcp/` stand up a complete instance (Cloud Run, Cloud SQL,
  Firebase, BigQuery, Secret Manager) in a new Google Cloud project.

- **Beyond India.** Weather (OpenWeather), satellite (Sentinel-2) and Gemini work worldwide. The India-specific
  parts are the pincode lookup, Soil Health Card values and data.gov.in feeds, so another BRICS country would
  replace those sources and keep the platform.

**Roadmap (not built yet):** shared recommendation models between states, anonymised district-level open data
exports, proactive advisories pushed to farmers, and more of India's 22 scheduled languages.

## Run locally

Requirements: Python 3.12, Node 20+, PostgreSQL 14+ with `pgvector`, and `gcloud` for Gemini.

```bash
# Database
createdb cropsense_dev
psql -d cropsense_dev -c 'CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pgcrypto; CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
psql -d cropsense_dev -f database/structure.sql -f database/relation.sql -f database/insert.sql

# Backend (http://localhost:8000, docs at /docs)
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in the values
gcloud auth application-default login
uvicorn app.main:app --reload --port 8000

# Frontend (http://localhost:3000)
cd solidjs
npm ci
VITE_API_URL=http://localhost:8000 npx vite --port 3000
```

The demo button works locally too: outside production it signs in with a mock token instead of creating a
Firebase user. Demo lifetime and limits: `DEMO_TTL_HOURS` (24), `DEMO_MAX_ACTIVE` (200), `DEMO_LOGIN_ENABLED`.

## Deploy to Google Cloud

```bash
./deploy-gcp.sh all        # first deploy: APIs, secrets, Terraform, schema, both services
./deploy-gcp.sh app        # later: rebuild and deploy backend + frontend
```

See the header of `deploy-gcp.sh` for the options.

## Repository layout

| Path | Contents |
|---|---|
| `python/app/` | FastAPI backend: `api/v1` (endpoints), `services` (Gemini, weather, soil, satellite…), `core` (DB, auth, config) |
| `solidjs/src/` | SolidJS + Tailwind frontend (PWA) |
| `database/` | Model JSON (source of truth), generated SQL, migrations |
| `stitch/` | Screen designs (Google Stitch prototypes) and design tokens |
| `terraform/gcp/`, `deploy-gcp.sh` | Infrastructure and deployment |

## Origin and credits

CropSense AI is a rewrite of the author's earlier open-source project
[puneetxp/apac-genaiacademy-c2](https://github.com/puneetxp/apac-genaiacademy-c2), started in July 2026. Its backend
(FastAPI services, API routes, core layer and data model) and deployment scripts were carried over and adapted. The
frontend was rebuilt from new Google Stitch designs for this hackathon, together with the voice assistant and the
grounding of Gemini crop plans in soil tests, weather, satellite data and regenerative practices.

Open-source components: [FastAPI](https://fastapi.tiangolo.com) (MIT), [SolidJS](https://www.solidjs.com) (MIT),
[Vite](https://vitejs.dev) (MIT), [Tailwind CSS](https://tailwindcss.com) (MIT),
[Material Symbols](https://fonts.google.com/icons) (Apache-2.0),
[puneetxp/compile-php](https://github.com/puneetxp/compile-php) (Apache-2.0, schema code generator), and the Python
packages in `python/requirements.txt`.

Data: India Post pincode API, data.gov.in (Government Open Data License – India), Soil Health Card and SLUSI
(Ministry of Agriculture & Farmers Welfare), OpenWeather, and Copernicus Sentinel-2 imagery via Microsoft Planetary
Computer.
