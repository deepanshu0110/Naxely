# Naxely — Documentation Audit Findings (Phase 1, read-only)

> Audited 2026-08-05. Every claim below was verified against the current code in
> this repo (git @ master), NOT against memory. Phase 2 (edits) starts only
> after this list is reviewed.
>
> Legend: 🔴 = wrong/critical, 🟠 = stale/superseded, 🟡 = minor/ambiguous.
> File paths are relative to repo root. Line numbers verified at audit time.

---

## 1. Cross-cutting (affects multiple docs)

### F-01 🔴 CI/CD is dead — workflows trigger on `main`, repo default branch is `master`
- **Docs:** `.github/workflows/backend-ci.yml:6`, `frontend-ci.yml:6`; `docs/08_DEP.md:75,121` (YAML matches files verbatim); `README.md` "Deployment" section.
- **Actual:** `git symbolic-ref HEAD` → `master`; `git branch -a` → only `master`/`origin/master`. Push events to `main` never happen, so both workflows (mypy + pytest + Render deploy hook; tsc + Vite build) never run. Deploys currently happen only via Vercel GitHub integration on `master` (see `frontend-ci.yml` comment) — the Render deploy hook step is dead.
- **Action (Phase 2):** change both workflows to `branches: [master]` (or `[master, main]`), update 08_DEP.md §3.1/3.2 to match, fix README wording.

### F-02 🟠 Domain drift: docs say `Naxely.io` / `api.Naxely.io`; live product is `naxely.com` / `api.naxely.com`
- **Docs:** `docs/05_ASD.md:10` (base URL), `docs/07_SEC.md:36` (Google redirect whitelist), `docs/07_SEC.md:81` (CORS), `docs/07_SEC.md:136-137` (share URL), `GITHUB_SECRETS.md` (VITE_API_BASE_URL), `DEPLOYMENT_CHECKLIST.md` (domains section), `docs/05_ASD.md` §3 share response.
- **Actual:** `frontend/vercel.json` CSP `connect-src … https://api.naxely.com`; `frontend/index.html` og/twitter/schema URLs `https://www.naxely.com`; `backend/app/main.py:53-61` CORS expansion hard-codes `https://naxely.com` + `www`. `api.Naxely.io` does not exist.
- **Action:** global find/replace in docs (keep one historical note).

### F-03 🔴 `render.yaml` points the frontend at a stale Vercel URL
- **File:** `backend/render.yaml` → `FRONTEND_BASE_URL: https://databrief-gamma.vercel.app`.
- **Actual:** live frontend is `https://naxely.com`. `FRONTEND_BASE_URL` is used at runtime for: share URLs (`reports.py:1338`), 402 upgrade links (`deps.py:74`, `reports.py:276`), Dodo checkout return URLs (`payments.py:150,162`), payment-failed emails (`payments.py:285`), customer-portal return (`payments.py:152`). This is a **config bug**, not just doc drift — every one of those links is wrong on any deploy created from render.yaml.
- **Action (code/config):** set to `https://naxely.com` in render.yaml AND verify the live Render env var.

### F-04 🟠 Brand color defaults are split between indigo `#6366F1` and amber `#D97A34`
- **Actual:** `chart_service.py:35` palette + `:818` default `#6366F1`; `report_service.py:196` default `#6366F1`; `auth.py:17` and `settings.py:87` profile default `#6366F1`; `pdf_service.py:65` `BRAND_COLOR_DEFAULT = '#D97A34'`; pptx fallback `#0E9F6E` (`reports.py:948`). `DESIGN_SYSTEM.md` declares amber as canonical default.
- **Docs affected:** `06_FSD.md:25,36` (accent `#6366F1`), `08_DEP.md:734,745` (tailwind palette), `04_DSD.md:113` (DB default `#6366F1`), `docs/archive/NAXELY_PROMPTS.md` (throughout).
- **Note:** 06_FSD/08_DEP/04_DSD actually *match the code* — it's the code that is inconsistent with DESIGN_SYSTEM.md. Phase 2 should fix code to amber (per DESIGN_SYSTEM), then docs to match. Do not "fix" docs to indigo.

---

## 2. docs/05_ASD.md (API Spec) — heaviest drift

