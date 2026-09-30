# gemini-crop vs apac-genaiacademy-c2: file-by-file comparison

_Generated 2026-09-30. Baseline: `/Users/waseemakram/Documents/apac-genaiacademy-c2` (origin `puneetxp/apac-genaiacademy-c2`, HEAD `e323b9d`)._

## 1. Method

- Walked both repos and compared text/source files (`.cfg`, `.css`, `.html`, `.ini`, `.js`, `.json`, `.jsx`, `.md`, `.php`, `.py`, `.sh`, `.sql`, `.tf`, `.toml`, `.ts`, `.tsx`, `.txt`, `.yaml`, `.yml`).
- Excluded: `.git`, `.hypothesis`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.venv`, `__pycache__`, `backups`, `build`, `coverage`, `dist`, `graphify-out`, `node_modules`, `playwright-report`, `test-results`, `vendor`, `venv`, lockfiles, and files over 2 MB.
- **Identical** means byte-for-byte equal at the same path. **Similarity** is the line-level `difflib.SequenceMatcher.ratio()` (0–100%).
- **Line overlap** counts gemini-crop lines that also appear, in order, in the apac file at the same path.
- JSON schema files often score low only because of reformatting, so section 5 compares `database/Model` by structure (fields and relations).

## 2. Summary

| | apac-genaiacademy-c2 | gemini-crop |
|---|---:|---:|
| Files | 1402 | 737 |
| Lines | 237,438 | 135,070 |

- Same path in both: **669**. Identical: **430**, modified: **239**.
- Only in apac: **733**. Only in gemini-crop: **68** (6 of them are identical to an apac file at a different path).
- **Line overlap: 83,380 / 135,070 = 61.7%** of gemini-crop's lines also appear in apac.

**Bottom line:** the backend is copied (services, api, schemas and jobs are identical). The `python/app/core` base layer was rewritten. The frontend pages were rewritten from the Stitch designs. The data model has the same 58 tables with the same columns; only the JSON formatting and relation syntax changed.

## 3. By layer

| Layer | apac | gemini | same path | identical | modified | avg similarity* | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| Backend services | 124 | 124 | 124 | 124 | 0 | 100% | copied |
| Backend API routes | 179 | 180 | 177 | 177 | 0 | 100% | copied |
| Backend schemas | 18 | 18 | 18 | 18 | 0 | 100% | copied |
| Backend jobs | 3 | 3 | 3 | 3 | 0 | 100% | copied |
| Backend agents | 2 | 2 | 2 | 1 | 1 | 69% | edited |
| Backend core | 23 | 24 | 23 | 14 | 9 | 72% | edited |
| Generated Pydantic models | 59 | 59 | 59 | 22 | 37 | 94% | edited |
| Generated ORM | 59 | 59 | 59 | 24 | 35 | 96% | edited |
| Other python | 251 | 3 | 3 | 2 | 1 | 68% | edited |
| Schema JSON | 58 | 58 | 58 | 2 | 56 | 70% | edited |
| Other database | 87 | 4 | 4 | 1 | 3 | 82% | edited |
| Generated TS interfaces | 62 | 58 | 58 | 23 | 35 | 92% | edited |
| Frontend shared | 21 | 5 | 4 | 1 | 3 | 62% | edited |
| Frontend pages | 47 | 42 | 42 | 0 | 42 | 8% | rewritten |
| Frontend components | 80 | 4 | 0 | 0 | 0 | – | only in one repo |
| Other frontend | 86 | 14 | 13 | 0 | 13 | 28% | rewritten |
| Terraform | 33 | 11 | 11 | 11 | 0 | 100% | copied |
| Skills | 7 | 8 | 7 | 6 | 1 | 89% | edited |
| Root files | 23 | 13 | 4 | 1 | 3 | 62% | edited |
| Other (cognito-only) | 3 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (.aws) | 2 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (Resource) | 14 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (docs) | 6 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (.claude) | 1 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (.github) | 4 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (.agents) | 83 | 8 | 0 | 0 | 0 | – | only in one repo |
| Other (e2e) | 40 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (schema_generator) | 11 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (tools) | 2 | 0 | 0 | 0 | 0 | – | only in one repo |
| Other (scripts) | 14 | 1 | 0 | 0 | 0 | – | only in one repo |
| Other (stitch) | 0 | 39 | 0 | 0 | 0 | – | only in one repo |

_*Average over same-path files, counting identical files as 100%._

## 4. Modified files

Sorted from least to most similar. `+`/`−` are lines added/removed in gemini-crop compared with apac.

### Backend agents (1)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `python/app/agents/orchestrator_agent.py` | 37.7% | 77 → 114 | +78 / −41 |

### Backend core (9)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `python/app/core/db.py` | 3.8% | 343 → 290 | +278 / −331 |
| `python/app/core/model.py` | 8.1% | 415 → 353 | +322 / −384 |
| `python/app/core/ownership.py` | 9.6% | 134 → 241 | +223 / −116 |
| `python/app/core/crud_service.py` | 13.9% | 126 → 191 | +169 / −104 |
| `python/app/core/rate_limiter.py` | 16.7% | 295 → 159 | +121 / −257 |
| `python/app/core/auth.py` | 17.3% | 359 → 311 | +253 / −301 |
| `python/app/core/dependencies.py` | 44.4% | 91 → 134 | +84 / −41 |
| `python/app/core/config.py` | 47.0% | 292 → 329 | +183 / −146 |
| `python/app/core/alerting.py` | 99.2% | 616 → 622 | +8 / −2 |

### Generated Pydantic models (37)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `python/app/models/soil_health.py` | 12.5% | 39 → 9 | +6 / −36 |
| `python/app/models/ndap_downloaded_file.py` | 68.6% | 14 → 21 | +9 / −2 |
| `python/app/models/advance_booking.py` | 85.7% | 42 → 42 | +6 / −6 |
| `python/app/models/breeding_record.py` | 85.7% | 42 → 42 | +6 / −6 |
| `python/app/models/offspring.py` | 85.7% | 42 → 42 | +6 / −6 |
| `python/app/models/fertilizer_application.py` | 86.1% | 72 → 72 | +10 / −10 |
| `python/app/models/supply_match.py` | 87.0% | 46 → 46 | +6 / −6 |
| `python/app/models/market_price.py` | 87.5% | 48 → 48 | +6 / −6 |
| `python/app/models/livestock_transaction.py` | 89.7% | 58 → 58 | +6 / −6 |
| `python/app/models/crop.py` | 91.3% | 46 → 46 | +4 / −4 |
| `python/app/models/pest_disease_alert.py` | 91.7% | 48 → 48 | +4 / −4 |
| `python/app/models/transport_booking.py` | 91.9% | 74 → 74 | +6 / −6 |
| `python/app/models/annual_strategy.py` | 92.3% | 52 → 52 | +4 / −4 |
| `python/app/models/crop_expense.py` | 92.3% | 26 → 26 | +2 / −2 |
| `python/app/models/ai_usage_quota.py` | 92.6% | 27 → 27 | +2 / −2 |
| `python/app/models/livestock.py` | 92.6% | 54 → 54 | +4 / −4 |
| `python/app/models/marketplace_listing.py` | 93.1% | 58 → 58 | +4 / −4 |
| `python/app/models/livestock_marketplace_listing.py` | 93.5% | 62 → 62 | +4 / −4 |
| `python/app/models/soil_test_result.py` | 93.5% | 62 → 62 | +4 / −4 |
| `python/app/models/livestock_health_record.py` | 93.8% | 32 → 32 | +2 / −2 |
| `python/app/models/payment_milestone.py` | 93.8% | 32 → 32 | +2 / −2 |
| `python/app/models/quality_verification.py` | 93.8% | 32 → 32 | +2 / −2 |
| `python/app/models/user_notification.py` | 93.8% | 32 → 32 | +2 / −2 |
| `python/app/models/weather_alert.py` | 94.4% | 36 → 36 | +2 / −2 |
| `python/app/models/crop_milestone.py` | 94.7% | 38 → 38 | +2 / −2 |
| `python/app/models/satellite_observation.py` | 94.7% | 38 → 38 | +2 / −2 |
| `python/app/models/soil_amendment.py` | 94.7% | 76 → 76 | +4 / −4 |
| `python/app/models/voice_assist_log.py` | 95.5% | 44 → 44 | +2 / −2 |
| `python/app/models/buyer_interest.py` | 95.7% | 46 → 46 | +2 / −2 |
| `python/app/models/livestock_listing.py` | 95.7% | 92 → 92 | +4 / −4 |
| `python/app/models/crop_diagnosis.py` | 95.8% | 48 → 48 | +2 / −2 |
| `python/app/models/farm_plot.py` | 96.3% | 54 → 54 | +2 / −2 |
| `python/app/models/supply_request.py` | 96.4% | 56 → 56 | +2 / −2 |
| `python/app/models/transport_provider.py` | 96.4% | 56 → 56 | +2 / −2 |
| `python/app/models/livestock_roi_prediction.py` | 96.5% | 114 → 114 | +4 / −4 |
| `python/app/models/active_role.py` | 97.3% | 19 → 18 | +0 / −1 |
| `python/app/models/soil_test.py` | 97.9% | 94 → 94 | +2 / −2 |

### Generated ORM (35)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `python/app/orm/advance_booking.py` | 78.9% | 62 → 47 | +4 / −19 |
| `python/app/orm/marketplace_listing.py` | 81.7% | 65 → 50 | +3 / −18 |
| `python/app/orm/market_price.py` | 88.0% | 50 → 50 | +6 / −6 |
| `python/app/orm/soil_amendment.py` | 88.1% | 59 → 59 | +7 / −7 |
| `python/app/orm/farm_plot.py` | 88.7% | 58 → 48 | +1 / −11 |
| `python/app/orm/livestock_transaction.py` | 88.7% | 60 → 55 | +4 / −9 |
| `python/app/orm/annual_strategy.py` | 88.9% | 52 → 47 | +3 / −8 |
| `python/app/orm/user.py` | 88.9% | 100 → 80 | +0 / −20 |
| `python/app/orm/supply_match.py` | 89.8% | 49 → 49 | +5 / −5 |
| `python/app/orm/fertilizer_application.py` | 91.7% | 72 → 72 | +6 / −6 |
| `python/app/orm/livestock_listing.py` | 92.1% | 72 → 67 | +3 / −8 |
| `python/app/orm/supply_request.py` | 92.5% | 49 → 44 | +1 / −6 |
| `python/app/orm/offspring.py` | 93.6% | 47 → 47 | +3 / −3 |
| `python/app/orm/payment_milestone.py` | 93.8% | 32 → 32 | +2 / −2 |
| `python/app/orm/quality_verification.py` | 93.8% | 32 → 32 | +2 / −2 |
| `python/app/orm/breeding_record.py` | 94.2% | 52 → 52 | +3 / −3 |
| `python/app/orm/soil_test_result.py` | 94.2% | 52 → 52 | +3 / −3 |
| `python/app/orm/transport_booking.py` | 95.2% | 63 → 63 | +3 / −3 |
| `python/app/orm/crop.py` | 95.3% | 64 → 64 | +3 / −3 |
| `python/app/orm/pest_disease_alert.py` | 95.6% | 45 → 45 | +2 / −2 |
| `python/app/orm/livestock.py` | 95.9% | 73 → 73 | +3 / −3 |
| `python/app/orm/livestock_marketplace_listing.py` | 96.2% | 52 → 52 | +2 / −2 |
| `python/app/orm/crop_expense.py` | 96.6% | 29 → 29 | +1 / −1 |
| `python/app/orm/ai_usage_quota.py` | 96.7% | 30 → 30 | +1 / −1 |
| `python/app/orm/livestock_health_record.py` | 96.9% | 32 → 32 | +1 / −1 |
| `python/app/orm/user_notification.py` | 96.9% | 32 → 32 | +1 / −1 |
| `python/app/orm/weather_alert.py` | 97.1% | 34 → 34 | +1 / −1 |
| `python/app/orm/crop_milestone.py` | 97.1% | 35 → 35 | +1 / −1 |
| `python/app/orm/satellite_observation.py` | 97.1% | 35 → 35 | +1 / −1 |
| `python/app/orm/voice_assist_log.py` | 97.4% | 38 → 38 | +1 / −1 |
| `python/app/orm/buyer_interest.py` | 97.4% | 39 → 39 | +1 / −1 |
| `python/app/orm/livestock_roi_prediction.py` | 97.4% | 78 → 78 | +2 / −2 |
| `python/app/orm/crop_diagnosis.py` | 97.5% | 40 → 40 | +1 / −1 |
| `python/app/orm/transport_provider.py` | 97.7% | 44 → 44 | +1 / −1 |
| `python/app/orm/soil_test.py` | 98.4% | 63 → 63 | +1 / −1 |

### Other python (1)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `python/requirements.txt` | 4.2% | 107 → 37 | +34 / −104 |

### Schema JSON (56)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `database/Model/supply_request.json` | 2.1% | 138 → 145 | +142 / −135 |
| `database/Model/supply_match.json` | 2.6% | 118 → 110 | +107 / −115 |
| `database/Model/advance_booking.json` | 3.0% | 106 → 97 | +94 / −103 |
| `database/Model/payment_milestone.json` | 4.4% | 66 → 71 | +68 / −63 |
| `database/Model/quality_verification.json` | 4.4% | 66 → 71 | +68 / −63 |
| `database/Model/active_role.json` | 54.8% | 45 → 28 | +8 / −25 |
| `database/Model/fertilizer_application.json` | 58.6% | 218 → 202 | +79 / −95 |
| `database/Model/offspring.json` | 62.0% | 118 → 98 | +31 / −51 |
| `database/Model/soil_test_result.json` | 62.3% | 173 → 177 | +68 / −64 |
| `database/Model/crop_expense.json` | 62.5% | 48 → 48 | +18 / −18 |
| `database/Model/breeding_record.json` | 64.2% | 118 → 97 | +28 / −49 |
| `database/Model/annual_strategy.json` | 65.9% | 143 → 133 | +42 / −52 |
| `database/Model/crop_diagnosis.json` | 67.2% | 122 → 119 | +38 / −41 |
| `database/Model/livestock_transaction.json` | 68.2% | 166 → 148 | +41 / −59 |
| `database/Model/soil_amendment.json` | 68.6% | 215 → 202 | +59 / −72 |
| `database/Model/soil_test.json` | 68.7% | 264 → 257 | +78 / −85 |
| `database/Model/voice_assist_log.json` | 69.8% | 109 → 103 | +29 / −35 |
| `database/Model/livestock_roi_prediction.json` | 71.0% | 329 → 316 | +87 / −100 |
| `database/Model/marketplace_listing.json` | 71.0% | 164 → 157 | +43 / −50 |
| `database/Model/market_price.json` | 72.1% | 136 → 122 | +29 / −43 |
| `database/Model/livestock.json` | 72.4% | 149 → 141 | +36 / −44 |
| `database/Model/weather_forecast.json` | 72.6% | 241 → 241 | +66 / −66 |
| `database/Model/satellite_observation.json` | 72.7% | 91 → 85 | +21 / −27 |
| `database/Model/veterinarian.json` | 73.0% | 108 → 125 | +40 / −23 |
| `database/Model/farm.json` | 73.2% | 348 → 351 | +95 / −92 |
| `database/Model/transport_booking.json` | 73.7% | 214 → 196 | +45 / −63 |
| `database/Model/buyer_interest.json` | 74.2% | 120 → 120 | +31 / −31 |
| `database/Model/slusi_lcc_report.json` | 74.3% | 153 → 170 | +50 / −33 |
| `database/Model/pest_disease_data.json` | 74.8% | 129 → 141 | +40 / −28 |
| `database/Model/crop.json` | 75.1% | 125 → 112 | +23 / −36 |
| `database/Model/crop_profitability.json` | 75.1% | 193 → 193 | +48 / −48 |
| `database/Model/seasonal_trend.json` | 75.1% | 169 → 169 | +42 / −42 |
| `database/Model/pest_disease_alert.json` | 75.3% | 131 → 116 | +23 / −38 |
| `database/Model/farm_plot.json` | 76.4% | 144 → 136 | +29 / −37 |
| `database/Model/user.json` | 77.4% | 152 → 166 | +43 / −29 |
| `database/Model/historical_yield.json` | 77.5% | 151 → 151 | +34 / −34 |
| `database/Model/opportunity_cost.json` | 77.5% | 187 → 187 | +42 / −42 |
| `database/Model/livestock_health_record.json` | 77.6% | 78 → 69 | +12 / −21 |
| `database/Model/livestock_listing.json` | 77.6% | 266 → 260 | +56 / −62 |
| `database/Model/slusi_ingestion_run.json` | 79.3% | 53 → 58 | +14 / −9 |
| `database/Model/livestock_marketplace_listing.json` | 79.6% | 173 → 161 | +28 / −40 |
| `database/Model/user_notification.json` | 80.6% | 77 → 67 | +9 / −19 |
| `database/Model/price_prediction.json` | 81.2% | 126 → 135 | +29 / −20 |
| `database/Model/crop_milestone.json` | 82.0% | 96 → 87 | +12 / −21 |
| `database/Model/shc_state_district_code.json` | 82.5% | 51 → 63 | +16 / −4 |
| `database/Model/slusi_microwatershed_map.json` | 83.3% | 39 → 45 | +10 / −4 |
| `database/Model/weather_alert.json` | 83.3% | 87 → 81 | +11 / −17 |
| `database/Model/service.json` | 83.5% | 129 → 132 | +23 / −20 |
| `database/Model/msp_rate.json` | 85.4% | 77 → 80 | +13 / −10 |
| `database/Model/ndap_ingestion_run.json` | 85.5% | 60 → 64 | +11 / −7 |
| `database/Model/ai_usage_quota.json` | 86.2% | 63 → 53 | +3 / −13 |
| `database/Model/transport_provider.json` | 87.0% | 153 → 146 | +16 / −23 |
| `database/Model/push_subscription.json` | 88.1% | 40 → 44 | +7 / −3 |
| `database/Model/crop_market_data.json` | 89.7% | 67 → 69 | +8 / −6 |
| `database/Model/system_setting.json` | 93.2% | 36 → 37 | +3 / −2 |
| `database/Model/soil_moisture_data.json` | 96.9% | 65 → 65 | +2 / −2 |

### Other database (3)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `database/structure.sql` | 52.2% | 115 → 115 | +55 / −55 |
| `database/Migration.sql` | 74.9% | 223 → 223 | +56 / −56 |
| `database/relation.sql` | 99.0% | 101 → 101 | +1 / −1 |

### Generated TS interfaces (35)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `solidjs/src/shared/Interface/Model/Advance_booking.ts` | 78.9% | 19 → 19 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Breeding_record.ts` | 78.9% | 19 → 19 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Offspring.ts` | 78.9% | 19 → 19 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Supply_match.ts` | 81.0% | 21 → 21 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Crop_expense.ts` | 81.8% | 11 → 11 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Market_price.ts` | 81.8% | 22 → 22 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Fertilizer_application.ts` | 82.4% | 34 → 34 | +6 / −6 |
| `solidjs/src/shared/Interface/Model/Ai_usage_quota.ts` | 83.3% | 12 → 12 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Livestock_transaction.ts` | 85.2% | 27 → 27 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Crop.ts` | 85.7% | 21 → 21 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Livestock_health_record.ts` | 85.7% | 14 → 14 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Payment_milestone.ts` | 85.7% | 14 → 14 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Quality_verification.ts` | 85.7% | 14 → 14 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/User_notification.ts` | 85.7% | 14 → 14 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Pest_disease_alert.ts` | 86.4% | 22 → 22 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Annual_strategy.ts` | 87.5% | 24 → 24 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Weather_alert.ts` | 87.5% | 16 → 16 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Livestock.ts` | 88.0% | 25 → 25 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Crop_milestone.ts` | 88.2% | 17 → 17 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Satellite_observation.ts` | 88.2% | 17 → 17 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Transport_booking.ts` | 88.6% | 35 → 35 | +4 / −4 |
| `solidjs/src/shared/Interface/Model/Marketplace_listing.ts` | 88.9% | 27 → 27 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Livestock_marketplace_listing.ts` | 89.7% | 29 → 29 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Soil_test_result.ts` | 89.7% | 29 → 29 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Voice_assist_log.ts` | 90.0% | 20 → 20 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Buyer_interest.ts` | 90.5% | 21 → 21 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Crop_diagnosis.ts` | 90.9% | 22 → 22 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Soil_amendment.ts` | 91.7% | 36 → 36 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Farm_plot.ts` | 92.0% | 25 → 25 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Supply_request.ts` | 92.3% | 26 → 26 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Transport_provider.ts` | 92.3% | 26 → 26 | +2 / −2 |
| `solidjs/src/shared/Interface/Model/Livestock_listing.ts` | 93.2% | 44 → 44 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Active_role.ts` | 93.3% | 8 → 7 | +0 / −1 |
| `solidjs/src/shared/Interface/Model/Livestock_roi_prediction.ts` | 94.5% | 55 → 55 | +3 / −3 |
| `solidjs/src/shared/Interface/Model/Soil_test.ts` | 95.6% | 45 → 45 | +2 / −2 |

