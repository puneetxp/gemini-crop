# Handoff: make gemini-crop work end to end and complete against the hackathon criteria

This file is for an agent picking up the work cold. Everything below was verified on 2026-09-30 (last
check 22:34 IST) against `/Users/waseemakram/Documents/gemini-crop`, the live Cloud Run services, and
the baseline repo `~/Documents/apac-genaiacademy-c2`.

Read first: `AGENTS.md` (project rules; **its §4 "production-ready" status is wrong**, see §2),
`APAC-COMPARISON.md` (file-by-file diff against the baseline). Submission material (description, deck
outline, video script) is in the Claude Doc "CropSense AI — Hackathon Submission Pack".

---

## 1. Status update (read before touching anything)

| Item | State at 22:34 IST, 30 Sep 2026 |
|---|---|
| Hackathon | "Build with AI: Code for Communities" (2nd ed.), [event page](https://hack2skill.com/event/codeforcommunities2), **Track 04 Agricultural Intelligence**. Submission closed 30 Sep 23:59 IST. **Top-20 shortlist 16 Oct, virtual demo day 23 Oct.** |
| Live link | Project `cropsense-ai-a4d5cf`, region `us-central1`. [frontend](https://cropsense-frontend-ttmistutza-uc.a.run.app) rev `00014-56j`, [backend](https://cropsense-backend-ttmistutza-uc.a.run.app) rev `00026-fhw`, both 100% traffic, both **gemini-crop built from uncommitted code** (`nogit-dirty`). `/farms` returns 500; `/crops/my-crops` and diagnosis fail; any token is accepted. |
| Rollback option | apac's last good revisions still exist: backend `00022-zxz`, frontend `00013-pwx` (27 Sep). No rollback had been done at 22:34. Commands are in the Submission Pack doc. |
| gemini-crop git | 3 local commits (`29f1ccf`, `3949d07`, `391a068`), **no GitHub remote**. |
| **Uncommitted work in progress by someone else** | `python/app/api/v1/auth.py`, `api/v1/voice_agent.py`, `services/cognito_service.py`, `solidjs/src/pages/Assistant.tsx`, `solidjs/src/stores/auth.store.ts`, `solidjs/package.json`. **Don't overwrite it; ask the user first.** Note that it **widens the auth hole**: `auth.py:675-689` returns a fake user (id 1) for any `mock-*` / `test-token` with no environment check, and `auth.store.ts:48-52` skips server verification for mock tokens. Treat this as part of item 1. |
| Baseline | apac is public at [puneetxp/apac-genaiacademy-c2](https://github.com/puneetxp/apac-genaiacademy-c2). First commit 6 Jul 2026; 33 of 35 commits after the 11 Aug hackathon start. |
| Estimated score | Live gemini-crop ≈ 4.3/10, apac ≈ 6.5/10 (weighted estimate across the five criteria; see §4). |

---

## 2. Background you need

- `gemini-crop` is derived from apac. Keep apac as a **read-only reference**. Never edit it.
- The backend was **copied** from apac: `python/app/services`, `python/app/api`, `schemas`, `jobs`
  and `main.py` are byte-identical.
- `python/app/core/` was **rewritten** (db.py, model.py, auth.py, ownership.py, crud_service.py,
  rate_limiter.py, config.py, dependencies.py). The copied code still calls the *old* apac core API.
  **This mismatch is the root cause of most backend bugs.**
- The SolidJS frontend (`solidjs/src/`) was **rewritten** from the Stitch designs (`stitch/screens/`).
  - 28 of 42 pages are static mockups.
  - The app calls only 12 endpoints.
  - Translation (`stores/i18n.store.ts`, about 20 strings × en/hi/mr/pa) reaches only the navigation.
- Google AI is real but thinly exposed:
  - Gemini via `genai.Client` in `services/vision_diagnosis_service.py:106` and in the misnamed
    `services/bedrock_service.py:33`.
  - Vertex AI in `api/v1/voice_agent.py:113` and `services/predictive_analytics_service.py:78`.
  - Models are set in `core/config.py:153-156` (`gemini-3.8-flash`, fallbacks `gemini-3.5-flash-lite`,
    `gemini-2.5-flash`).
  - 24 service/API files still mention Bedrock, SageMaker or boto3.
- Code generation: `/opt/homebrew/bin/php setup.php` regenerates the DDL, Pydantic models, ORM and TS
  interfaces from `database/Model/*.json`. Don't hand-edit generated files (`python/app/models`,
  `python/app/orm`, `python/app/api/{isuper,islogin,ipublic}`, `solidjs/src/shared/Interface/Model`).
- Schema: all 58 tables have the same columns as apac. gemini-crop uses the newer compile-php `relation`
  array (FK columns implied) instead of apac's `relations` object.
- Python: `.venv/` at the repo root (Python 3.14, FastAPI 0.142). It has **no**
  `pytest_asyncio`/`hypothesis`; apac's venv (`~/Documents/apac-genaiacademy-c2/python/.venv`) has them.
- Local Postgres 18 runs via Homebrew, but there is no `postgres` role, so the app falls back to
  in-memory SQLite (`core/db.py:137`).
- `./pipeline.sh check` passes, but its "backend tests" are an inline smoke script
  (`scripts/pipeline.py:211`) that only checks the new core API. It catches none of the problems here.
- data.gov.in: apac ingests Agmarknet daily mandi prices in `python/scripts/fetch_live_api_prices.py`
  (resource `9ef84268-d588-465a-a308-a864a43d0070`, key `DATAGOV_API_KEY` via `get_system_setting`),
  orchestrated by `ingest_all.py`, plus `seed_msp_data.py`. **gemini-crop dropped `python/scripts/`
  entirely.** NDAP tables (`ndap_ingestion_run`, `ndap_downloaded_file`) exist but have no ingestion
  code.

---

## 3. The plan: phases, in order, with dates

Each phase has a gate. Don't start the next phase until its gate passes.

### Phase 1: Restore a working backend (1–4 Oct)
Put the backend back on apac's proven core instead of writing a compatibility layer. apac's own tests
(811 passing) already confirm that its core and these services work together.

1. Replace `python/app/core/{model.py, db.py, crud_service.py, auth.py, dependencies.py,
   rate_limiter.py, config.py}` with apac's versions. Keep from gemini-crop only what apac lacks:
   - `ownership.py` requester visibility for transport bookings (lines 65 and 90). Merge it into
     apac's `ownership.py`.
   - `core/__init__.py`.
   apac's `auth.py:69-76` already restricts mock tokens to development/test. Also revert the
   in-progress mock-user block in `api/v1/auth.py:675-689` (**ask the user first**, see §1).
2. Align the generated code with apac's core. The ORM differs only in column order and one relation key
   (`annual_strategy` → `strategy`, e.g. `orm/crop.py:39`).
   - Run `php setup.php`, then the harness in §6.
   - If the generated code breaks, restore apac's `database/Model/*.json` relation format and
     regenerate.
3. Bring over tests:
   - Copy apac's `python/tests/`, `python/pytest.ini` and `requirements-test.txt`.
   - Fix or delete the 12 test files that already fail to collect.
   - Make `scripts/pipeline.py:211` `test_backend()` run pytest.
   - Add a local Postgres test DB (`createdb cropsense_test`, load `database/structure.sql` +
     `relation.sql`, set `DATABASE_URL`).
4. **Gate:** the harness shows 0 tests failing only in gemini-crop. The smoke endpoints in §6 return 200.

### Phase 2: Security (4–5 Oct)
Items 1–6 in §5 P0-A. Also:
- change the `DEBUG` default to false (`core/config.py:49`),
- add `DEBUG=false` to `deploy-gcp.sh:312`,
- add one test per hole.

**Gate:** a mock token in `ENVIRONMENT=production` gets 401; other users' data gets 403; anonymous
writes get 401.

### Phase 3: Connect every page, all languages (5–11 Oct)
1. Copy apac's 22 frontend service modules (`apac/solidjs/src/services/*.service.ts`) into
   `solidjs/src/services/`, using gemini-crop's `lib/api-client.ts`.
2. Connect the 28 static pages in demo order:
   1. auth (`/auth/signin`, not `/auth/login`; Firebase refresh)
   2. farm register/detail
   3. plot create (`/farms/{id}/plots`, not `/plots`)
   4. recommendation / annual strategy (fix `annual_strategy.py:552`)
   5. plant / my crops
   6. diagnose
   7. voice / assistant
   8. soil hub
   9. climate and pest alerts
   10. marketplace and bookings (fix the booking status mismatch; add confirm/pay/complete/cancel)
   11. livestock
   12. admin
3. Translations:
   - Copy apac's `solidjs/src/i18n/{en,hi,mr,pa}.ts` (1,595 lines) into `stores/i18n.store.ts`.
   - Wrap every page string in `t()` (apac had 238 calls).
   - Save the chosen language to the profile.
4. Restore the missing pages: `plots/Analyze`, `plots/Compare`, `strategy/Results`.
5. Bring over apac's `e2e/` Playwright suite (40 files).

**Gate:** Playwright passes the demo flow in all 4 languages: sign in → farm → plot → recommendation
→ plant → diagnose → voice question.

### Phase 4: Google AI depth (8–14 Oct), the 25% criterion
- Rename `services/bedrock_service.py` → `gemini_service.py`.
- Remove the AWS leftovers: 24 files; Cognito MFA `api/v1/users.py:186,216`; CloudWatch
  `core/monitoring.py`; `/health/bedrock`.
- Rewrite the README for the Google stack and credit reused open-source code (rule 03).
- **Google Earth Engine:** Sentinel-2 NDVI/moisture per plot next to Planetary Computer. Show it on the
  plot page and feed it into recommendations.
- **Regenerative recommendations:** extend the Gemini prompt and schema with cover crops, intercropping,
  residue management instead of burning, and reduced tillage. Give each a reason and its source data.
  This is the track's exact wording.
- **Real-time localised advisories:** a daily per-district job (IMD forecast + pest alerts + crop stage)
  that sends a Gemini-written advisory in the farmer's language (push + WhatsApp link).
- **Voice/languages:** Cloud Speech-to-Text / Text-to-Speech on `/voice/assist`, plus the Translation
  API for more scheduled languages.
- **Prediction:** a BigQuery ML / Vertex AI price and yield model trained on the Phase 5 data, served
  from `predictive_analytics_service.py`.

**Gate:** each AI feature is reachable from the UI and demoed in the E2E flow. No AWS code paths remain.

### Phase 5: data.gov.in: ingest, measure impact, publish back (8–15 Oct)
**A. Ingest.**
- Bring over apac's `fetch_live_api_prices.py`, `ingest_all.py` and `seed_msp_data.py`.
- Run them as a **Cloud Run Job + Cloud Scheduler** (daily), not in-process. Store `DATAGOV_API_KEY`
  in Secret Manager.
- Load into Cloud SQL and mirror to BigQuery (`terraform/gcp/bigquery.tf`).
- Add these datasets, finding and recording each resource ID on data.gov.in (**don't guess IDs**):
  - district crop area/production/yield,
  - Agriculture Census land holdings by size class,
  - district rainfall.

**B. Impact dashboard.**
- Connect `pages/admin/PlatformAnalytics.tsx`, and add a public `/impact` page.
- Per state and district, show:
  - farmers onboarded,
  - share of small/marginal holdings reached (users ÷ data.gov.in holdings),
  - area advised,
  - advisories sent, diagnoses run,
  - price realised vs MSP / mandi average,
  - estimated fertiliser savings.
- Build them as BigQuery views behind a cached API.

**C. Publish back (digital public good).**
- Add read-only `/api/v1/open/*` endpoints with district-level anonymised aggregates (no cell under
  10 farmers).
- Offer CSV/JSON downloads and an OpenAPI spec, under CC-BY.
- Publish a DCAT/NDAP-style catalogue file.
- Put shared models in the Vertex AI Model Registry, with a Terraform variable per state.
- Make data sources pluggable adapters, so another BRICS country swaps sources, not code (rule 04).

**Gate:**
- The ingestion job runs in staging, and row counts show in Cloud SQL and BigQuery.
- `/impact` numbers reconcile with source totals for one district.
- `/open/*` returns no cell under 10 farmers.

### Phase 6: Deployability and operations (12–16 Oct)
- Push gemini-crop to a public GitHub repo, with CI: pytest, frontend build, Playwright smoke tests,
  deploy on main.
- Add a staging Cloud Run service. Production takes tagged builds from main only (no `nogit-dirty`).
- Fix the P2 items in §5.
- Write a one-page pilot runbook: a 2-week district pilot with a KVK (accounts, data load, training,
  metrics).
- Update `AGENTS.md` §4 to the real status.

**Gate:** CI is green on main, and production runs a tagged build.

### Phase 7: Demo day readiness (17–23 Oct)
- Rebuild the deck and video around the working product and the impact dashboard.
- Rehearse against production.
- Freeze deploys 48 h before 23 Oct.

### Criteria coverage
| Criterion (weight) | Gap today | Closed by |
|---|---|---|
| Problem-solution fit (20%) | Advice/diagnosis not in the UI; no regenerative framing | Phase 3, Phase 4 |
| AI / technical execution (25%) | Core flows crash; AWS leftovers | Phase 1, Phase 4 |
| Reach across India (20%) | English-only UI | Phase 3 i18n, Phase 4 Translation/Speech |
| Impact potential (15%) | No measurement | Phase 5B |
| Deployability & scalability (20%) | Live auth hole, dirty builds, no CI | Phase 2, Phase 5C, Phase 6 |

---

## 4. Scorecard at handoff (estimates, not judges' scores)

| Criterion | Weight | gemini-crop live | apac |
|---|---|---|---|
| AI / technical execution | 25% | 3/10 | 6.5/10 |
| Problem-solution fit | 20% | 5/10 | 7/10 |
| Depth & reach across India | 20% | 4/10 | 7/10 |
| Deployability & scalability | 20% | 5/10 | 6/10 |
| Impact potential | 15% | 5/10 | 6/10 |
| **Weighted** | | **≈4.3** | **≈6.5** |

---

## 5. Detailed item list (file:line)

### P0-A: Security
| # | Problem | Where | Fix |
|---|---|---|---|
| 1 | **Anyone can sign in as any user in production.** `mock-token-<email>` is accepted in every environment. `DEBUG` defaults to `true`, so any invalid Firebase token becomes `farmer@cropsense.ai`. The **uncommitted** edits make it worse (fake user id 1). Verified live: a garbage token reaches `/crops/my-crops`. | `core/auth.py:77-84`, `:94-99`; `core/config.py:49`; `deploy-gcp.sh:312`; uncommitted `api/v1/auth.py:675-689`, `stores/auth.store.ts:48-52` | Phase 1 step 1 (apac's gated `auth.py`), `DEBUG=false`, revert the mock-user block |
| 2 | Any signed-in user can read any farmer's herd and portfolio | `api/v1/livestock.py:141-170`, `:274` | Use `current_user`; forbid other farmers (admins excepted) |
| 3 | Market-data POSTs need no sign-in | `api/v1/market_data.py:26,70,115,154,408,766` | `Depends(get_current_admin)` |
| 4 | The admin pages accept any signed-in user | `solidjs/src/index.tsx:108-123` | `roles={["admin"]}` on `ProtectedRoute`; confirm the backend checks too |
| 5 | Listing counters can be inflated anonymously | `api/v1/livestock_listings.py:261,279` | Require a signed-in user; count each user once |
| 6 | Sign-out leaves data behind on a shared phone | `stores/auth.store.ts:115-133`; `public/sw.js:50-62` | Clear IndexedDB; don't cache requests with `Authorization` |

### P0-B: Backend broken by the core rewrite (all fixed by Phase 1)
7. **Model contract.** apac's `Model.where(dict)` is a class method; `.all()`, `.get_inserted()`,
   `.insert()` and `.and_where_custom()` were removed. About 150 call sites break:
   - `.where({` 52 calls / 12 files
   - `.all()` 70 calls / 66 files (every generated router)
   - `.get_inserted(` 11 calls / 6 files
   - `.and_where_custom(` 21 calls / 2 files

   Repro: `from app.orm.marketplace_listing import MarketplaceListing as M; M.where({'status':['active']})`
   → `TypeError: Model.where() missing 2 required positional arguments`.
8. **The current user is a dict** (`core/auth.py:108` `resolve_user_from_db`). 100 `current_user.<attr>`
   uses in 22 files fail, including `api/v1/vision_diagnosis.py:163,196` (**diagnosis is broken**) and
   `/crops/my-crops`.
9. **`get_db` hides errors** (`core/dependencies.py:53-68`): the `except` wraps the `yield`, so
   endpoint errors become `RuntimeError: generator didn't stop after throw()` (`/farms`,
   `/marketplace/listings`).

### P1: Frontend and flows (Phase 3)
10. 28 of 42 pages are static (e.g. `pages/marketplace/Browse.tsx:5`, booking pages, `livestock/*`,
    `admin/*`, `quota/QuotaHistory.tsx`, `soil/SoilFertilizerHub.tsx`,
    `pest-disease/PestDiseaseHub.tsx`, `strategy/Request.tsx`, `users/Security.tsx`).
11. Wrong or missing routes:
    - `pages/plots/Create.tsx:66` POSTs `/plots`, which doesn't exist.
    - `stores/auth.store.ts:72` POSTs `/auth/login`; the backend route is `/auth/signin`
      (`api/v1/auth.py:287`).
    - Refresh (`lib/api-client.ts:86-94` → `/auth/refresh-token`, `api/v1/auth.py:542`) returns 404
      without a `cognito_user_id`.
12. Broken flows:
    - Booking confirm: `services/supply_request_matching_service.py:1225,1278` write
      `pending_farmer_confirmation`, but `services/booking_workflow.py:174` requires `pending`.
    - `/strategy/results` returns 500: `api/v1/annual_strategy.py:552` passes `total_annual_profit`,
      but the schema field is `total_expected_profit` (`schemas/crop.py:195`).
    - No booking action UI. "Save Draft" is only `alert()` (`strategy/Request.tsx:560`). The Security
      page's 2FA toggles default to ON and are never saved.
13. Missing pages: `plots/Analyze`, `plots/Compare`, `strategy/Results`, `marketplace/BrowseInfinite`.

### P2: Tests, CI, operations (Phases 1 and 6)
14. No tests in the repo. Bring over apac's 1,416 backend tests, 40 E2E files and CI.
15. Schedulers run on every instance (`main.py:317-345`). Move them to Cloud Scheduler.
16. `jobs/weekly_yield_update.py` is never scheduled.
17. Uploads fall back to `/tmp` (`services/file_storage.py:19,29`).
18. Generated list routers don't pass pagination (e.g. `api/islogin/farm/farm.py:13-14`).
19. `deploy-gcp.sh:241-249` lists migration files from `database/migrations/`, which doesn't exist;
    `:311` `--min-instances=1` (cost decision).
20. `regex=` → `pattern=` in `api/v1/livestock_listings.py:179-184`.

### P3: Clean-up (Phase 4)
21. Dead code: `shared/run.ts`, `shared/Service/Services.ts` (calls controllers that don't exist),
    `shared/indexdb.ts`.
22. AWS leftovers: `core/monitoring.py`, `services/bedrock_service.py` (rename; it's Gemini),
    `api/v1/health.py:244`, `api/v1/users.py:186,216`.
23. Language choice saved only to localStorage (`stores/i18n.store.ts:101-104`).

Already fixed compared with apac: transport bookings visible to the requester, POSTs not retried on
5xx, no links to routes that don't exist.

---

## 6. Regression test harness (run before and after Phase 1)

Runs **apac's** tests against **gemini-crop's** `app/` without changing either repo:

```bash
H=$(mktemp -d); A=~/Documents/apac-genaiacademy-c2/python; G=~/Documents/gemini-crop/python
for n in apac gemini; do mkdir -p $H/$n; cp -R $A/tests $H/$n/tests; cp $A/pytest.ini $H/$n/; done
ln -s $A/app $H/apac/app; ln -s $G/app $H/gemini/app
for n in apac gemini; do (cd $H/$n && PYTHONPATH=$H/$n $A/.venv/bin/python -m pytest tests -q \
  -p no:cacheprovider --tb=line --continue-on-collection-errors -o addopts="" > $H/res_$n.txt 2>&1) & done; wait
for n in apac gemini; do tail -1 $H/res_$n.txt; grep -E "^(FAILED|ERROR) tests/" $H/res_$n.txt \
  | sed -E 's/ - .*//; s/^(FAILED|ERROR) //' | sort -u > $H/f_$n.txt; done
comm -13 $H/f_apac.txt $H/f_gemini.txt   # tests failing only in gemini (target: none)
```

Baseline, 30 Sep (about 8 min each, no Postgres):
- apac: 316 failed / 811 passed / 102 errors
- gemini: 338 failed / 780 passed / 111 errors
- **48 tests fail only in gemini:** `test_lightweight_orm.py` 14, `test_livestock_breeding.py` 14,
  `test_rate_limiter.py` 11, `test_veterinary_services.py` 4, `test_soil_moisture.py` 2,
  `test_generated_orm.py` 2, `test_ac2_integration.py` 1.
- About 40% fail on both sides for lack of a DB, so the real breakage is larger. Use a local Postgres
  test DB for a true picture.

Local smoke check (a mock token works only in dev/test once item 1 is fixed):
```bash
cd python && E2E_MODE=true E2E_ACTIVE=true ../.venv/bin/python - <<'EOF'
import logging; logging.disable(50)
from fastapi.testclient import TestClient
from app.main import app
H={"Authorization":"Bearer mock-token-farmer@test.local"}
with TestClient(app, raise_server_exceptions=False) as c:
    for p in ["/api/v1/farms","/api/v1/crops/my-crops","/api/v1/analytics/farm/1",
              "/api/v1/marketplace/listings","/api/v1/islogin/crop","/api/v1/auth/user"]:
        r=c.get(p,headers=H); print(r.status_code, p, r.text[:100])
EOF
```
Before the fixes: `/farms` and `/marketplace/listings` return 500 (`RuntimeError: generator didn't stop
after throw()` with `raise_server_exceptions=True`), and `/crops/my-crops` returns 500 (`'dict' object
has no attribute 'id'`).

Live smoke check (read-only):
```bash
B=https://cropsense-backend-ttmistutza-uc.a.run.app/api/v1
for p in /farms /crops/my-crops /analytics/profile-status; do echo "$p $(curl -s -H 'Authorization: Bearer garbage-token' $B$p | head -c 100)"; done
```
After Phase 1–2, every line must be 401.

---

## 7. Rules for whoever does this
- Work in phase order. Each gate must pass before the next phase.
- Don't overwrite the uncommitted in-progress files (§1) without asking the user.
- Don't redeploy or move Cloud Run traffic without the user's explicit OK. The live link is what judges
  see.
- Always keep `./pipeline.sh check` green (screens, index sync, frontend build).
- Follow `AGENTS.md`: no loose HTML in the root, keep the responsive shell classes, regenerate with
  `setup.php` rather than hand-editing generated files.
- Commit per phase with clear messages. Push only once the user has approved creating the GitHub remote.