### F-10 🔴 Error envelope is wrong
- **Doc:** §1 — all responses `{"success": true, "data": {}, "error": null}`.
- **Actual:** errors are `{"error": true, "code", "message", "detail"}` with NO `success` key (`backend/app/core/exceptions.py:30-35`, handlers `:49-72`); success responses have NO `error` key.
- **Action:** rewrite §1 envelope + every error example (`"error": null` / `"success": false` cases in §3 status-failed etc.).

### F-11 🔴 Tier gating: docs say 402, code returns 403
- **Doc:** §9 table (`❌ 402` for Pro/Agency features), §3 upload-sheets "Response 402: Free tier", §3 generate "Pro feature accessed without Pro tier → 402".
- **Actual:** `require_pro_or_above`/`require_agency` raise **403** `UPGRADE_REQUIRED` (`deps.py:99-112`). Only the free monthly cap is **402** `MONTHLY_LIMIT_REACHED` (`deps.py:69-79`; `reports.py:275-282`). This confirms the earlier flagged `05_ASD.md:686` instance — the whole §9 table plus §3/§4/§5 402 references are affected.
- **Action:** 402→403 in §3, §4, §5, §6, §9; keep 402 only for monthly-limit rows.

### F-12 🔴 POST /reports/generate documented 202, actual 200
- **Doc:** §3 "Response 202 (Accepted — async generation)".
- **Actual:** `reports.py:699` route has no `status_code`, returns 200 with the 202-style body.
- **Action:** either set `status_code=202` in code (preferred, matches docs + semantics) or document 200.

### F-13 🔴 Rate limits table is wrong
- **Doc:** §10 — generate 5/hour, upload 20/hour, api-key 10/hour, auth/verify 60/min per IP, webhook no limit, others 100/min.
- **Actual (slowapi, per-IP — `limiter.py:5`):** upload **10/minute** (`reports.py:272`), generate **10/minute** (`reports.py:703`), api-key **5/minute** (`settings.py:179`), webhook **20/minute** (`payments.py:169`), checkout 10/min (`payments.py:99`), downgrade 10/min (`payments.py:332`). `/auth/verify` has no limiter.
- **Action:** rewrite §10 from actual decorators.

### F-14 🟠 Settings API-key section stale
- **Doc:** §4 — Pro+ only; providers "openai" or "claude".
- **Actual:** `POST /settings/api-key` is open to all tiers (`get_current_user` only, `settings.py:178-183`); providers are **7**: openai, claude, gemini, groq, deepseek, mistral, together (`settings.py:21-28`); `DELETE /settings/api-key` is Pro+ gated. Response shape otherwise matches.

### F-15 🟠 Payments section stale
- **Doc:** §7 — agency features "5 team seats / Client workspaces / PPT export / API access"; webhook events list; "payment.failed → keep access 3 days grace".
- **Actual:** `PLANS_DATA` agency features = ["Everything in Pro", "White-label", "Dedicated support"] (`payments.py:34-36`); webhook handles `subscription.active`, `subscription.plan_changed`, `dunning.recovered`, `subscription.on_hold` (→ free) plus a downgrade event set incl. `refund.*`, `dispute.*` (`payments.py:40-49`); `payment.failed` only sends an email, no grace period (`payments.py:270-286`); webhook verified via `standardwebhooks` (not custom hmac).

### F-16 🔴 §6 Workspace endpoints don't exist
- **Doc:** full §6 (GET/POST/PATCH/DELETE /workspaces, Agency).
- **Actual:** no workspaces router exists. `Workspace`/`WorkspaceMember` models + `reports.workspace_id` FK exist (`models/workspace.py`, `models/report.py:13`), `GET /reports` accepts a `workspace_id` filter (`reports.py:1070-1079`), but there are no workspace CRUD endpoints. No frontend routes either (`App.tsx`).
- **Action:** delete §6 or add "planned/removed — models only" note; also remove agency `/workspaces` claims from FSD §2 and NAXELY_PROMPTS Prompt 10 (archived — see §6).

### F-17 🟡 §2 /auth/verify shape differs
- **Doc:** envelope `{"success": true, "data": {...}}`.
- **Actual:** bare user object, extra fields `theme_preference`, `has_completed_onboarding` (`auth.py:16-39`); also undocumented `POST /auth/complete-onboarding`, `POST /auth/skip-onboarding`.