### Frontend shared (3)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `solidjs/src/shared/indexdb.ts` | 1.8% | 205 → 14 | +12 / −203 |
| `solidjs/src/shared/guard/all.ts` | 47.6% | 14 → 7 | +2 / −9 |
| `solidjs/src/shared/Service/Services.ts` | 98.7% | 238 → 234 | +1 / −5 |

### Frontend pages (42)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `solidjs/src/pages/crops/Diagnose.tsx` | 1.2% | 314 → 191 | +188 / −311 |
| `solidjs/src/pages/Assistant.tsx` | 2.1% | 550 → 132 | +125 / −543 |
| `solidjs/src/pages/AllServices.tsx` | 2.4% | 28 → 382 | +377 / −23 |
| `solidjs/src/pages/users/Profile.tsx` | 3.8% | 222 → 38 | +33 / −217 |
| `solidjs/src/pages/soil/SoilFertilizerHub.tsx` | 4.4% | 228 → 43 | +37 / −222 |
| `solidjs/src/pages/farm/Register.tsx` | 4.7% | 43 → 511 | +498 / −30 |
| `solidjs/src/pages/Dashboard.tsx` | 4.7% | 513 → 250 | +232 / −495 |
| `solidjs/src/pages/livestock/DietPlan.tsx` | 4.7% | 172 → 547 | +530 / −155 |
| `solidjs/src/pages/plots/Create.tsx` | 4.8% | 315 → 689 | +665 / −291 |
| `solidjs/src/pages/livestock/PashuHome.tsx` | 4.9% | 321 → 126 | +115 / −310 |
| `solidjs/src/pages/livestock/VeterinaryDoctors.tsx` | 5.0% | 404 → 707 | +679 / −376 |
| `solidjs/src/pages/notifications/Notifications.tsx` | 5.2% | 168 → 63 | +57 / −162 |
| `solidjs/src/pages/climate/ClimateHub.tsx` | 5.3% | 240 → 662 | +638 / −216 |
| `solidjs/src/pages/users/Security.tsx` | 5.5% | 188 → 575 | +554 / −167 |
| `solidjs/src/pages/farm/FarmAnalytics.tsx` | 5.7% | 610 → 509 | +477 / −578 |
| `solidjs/src/pages/livestock/LivestockHub.tsx` | 6.0% | 186 → 518 | +497 / −165 |
| `solidjs/src/pages/services/ServicesDirectory.tsx` | 6.0% | 291 → 476 | +453 / −268 |
| `solidjs/src/pages/pest-disease/PestDiseaseHub.tsx` | 6.7% | 238 → 483 | +459 / −214 |
| `solidjs/src/pages/transport/TransportTracking.tsx` | 7.1% | 168 → 368 | +349 / −149 |
| `solidjs/src/pages/marketplace/MarketIntelligence.tsx` | 7.1% | 452 → 305 | +278 / −425 |
| `solidjs/src/pages/strategy/Request.tsx` | 7.3% | 181 → 591 | +563 / −153 |
| `solidjs/src/pages/livestock-marketplace/Browse.tsx` | 7.5% | 308 → 437 | +409 / −280 |
| `solidjs/src/pages/farm/FarmDashboard.tsx` | 7.6% | 137 → 520 | +495 / −112 |
| `solidjs/src/pages/crops/MyCrops.tsx` | 7.6% | 261 → 524 | +494 / −231 |
| `solidjs/src/pages/crops/PlantCrop.tsx` | 7.7% | 330 → 740 | +699 / −289 |
| `solidjs/src/pages/Configuration.tsx` | 8.0% | 109 → 90 | +82 / −101 |
| `solidjs/src/pages/marketplace/Detail.tsx` | 8.4% | 139 → 316 | +297 / −120 |
| `solidjs/src/pages/marketplace/BuyerDashboard.tsx` | 8.5% | 276 → 453 | +422 / −245 |
| `solidjs/src/pages/strategy/SelectFarm.tsx` | 8.7% | 129 → 447 | +422 / −104 |
| `solidjs/src/pages/marketplace/Browse.tsx` | 9.5% | 121 → 90 | +80 / −111 |
| `solidjs/src/pages/marketplace/Bookings.tsx` | 9.6% | 219 → 346 | +319 / −192 |
| `solidjs/src/pages/marketplace/SupplyPlanning.tsx` | 10.3% | 394 → 460 | +416 / −350 |
| `solidjs/src/pages/admin/PlatformAnalytics.tsx` | 10.6% | 368 → 369 | +330 / −329 |
| `solidjs/src/pages/marketplace/BookingDetails.tsx` | 11.0% | 290 → 74 | +54 / −270 |
| `solidjs/src/pages/farm/Index.tsx` | 11.3% | 97 → 97 | +86 / −86 |
| `solidjs/src/pages/auth/SignUp.tsx` | 11.5% | 54 → 173 | +160 / −41 |
| `solidjs/src/pages/marketplace/MyListings.tsx` | 12.0% | 113 → 404 | +373 / −82 |
| `solidjs/src/pages/admin/QuotaMonitoring.tsx` | 12.5% | 287 → 401 | +358 / −244 |
| `solidjs/src/pages/auth/SignIn.tsx` | 12.6% | 82 → 108 | +96 / −70 |
| `solidjs/src/pages/quota/QuotaHistory.tsx` | 12.9% | 233 → 436 | +393 / −190 |
| `solidjs/src/pages/Home.tsx` | 13.6% | 206 → 117 | +95 / −184 |
| `solidjs/src/pages/crops/AnnualStrategyDetail.tsx` | 17.2% | 87 → 64 | +51 / −74 |

### Other frontend (13)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `solidjs/src/stores/i18n.store.ts` | 5.4% | 77 → 109 | +104 / −72 |
| `solidjs/src/index.tsx` | 5.9% | 175 → 370 | +354 / −159 |
| `solidjs/src/lib/api-client.ts` | 7.0% | 576 → 285 | +255 / −546 |
| `solidjs/src/stores/auth.store.ts` | 13.9% | 270 → 134 | +106 / −242 |
| `solidjs/public/sw.js` | 15.3% | 318 → 73 | +43 / −288 |
| `solidjs/vite.config.ts` | 15.8% | 88 → 13 | +5 / −80 |
| `solidjs/src/App.tsx` | 18.3% | 37 → 72 | +62 / −27 |
| `solidjs/public/manifest.json` | 21.2% | 88 → 16 | +5 / −77 |
| `solidjs/index.html` | 29.9% | 47 → 20 | +10 / −37 |
| `solidjs/tailwind.config.js` | 34.1% | 50 → 38 | +23 / −35 |
| `solidjs/package.json` | 37.5% | 40 → 24 | +12 / −28 |
| `solidjs/tsconfig.json` | 76.2% | 22 → 20 | +4 / −6 |
| `solidjs/postcss.config.js` | 83.3% | 6 → 6 | +1 / −1 |

