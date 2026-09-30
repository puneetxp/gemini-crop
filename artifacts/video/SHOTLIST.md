# CropSense AI demo video: shot list, fix list, editing notes

Recorded 1 Oct 2026, 00:04 IST, with `node scripts/record_demo.cjs --url http://localhost:3002 --api http://localhost:8001`
(the local stack with tonight's fixes; see "Local stack" below). Headed Chromium, 1920×1080, one `.webm` per segment,
stills in `stills/`. Raw results are in `summary.json`.

## 1. Shot list

| # | File | Length (raw) | On screen | Narration | Status |
|---|---|---|---|---|---|
| 01 | your own captures | 0:40 | Udaipur farmers; Gemini Deep Research, NotebookLM, Stitch, Antigravity | "Our first version of CropSense did too much… Antigravity's Gemini agents turned them into working code." | **Needs your footage** |
| 02 | `02-landing.webm` | 22 s | Home hero, slow scroll through the feature cards, back to top | "CropSense gives every small farmer advice for their own field, in their own language, powered by Gemini 3.8 Flash." | **Ready** |
| 03 | `03-signin-language.webm` | 16 s | Sign-in → "Instant Demo Sign-In" → dashboard → language switch to हिंदी → back to English | "Farmers sign in with Google, and the whole app switches to Hindi, Marathi or Punjabi." | **Needs a re-record.** Only the sidebar switches to Hindi; the dashboard body stays English and is sample data. The button says "Instant Demo Sign-In (Dev/E2E)", not Google. See fixes F4 and F8. |
| 04 | `04-register-farm.webm` | 31 s | Register farm: name, pincode 313001 → "✓ Udaipur, Rajasthan", state/district/village auto-fill, 2.5 acres, submit → **real** farm in the list | "Here's a farm near Udaipur. From just the pincode we know the district. Soil nutrients come from the Soil Health Card…" | **Ready** (real API; `POST /farms` 201). The screen shows no soil-card nutrients, and the page still has Nashik/MahaBhumi decorations (F6). |
| 05 | `05-crop-plan.webm` | 22 s | Select farm → request strategy → "Generate 365-Day Strategy" → strategy page | "Now we ask what to grow. Gemini 3.8 Flash on Vertex AI reads the soil card…" | **Uses sample data.** Don't use it with this narration. "Generate" never calls the API, and the farm picker and result page are hardcoded (F2). |
| 06 | — | — | Diagnose: upload a leaf photo, AI result | "When something goes wrong, the farmer just takes a photo…" | **Not recorded.** `artifacts/video/leaf.jpg` is missing, and Gemini has no credentials locally (F1, F3). The page now works end to end apart from those two. |
| 07 | `07-voice.webm` | 23 s | Assistant: types "Is rabi mein kaunsi fasal lagaun?", send | "Many farmers don't type, so they just ask…" | **Failed.** The reply is "Sorry, the AI assistant is unavailable right now". There are no Gemini credentials (F1). Re-record after F1. |
| 08 | `08-alerts-market.webm` | 18 s | Climate hub (alerts), scroll → Mandi marketplace, scroll | "Advice doesn't stop at planting: weather and pest alerts, mandi prices from data.gov.in…" | **Uses sample data.** Neither page calls the API (F5). Usable as a quick visual if the narration doesn't say "live". |
| 09 | deck slides 5 / 11 | 0:30 | Architecture slide | "It's Gemini on Google Cloud…" | **Needs your slides** |

Re-record one segment after fixing it with `node scripts/record_demo.cjs --url http://localhost:3002 --api http://localhost:8001 --only 07`.
The script never fakes a result. A failing step shows as failing on video and as FAIL in the summary.

## 2. Fix list (what blocks the video first)

### Already fixed tonight (uncommitted)
| Item | File | What changed |
|---|---|---|
| N2/N7 Register farm | `solidjs/src/pages/farm/Register.tsx` | Pincode → `GET /address/pincode/{pin}` fills state/district/village. The soil and irrigation values now match the backend enums. "Success" shows only on 2xx; otherwise the API's error appears. The fake "saved in offline cache" success is removed. |
| N8 Farm list | `solidjs/src/pages/farm/Index.tsx` | Loads `GET /farms`, keeps the card design, and shows an empty state with a "Register farm" button. |
| N9 My Crops | `solidjs/src/pages/crops/MyCrops.tsx` | Renders `GET /crops/my-crops`, with an empty state instead of sample crops. Sensor tiles are hidden when there's no sensor data. |
| Mock token gate | `solidjs/src/stores/auth.store.ts:48` | Already gated on `import.meta.env.DEV`; no change needed. |
| **Fake diagnosis** | `solidjs/src/pages/crops/Diagnose.tsx` | It sent multipart data to a JSON endpoint, so every scan returned 422 and the page then showed a hardcoded "Yellow Rust 94%". It now sends `{image_base64, mime_type, lang}`, maps the real response, and shows the API error on failure. |
| **Fake assistant reply** | `solidjs/src/pages/Assistant.tsx` | Any failure showed a canned "wheat plot on Sector 4" answer, and real replies rendered blank (it read `data.reply` but displayed `data.response`). It now shows the real reply, or an honest "unavailable" message. |
| **Crop plan crashed** | `python/app/services/bedrock_service.py:463` | An `import json` inside the function shadowed the module import, so `POST /annual-strategy` always returned 500 ("cannot access local variable 'json'"). Removed the line. |

### Still open, in order
**F1. Gemini credentials (blocks 05, 06, 07).** This is your action: run `gcloud auth application-default login`, then restart the backend with
`GOOGLE_CLOUD_PROJECT=cropsense-ai-a4d5cf GOOGLE_CLOUD_REGION=us-central1`. Until then, `/voice/assist` returns `fallback: true` and `/vision/diagnose-crop` returns 503.

**F2. The crop-plan screens are hardcoded (blocks 05).** `solidjs/src/pages/strategy/Request.tsx:126` `handleGenerate` just runs `setTimeout(…1200)` and navigates to `/crops/annual-strategy/1`.
`pages/strategy/SelectFarm.tsx:23-80` lists hardcoded farms ("Krishna Valley Farm"), and `pages/crops/AnnualStrategyDetail.tsx` shows fixed numbers (₹6,42,000).
The fix is to load farms from `GET /farms`, POST `/annual-strategy` with `{farm_id, budget_per_acre}`, and render the returned `kharif/rabi/zaid/annual_summary`.
> Prompt for Gemini (Antigravity): "In solidjs/src/pages/strategy/SelectFarm.tsx replace the hardcoded farms array with data from apiClient.get('/farms') (response `{farms:[{id,name,village,district,state,total_area_acres,primary_soil_type,irrigation_type}]}`), keeping the card design and adding an empty state. In solidjs/src/pages/strategy/Request.tsx make handleGenerate call apiClient.post('/annual-strategy', {farm_id: Number(new URLSearchParams(location.search).get('farmId')), budget_per_acre: budget()/acres}) with timeoutMs 90000, store the response in sessionStorage keyed by farm id, and navigate to /crops/annual-strategy/<farm_id>; show the API error on failure and never fake a result. In solidjs/src/pages/crops/AnnualStrategyDetail.tsx render kharif, rabi and zaid (recommended_crop, variety, expected_profit_per_acre, planting_window, harvest_window, key_success_factors) and annual_summary (total_expected_profit_per_acre, roi_percentage, risk_level) from that response instead of the hardcoded values. Run ./pipeline.sh build-frontend."

**F2b. The crop plan silently falls back without Gemini.** With no credentials, `POST /annual-strategy` still returns 201 with a generic plan ("Cotton/Wheat, Local variety", confidence 0.6) and no fallback flag, so a UI would show it as AI advice.
In `python/app/services/bedrock_service.py` `_create_fallback_strategy` (≈line 1179), add `"fallback": true` to the response, and have the page label it.
> Prompt: "In python/app/services/bedrock_service.py, whenever get_annual_crop_strategy returns the result of _create_fallback_strategy (model unavailable or unparsable), add `\"is_fallback\": True` and a `\"fallback_reason\"` string to the returned dict, and expose `is_fallback` in AnnualStrategyResponse (python/app/schemas/crop.py). Don't change the success path."

**F3. Leaf photo (blocks 06).** This is your action: put a real diseased-leaf photo at `artifacts/video/leaf.jpg`.

**F4. Hindi switch only translates the sidebar (blocks 03).** The dashboard (`solidjs/src/pages/Dashboard*.tsx`) uses hardcoded English strings and sample figures ("Green Valley Plot 4A", "14 Animals", "₹4,85,000").
The narration says "the whole app switches". Either re-word it to "the menus switch…", or translate the dashboard headings with `t()` from `stores/i18n.store.ts`.
> Prompt: "In the SolidJS dashboard page (route /dashboard), wrap every user-visible heading, label and button in t('dashboard.<key>') from solidjs/src/stores/i18n.store.ts and add en/hi/mr/pa strings for each key to the store. Don't change layout or data."

**F5. Climate hub and marketplace are hardcoded (08).** `pages/climate/ClimateHub.tsx` and `pages/marketplace/Browse.tsx` make no API calls. Wire them to the backend's `/weather`, `/severe-weather`, `/market-data` and `/marketplace` endpoints, or narrate them as "screens" rather than live data.
> Prompt: "solidjs/src/pages/climate/ClimateHub.tsx and solidjs/src/pages/marketplace/Browse.tsx render hardcoded arrays. Read python/app/api/v1/weather.py, severe_weather.py, market_data.py and marketplace.py, and replace the hardcoded arrays with apiClient calls to the matching GET endpoints (use the signed-in farmer's first farm from GET /farms for location). Keep the design, add loading and empty states, and show the API error on failure."

**F6. Register page leftovers (04 cosmetics).** `Register.tsx` still defaults to Nashik values: survey "Pimpalgaon Baswant — Gut #142/2A", 18.5 acres, and map labels "MahaBhumi Cadastral Gut #142/2A" / "MahaBhumi Verified".
Neither the Soil Health Card nor SLUSI nutrients are shown, although the narration mentions them. Blank the defaults, and add a soil panel from `/soil-health` or `/slusi` for the district.

**F7. `DELETE /farms/{id}` returns 500.** `python/app/api/v1/farms.py:716` runs `FarmPlot.where(...).update({"is_active": False})`, which builds `UPDATE "farm_plots" SET WHERE …`. `farm_plots` has no `is_active` column, so the SET is empty. The farm is still hidden, because the farm update runs first.
> Prompt: "In python/app/api/v1/farms.py delete_farm, the FarmPlot.where({'farm_id':[id]}).update({'is_active': False}) call generates an empty SET because farm_plots has no is_active column. Check database/Model/farm_plot.json; either drop that call, or add the column via the model JSON and regenerate with /opt/homebrew/bin/php setup.php. Add a test that DELETE /api/v1/farms/{id} returns 200."

**F8. Sign-in vs narration (03).** The demo uses "Instant Demo Sign-In (Dev/E2E)", which only works because the backend runs with `ENVIRONMENT=development`. For "sign in with Google", record the real Google sign-in on the deployed app, or crop the button label.

**F9. The mock user id doesn't match the database.** `solidjs/src/stores/auth.store.ts:110` `signInWithMock` hardcodes `id: 1`, but `farmer@cropsense.ai` is user 2 in `cropsense_dev`. Only cached UI state is affected; the backend resolves the real user from the token.

**F10. The crop-plan ownership check may be wrong.** `python/app/api/v1/annual_strategy.py:200` reads `farm.get("owner_id") or farm.get("user_id")`, while the API schema calls it `farmer_id`. It works locally because the `farms` table has `owner_id`; verify this on Cloud SQL.

Everything else is in `HANDOFF-FIXES.md` (auth hole in production, CI, migrations).

## 3. Editing notes
- **Order:** 01 (your footage) → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 (slides). Target 4:50; the final export **must be 1920×1080, 3–5 min**.
- **Trims:** every clip starts with ~1.5 s of page load and ends with a 1.5 s hold, so trim the white first frames.
- **Too short for their narration:** 03 (16 s vs 20 s), 04 (31 s vs 45 s), 05 (22 s vs 45 s), 07 (23 s vs 35 s). Lengthen them with freeze frames on the key moment:
  03 on the Hindi dashboard, 04 on "✓ Udaipur, Rajasthan" and on the new farm card, 07 on the reply.
- **Stills** (`stills/`, 1920×1080): `02-landing.png` for the thumbnail and deck title, `04-register-farm.png` for the "pincode → district" deck slide, and `03-signin-language.png` for the language slide.
  `05-crop-plan.png`, `07-voice.png` and `08-alerts-market.png` currently show sample data or an error, so don't use them in the deck until they're re-recorded.
- **Cursor:** the yellow dot is a recording overlay (Playwright doesn't capture the OS pointer), and it's hidden in stills.
- **Wording rules:** say "rewrote" or "rebuilt", never "built from scratch", and "with Gemini at every step", never "only Gemini". You confirm the Udaipur details.

## Local stack used
The servers on :3000/:8000 belong to another session, and that backend doesn't auto-reload, so it doesn't have the `bedrock_service.py` fix.
This recording used `.claude/launch.json` entries `backend-rec` (:8001, `--reload`) and `frontend-rec` (:3002). Both use the same `cropsense_dev` database.