### F-18 🟡 Share: `password` accepted but never enforced
- **Doc + code:** `ShareRequest.password` exists (`reports.py:120`) and ASD §3 documents it; `GET /share/{token}` (`reports.py:1411`) never checks a password. Either implement password protection or drop the field from schema + docs.

### F-19 🟠 Large surface undocumented (built beyond spec)
- **Not in ASD at all:** `GET /reports/sheets-config`, `POST /reports/sample-upload`, `GET /uploads`, `POST /reports/preview-charts`, `POST /reports/{id}/retry`, `POST /reports/bulk-delete`, `GET /reports/{id}/download`, `GET /reports/{id}/export/pptx`, `POST /reports/{id}/send`, `DELETE /reports/{id}/share`, `POST /payments/checkout`, `POST /payments/downgrade`, `GET /payments/subscription`, `POST /payments/cancel-scheduled-change`, `POST /settings/theme`, `DELETE /settings/account`, `POST/GET/DELETE /settings/api-keys` (+ `/permanent`) [nax_ API keys], `GET /internal/scheduled-reports/*` (cron), `/v1/*` public API, scheduled-reports router. `POST /templates` returns 200 not 201 (`templates.py:66`) and response includes `config`.
- **Action:** add an "Implemented beyond spec" appendix (or annotate), so the doc stops being treated as exhaustive.

---

## 3. Design docs (06_FSD.md, 08_DEP.md, 02_TRD.md)

### F-20 🟠 FSD §1.1 + DEP §15/17/18 describe the pre-rebrand design (indigo + Inter)
- **Docs:** `06_FSD.md:25,36,48,138,144,241,305` (accent `#6366F1`, `--chart-1`, font Inter, indigo buttons); `08_DEP.md:619-622` (Inter Google Fonts link), `:734,745,756` (tailwind `#6366F1`, Inter sans).
- **Actual:** DESIGN_SYSTEM.md (canonical): amber `#D97A34`, cream `#F7F2E9`, ink `#14131F`, warm dark `#1C1A16`, Fraunces + IBM Plex Sans/Mono. `frontend/index.html` loads Fraunces + IBM Plex (no Inter); `frontend/src/index.css`/`tailwind.config.ts` map paper/ink/amber/slate/mint/darkBg tokens; blog/landing components use `text-ink dark:text-paper` + amber (e.g. `BlogPostFlatPricing.tsx:27`).
- **Action:** replace FSD/DEP design sections with a pointer to DESIGN_SYSTEM.md (or rewrite tokens); fix DEP §15 index.html block.

### F-21 🟠 PDF fonts: docs say Helvetica, code embeds brand fonts
- **Docs:** `02_TRD.md:539`, `NAXELY_PROMPTS.md` Prompt 7 ("Font: Helvetica … no embedding needed").
- **Actual:** `pdf_service.py:40-52` registers and embeds Fraunces + IBM Plex Sans/Mono TTFs from a font dir.
- **Action:** update TRD §6.4 (done 2026-08-05); NAXELY_PROMPTS is historical (archived — see §6).

### F-22 🟡 AI models: docs say gpt-4o-mini / claude-haiku-4-5; code uses heavier models + more providers
- **Docs:** `docs/archive/NAXELY_PROMPTS.md:472,483`; TRD §6.3 (per NAXELY_PROMPTS).
- **Actual:** `ai_service.py:44-49` — gemini `gemini-2.0-flash` (app-level key; default provider when user has none), openai `gpt-4o`, claude `claude-sonnet-4-6`, groq `openai/gpt-oss-120b`, deepseek `deepseek-chat`, mistral `mistral-large-latest` (+together per settings). README's "OpenAI GPT-4/Claude 3.5 (user's own API key)" is also stale on all three counts (models, providers, and the gemini default).

### F-23 🟡 FSD §2 routes stale
- **Doc:** `/workspaces`, `/workspaces/:id` (agency); `/settings/api-key`, `/settings/billing`, `/settings/branding` as real routes.
- **Actual:** `App.tsx` — no workspaces routes; the three settings subroutes are `<Navigate to="/settings">` redirects (settings is a tabbed single page); plus unlisted: `/forgot-password`, `/auth/reset-password`, `/templates`, `/scheduled-reports`, blog (14 posts), 5 `/compare/*`, `/faq`, `/changelog`.