### Skills (1)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `skills/SKILL.md` | 23.9% | 207 → 321 | +258 / −144 |

### Root files (3)

| File | Similarity | apac → gemini lines | + / − |
|---|---:|---:|---:|
| `setup.php` | 9.7% | 91 → 12 | +7 / −86 |
| `config.json` | 43.6% | 98 → 90 | +49 / −57 |
| `deploy-gcp.sh` | 92.9% | 353 → 377 | +38 / −14 |

## 5. Schema JSON compared by structure (`database/Model`)

The two repos use different relation formats. apac uses a `relations` object **plus** an explicit FK column in `data`. gemini-crop uses the newer compile-php `relation` array, where the FK column is implied (`"farm_plot"` means `farm_plot_id`, and `{name, alias}` means `alias`). The generator adds those columns to the end of each table, so the generated DDL still has them. The comparison below counts implied FKs as columns.

| Model | text similarity | columns apac → gemini | only in apac | only in gemini | FK relations apac → gemini |
|---|---:|---:|---|---|---:|
| `active_role` | 55% | 2 → 2 | – | – | 2 → 2 |
| `advance_booking` | 3% | 13 → 13 | – | – | 3 → 3 |
| `ai_usage_quota` | 86% | 6 → 6 | – | – | 1 → 1 |
| `annual_strategy` | 66% | 18 → 18 | – | – | 2 → 2 |
| `breeding_record` | 64% | 13 → 13 | – | – | 3 → 3 |
| `buyer_interest` | 74% | 15 → 15 | – | – | 1 → 1 |
| `crop` | 75% | 15 → 15 | – | – | 2 → 2 |
| `crop_diagnosis` | 67% | 16 → 16 | – | – | 1 → 1 |
| `crop_expense` | 62% | 5 → 5 | – | – | 1 → 1 |
| `crop_market_data` | 90% | 8 → 8 | – | – | 0 → 0 |
| `crop_milestone` | 82% | 11 → 11 | – | – | 1 → 1 |
| `crop_profitability` | 75% | 28 → 28 | – | – | 0 → 0 |
| `farm` | 73% | 47 → 47 | – | – | 2 → 2 |
| `farm_plot` | 76% | 19 → 19 | – | – | 1 → 1 |
| `fertilizer_application` | 59% | 28 → 28 | – | – | 5 → 5 |
| `historical_yield` | 77% | 21 → 21 | – | – | 0 → 0 |
| `livestock` | 72% | 19 → 19 | – | – | 2 → 2 |
| `livestock_health_record` | 78% | 8 → 8 | – | – | 1 → 1 |
| `livestock_listing` | 78% | 38 → 38 | – | – | 2 → 2 |
| `livestock_marketplace_listing` | 80% | 23 → 23 | – | – | 2 → 2 |
| `livestock_roi_prediction` | 71% | 49 → 49 | – | – | 2 → 2 |
| `livestock_transaction` | 68% | 21 → 21 | – | – | 3 → 3 |
| `market_price` | 72% | 16 → 16 | – | – | 3 → 3 |
| `marketplace_listing` | 71% | 21 → 21 | – | – | 2 → 2 |
| `msp_rate` | 85% | 9 → 9 | – | – | 0 → 0 |
| `ndap_downloaded_file` | 100% | 3 → 3 | – | – | 0 → 0 |
| `ndap_ingestion_run` | 85% | 7 → 7 | – | – | 0 → 0 |
| `offspring` | 62% | 13 → 13 | – | – | 3 → 3 |
| `opportunity_cost` | 78% | 27 → 27 | – | – | 0 → 0 |
| `payment_milestone` | 4% | 8 → 8 | – | – | 1 → 1 |
| `pest_disease_alert` | 75% | 16 → 16 | – | – | 2 → 2 |
| `pest_disease_data` | 75% | 18 → 18 | – | – | 0 → 0 |
| `price_prediction` | 81% | 17 → 17 | – | – | 0 → 0 |
| `push_subscription` | 88% | 5 → 5 | – | – | 0 → 0 |
| `quality_verification` | 4% | 8 → 8 | – | – | 1 → 1 |
| `role` | 100% | 1 → 1 | – | – | 0 → 0 |
| `satellite_observation` | 73% | 11 → 11 | – | – | 1 → 1 |
| `seasonal_trend` | 75% | 24 → 24 | – | – | 0 → 0 |
| `service` | 84% | 16 → 16 | – | – | 0 → 0 |
| `shc_state_district_code` | 82% | 4 → 4 | – | – | 0 → 0 |
| `slusi_ingestion_run` | 79% | 6 → 6 | – | – | 0 → 0 |
| `slusi_lcc_report` | 74% | 18 → 18 | – | – | 0 → 0 |
| `slusi_microwatershed_map` | 83% | 4 → 4 | – | – | 0 → 0 |
| `soil_amendment` | 69% | 30 → 30 | – | – | 2 → 2 |
| `soil_moisture_data` | 97% | 7 → 7 | – | – | 0 → 0 |
| `soil_test` | 69% | 39 → 39 | – | – | 1 → 1 |
| `soil_test_result` | 62% | 23 → 23 | – | – | 2 → 2 |
| `supply_match` | 3% | 15 → 15 | – | – | 3 → 3 |
| `supply_request` | 2% | 20 → 20 | – | – | 1 → 1 |
| `system_setting` | 93% | 3 → 3 | – | – | 0 → 0 |
| `transport_booking` | 74% | 29 → 29 | – | – | 3 → 3 |
| `transport_provider` | 87% | 20 → 20 | – | – | 1 → 1 |
| `user` | 77% | 21 → 21 | – | – | 0 → 0 |
| `user_notification` | 81% | 8 → 8 | – | – | 1 → 1 |
| `veterinarian` | 73% | 16 → 16 | – | – | 0 → 0 |
| `voice_assist_log` | 70% | 14 → 14 | – | – | 1 → 1 |
| `weather_alert` | 83% | 10 → 10 | – | – | 1 → 1 |
| `weather_forecast` | 73% | 36 → 36 | – | – | 0 → 0 |

**All 58 models have exactly the same columns** once implied FKs are resolved (apac FK names are taken from both `data` and `relations`). The low text similarity comes only from formatting and relation syntax.

## 6. Notable differences

### Backend: copied except the core base layer
- `python/app/services` (124), `python/app/api` (177), `python/app/schemas` (18) and `python/app/jobs` (3) are **byte-identical** to apac.
- `python/app/core` was rewritten for task T0.5. 14 of 23 files are identical. The rewritten ones:
  - `db.py` (4%): apac's `DatabaseSettings`, `_pool()` and `DB` class were replaced by `RawQuery` and `DatabaseManager`, with psycopg3 and a SQLite fallback.
  - `model.py` (8%): the ActiveRecord `Model` was rewritten; the class name is the same.
  - `ownership.py` (10%): gemini-crop keeps apac's `owner_condition` and `is_scoped`, and adds `get_ownership_clause`, `is_shared_read`, `enforce_owner_columns`, `validate_parent_ownership` and `can_access`.
  - `auth.py` (17%): same Firebase validator and role dependencies. gemini-crop adds `resolve_user_from_db` and mock E2E tokens.
  - `crud_service.py` (14%) and `rate_limiter.py` (17%) were rewritten. `config.py` (47%) and `dependencies.py` (44%) were edited.
  - `alerting.py` is 99% the same. gemini-crop adds `core/__init__.py`.
- `agents/orchestrator_agent.py` (38%): same functions, but the `google.adk` / `google.genai` imports are wrapped in `try/except` with a `HAS_ADK` fallback, so the app still runs without ADK installed.
- Not brought over from apac `python/`: `tests/` (118 test files), `alembic/` migrations, `scripts/`, `tools/`, `examples/`, and the AWS/Cognito helpers and setup docs. `requirements.txt` went from 107 lines to 37.

### Data model: same 58 tables in a new relation format
- Every table in apac also exists in gemini-crop, and vice versa.
- Text similarity is low (2–4% for `supply_request`, `supply_match`, `advance_booking`, `payment_milestone`, `quality_verification`) mainly because of reformatting (arrays written one item per line) and the switch from `relations` to `relation`. Section 5 confirms that every table has exactly the same columns.
- The generated `database/relation.sql` is 99% the same. `structure.sql` scores 52% only because FK columns now come at the end of each table and `NULL` is written as `DEFAULT NULL`.

### Frontend: rewritten
- None of the 42 shared page files are identical; most are 1–18% similar. The pages were rebuilt from the Stitch screens (`stitch/screens/`) with the responsive Sidebar/BottomDock shell.
- Pages only in apac: `marketplace/BrowseInfinite`, `plots/Analyze`, `plots/Compare`, `strategy/Results`, `test/GeolocationTest`.
- `src/components` went from 80 files to 4. apac's shared component library was not brought over.
- `lib/api-client.ts` (7%), `stores/auth.store.ts` (14%), `stores/i18n.store.ts` (5%), `index.tsx` (6%) and `public/sw.js` (15%) were rewritten (task T0.6).
- The generated TS interfaces (`shared/Interface/Model/*`) are 79–96% the same, regenerated from the edited schema. `shared/Service/Services.ts` is 99% the same.

### Infra and tooling
- `terraform/gcp/*` (11 files) is identical. apac's other 22 terraform files (non-GCP) were dropped. `deploy-gcp.sh` is 93% the same.
- Only in apac: `e2e/` Playwright suite (40), `.github` CI (4), `schema_generator/`, `cognito-only/`, `.aws/`, `Resource/`, `docs/`.
- Only in gemini-crop: `stitch/` (39 screens and specs), the root `index.html` viewer, `pipeline.sh` / `scripts/pipeline.py`, and the `*-v2.md` design docs.

## 7. Identical files (430)

| Area | Files |
|---|---:|
| Backend API routes | 177 |
| Backend services | 124 |
| Generated ORM | 24 |
| Generated TS interfaces | 23 |
| Generated Pydantic models | 22 |
| Backend schemas | 18 |
| Backend core | 14 |
| Terraform | 11 |
| Skills | 6 |
| Backend jobs | 3 |
| Schema JSON | 2 |
| Other python | 2 |
| Root files | 1 |
| Other database | 1 |
| Backend agents | 1 |
| Frontend shared | 1 |

<details><summary>Backend API routes: 177 files</summary>

