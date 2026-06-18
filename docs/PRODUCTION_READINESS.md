# Naxely — Production Readiness Checklist

## Static Correctness
- [x] ruff: 0 errors (fixed 38)
- [x] mypy: 0 errors (fixed 21)

## Known-Issue Regression (7 rules)
- [x] `matplotlib.use('Agg')` called before all other imports in chart_service.py
- [x] `pyplot`/`seaborn` only imported inside functions in chart_service.py
- [x] Sync calls (`generate_sync`, `build_sync`) wrapped in `run_in_executor` inside `run_report_pipeline`
- [x] Supabase signed URLs generated fresh per GET request (never stored in DB)
- [x] CSV deleted from Supabase Storage after chart generation completes
- [x] JWT uses HS256 (jose.decode algorithms=["HS256"])
- [x] API keys encrypted with AES-256-GCM; never logged or returned

## Async & Concurrency
- [x] No `time.sleep` or `requests.get` in async functions
- [x] No shared mutable state without locks
- [x] **Low-risk exception:** `open(pdf_path, 'rb').read()` in `run_report_pipeline` (fast, local file)

## Security
- [x] CORS restricted to `https://Naxely.io,https://www.Naxely.io` (production)
- [x] Rate limiting on: reports (10/min), webhook (20/min), API-key save (5/min)
- [x] File upload validates MIME type + size cap (10MB) before storage
- [x] No secrets hardcoded in source
- [x] Error responses sanitized (500 → "An unexpected error occurred.")
- [x] RLS policies match SEC docs

## Data & Migration Consistency
- [x] Migration history linear (001 only)
- [x] SQLAlchemy models match Supabase schema
- [x] Foreign keys have appropriate ON DELETE actions

## Frontend ↔ Backend Contract
- [x] Axios response interceptor unwraps `response.data.data` when `success===true`
- [x] `/auth/verify` endpoint exists (was missing, causing silent auth failure)
- [x] Pricing.tsx CTA buttons point to `/settings?tab=billing` (not `#`)
- [x] Settings.tsx upgrade button links to `/pricing`
- [x] render.yaml has all required env vars (added 10 missing)

## Tests
- [x] 103 tests passing (unit tests for models, validation, services, routes)

## Deployment
- [x] render.yaml has build command, start command, health check path
- [x] All env vars listed (secrets marked `sync: false`)
- [x] Health endpoint returns `{"status": "ok", "version": "1.0.0"}`
- [x] DEBUG behavior gated behind `ENVIRONMENT=development`
- [x] Logging goes to stdout (captured by Render)
- [x] Log level configurable via `LOG_LEVEL` env var