### F-24 🟡 TRD §7.2 testing note stale
- **Doc:** `02_TRD.md:626` "Automated: not required for MVP (add Vitest in Phase 2)".
- **Actual:** frontend has a vitest suite (305 passing); backend 811 pytest passing.

---

## 4. Security doc (07_SEC.md)

### F-30 🔴 JWT: docs say HS256 shared-secret, code verifies via Supabase JWKS (RS256)
- **Doc:** `07_SEC.md` §1.1 — "Tokens issued by Supabase Auth using **HS256** … NOT RS256 — the SEC doc previously stated RS256 incorrectly."
- **Actual:** `security.py:31-68` fetches `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (cached 1h) and verifies with the JWK key + `algorithms=[key_data["alg"]]` (RS256). The doc's correction is now wrong in the opposite direction. `docs/archive/NAXELY_PROMPTS.md` Prompt 3 (HS256, SUPABASE_JWT_SECRET) matches the old design only.
- **Action:** rewrite §1.1 with the JWKS flow; note SUPABASE_JWT_SECRET is no longer used for verification.

### F-31 🟠 Webhook verification implementation differs
- **Doc:** §5.1 custom `hmac`/`compare_digest` with `X-Dodo-Signature`.
- **Actual:** `payments.py:108-121` uses `standardwebhooks.Webhook.verify` with `webhook-id` / `webhook-signature` / `webhook-timestamp` headers (Svix standard).
- **Action:** update §5.1.

### F-32 🟠 CORS block stale
- **Doc:** §4.2 hard-coded `["https://Naxely.io", "https://www.Naxely.io"]`.
- **Actual:** env-driven `settings.resolved_allowed_origins` with `_resolve_origins()` expansion (`main.py:53-61`) + domain case (F-02).

### F-33 🟡 HSTS not implemented
- **Doc:** §4.1 "HSTS header: max-age=31536000; includeSubDomains".
- **Actual:** `main.py:66-80` sets X-Content-Type-Options, X-Frame-Options (DENY), X-XSS-Protection, Referrer-Policy, CSP — no HSTS. Not added by Render; Vercel adds HSTS for `www`-less apex only. Either implement (middleware) or document as platform-provided.

### F-34 🟠 Retention claims unenforced
- **Doc:** §3.2/§7.1 "PDFs retained 90 days then auto-deleted"; §7.3 "cron job hard-deletes soft-deleted records older than 30 days"; "CSV deleted immediately after report generation completes" (§3.1).
- **Actual:** CSV deletion happens right after chart generation (AGENTS.md rule, SDD step h) — §3.1 wording conflicts with SDD; no 90-day PDF cleanup and no 30-day purge cron exist anywhere (only the scheduled-reports cron in render.yaml). Account deletion is hard-delete + storage cleanup (`settings.py:325-391`), not soft-delete.
- **Action:** align SEC wording with SDD; either implement cleanup jobs or mark claims as "planned".

### F-35 🟡 Rate limiting key: docs say per-user, code is per-IP
- **Doc:** §8 threat model "Rate limiting per user_id (not IP, harder to bypass)".
- **Actual:** `limiter.py:5` `key_func=get_remote_address`. (Also contradicts ASD §10's "per IP" wording for auth/verify.)

---

## 5. Infra/ops docs

### F-40 🟠 GITHUB_SECRETS.md — VITE_API_BASE_URL value stale (domain), count mismatches
- **Doc:** `VITE_API_BASE_URL` → `https://api.Naxely.io` (F-02); secret table lists 7.
- **Actual:** vercel.json CSP proves `api.naxely.com`; frontend `.env.example` declares **5** VITE_ vars (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`, `VITE_DODO_CLIENT_TOKEN`, `VITE_ENVIRONMENT`), of which only 3 are needed by frontend-ci. Workflow secret usage matches the table otherwise (`backend-ci.yml:35-37,43`).

### F-41 🟠 DEPLOYMENT_CHECKLIST.md — counts, domains, CI all stale
- **Doc:** "All 8 env vars set on Render.com" / "All 4 env vars set on Vercel"; domains `Naxely.io` + `api.Naxely.io`; "CI/CD pipelines tested with a dummy commit".
- **Actual:** `render.yaml` declares **22** envVars (13 `sync: false` + 9 with values, incl. CRON_SECRET for the cron service); frontend needs **5** (see F-40); CI has never run (F-01); live domain `naxely.com`.

### F-42 🟠 PRODUCTION_READINESS*.md / FINAL_LAUNCH_READINESS.md — dated audit artifacts
- **Examples:** `PRODUCTION_READINESS.md:42` "103 tests passing" (now 811 backend); `FINAL_LAUNCH_READINESS.md` "166 passed" (now 811); `PRODUCTION_READINESS.md:22` CORS/domain claims (F-02/F-32).
- **Action:** add explicit "as-of <date>" headers and update the test counts, or archive under `docs/archive/` with a status line pointing at current sources.

---

## 6. Build archives (docs/archive/NAXELY_PROMPTS.md, docs/archive/naxely-master-build-prompt.md)

### F-50 🟠 Both are historical build scripts that no longer match the product
- **Evidence of staleness:** NVIDIA-NIM setup (outdated), indigo/Inter design (F-20), HS256 (F-30), gpt-4o-mini/claude-haiku (F-22), 402 tier gating (F-11), Helvetica PDF fonts (F-21), `check_pro_tier` deps that were renamed to `require_pro_or_above`, workspaces routes (F-16).
- **Resolution (2026-08-05):** archived — content NOT rewritten (they're a record of how the app was built). Both files moved to `docs/archive/` with a HISTORICAL banner pointing at the current sources of truth (spec docs + DESIGN_SYSTEM.md + AGENTS.md). 09_BACKLOG kept where it is — it's current.

---

## 7. Things checked and found CORRECT (no change needed)

- 09_BACKLOG.md — current, accurate (B-001/B-002 noted 2026-08-04).
- README Quick Start `alembic upgrade head` — correct: `alembic.ini` → `script_location = migrations`; `migrations/versions/001..014` exist; `render.yaml` buildCommand runs it.
- README React 18 + TypeScript + Vite + Tailwind + FastAPI/Python 3.11/SQLAlchemy/Supabase PG + Matplotlib/Recharts + ReportLab + Vercel/Render — all true.
- 03_SDD §7 free-limit 402 (`MONTHLY_LIMIT_REACHED`, 3/month) — matches `deps.py:69-79`.
- AGENTS.md critical rules (Agg backend, run_in_executor, signed URLs never stored, CSV delete after charts) — all implemented (`chart_service.py` header, `report_service.py`, `reports.py:105-117`).
- Signed URLs regenerated fresh on every read — `reports.py:105-117, 855-863, 1086-1093` (1h expiry).
- Error envelope shape `{error, code, message, detail}` — matches 02_TRD §7.2 and exceptions.py.
- 07_SEC AES-256-GCM key encryption flow (§2.2) — matches `app/utils/encryption.py` usage (`settings.py:191-194`).
- README/TRD version pins (fastapi 0.111.0, uvicorn 0.29.0, zustand ^4.5.0, recharts 2.x, vite 5.x, sqlalchemy 2.0.30) — match `requirements.txt` / `package.json`.

---

## Suggested Phase-2 order (pending your review)

1. **F-03** render.yaml `FRONTEND_BASE_URL` (config bug, live impact) — then re-verify on Render.
2. **F-01** CI branch fix (workflows + DEP §3 + README).
3. **F-02** domain sweep (ASD/SEC/GITHUB_SECRETS/DEPLOYMENT_CHECKLIST).
4. **F-10..F-19** ASD rewrite pass (envelope, 403s, rate limits, §6 removal, appendix of undocumented endpoints).
5. **F-30..F-35** SEC update (JWKS, webhook lib, CORS, retention claims, per-IP).
6. **F-20..F-24** FSD/DEP/TRD design + font + AI + routes alignment with DESIGN_SYSTEM.md/code.
7. **F-40..F-42** ops docs refresh; **F-50** archive build prompts; **F-04** code-side brand-color default alignment (code change, separate from doc edits).