- `python/app/api/__init__.py`
- `python/app/api/ipublic/crop_market_data/crop_market_data.py`
- `python/app/api/ipublic/crop_profitability/crop_profitability.py`
- `python/app/api/ipublic/historical_yield/historical_yield.py`
- `python/app/api/ipublic/livestock_listing/livestock_listing.py`
- `python/app/api/ipublic/market_price/market_price.py`
- `python/app/api/ipublic/marketplace_listing/marketplace_listing.py`
- `python/app/api/ipublic/msp_rate/msp_rate.py`
- `python/app/api/ipublic/opportunity_cost/opportunity_cost.py`
- `python/app/api/ipublic/price_prediction/price_prediction.py`
- `python/app/api/ipublic/seasonal_trend/seasonal_trend.py`
- `python/app/api/ipublic/service/service.py`
- `python/app/api/ipublic/soil_moisture_data/soil_moisture_data.py`
- `python/app/api/ipublic/transport_provider/transport_provider.py`
- `python/app/api/ipublic/veterinarian/veterinarian.py`
- `python/app/api/ipublic/weather_forecast/weather_forecast.py`
- `python/app/api/islogin/active_role/active_role.py`
- `python/app/api/islogin/advance_booking/advance_booking.py`
- `python/app/api/islogin/ai_usage_quota/ai_usage_quota.py`
- `python/app/api/islogin/annual_strategy/annual_strategy.py`
- `python/app/api/islogin/breeding_record/breeding_record.py`
- `python/app/api/islogin/buyer_interest/buyer_interest.py`
- `python/app/api/islogin/crop/crop.py`
- `python/app/api/islogin/crop_diagnosis/crop_diagnosis.py`
- `python/app/api/islogin/crop_expense/crop_expense.py`
- `python/app/api/islogin/crop_milestone/crop_milestone.py`
- `python/app/api/islogin/crop_profitability/crop_profitability.py`
- `python/app/api/islogin/farm/farm.py`
- `python/app/api/islogin/farm_plot/farm_plot.py`
- `python/app/api/islogin/fertilizer_application/fertilizer_application.py`
- `python/app/api/islogin/historical_yield/historical_yield.py`
- `python/app/api/islogin/livestock/livestock.py`
- `python/app/api/islogin/livestock_health_record/livestock_health_record.py`
- `python/app/api/islogin/livestock_listing/livestock_listing.py`
- `python/app/api/islogin/livestock_marketplace_listing/livestock_marketplace_listing.py`
- `python/app/api/islogin/livestock_roi_prediction/livestock_roi_prediction.py`
- `python/app/api/islogin/livestock_transaction/livestock_transaction.py`
- `python/app/api/islogin/market_price/market_price.py`
- `python/app/api/islogin/marketplace_listing/marketplace_listing.py`
- `python/app/api/islogin/msp_rate/msp_rate.py`
- `python/app/api/islogin/offspring/offspring.py`
- `python/app/api/islogin/opportunity_cost/opportunity_cost.py`
- `python/app/api/islogin/payment_milestone/payment_milestone.py`
- `python/app/api/islogin/pest_disease_alert/pest_disease_alert.py`
- `python/app/api/islogin/pest_disease_data/pest_disease_data.py`
- `python/app/api/islogin/price_prediction/price_prediction.py`
- `python/app/api/islogin/quality_verification/quality_verification.py`
- `python/app/api/islogin/satellite_observation/satellite_observation.py`
- `python/app/api/islogin/seasonal_trend/seasonal_trend.py`
- `python/app/api/islogin/service/service.py`
- `python/app/api/islogin/shc_state_district_code/shc_state_district_code.py`
- `python/app/api/islogin/slusi_lcc_report/slusi_lcc_report.py`
- `python/app/api/islogin/slusi_microwatershed_map/slusi_microwatershed_map.py`
- `python/app/api/islogin/soil_amendment/soil_amendment.py`
- `python/app/api/islogin/soil_moisture_data/soil_moisture_data.py`
- `python/app/api/islogin/soil_test/soil_test.py`
- `python/app/api/islogin/soil_test_result/soil_test_result.py`
- `python/app/api/islogin/supply_match/supply_match.py`
- `python/app/api/islogin/supply_request/supply_request.py`
- `python/app/api/islogin/transport_booking/transport_booking.py`
- `python/app/api/islogin/transport_provider/transport_provider.py`
- `python/app/api/islogin/user/user.py`
- `python/app/api/islogin/user_notification/user_notification.py`
- `python/app/api/islogin/veterinarian/veterinarian.py`
- `python/app/api/islogin/voice_assist_log/voice_assist_log.py`
- `python/app/api/islogin/weather_alert/weather_alert.py`
- `python/app/api/islogin/weather_forecast/weather_forecast.py`
- `python/app/api/isuper/active_role/active_role.py`
- `python/app/api/isuper/advance_booking/advance_booking.py`
- `python/app/api/isuper/ai_usage_quota/ai_usage_quota.py`
- `python/app/api/isuper/annual_strategy/annual_strategy.py`
- `python/app/api/isuper/breeding_record/breeding_record.py`
- `python/app/api/isuper/buyer_interest/buyer_interest.py`
- `python/app/api/isuper/crop/crop.py`
- `python/app/api/isuper/crop_diagnosis/crop_diagnosis.py`
- `python/app/api/isuper/crop_expense/crop_expense.py`
- `python/app/api/isuper/crop_market_data/crop_market_data.py`
- `python/app/api/isuper/crop_milestone/crop_milestone.py`
- `python/app/api/isuper/crop_profitability/crop_profitability.py`
- `python/app/api/isuper/farm/farm.py`
- `python/app/api/isuper/farm_plot/farm_plot.py`
- `python/app/api/isuper/fertilizer_application/fertilizer_application.py`
- `python/app/api/isuper/historical_yield/historical_yield.py`
- `python/app/api/isuper/livestock/livestock.py`
- `python/app/api/isuper/livestock_health_record/livestock_health_record.py`
- `python/app/api/isuper/livestock_listing/livestock_listing.py`
- `python/app/api/isuper/livestock_marketplace_listing/livestock_marketplace_listing.py`
- `python/app/api/isuper/livestock_roi_prediction/livestock_roi_prediction.py`
- `python/app/api/isuper/livestock_transaction/livestock_transaction.py`
- `python/app/api/isuper/market_price/market_price.py`
- `python/app/api/isuper/marketplace_listing/marketplace_listing.py`
- `python/app/api/isuper/msp_rate/msp_rate.py`
- `python/app/api/isuper/ndap_ingestion_run/ndap_ingestion_run.py`
- `python/app/api/isuper/offspring/offspring.py`
- `python/app/api/isuper/opportunity_cost/opportunity_cost.py`
- `python/app/api/isuper/payment_milestone/payment_milestone.py`
- `python/app/api/isuper/pest_disease_alert/pest_disease_alert.py`
- `python/app/api/isuper/pest_disease_data/pest_disease_data.py`
- `python/app/api/isuper/price_prediction/price_prediction.py`
- `python/app/api/isuper/push_subscription/push_subscription.py`
- `python/app/api/isuper/quality_verification/quality_verification.py`
- `python/app/api/isuper/role/role.py`
- `python/app/api/isuper/satellite_observation/satellite_observation.py`
- `python/app/api/isuper/seasonal_trend/seasonal_trend.py`
- `python/app/api/isuper/service/service.py`
- `python/app/api/isuper/shc_state_district_code/shc_state_district_code.py`
- `python/app/api/isuper/slusi_ingestion_run/slusi_ingestion_run.py`
- `python/app/api/isuper/slusi_lcc_report/slusi_lcc_report.py`
- `python/app/api/isuper/slusi_microwatershed_map/slusi_microwatershed_map.py`
- `python/app/api/isuper/soil_amendment/soil_amendment.py`
- `python/app/api/isuper/soil_moisture_data/soil_moisture_data.py`
- `python/app/api/isuper/soil_test/soil_test.py`
- `python/app/api/isuper/soil_test_result/soil_test_result.py`
- `python/app/api/isuper/supply_match/supply_match.py`
- `python/app/api/isuper/supply_request/supply_request.py`
- `python/app/api/isuper/system_setting/system_setting.py`
- `python/app/api/isuper/transport_booking/transport_booking.py`
- `python/app/api/isuper/transport_provider/transport_provider.py`
- `python/app/api/isuper/user/user.py`
- `python/app/api/isuper/user_notification/user_notification.py`
- `python/app/api/isuper/veterinarian/veterinarian.py`
- `python/app/api/isuper/voice_assist_log/voice_assist_log.py`
- `python/app/api/isuper/weather_alert/weather_alert.py`
- `python/app/api/isuper/weather_forecast/weather_forecast.py`
- `python/app/api/roles/service_provider/service/service.py`
- `python/app/api/routers.py`
- `python/app/api/v1/address.py`
- `python/app/api/v1/advance_booking.py`
- `python/app/api/v1/agents.py`
- `python/app/api/v1/ai_quota.py`
- `python/app/api/v1/analytics.py`
- `python/app/api/v1/annual_strategy.py`
- `python/app/api/v1/auth.py`
- `python/app/api/v1/community_dashboard.py`
- `python/app/api/v1/crop_milestones.py`
- `python/app/api/v1/crop_recommendations.py`
- `python/app/api/v1/crops.py`
- `python/app/api/v1/farms.py`
- `python/app/api/v1/fertilizer_recommendations.py`
- `python/app/api/v1/fertilizer_tracking.py`
- `python/app/api/v1/health.py`
- `python/app/api/v1/hybrid_ai.py`
- `python/app/api/v1/livestock.py`
- `python/app/api/v1/livestock_breeding.py`
- `python/app/api/v1/livestock_health.py`
- `python/app/api/v1/livestock_listings.py`
- `python/app/api/v1/livestock_marketplace.py`
- `python/app/api/v1/livestock_nutrition.py`
- `python/app/api/v1/livestock_transactions.py`
- `python/app/api/v1/market_data.py`
- `python/app/api/v1/market_intelligence.py`
- `python/app/api/v1/marketplace.py`
- `python/app/api/v1/model_training.py`
- `python/app/api/v1/notifications.py`
- `python/app/api/v1/pest_disease.py`
- `python/app/api/v1/plot_analysis.py`
- `python/app/api/v1/plot_publishing.py`
- `python/app/api/v1/predictive_analytics.py`
- `python/app/api/v1/sagemaker.py`
- `python/app/api/v1/satellite.py`
- `python/app/api/v1/severe_weather.py`
- `python/app/api/v1/slusi.py`
- `python/app/api/v1/soil.py`
- `python/app/api/v1/soil_health.py`
- `python/app/api/v1/soil_maps.py`
- `python/app/api/v1/soil_testing.py`
- `python/app/api/v1/supply_requests.py`
- `python/app/api/v1/transport.py`
- `python/app/api/v1/upload.py`
- `python/app/api/v1/users.py`
- `python/app/api/v1/vaccination_reminders.py`
- `python/app/api/v1/veterinary.py`
- `python/app/api/v1/vision_diagnosis.py`
- `python/app/api/v1/voice_agent.py`
- `python/app/api/v1/weather.py`
- `python/app/api/v1/weather_recommendations.py`
- `python/app/api/v1/yield_predictions.py`

</details>

<details><summary>Backend services: 124 files</summary>

- `python/app/services/README_MARKET_DATA.md`
- `python/app/services/active_role_service.py`
- `python/app/services/address_service.py`
- `python/app/services/advance_booking_service.py`
- `python/app/services/agro_safety.py`
- `python/app/services/ai_quota_service.py`
- `python/app/services/ai_usage_quota_service.py`
- `python/app/services/analytics_service.py`
- `python/app/services/annual_strategy_service.py`
- `python/app/services/bedrock_service.py`
- `python/app/services/bigquery_service.py`
- `python/app/services/booking_reminder_service.py`
- `python/app/services/booking_workflow.py`
- `python/app/services/breeding_record_service.py`
- `python/app/services/buyer_interest_service.py`
- `python/app/services/cognito_service.py`
- `python/app/services/crop_diagnosis_service.py`
- `python/app/services/crop_expense_service.py`
- `python/app/services/crop_growth_tracker.py`
- `python/app/services/crop_market_data_service.py`
- `python/app/services/crop_milestone_service.py`
- `python/app/services/crop_profitability_service.py`
- `python/app/services/crop_recommendation_service.py`
- `python/app/services/crop_service.py`
- `python/app/services/dss_parser.py`
- `python/app/services/explainability.py`
- `python/app/services/farm_access.py`
- `python/app/services/farm_plot_service.py`
- `python/app/services/farm_service.py`
- `python/app/services/fertilizer_application_service.py`
- `python/app/services/fertilizer_recommendation_service.py`
- `python/app/services/fertilizer_tracking_service.py`
- `python/app/services/file_storage.py`
- `python/app/services/firestore_service.py`
- `python/app/services/historical_yield_service.py`
- `python/app/services/hybrid_ai_service.py`
- `python/app/services/imd_service.py`
- `python/app/services/livestock_breeding_service.py`
- `python/app/services/livestock_health_record_service.py`
- `python/app/services/livestock_health_service.py`
- `python/app/services/livestock_listing_catalog.py`
- `python/app/services/livestock_listing_service.py`
- `python/app/services/livestock_marketplace_listing_service.py`
- `python/app/services/livestock_nutrition_service.py`
- `python/app/services/livestock_repository.py`
- `python/app/services/livestock_roi_prediction_service.py`
- `python/app/services/livestock_roi_service.py`
- `python/app/services/livestock_service.py`
- `python/app/services/livestock_trade_workflow.py`
- `python/app/services/livestock_transaction_service.py`
- `python/app/services/market_data_service.py`
- `python/app/services/market_price_service.py`
- `python/app/services/marketplace_listing_service.py`
- `python/app/services/marketplace_service.py`
- `python/app/services/model_training_service.py`
- `python/app/services/msp_rate_service.py`
- `python/app/services/nbss_service.py`
- `python/app/services/ndap_downloaded_file_service.py`
- `python/app/services/ndap_ingestion_run_service.py`
- `python/app/services/notification_inbox.py`
- `python/app/services/notification_service.py`
- `python/app/services/offspring_service.py`
- `python/app/services/openweathermap_service.py`
- `python/app/services/opportunity_cost_service.py`
- `python/app/services/payment_milestone_service.py`
- `python/app/services/pest_disease_alert_service.py`
- `python/app/services/pest_disease_data_service.py`
- `python/app/services/pest_disease_service.py`
- `python/app/services/pincode_lookup_service.py`
- `python/app/services/plot_analysis_service.py`
- `python/app/services/plot_publishing_service.py`
- `python/app/services/predictive_analytics_service.py`
- `python/app/services/price_prediction_service.py`
- `python/app/services/price_tracking_service.py`
- `python/app/services/profit_margin_service.py`
- `python/app/services/push_subscription_service.py`
- `python/app/services/quality_verification_service.py`
- `python/app/services/role_service.py`
- `python/app/services/sagemaker_service.py`
- `python/app/services/satellite_health.py`
- `python/app/services/satellite_observation_service.py`
- `python/app/services/seasonal_trend_analysis.py`
- `python/app/services/seasonal_trend_service.py`
- `python/app/services/service_service.py`
- `python/app/services/severe_weather_service.py`
- `python/app/services/shc_code_mapper.py`
- `python/app/services/shc_fetcher.py`
- `python/app/services/shc_state_district_code_service.py`
- `python/app/services/slusi_ingestion_run_service.py`
- `python/app/services/slusi_lcc_report_service.py`
- `python/app/services/slusi_microwatershed_map_service.py`
- `python/app/services/slusi_service.py`
- `python/app/services/soil_amendment_service.py`
- `python/app/services/soil_health_report_service.py`
- `python/app/services/soil_mapping.py`
- `python/app/services/soil_moisture_data_service.py`
- `python/app/services/soil_test_result_service.py`
- `python/app/services/soil_test_service.py`
- `python/app/services/soil_testing_service.py`
- `python/app/services/supply_match_service.py`
- `python/app/services/supply_request_matching_service.py`
- `python/app/services/supply_request_service.py`
- `python/app/services/system_setting_service.py`
- `python/app/services/transport_booking_service.py`
- `python/app/services/transport_provider_service.py`
- `python/app/services/transport_service.py`
- `python/app/services/user_notification_service.py`
- `python/app/services/user_service.py`
- `python/app/services/vaccination_reminder_service.py`
- `python/app/services/vector_service.py`
- `python/app/services/veterinarian_directory_service.py`
- `python/app/services/veterinarian_service.py`
- `python/app/services/veterinary_service.py`
- `python/app/services/vision_diagnosis_service.py`
- `python/app/services/voice_assist_audit.py`
- `python/app/services/voice_assist_log_service.py`
- `python/app/services/voice_assist_service.py`
- `python/app/services/weather_alert_service.py`
- `python/app/services/weather_forecast_service.py`
- `python/app/services/weather_recommendations_service.py`
- `python/app/services/weather_service.py`
- `python/app/services/web_push_service.py`
- `python/app/services/yield_prediction_update_service.py`
- `python/app/services/yield_profit_service.py`

</details>

<details><summary>Generated ORM: 24 files</summary>

- `python/app/orm/active_role.py`
- `python/app/orm/crop_market_data.py`
- `python/app/orm/crop_profitability.py`
- `python/app/orm/farm.py`
- `python/app/orm/historical_yield.py`
- `python/app/orm/msp_rate.py`
- `python/app/orm/ndap_downloaded_file.py`
- `python/app/orm/ndap_ingestion_run.py`
- `python/app/orm/opportunity_cost.py`
- `python/app/orm/pest_disease_data.py`
- `python/app/orm/price_prediction.py`
- `python/app/orm/push_subscription.py`
- `python/app/orm/role.py`
- `python/app/orm/seasonal_trend.py`
- `python/app/orm/service.py`
- `python/app/orm/shc_state_district_code.py`
- `python/app/orm/slusi_ingestion_run.py`
- `python/app/orm/slusi_lcc_report.py`
- `python/app/orm/slusi_microwatershed_map.py`
- `python/app/orm/soil_moisture_data.py`
- `python/app/orm/system_setting.py`
- `python/app/orm/user_sqlalchemy.py`
- `python/app/orm/veterinarian.py`
- `python/app/orm/weather_forecast.py`

</details>

<details><summary>Generated TS interfaces: 23 files</summary>

- `solidjs/src/shared/Interface/Model/Crop_market_data.ts`
- `solidjs/src/shared/Interface/Model/Crop_profitability.ts`
- `solidjs/src/shared/Interface/Model/Farm.ts`
- `solidjs/src/shared/Interface/Model/Historical_yield.ts`
- `solidjs/src/shared/Interface/Model/Msp_rate.ts`
- `solidjs/src/shared/Interface/Model/Ndap_downloaded_file.ts`
- `solidjs/src/shared/Interface/Model/Ndap_ingestion_run.ts`
- `solidjs/src/shared/Interface/Model/Opportunity_cost.ts`
- `solidjs/src/shared/Interface/Model/Pest_disease_data.ts`
- `solidjs/src/shared/Interface/Model/Price_prediction.ts`
- `solidjs/src/shared/Interface/Model/Push_subscription.ts`
- `solidjs/src/shared/Interface/Model/Role.ts`
- `solidjs/src/shared/Interface/Model/Seasonal_trend.ts`
- `solidjs/src/shared/Interface/Model/Service.ts`
- `solidjs/src/shared/Interface/Model/Shc_state_district_code.ts`
- `solidjs/src/shared/Interface/Model/Slusi_ingestion_run.ts`
- `solidjs/src/shared/Interface/Model/Slusi_lcc_report.ts`
- `solidjs/src/shared/Interface/Model/Slusi_microwatershed_map.ts`
- `solidjs/src/shared/Interface/Model/Soil_moisture_data.ts`
- `solidjs/src/shared/Interface/Model/System_setting.ts`
- `solidjs/src/shared/Interface/Model/User.ts`
- `solidjs/src/shared/Interface/Model/Veterinarian.ts`
- `solidjs/src/shared/Interface/Model/Weather_forecast.ts`

</details>

<details><summary>Generated Pydantic models: 22 files</summary>

- `python/app/models/crop_market_data.py`
- `python/app/models/crop_profitability.py`
- `python/app/models/farm.py`
- `python/app/models/historical_yield.py`
- `python/app/models/msp_rate.py`
- `python/app/models/ndap_ingestion_run.py`
- `python/app/models/opportunity_cost.py`
- `python/app/models/pest_disease_data.py`
- `python/app/models/price_prediction.py`
- `python/app/models/push_subscription.py`
- `python/app/models/role.py`
- `python/app/models/seasonal_trend.py`
- `python/app/models/service.py`
- `python/app/models/shc_state_district_code.py`
- `python/app/models/slusi_ingestion_run.py`
- `python/app/models/slusi_lcc_report.py`
- `python/app/models/slusi_microwatershed_map.py`
- `python/app/models/soil_moisture_data.py`
- `python/app/models/system_setting.py`
- `python/app/models/user.py`
- `python/app/models/veterinarian.py`
- `python/app/models/weather_forecast.py`

</details>

<details><summary>Backend schemas: 18 files</summary>

- `python/app/schemas/address.py`
- `python/app/schemas/ai_quota.py`
- `python/app/schemas/auth.py`
- `python/app/schemas/breeding.py`
- `python/app/schemas/crop.py`
- `python/app/schemas/farm.py`
- `python/app/schemas/livestock.py`
- `python/app/schemas/livestock_health_record.py`
- `python/app/schemas/livestock_listing.py`
- `python/app/schemas/livestock_marketplace_listing.py`
- `python/app/schemas/livestock_transaction.py`
- `python/app/schemas/market_data.py`
- `python/app/schemas/marketplace.py`
- `python/app/schemas/slusi.py`
- `python/app/schemas/soil.py`
- `python/app/schemas/types.py`
- `python/app/schemas/user.py`
- `python/app/schemas/veterinarian.py`

</details>

<details><summary>Backend core: 14 files</summary>

- `python/app/core/cache.py`
- `python/app/core/database.py`
- `python/app/core/encryption.py`
- `python/app/core/init_db.py`
- `python/app/core/model_router.py`
- `python/app/core/model_service.py`
- `python/app/core/monitoring.py`
- `python/app/core/monitoring_middleware.py`
- `python/app/core/password.py`
- `python/app/core/query_optimizer.py`
- `python/app/core/security_middleware.py`
- `python/app/core/tls_config.py`
- `python/app/core/validation.py`
- `python/app/core/vector_indexes.py`

</details>

<details><summary>Terraform: 11 files</summary>

- `terraform/gcp/.terraform/providers/registry.terraform.io/hashicorp/google/5.45.2/darwin_arm64/LICENSE.txt`
- `terraform/gcp/bigquery.tf`
- `terraform/gcp/cloud_run.tf`
- `terraform/gcp/cloud_sql.tf`
- `terraform/gcp/firestore.tf`
- `terraform/gcp/iam.tf`
- `terraform/gcp/import-existing.sh`
- `terraform/gcp/main.tf`
- `terraform/gcp/outputs.tf`
- `terraform/gcp/variables.tf`
- `terraform/gcp/vpc.tf`

</details>

<details><summary>Skills: 6 files</summary>

- `skills/references/angular-frontend.md`
- `skills/references/deno-backend.md`
- `skills/references/dotnet-backend.md`
- `skills/references/php-backend.md`
- `skills/references/python-backend.md`
- `skills/references/solidjs-frontend.md`

</details>

<details><summary>Backend jobs: 3 files</summary>

- `python/app/jobs/quota_reset_job.py`
- `python/app/jobs/slusi_ingestion_job.py`
- `python/app/jobs/weekly_yield_update.py`

</details>

<details><summary>Schema JSON: 2 files</summary>

- `database/Model/ndap_downloaded_file.json`
- `database/Model/role.json`

</details>

<details><summary>Other python: 2 files</summary>

- `python/app/__init__.py`
- `python/app/main.py`

</details>

<details><summary>Root files: 1 files</summary>

- `composer.json`

</details>

<details><summary>Other database: 1 files</summary>

- `database/insert.sql`

</details>

<details><summary>Backend agents: 1 files</summary>

- `python/app/agents/agent_tools.py`

</details>

<details><summary>Frontend shared: 1 files</summary>

- `solidjs/src/shared/run.ts`

</details>

## 8. Only in apac-genaiacademy-c2 (733)
Present in apac and missing from gemini-crop.

| Area | Files |
|---|---:|
| Other python | 248 |
| Other (.agents) | 83 |
| Other database | 83 |
| Frontend components | 80 |
| Other frontend | 73 |
| Other (e2e) | 40 |
| Terraform | 22 |
| Root files | 19 |
| Frontend shared | 17 |
| Other (Resource) | 14 |
| Other (scripts) | 14 |
| Other (schema_generator) | 11 |
| Other (docs) | 6 |
| Frontend pages | 5 |
| Other (.github) | 4 |
| Generated TS interfaces | 4 |
| Other (cognito-only) | 3 |
| Other (.aws) | 2 |
| Backend API routes | 2 |
| Other (tools) | 2 |
| Other (.claude) | 1 |

<details><summary>Other python: 248 files</summary>

- `python/COMPREHENSIVE_TEST_RESULTS.md`
- `python/ENVIRONMENT_SETUP_README.md`
- `python/IMPORT_GUIDELINES.md`
- `python/LIVESTOCK_TYPING_FIX.md`
- `python/PHASE_10_COMMITS_SUMMARY.md`
- `python/PHASE_10_COMPLETION_SUMMARY.md`
- `python/QUICK_REFERENCE.md`
- `python/QUICK_START_314.md`
- `python/README_SETUP.md`
- `python/SECURITY_IMPLEMENTATION.md`
- `python/TEST_RUN_SUMMARY.md`
- `python/activate_venv.sh`
- `python/add_username_to_cognito.py`
- `python/alembic.ini`
- `python/alembic/README-DO-NOT-RUN.md`
- `python/alembic/README.md`
- `python/alembic/env.py`
- `python/alembic/versions/001_initial_schema.py`
- `python/alembic/versions/022_create_soil_map_cache.py`
- `python/alembic/versions/023_create_weather_data_tables.py`
- `python/alembic/versions/024_create_soil_test_results_table.py`
- `python/alembic/versions/025_create_fertilizer_applications_table.py`
- `python/alembic/versions/026_add_available_quantity_to_marketplace_listings.py`
- `python/alembic/versions/027_create_advance_bookings_and_update_listings.sql`
- `python/alembic/versions/030_create_breeding_records_table.py`
- `python/alembic/versions/031_create_ai_usage_quota_table.py`
- `python/alembic/versions/2026_02_22_1632-d35ffb77671d_add_remaining_tables_for_market_.py`
- `python/alembic/versions/2026_02_22_1732-02ce9fcea720_add_annual_strategy_and_reminders_tables.py`
- `python/alembic/versions/2026_02_23_add_embeddings_to_supply_matching.py`
- `python/alembic/versions/2026_03_10_create_marketplace_listings_table.py`
- `python/alembic/versions/2026_03_10_create_supply_requests_table.py`
- `python/alembic/versions/add_username_column.sql`
- `python/app.yaml`
- `python/aws_services_config.py`
- `python/check_cognito_ses_status.py`
- `python/create_test_user.py`
- `python/database/bigquery_schemas.json`
- `python/docs/AC4_IMPLEMENTATION_SUMMARY.md`
- `python/docs/confidence_scoring_implementation.md`
- `python/docs/crop_rotation_optimization_implementation.md`
- `python/docs/opportunity_cost_implementation.md`
- `python/docs/opportunity_cost_summary.md`
- `python/docs/profit_margin_implementation.md`
- `python/docs/rag_crop_recommendation_implementation.md`
- `python/docs/seasonal_trend_analysis.md`
- `python/docs/seasonal_trend_implementation_summary.md`
- `python/docs/yoy_growth_calculations.md`
- `python/docs/yoy_implementation_summary.md`
- `python/examples/seasonal_trend_example.py`
- `python/examples/test_rate_limiting.py`
- `python/examples/verify_ac3_bedrock_intelligence.py`
- `python/examples/verify_ac6_weather_integration.py`
- `python/examples/yoy_calculation_example.py`
- `python/generate_orm_models.py`
- `python/pyproject.toml`
- `python/pytest.ini`
- `python/quick_setup.sh`
- `python/requirements-caching.txt`
- `python/requirements-minimal.txt`
- `python/requirements-test.txt`
- `python/run_critical_tests.sh`
- `python/scripts/README.md`
- `python/scripts/add_performance_indexes.py`
- `python/scripts/audit_api_routes.py`
- `python/scripts/clear_db.py`
- `python/scripts/encrypt_sensitive_fields.py`
- `python/scripts/fetch_and_update_prices.py`
- `python/scripts/fetch_email_link.py`
- `python/scripts/fetch_live_api_prices.py`
- `python/scripts/fetch_ndap_from_email.py`
- `python/scripts/fetch_soil_moisture.py`
- `python/scripts/generate_api_registry.py`
- `python/scripts/generate_api_registry_simple.py`
- `python/scripts/ingest_all.py`
- `python/scripts/ingest_sample_market_data.py`
- `python/scripts/remove_init_files.py`
- `python/scripts/run_migrations.py`
- `python/scripts/seed_market_embeddings.py`
- `python/scripts/seed_msp_data.py`
- `python/scripts/setup_cloudwatch_alarms.py`
- `python/scripts/setup_cloudwatch_dashboards.py`
- `python/scripts/setup_database.py`
- `python/scripts/test_agents_gcp.py`
- `python/scripts/test_anthropic.py`
- `python/scripts/test_bedrock_api_key.py`
- `python/scripts/test_bedrock_direct.py`
- `python/scripts/test_bedrock_models.py`
- `python/scripts/test_clean_boto.py`
- `python/scripts/test_llama.py`
- `python/scripts/test_routes.py`
- `python/scripts/test_sonnet4.py`
- `python/scripts/test_user_id.py`
- `python/scripts/test_user_snippet.py`
- `python/scripts/update_db_schema.py`
- `python/scripts/verify_no_init_files.py`
- `python/scripts/verify_security.py`
- `python/setup_environment.sh`
- `python/setup_python314.sh`
- `python/start_backend.sh`
- `python/strategy_response.json`
- `python/test_bigint_migration.sh`
- `python/test_cors.sh`
- `python/test_db.py`
- `python/test_farm_registration_bigint.py`
- `python/test_import_fix.py`
- `python/test_matching_logic.py`
- `python/test_password_reset_flow.sh`
- `python/test_password_reset_quick.sh`
- `python/test_reset_with_code.sh`
- `python/test_security_basic.py`
- `python/tests/CSRF_BUG_EXPLORATION_RESULTS.md`
- `python/tests/FIX_SUMMARY.md`
- `python/tests/MARKETPLACE_LISTINGS_BUG_EXPLORATION_RESULTS.md`
- `python/tests/MARKETPLACE_PRESERVATION_TEST_RESULTS.md`
- `python/tests/PRESERVATION_TEST_RESULTS.md`
- `python/tests/conftest.py`
- `python/tests/manual_test_advance_booking.py`
- `python/tests/manual_test_fertilizer_tracking.py`
- `python/tests/manual_test_pincode.py`
- `python/tests/manual_test_quota_reset.py`
- `python/tests/manual_test_weather_recommendations.py`
- `python/tests/smoke/test_health_checks.py`
- `python/tests/test_ac2_annual_strategy.py`
- `python/tests/test_ac2_integration.py`
- `python/tests/test_address_api.py`
- `python/tests/test_address_lookup_preservation.py`
- `python/tests/test_address_service.py`
- `python/tests/test_advance_booking.py`
- `python/tests/test_ai_quota_bug_exploration.py`
- `python/tests/test_ai_quota_preservation.py`
- `python/tests/test_alerting.py`
- `python/tests/test_analytics.py`
- `python/tests/test_annual_strategy_response.py`
- `python/tests/test_api_response_time.py`
- `python/tests/test_automatic_marketplace_listing.py`
- `python/tests/test_aws_services_config.py`
- `python/tests/test_bedrock_api_integration.py`
- `python/tests/test_bedrock_cost_efficiency.py`
- `python/tests/test_bedrock_quota_integration.py`
- `python/tests/test_booking_notifications.py`
- `python/tests/test_buyer_farmer_connection.py`
- `python/tests/test_confidence_scoring.py`
- `python/tests/test_confidence_scoring_integration.py`
- `python/tests/test_cost_accuracy_metrics.py`
- `python/tests/test_crop_milestones.py`
- `python/tests/test_crop_recommendations.py`
- `python/tests/test_csrf_simple.sh`
- `python/tests/test_data_validation_security.py`
- `python/tests/test_farm_address.py`
- `python/tests/test_farm_plots_api.py`
- `python/tests/test_farm_profile_management.py`
- `python/tests/test_farm_registration_csrf_bug.py`
- `python/tests/test_farm_registration_csrf_bug.sh`
- `python/tests/test_fertilizer_recommendations.py`
- `python/tests/test_fertilizer_tracking.py`
- `python/tests/test_fertilizer_tracking_api.py`
- `python/tests/test_fertilizer_tracking_service.py`
- `python/tests/test_fix_verification.sh`
- `python/tests/test_generated_orm.py`
- `python/tests/test_hybrid_ai.py`
- `python/tests/test_integration_critical_flows.py`
- `python/tests/test_lightweight_orm.py`
- `python/tests/test_listing_detail.py`
- `python/tests/test_livestock_address.py`
- `python/tests/test_livestock_breeding.py`
- `python/tests/test_livestock_health_management.py`
- `python/tests/test_livestock_health_property.py`
- `python/tests/test_livestock_listing_api.py`
- `python/tests/test_livestock_nutrition.py`
- `python/tests/test_livestock_registration.py`
- `python/tests/test_livestock_roi_calculator.py`
- `python/tests/test_livestock_roi_property.py`
- `python/tests/test_livestock_transaction_workflow.py`
- `python/tests/test_load_performance.py`
- `python/tests/test_market_data_yoy.py`
- `python/tests/test_marketplace_address.py`
- `python/tests/test_marketplace_integration.py`
- `python/tests/test_marketplace_listings_bug.sh`
- `python/tests/test_marketplace_preservation.py`
- `python/tests/test_marketplace_preservation.sh`
- `python/tests/test_marketplace_search.py`
- `python/tests/test_match_acceptance_coordination.py`
- `python/tests/test_mfa_security.py`
- `python/tests/test_model_training.py`
- `python/tests/test_model_training_property.py`
- `python/tests/test_monitoring.py`
- `python/tests/test_nbss_service.py`
- `python/tests/test_notification_service.py`
- `python/tests/test_offline_sync.py`
- `python/tests/test_opportunity_cost.py`
- `python/tests/test_pest_disease_api.py`
- `python/tests/test_pest_disease_early_warning.py`
- `python/tests/test_pest_disease_service.py`
- `python/tests/test_pincode_api_endpoint_verification.py`
- `python/tests/test_pincode_lookup_service.py`
- `python/tests/test_plot_analysis_api.py`
- `python/tests/test_plot_analysis_property.py`
- `python/tests/test_plot_analysis_service.py`
- `python/tests/test_plot_publishing_api.py`
- `python/tests/test_plot_publishing_property.py`
- `python/tests/test_plot_publishing_service.py`
- `python/tests/test_prediction_accuracy.py`
- `python/tests/test_predictive_analytics.py`
- `python/tests/test_predictive_analytics_service.py`
- `python/tests/test_preservation_before_fix.sh`
- `python/tests/test_price_tracking_service.py`
- `python/tests/test_profit_margin_integration.py`
- `python/tests/test_profit_margin_service.py`
- `python/tests/test_profit_margin_standalone.py`
- `python/tests/test_profitability_accuracy_property.py`
- `python/tests/test_quota_reset_job.py`
- `python/tests/test_rate_limiter.py`
- `python/tests/test_recommendation_quality.py`
- `python/tests/test_redis_caching.py`
- `python/tests/test_sagemaker_infrastructure.py`
- `python/tests/test_schema_driven_generation.py`
- `python/tests/test_seasonal_trend_service.py`
- `python/tests/test_seasonal_trends.py`
- `python/tests/test_security_headers.py`
- `python/tests/test_severe_weather_monitoring.py`
- `python/tests/test_soil_health_tracking.py`
- `python/tests/test_soil_moisture.py`
- `python/tests/test_soil_testing_service.py`
- `python/tests/test_strategy_persistence.py`
- `python/tests/test_supply_matching_pgvector.py`
- `python/tests/test_supply_request_system.py`
- `python/tests/test_transport_service.py`
- `python/tests/test_user_id_bug_exploration.py`
- `python/tests/test_user_id_preservation.py`
- `python/tests/test_user_journeys.py`
- `python/tests/test_user_registration_auth.py`
- `python/tests/test_vaccination_reminders.py`
- `python/tests/test_validation.py`
- `python/tests/test_veterinary_services.py`
- `python/tests/test_voice_assist_service.py`
- `python/tests/test_weather_api_integration.py`
- `python/tests/test_weather_integration.py`
- `python/tests/test_weather_recommendations.py`
- `python/tests/test_yield_prediction_update.py`
- `python/tools/__init__.py`
- `python/tools/slusi/__init__.py`
- `python/tools/slusi/base.py`
- `python/tools/slusi/discover_wms_layers.py`
- `python/tools/slusi/fetch_lcc_data.py`
- `python/tools/slusi/fetch_microwatershed.py`
- `python/tools/slusi/fetch_soil_profile.py`
- `python/tools/slusi/seed_state_district_codes.py`
- `python/update_existing_user_username.py`

</details>

<details><summary>Other (.agents): 83 files</summary>

- `.agents/skills/extension-to-functions-codebase/SKILL.md`
- `.agents/skills/extension-to-functions-codebase/references/configuration-migration.md`
- `.agents/skills/extension-to-functions-codebase/references/destructuring-shim.md`
- `.agents/skills/extension-to-functions-codebase/references/signature-mapping.md`
- `.agents/skills/firebase-ai-logic-basics/SKILL.md`
- `.agents/skills/firebase-ai-logic-basics/references/flutter_setup.md`
- `.agents/skills/firebase-ai-logic-basics/references/ios_setup.md`
- `.agents/skills/firebase-ai-logic-basics/references/usage_patterns_android.md`
- `.agents/skills/firebase-ai-logic-basics/references/usage_patterns_web.md`
- `.agents/skills/firebase-app-hosting-basics/SKILL.md`
- `.agents/skills/firebase-app-hosting-basics/references/cli_commands.md`
- `.agents/skills/firebase-app-hosting-basics/references/configuration.md`
- `.agents/skills/firebase-app-hosting-basics/references/emulation.md`
- `.agents/skills/firebase-auth-basics/SKILL.md`
- `.agents/skills/firebase-auth-basics/references/client_sdk_android.md`
- `.agents/skills/firebase-auth-basics/references/client_sdk_web.md`
- `.agents/skills/firebase-auth-basics/references/flutter_setup.md`
- `.agents/skills/firebase-auth-basics/references/ios_setup.md`
- `.agents/skills/firebase-auth-basics/references/security_rules.md`
- `.agents/skills/firebase-basics/SKILL.md`
- `.agents/skills/firebase-basics/references/android_setup.md`
- `.agents/skills/firebase-basics/references/firebase-cli-guide.md`
- `.agents/skills/firebase-basics/references/firebase-service-init.md`
- `.agents/skills/firebase-basics/references/flutter_setup.md`
- `.agents/skills/firebase-basics/references/ios_setup.md`
- `.agents/skills/firebase-basics/references/local-env-setup.md`
- `.agents/skills/firebase-basics/references/refresh/android_studio.md`
- `.agents/skills/firebase-basics/references/refresh/antigravity.md`
- `.agents/skills/firebase-basics/references/refresh/claude.md`
- `.agents/skills/firebase-basics/references/refresh/gemini-cli.md`
- `.agents/skills/firebase-basics/references/refresh/other-agents.md`
- `.agents/skills/firebase-basics/references/setup/android_studio.md`
- `.agents/skills/firebase-basics/references/setup/antigravity.md`
- `.agents/skills/firebase-basics/references/setup/claude_code.md`
- `.agents/skills/firebase-basics/references/setup/cursor.md`
- `.agents/skills/firebase-basics/references/setup/gemini_cli.md`
- `.agents/skills/firebase-basics/references/setup/github_copilot.md`
- `.agents/skills/firebase-basics/references/setup/other_agents.md`
- `.agents/skills/firebase-basics/references/web_setup.md`
- `.agents/skills/firebase-crashlytics/SKILL.md`
- `.agents/skills/firebase-crashlytics/references/android_setup.md`
- `.agents/skills/firebase-crashlytics/references/ios_setup.md`
- `.agents/skills/firebase-data-connect/SKILL.md`
- `.agents/skills/firebase-data-connect/examples.md`
- `.agents/skills/firebase-data-connect/reference/cloud_functions.md`
- `.agents/skills/firebase-data-connect/reference/config.md`
- `.agents/skills/firebase-data-connect/reference/data_seeding.md`
- `.agents/skills/firebase-data-connect/reference/native_sql.md`
- `.agents/skills/firebase-data-connect/reference/operations.md`
- `.agents/skills/firebase-data-connect/reference/realtime.md`
- `.agents/skills/firebase-data-connect/reference/schema.md`
- `.agents/skills/firebase-data-connect/reference/sdk_admin_node.md`
- `.agents/skills/firebase-data-connect/reference/sdk_android.md`
- `.agents/skills/firebase-data-connect/reference/sdk_flutter.md`
- `.agents/skills/firebase-data-connect/reference/sdk_ios.md`
- `.agents/skills/firebase-data-connect/reference/sdk_web.md`
- `.agents/skills/firebase-data-connect/reference/search.md`
- `.agents/skills/firebase-data-connect/reference/security.md`
- `.agents/skills/firebase-data-connect/templates.md`
- `.agents/skills/firebase-firestore/SKILL.md`
- `.agents/skills/firebase-firestore/references/enterprise/android_sdk_usage.md`
- `.agents/skills/firebase-firestore/references/enterprise/data_model.md`
- `.agents/skills/firebase-firestore/references/enterprise/flutter_setup.md`
- `.agents/skills/firebase-firestore/references/enterprise/indexes.md`
- `.agents/skills/firebase-firestore/references/enterprise/ios_setup.md`
- `.agents/skills/firebase-firestore/references/enterprise/provisioning.md`
- `.agents/skills/firebase-firestore/references/enterprise/python_sdk_usage.md`
- `.agents/skills/firebase-firestore/references/enterprise/web_sdk_usage.md`
- `.agents/skills/firebase-firestore/references/standard/android_sdk_usage.md`
- `.agents/skills/firebase-firestore/references/standard/flutter_setup.md`
- `.agents/skills/firebase-firestore/references/standard/indexes.md`
- `.agents/skills/firebase-firestore/references/standard/ios_setup.md`
- `.agents/skills/firebase-firestore/references/standard/provisioning.md`
- `.agents/skills/firebase-firestore/references/standard/web_sdk_usage.md`
- `.agents/skills/firebase-hosting-basics/SKILL.md`
- `.agents/skills/firebase-hosting-basics/references/configuration.md`
- `.agents/skills/firebase-hosting-basics/references/deploying.md`
- `.agents/skills/firebase-remote-config-basics/SKILL.md`
- `.agents/skills/firebase-remote-config-basics/references/android_setup.md`
- `.agents/skills/firebase-remote-config-basics/references/ios_setup.md`
- `.agents/skills/firebase-security-rules-auditor/SKILL.md`
- `.agents/skills/firestore-rules-creation/SKILL.md`
- `.agents/skills/xcode-project-setup/SKILL.md`

</details>

<details><summary>Other database: 83 files</summary>

- `database/Mysql/Insert/Roles_insert.sql`
- `database/Mysql/Relations/Active_role_relation.sql`
- `database/Mysql/Relations/Advance_booking_relation.sql`
- `database/Mysql/Relations/Ai_usage_quota_relation.sql`
- `database/Mysql/Relations/Annual_strategy_relation.sql`
- `database/Mysql/Relations/Buyer_interest_relation.sql`
- `database/Mysql/Relations/Crop_market_data_relation.sql`
- `database/Mysql/Relations/Crop_milestone_relation.sql`
- `database/Mysql/Relations/Crop_relation.sql`
- `database/Mysql/Relations/Farm_plot_relation.sql`
- `database/Mysql/Relations/Farm_relation.sql`
- `database/Mysql/Relations/Fertilizer_application_relation.sql`
- `database/Mysql/Relations/Livestock_health_record_relation.sql`
- `database/Mysql/Relations/Livestock_listing_relation.sql`
- `database/Mysql/Relations/Livestock_marketplace_listing_relation.sql`
- `database/Mysql/Relations/Livestock_relation.sql`
- `database/Mysql/Relations/Livestock_transaction_relation.sql`
- `database/Mysql/Relations/Market_price_relation.sql`
- `database/Mysql/Relations/Marketplace_listing_relation.sql`
- `database/Mysql/Relations/Payment_milestone_relation.sql`
- `database/Mysql/Relations/Pest_disease_alert_relation.sql`
- `database/Mysql/Relations/Pest_disease_data_relation.sql`
- `database/Mysql/Relations/Price_prediction_relation.sql`
- `database/Mysql/Relations/Quality_verification_relation.sql`
- `database/Mysql/Relations/Role_relation.sql`
- `database/Mysql/Relations/Soil_test_result_relation.sql`
- `database/Mysql/Relations/Supply_match_relation.sql`
- `database/Mysql/Relations/Supply_request_relation.sql`
- `database/Mysql/Relations/Transport_booking_relation.sql`
- `database/Mysql/Relations/Transport_provider_relation.sql`
- `database/Mysql/Relations/User_relation.sql`
- `database/Mysql/Relations/Weather_alert_relation.sql`
- `database/Mysql/Structure/Active_role.sql`
- `database/Mysql/Structure/Advance_booking.sql`
- `database/Mysql/Structure/Ai_usage_quota.sql`
- `database/Mysql/Structure/Annual_strategy.sql`
- `database/Mysql/Structure/Buyer_interest.sql`
- `database/Mysql/Structure/Crop.sql`
- `database/Mysql/Structure/Crop_market_data.sql`
- `database/Mysql/Structure/Crop_milestone.sql`
- `database/Mysql/Structure/Farm.sql`
- `database/Mysql/Structure/Farm_plot.sql`
- `database/Mysql/Structure/Fertilizer_application.sql`
- `database/Mysql/Structure/Livestock.sql`
- `database/Mysql/Structure/Livestock_health_record.sql`
- `database/Mysql/Structure/Livestock_listing.sql`
- `database/Mysql/Structure/Livestock_marketplace_listing.sql`
- `database/Mysql/Structure/Livestock_transaction.sql`
- `database/Mysql/Structure/Market_price.sql`
- `database/Mysql/Structure/Marketplace_listing.sql`
- `database/Mysql/Structure/Payment_milestone.sql`
- `database/Mysql/Structure/Pest_disease_alert.sql`
- `database/Mysql/Structure/Pest_disease_data.sql`
- `database/Mysql/Structure/Price_prediction.sql`
- `database/Mysql/Structure/Quality_verification.sql`
- `database/Mysql/Structure/Role.sql`
- `database/Mysql/Structure/Soil_test_result.sql`
- `database/Mysql/Structure/Supply_match.sql`
- `database/Mysql/Structure/Supply_request.sql`
- `database/Mysql/Structure/Transport_booking.sql`
- `database/Mysql/Structure/Transport_provider.sql`
- `database/Mysql/Structure/User.sql`
- `database/Mysql/Structure/Weather_alert.sql`
- `database/migrations/001_create_marketplace_tables.sql`
- `database/migrations/2026-09-26-cloudsql-additive.sql`
- `database/migrations/2026-09-27-crop-diagnoses.sql`
- `database/migrations/2026-09-27-crops-supporting-crop.sql`
- `database/migrations/2026-09-27-ndap-ingestion-tables.sql`
- `database/migrations/2026-09-27-satellite-observations.sql`
- `database/migrations/2026-09-27-services-livestock-name.sql`
- `database/migrations/2026-09-27-voice-assist-logs.sql`
- `database/migrations/create_push_subscriptions_table.sql`
- `database/migrations/create_veterinarians_table.sql`
- `database/migrations/fix_foreign_keys.sql`
- `database/migrations/fix_users_table_schema.sql`
- `database/migrations/migrate_uuid_to_bigint.sql`
- `database/migrations/migrate_uuid_to_bigint_comprehensive.sql`
- `database/migrations/msp_rates.sql`
- `database/migrations/recreate_with_bigserial.sh`
- `database/migrations/run_users_table_fix.sh`
- `database/migrations/slusi_integration.sql`
- `database/migrations/soil_moisture.sql`
- `database/migrations/system_settings.sql`

</details>

<details><summary>Frontend components: 80 files</summary>

- `solidjs/src/components/ProtectedRoute.tsx`
- `solidjs/src/components/assistant/AddLivestockCard.tsx`
- `solidjs/src/components/assistant/AskAnythingCard.tsx`
- `solidjs/src/components/assistant/ClipPlayer.tsx`
- `solidjs/src/components/assistant/ProposalCard.tsx`
- `solidjs/src/components/assistant/VoiceAssistant.tsx`
- `solidjs/src/components/assistant/useRecorder.ts`
- `solidjs/src/components/auth/AddressFields.tsx`
- `solidjs/src/components/auth/EmailConfirmation.tsx`
- `solidjs/src/components/auth/MFAVerification.tsx`
- `solidjs/src/components/auth/PasswordReset.tsx`
- `solidjs/src/components/auth/QuickSignIn.tsx`
- `solidjs/src/components/auth/SignInForm.tsx`
- `solidjs/src/components/auth/SignUpForm.tsx`
- `solidjs/src/components/dashboard/ActiveCropsCard.tsx`
- `solidjs/src/components/dashboard/BuyerInterestsCard.tsx`
- `solidjs/src/components/dashboard/CropProgressIndicator.tsx`
- `solidjs/src/components/dashboard/FarmJourney.tsx`
- `solidjs/src/components/dashboard/HarvestCountdown.tsx`
- `solidjs/src/components/dashboard/MarketplaceListingsCard.tsx`
- `solidjs/src/components/dashboard/QuickStats.tsx`
- `solidjs/src/components/dashboard/StrategyTimelineProgress.tsx`
- `solidjs/src/components/dashboard/TaskProgressBar.tsx`
- `solidjs/src/components/dashboard/UpcomingTasksCard.tsx`
- `solidjs/src/components/dashboard/WeatherAlertsCard.tsx`
- `solidjs/src/components/dashboard/board/AnalyticsBoard.tsx`
- `solidjs/src/components/dashboard/board/charts.tsx`
- `solidjs/src/components/farm/FarmAddressFields.tsx`
- `solidjs/src/components/farm/FarmEditForm.tsx`
- `solidjs/src/components/farm/FarmList.tsx`
- `solidjs/src/components/farm/FarmProfileDashboard.tsx`
- `solidjs/src/components/farm/FarmRegistrationForm.tsx`
- `solidjs/src/components/farm/PlotManagement.tsx`
- `solidjs/src/components/farm/SatelliteHealthCard.tsx`
- `solidjs/src/components/livestock/LivestockLocationFields.tsx`
- `solidjs/src/components/location/GeolocationCapture.tsx`
- `solidjs/src/components/marketplace/BuyerInterestForm.tsx`
- `solidjs/src/components/marketplace/DeliveryAddressFields.tsx`
- `solidjs/src/components/marketplace/ListingDetail.tsx`
- `solidjs/src/components/marketplace/ListingGrid.tsx`
- `solidjs/src/components/marketplace/MarketIntelligenceNav.tsx`
- `solidjs/src/components/marketplace/QualityDispute.tsx`
- `solidjs/src/components/marketplace/QualityHistory.tsx`
- `solidjs/src/components/marketplace/QualityPremiumCalculator.tsx`
- `solidjs/src/components/marketplace/QualityVerificationForm.tsx`
- `solidjs/src/components/marketplace/SearchFilters.tsx`
- `solidjs/src/components/marketplace/SupplyMatches.tsx`
- `solidjs/src/components/marketplace/SupplyRequestForm.tsx`
- `solidjs/src/components/marketplace/VerifierManagement.tsx`
- `solidjs/src/components/notifications/NotificationPermissionPrompt.tsx`
- `solidjs/src/components/notifications/NotificationSettings.tsx`
- `solidjs/src/components/quota/QuotaExceededNotification.tsx`
- `solidjs/src/components/quota/QuotaStatus.tsx`
- `solidjs/src/components/quota/QuotaWarning.tsx`
- `solidjs/src/components/quota/__tests__/QuotaExceededNotification.test.tsx`
- `solidjs/src/components/quota/__tests__/QuotaStatus.test.tsx`
- `solidjs/src/components/quota/__tests__/QuotaWarning.test.tsx`
- `solidjs/src/components/quota/index.ts`
- `solidjs/src/components/strategy/ImplementationTimeline.tsx`
- `solidjs/src/components/strategy/SeasonalRecommendations.tsx`
- `solidjs/src/components/strategy/StrategyRequestForm.tsx`
- `solidjs/src/components/strategy/StrategyResults.tsx`
- `solidjs/src/components/transport/TransportBooking.tsx`
- `solidjs/src/components/transport/TransportProviderRegistration.tsx`
- `solidjs/src/components/transport/TransportTracking.tsx`
- `solidjs/src/components/ui/BottomNav.tsx`
- `solidjs/src/components/ui/DesktopServicesButton.tsx`
- `solidjs/src/components/ui/ErrorDisplay.tsx`
- `solidjs/src/components/ui/InstallPrompt.tsx`
- `solidjs/src/components/ui/LanguageSwitcher.tsx`
- `solidjs/src/components/ui/LoadingSpinner.tsx`
- `solidjs/src/components/ui/MainNav.tsx`
- `solidjs/src/components/ui/OfflineIndicator.tsx`
- `solidjs/src/components/ui/ProfileDrawer.tsx`
- `solidjs/src/components/ui/ServicesMenu.tsx`
- `solidjs/src/components/ui/SimpleChart.tsx`
- `solidjs/src/components/ui/SkeletonLoader.tsx`
- `solidjs/src/components/ui/SkeletonScreen.tsx`
- `solidjs/src/components/ui/Toast.tsx`
- `solidjs/src/components/ui/index.ts`

</details>

<details><summary>Other frontend: 73 files</summary>

- `solidjs/API_CLIENT_DOCUMENTATION.md`
- `solidjs/API_CLIENT_IMPLEMENTATION.md`
- `solidjs/CSP_FIX.md`
- `solidjs/HARD_RESTART.sh`
- `solidjs/LAZY_LOADING.md`
- `solidjs/LOADING_ERROR_HANDLING.md`
- `solidjs/MIGRATE_TO_API_REGISTRY.md`
- `solidjs/MOBILE_OPTIMIZATION.md`
- `solidjs/NOTIFICATIONS_IMPLEMENTATION.md`
- `solidjs/OFFLINE_SUPPORT.md`
- `solidjs/PROGRESSIVE_LOADING.md`
- `solidjs/QUICK_START_NOTIFICATIONS.md`
- `solidjs/RESTART_FRONTEND.sh`
- `solidjs/TASK_16.2_COMPLETE.md`
- `solidjs/firebase.json`
- `solidjs/public/ICONS_README.md`
- `solidjs/public/generate-icons.html`
- `solidjs/src/__tests__/router-context-bug-exploration.test.ts`
- `solidjs/src/__tests__/router-preservation.test.ts`
- `solidjs/src/assets/styles/index.css`
- `solidjs/src/config/API_REGISTRY_USAGE.md`
- `solidjs/src/config/api-registry.json`
- `solidjs/src/config/api-registry.ts`
- `solidjs/src/hooks/__tests__/useGeolocation.test.ts`
- `solidjs/src/hooks/useGeolocation.ts`
- `solidjs/src/i18n/.hashes.json`
- `solidjs/src/i18n/en.ts`
- `solidjs/src/i18n/hi.ts`
- `solidjs/src/i18n/languages.json`
- `solidjs/src/i18n/mr.ts`
- `solidjs/src/i18n/pa.ts`
- `solidjs/src/lib/firebase.ts`
- `solidjs/src/services/advance-booking.service.ts`
- `solidjs/src/services/ai-quota.service.ts`
- `solidjs/src/services/assistant-context.ts`
- `solidjs/src/services/assistant.service.ts`
- `solidjs/src/services/auth.service.ts`
- `solidjs/src/services/board.service.ts`
- `solidjs/src/services/crop.service.ts`
- `solidjs/src/services/dashboard.service.ts`
- `solidjs/src/services/diagnosis.service.ts`
- `solidjs/src/services/farm.service.ts`
- `solidjs/src/services/livestock-marketplace.service.ts`
- `solidjs/src/services/market-intelligence.service.ts`
- `solidjs/src/services/marketplace.service.ts`
- `solidjs/src/services/notification.service.ts`
- `solidjs/src/services/pest-disease.service.ts`
- `solidjs/src/services/services-directory.service.ts`
- `solidjs/src/services/slusi.service.ts`
- `solidjs/src/services/soil.service.ts`
- `solidjs/src/services/strategy.service.ts`
- `solidjs/src/services/user.service.ts`
- `solidjs/src/services/veterinary-doctors.service.ts`
- `solidjs/src/services/weather.service.ts`
- `solidjs/src/setupTests.ts`
- `solidjs/src/stores/app-config.store.ts`
- `solidjs/src/stores/farm.store.ts`
- `solidjs/src/stores/livestock-marketplace.store.ts`
- `solidjs/src/stores/marketplace.store.ts`
- `solidjs/src/stores/strategy.store.ts`
- `solidjs/src/types/index.ts`
- `solidjs/src/utils/__tests__/dietPlan.test.ts`
- `solidjs/src/utils/dietPlan.ts`
- `solidjs/src/utils/infiniteScroll.ts`
- `solidjs/src/utils/initServiceWorker.ts`
- `solidjs/src/utils/offlineQueue.ts`
- `solidjs/src/utils/prefetch.ts`
- `solidjs/src/utils/touchGestures.ts`
- `solidjs/src/utils/useAsync.ts`
- `solidjs/src/utils/useResponsive.ts`
- `solidjs/test-offline.html`
- `solidjs/test_dashboard_service.js`
- `solidjs/vitest.config.ts`

</details>

<details><summary>Other (e2e): 40 files</summary>

- `e2e/.auth/sandbox-admin.json`
- `e2e/.auth/sandbox-buyer.json`
- `e2e/.auth/sandbox-farmer.json`
- `e2e/.sandbox-logs/run1.txt`
- `e2e/.sandbox-logs/run2.txt`
- `e2e/E2E_LOGIN_TROUBLESHOOTING.md`
- `e2e/README.md`
- `e2e/SEED_DATA_INSTRUCTIONS.md`
- `e2e/SESSION_BASED_TESTING_COMPLETE.md`
- `e2e/TESTING_GUIDE.md`
- `e2e/TEST_USER_SETUP.md`
- `e2e/global-setup.ts`
- `e2e/package.json`
- `e2e/playwright.config.ts`
- `e2e/run_tests.sh`
- `e2e/sandbox-report/index.html`
- `e2e/sandbox-results/.last-run.json`
- `e2e/sandbox.config.ts`
- `e2e/sandbox/README.md`
- `e2e/sandbox/reset-db.sh`
- `e2e/sandbox/seed.sql`
- `e2e/sandbox/start-backend.sh`
- `e2e/sandbox/start-frontend.sh`
- `e2e/specs/01-auth.spec.ts`
- `e2e/specs/02-api-security.spec.ts`
- `e2e/specs/03-page-health.spec.ts`
- `e2e/specs/fixtures.ts`
- `e2e/specs/global-setup.ts`
- `e2e/test_422.py`
- `e2e/tests/00-seed-demo-data-adaptive.spec.ts`
- `e2e/tests/00-seed-demo-data-simple.spec.ts`
- `e2e/tests/00-seed-demo-data.spec.ts`
- `e2e/tests/01-auth-flow.spec.ts`
- `e2e/tests/02-farm-registration.spec.ts`
- `e2e/tests/03-ai-crop-planning.spec.ts`
- `e2e/tests/04-ai-plot-analysis.spec.ts`
- `e2e/tests/05-ai-marketplace.spec.ts`
- `e2e/tests/06-marketplace-integration.spec.ts`
- `e2e/tests/demo-complete-workflow.spec.ts`
- `e2e/tsconfig.json`

</details>

<details><summary>Terraform: 22 files</summary>

- `terraform/COGNITO_DEPLOYMENT.md`
- `terraform/CREATE_NEW_COGNITO.md`
- `terraform/EC2_DEPLOYMENT_GUIDE.md`
- `terraform/IAM_PERMISSIONS_UPDATE.md`
- `terraform/QUICK_START.md`
- `terraform/README.md`
- `terraform/RUN_TERRAFORM.md`
- `terraform/cognito.tf`
- `terraform/cognito_minimal.tf`
- `terraform/create_cognito.sh`
- `terraform/deploy.sh`
- `terraform/ec2.tf`
- `terraform/iam.tf`
- `terraform/main.tf`
- `terraform/outputs.tf`
- `terraform/rds.tf`
- `terraform/s3.tf`
- `terraform/update_env.sh`
- `terraform/user-data/backend-setup.sh`
- `terraform/user-data/frontend-setup.sh`
- `terraform/variables.tf`
- `terraform/vpc.tf`

</details>

<details><summary>Root files: 19 files</summary>

- `CREATE_TEST_USER.sh`
- `FEATURES.md`
- `HANDOFF.md`
- `IAM_POLICY_FOR_COGNITO.json`
- `README.md`
- `check_system_health.sh`
- `compile.php`
- `copy_backend.sh`
- `create_test_user_api.sh`
- `fix_schemas.php`
- `gcp-sa-key.json`
- `gitpush.sh`
- `init_solidjs.sh`
- `install.sh`
- `package.json`
- `realtime.sh`
- `skills-lock.json`
- `vite.config.js`
- `webpack.config.js`

</details>

<details><summary>Frontend shared: 17 files</summary>

- `solidjs/src/shared/Service/Livestock.ts`
- `solidjs/src/shared/Service/Login.ts`
- `solidjs/src/shared/Service/Marketplace.ts`
- `solidjs/src/shared/Service/ModelService.ts`
- `solidjs/src/shared/Service/Notification.ts`
- `solidjs/src/shared/Service/Payments.ts`
- `solidjs/src/shared/Service/PestDisease.ts`
- `solidjs/src/shared/Service/Soil.ts`
- `solidjs/src/shared/Service/Store.ts`
- `solidjs/src/shared/Service/Supply.ts`
- `solidjs/src/shared/Service/Transport.ts`
- `solidjs/src/shared/Service/User.ts`
- `solidjs/src/shared/Service/Weather.ts`
- `solidjs/src/shared/Service/index.ts`
- `solidjs/src/shared/Store/Active_Farm.ts`
- `solidjs/src/shared/Store/Login.ts`
- `solidjs/src/shared/thelib.ts`

</details>

<details><summary>Other (Resource): 14 files</summary>

- `Resource/Js/index.js`
- `Resource/View/Component/Home/Head.html`
- `Resource/View/Component/Page/Footer.html`
- `Resource/View/Component/Page/Header.html`
- `Resource/View/Component/Page/HeaderAdmin.html`
- `Resource/View/Layout/base.html`
- `Resource/View/Layout/guest.html`
- `Resource/View/Layout/isuper.html`
- `Resource/View/Pages/Auth/dashboard.html`
- `Resource/View/Pages/Public/aboutus.html`
- `Resource/View/Pages/Public/contactus.html`
- `Resource/View/Pages/Public/index.html`
- `Resource/View/Pages/Public/login.html`
- `Resource/View/Pages/Public/register.html`

</details>

<details><summary>Other (scripts): 14 files</summary>

- `scripts/check_cognito_config.py`
- `scripts/deploy-to-ec2.sh`
- `scripts/fix_cognito_auth_flow.sh`
- `scripts/github-ec2-deploy.sh`
- `scripts/github-to-ec2-deploy.sh`
- `scripts/quick-deploy.sh`
- `scripts/regenerate_code.sh`
- `scripts/reset_database.sh`
- `scripts/restore_db_from_dump.sh`
- `scripts/run-local.sh`
- `scripts/run_migrations.sh`
- `scripts/setup-ec2-server.sh`
- `scripts/setup_aws_services.sh`
- `scripts/setup_cicd_infrastructure.sh`

</details>

<details><summary>Other (schema_generator): 11 files</summary>

- `schema_generator/__init__.py`
- `schema_generator/core/__init__.py`
- `schema_generator/core/schema_parser.py`
- `schema_generator/core/schema_validator.py`
- `schema_generator/core/template_renderer.py`
- `schema_generator/generators/__init__.py`
- `schema_generator/generators/base.py`
- `schema_generator/utils/__init__.py`
- `schema_generator/utils/file_writer.py`
- `schema_generator/utils/naming.py`
- `schema_generator/utils/type_mapping.py`

</details>

<details><summary>Other (docs): 6 files</summary>

- `docs/ARCHITECTURE.md`
- `docs/BACKEND.md`
- `docs/DATA_MODEL.md`
- `docs/FRONTEND.md`
- `docs/IMPROVEMENTS.md`
- `docs/SETUP.md`

</details>

<details><summary>Frontend pages: 5 files</summary>

- `solidjs/src/pages/marketplace/BrowseInfinite.tsx`
- `solidjs/src/pages/plots/Analyze.tsx`
- `solidjs/src/pages/plots/Compare.tsx`
- `solidjs/src/pages/strategy/Results.tsx`
- `solidjs/src/pages/test/GeolocationTest.tsx`

</details>

<details><summary>Other (.github): 4 files</summary>

- `.github/workflows/backend-ci.yml`
- `.github/workflows/deploy-production-gcp.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/scheduled-tests.yml`

</details>

<details><summary>Generated TS interfaces: 4 files</summary>

- `solidjs/src/shared/Interface/Model/Notification.ts`
- `solidjs/src/shared/Interface/Model/Soil.ts`
- `solidjs/src/shared/Interface/Model/Weather.ts`
- `solidjs/src/shared/Interface/TheType.ts`

</details>

<details><summary>Other (cognito-only): 3 files</summary>

- `cognito-only/apply_username_attribute.sh`
- `cognito-only/main.tf`
- `cognito-only/update_env.sh`

</details>

<details><summary>Other (.aws): 2 files</summary>

- `.aws/task-definition-production.json`
- `.aws/task-definition-staging.json`

</details>

<details><summary>Backend API routes: 2 files</summary>

- `python/app/api/README.md`
- `python/app/api/islogin/system_setting/system_setting.py`

</details>

<details><summary>Other (tools): 2 files</summary>

- `tools/slusi/explore_wms_api.ts`
- `tools/slusi/inspect_wms_requests.spec.ts`

</details>

<details><summary>Other (.claude): 1 files</summary>

- `.claude/settings.local.json`

</details>

## 9. Only in gemini-crop (68)
New in gemini-crop.

| Area | Files |
|---|---:|
| Other (stitch) | 39 |
| Root files | 9 |
| Other (.agents) | 8 |
| Frontend components | 4 |
| Backend API routes | 3 |
| Backend core | 1 |
| Other (scripts) | 1 |
| Skills | 1 |
| Other frontend | 1 |
| Frontend shared | 1 |

<details><summary>Other (stitch): 39 files</summary>

- `stitch/screens/screen1_dashboard.html`
- `stitch/screens/screen2_diagnose.html`
- `stitch/screens/screen3_booking.html`
- `stitch/screens/screen4_livestock.html`
- `stitch/screens/screen5_soil_satellite.html`
- `stitch/screens/screen_desktop_admin_analytics.html`
- `stitch/screens/screen_desktop_admin_quota.html`
- `stitch/screens/screen_desktop_booking.html`
- `stitch/screens/screen_desktop_buyer_dashboard.html`
- `stitch/screens/screen_desktop_climate_hub.html`
- `stitch/screens/screen_desktop_dashboard.html`
- `stitch/screens/screen_desktop_diagnose.html`
- `stitch/screens/screen_desktop_diet_plan.html`
- `stitch/screens/screen_desktop_farm_analytics.html`
- `stitch/screens/screen_desktop_farm_detail.html`
- `stitch/screens/screen_desktop_farm_register.html`
- `stitch/screens/screen_desktop_livestock.html`
- `stitch/screens/screen_desktop_livestock_hub.html`
- `stitch/screens/screen_desktop_livestock_marketplace.html`
- `stitch/screens/screen_desktop_market_intelligence.html`
- `stitch/screens/screen_desktop_marketplace_bookings.html`
- `stitch/screens/screen_desktop_marketplace_detail.html`
- `stitch/screens/screen_desktop_menu.html`
- `stitch/screens/screen_desktop_my_crops.html`
- `stitch/screens/screen_desktop_my_listings.html`
- `stitch/screens/screen_desktop_pest_disease.html`
- `stitch/screens/screen_desktop_plant_crop.html`
- `stitch/screens/screen_desktop_plot_create.html`
- `stitch/screens/screen_desktop_quota.html`
- `stitch/screens/screen_desktop_security.html`
- `stitch/screens/screen_desktop_services_directory.html`
- `stitch/screens/screen_desktop_soil_satellite.html`
- `stitch/screens/screen_desktop_strategy.html`
- `stitch/screens/screen_desktop_strategy_request.html`
- `stitch/screens/screen_desktop_strategy_select.html`
- `stitch/screens/screen_desktop_supply_planning.html`
- `stitch/screens/screen_desktop_transport_tracking.html`
- `stitch/screens/screen_desktop_veterinary_doctors.html`
- `stitch/specs/design_system.md`

</details>

<details><summary>Root files: 9 files</summary>

- `AGENTS.md`
- `ARCHITECTURE-v2.md`
- `BACKEND-v2.md`
- `DATA_MODEL-v2.md`
- `DESIGN.md`
- `FRONTEND-v2.md`
- `TASKS.md`
- `index.html`
- `pipeline.sh`

</details>

<details><summary>Other (.agents): 8 files</summary>

- `.agents/skills/puneetxp-compile-php/SKILL.md`
- `.agents/skills/puneetxp-compile-php/references/angular-frontend.md` (identical to apac `skills/references/angular-frontend.md`)
- `.agents/skills/puneetxp-compile-php/references/deno-backend.md` (identical to apac `skills/references/deno-backend.md`)
- `.agents/skills/puneetxp-compile-php/references/dotnet-backend.md` (identical to apac `skills/references/dotnet-backend.md`)
- `.agents/skills/puneetxp-compile-php/references/php-backend.md` (identical to apac `skills/references/php-backend.md`)
- `.agents/skills/puneetxp-compile-php/references/python-backend.md` (identical to apac `skills/references/python-backend.md`)
- `.agents/skills/puneetxp-compile-php/references/solidjs-frontend.md` (identical to apac `skills/references/solidjs-frontend.md`)
- `.agents/skills/stitch-to-code/SKILL.md`

</details>

<details><summary>Frontend components: 4 files</summary>

- `solidjs/src/components/common/OfflineIndicator.tsx`
- `solidjs/src/components/common/ProtectedRoute.tsx`
- `solidjs/src/components/layout/BottomDock.tsx`
- `solidjs/src/components/layout/Sidebar.tsx`

</details>

<details><summary>Backend API routes: 3 files</summary>

- `python/app/api/ipublic/crop/crop.py`
- `python/app/api/ipublic/livestock/livestock.py`
- `python/app/api/ipublic/weather_alert/weather_alert.py`

</details>

<details><summary>Backend core: 1 files</summary>

- `python/app/core/__init__.py`

</details>

<details><summary>Other (scripts): 1 files</summary>

- `scripts/pipeline.py`

</details>

<details><summary>Skills: 1 files</summary>

- `skills/stitch-to-code/SKILL.md`

</details>

<details><summary>Other frontend: 1 files</summary>

- `solidjs/src/index.css`

</details>

<details><summary>Frontend shared: 1 files</summary>

- `solidjs/src/shared/Service/Service.ts`

</details>

