
# ASD — API Specification Document
## Naxely: AI-Powered Report Generator
> Version: 1.1 | Date: August 2026 | Status: Final

> This document was rewritten to match the implemented backend
> (`backend/app/api/routes/*`, `backend/app/core/exceptions.py`,
> `backend/app/main.py`). Every endpoint below is cited to its route
> source. Where the spec previously described behavior the backend does
> not implement (e.g. password-protected shares, Workspace management
> endpoints), the discrepancy is called out explicitly instead of being
> silently corrected.

---

## 1. API OVERVIEW

- Base URL (production): `https://api.naxely.com`
- Base URL (development): `http://localhost:8000`
- All JSON requests: `Content-Type: application/json` unless file upload (`multipart/form-data`)
- All protected routes require: `Authorization: Bearer <supabase_jwt>`
- Public API (v1) routes require instead: `X-API-Key: <key>` (see §8)
- The payments webhook authenticates via Standard Webhooks signature headers (see §7)
- Allowed HTTP methods (CORS): `GET`, `POST`, `PATCH`, `DELETE`

### Success envelope

Most endpoints return the standard envelope:

```json
{
  "success": true,
  "data": {}
}
```

**Exceptions (documented per endpoint):** `GET /auth/verify`, `GET /reports/sheets-config`,
`POST /reports/preview-charts`, `POST /reports/bulk-delete`, `POST /payments/checkout`,
`POST /settings/api-keys` (201), `GET /settings/api-keys`, all `/scheduled-reports` and
all `/v1/reports` responses return flat bodies (no envelope). `GET /share/{token}`,
`GET /reports/{id}/status` (failed state) and download endpoints are documented below.

### Error envelope

All HTTP errors raised through FastAPI/Starlette are normalized to:

```json
{
  "error": true,
  "code": "NOT_FOUND",
  "message": "Report not found",
  "detail": null
}
```

| HTTP | `code` |
|---|---|
| 400 | `BAD_REQUEST` |
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` |
| 422 | `VALIDATION_ERROR` |
| 429 | `RATE_LIMITED` |
| 500 | `INTERNAL_ERROR` |

Notes:
- When a handler raises `HTTPException(detail=<dict>)` (e.g. `UPGRADE_REQUIRED`,
  `MONTHLY_LIMIT_REACHED`, `PENDING_SCHEDULED_CHANGE`), the dict is passed through
  verbatim in `detail`, and `message` falls back to
  `"An unexpected error occurred."` (`backend/app/core/exceptions.py`).
- 422 request-validation failures include `exc.errors()` in `detail`.
- **Rate-limit (429) responses do NOT use this envelope** — they come from slowapi's
  default handler: `{"error": "Rate limit exceeded: <limit>"}`.

### Tier gating — two distinct mechanisms

| Gate | Status | `detail.code` | Source |
|---|---|---|---|
| Free monthly report cap (3/month) | **402** | `MONTHLY_LIMIT_REACHED` (+ `upgrade_url`) | `check_report_limit`, upload handler |
| Pro/Agency feature required | **403** | `UPGRADE_REQUIRED` (+ `current_tier`, `required_tier`) | `require_pro_or_above` / `require_agency` |

### Signed URLs

Storage paths (e.g. `reports/{user_id}/{report_id}/report.pdf`) are stored in the
database. Every response that includes a `pdf_url`/`logo_url` generates a **fresh
signed URL (1 hour expiry)** at request time. Never persist or cache these URLs.

---

## 2. AUTH ENDPOINTS

### GET /auth/verify
Verifies the JWT and returns the full user profile. Called on app load.

**Headers:** `Authorization: Bearer <jwt>`
**Request:** None
**Response 200 (flat body — no envelope):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Sarah Johnson",
  "avatar_url": null,
  "tier": "pro",
  "tier_expires_at": "2026-09-01T00:00:00Z",
  "has_api_key": true,
  "ai_provider": "openai",
  "logo_url": "raw/storage/path",
  "brand_color": "#6366F1",
  "company_name": "Acme Corp",
  "reports_this_month": 2,
  "monthly_limit": null,
  "theme_preference": "light",
  "has_completed_onboarding": true
}
```
**Notes:**
- Response is flat — it is NOT wrapped in `success`/`data`.
- `logo_url` is the raw storage path here (contrast `GET /settings/profile`, which
  returns a signed URL).
- If no DB row exists for the JWT subject, the endpoint **auto-creates** a fallback
  user row (tier `free`) and returns the defaults.
- `monthly_limit` is `3` for free, `null` for pro/agency.

**Response 401:** Missing/invalid/expired JWT (`UNAUTHORIZED` or `INVALID_TOKEN` in detail).

---

### POST /auth/complete-onboarding
Marks onboarding as complete.

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:** `{"success": true}`

---

### POST /auth/skip-onboarding
Marks onboarding as complete (same effect as complete-onboarding).

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:** `{"success": true}`

---

## 3. REPORT ENDPOINTS

### POST /reports/upload
Upload a CSV/XLSX file. Returns file metadata + column preview.

**Rate limit:** 10/minute per IP
**Headers:** `Authorization: Bearer <jwt>`, `Content-Type: multipart/form-data`
**Request (form-data):**
```
file: <CSV or XLSX file>
```
**Validations** (failure → 400):
- MIME type must be `text/csv` or `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Max size: 10MB
- Max rows: 50,000; min columns: 2 (`data_service.validate_csv`)
- Formula-injection scan on string cells (`validate_for_injection`)
- Free tier at 3 reports/month → **402** `MONTHLY_LIMIT_REACHED`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "upload_id": "uuid",
    "filename": "marketing_q1.csv",
    "file_url": "uploads/.../raw.csv",
    "row_count": 1250,
    "column_count": 8,
    "columns": [
      {
        "original_name": "col_1",
        "suggested_name": "Date",
        "suggested_type": "date",
        "sample_values": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "null_count": 0,
        "unique_count": 90
      }
    ],
    "preview_rows": [
      {"col_1": "2024-01-01", "col_2": "4500", "col_3": "North"}
    ]
  }
}
```
> `file_url` is a storage path, not a download URL.

---

### POST /reports/upload-sheets
Ingest a Google Sheet as a data source (user must share the sheet with the Naxely
service-account email — see `GET /reports/sheets-config`).

**Auth:** `Authorization: Bearer <jwt>` — **Pro+ required** (else **403** `UPGRADE_REQUIRED`)
**Request:**
```json
{
  "sheets_url": "https://docs.google.com/spreadsheets/d/..."
}
```
> Only `sheets_url` is accepted. The previously documented `sheet_name` field does
> not exist.

**Response 200:** Same structure as `/reports/upload`, plus:
```json
{
  "source_type": "sheets",
  "sheets_url": "https://docs.google.com/spreadsheets/d/..."
}
```
**Error responses:**
- **400** missing/invalid URL, or data validation failed
- **403** sheet not shared with the service account (permission error)
- **422** sheet could not be fetched (value error)
- **502** sheets fetch runtime error
- **503** Google Sheets integration not configured on server

---

### GET /reports/sheets-config
Returns the service-account email users must share sheets with.

**Auth:** `Authorization: Bearer <jwt>` — Pro+
**Response 200 (flat body):**
```json
{
  "configured": true,
  "service_account_email": "naxely-report@...iam.gserviceaccount.com"
}
```

---

### POST /reports/sample-upload
Uploads the bundled sample dataset (`agency_billable_hours.csv`) as an upload.

**Auth:** `Authorization: Bearer <jwt>` (any tier)
**Response 200:** Same envelope as `/reports/upload` (`upload_id`, `filename`,
`file_url`, `row_count`, `column_count`, `columns`, `preview_rows`)
**Response 500:** Sample file missing / storage failure

---

### GET /uploads
Lists the user's **unused** uploads (max 50, newest first). Used uploads are
excluded (`used = FALSE`).

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "upload_id": "uuid",
      "filename": "marketing_q1.csv",
      "row_count": 1250,
      "column_count": 8,
      "created_at": "2026-08-05T10:30:00+00:00"
    }
  ]
}
```

---

### POST /reports/preview-charts
Computes recommended chart specs for an upload. Uses AI chart selection when the
user has a BYOK key configured, otherwise rule-based fallback.

**Auth:** `Authorization: Bearer <jwt>` (any tier)
**Request:**
```json
{
  "upload_id": "uuid",
  "column_config": [
    {"original_name": "col_1", "display_name": "Date", "type": "date", "include": true}
  ]
}
```
**Response 200 (flat body — no envelope):**
```json
{
  "chart_specs": [
    {"x": "Date", "y": "Revenue", "type": "line", "title": "Revenue by Date", "recommended": true}
  ]
}
```
**Response 404:** Upload not found

---

### POST /reports/generate
Main endpoint. Triggers the report generation pipeline in the background.

**Rate limit:** 10/minute per IP
**Auth:** `Authorization: Bearer <jwt>`
**Request:**
```json
{
  "upload_id": "uuid",
  "title": "Q1 2024 Marketing Performance",
  "template_type": "marketing",
  "tone": "professional",
  "sections": ["executive_summary", "kpi_overview", "charts", "insights", "data_table"],
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-03-31"
  },
  "column_config": [
    {"original_name": "col_1", "display_name": "Date", "type": "date", "include": true},
    {"original_name": "col_2", "display_name": "Revenue", "type": "metric", "include": true}
  ],
  "brand": {
    "company_name": "Acme Corp",
    "prepared_by": "Sarah Johnson",
    "color": "#1F3864",
    "logo_url": null
  },
  "workspace_id": null,
  "chart_specs": [
    {"x": "Date", "y": "Revenue", "type": "line", "title": "Revenue by Date"}
  ]
}
```
**Defaults:** `template_type="marketing"`, `tone="professional"`, `sections=[]`.

**Response 200 (Accepted — async generation):**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "processing",
    "estimated_seconds": 45,
    "poll_url": "/reports/uuid/status"
  }
}
```
> ⚠️ Returns **200**, not 202. Also returned verbatim when a `pending`/`processing`
> report already exists for the same upload (dedupe).

**Error responses:**
- **402** `MONTHLY_LIMIT_REACHED` — free user at 3 reports/month
- **403** `UPGRADE_REQUIRED` — any section in `{"executive_summary", "insights", "anomalies", "trends"}` requires Pro+
- **404** Upload not found

> `workspace_id` is accepted and persisted into the report config, but there is no
> Workspace management API (see §6 note) — the field has no effect on generation.

---

### GET /reports/{report_id}/status
Poll for report generation progress.

**Auth:** `Authorization: Bearer <jwt>`
**Response 200 (processing):**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "processing",
    "progress_percent": 65,
    "current_step": "Generating AI insights...",
    "steps_completed": ["parsing", "charts", "ai_insights"],
    "steps_remaining": ["pdf_build"]
  }
}
```
Progress steps: `data` → 20%, `charts` → 45%, `ai` → 65%, `pdf` → 85% (steps
vary with AI sections enabled).

**When status = "completed":**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "completed",
    "progress_percent": 100,
    "pdf_url": "https://supabase-signed-url-generated-fresh...",
    "generation_time_seconds": 42.3,
    "error_message": null
  }
}
```
> ⚠️ `pdf_url` is a **freshly generated signed URL** (1hr expiry) on every request.

**When status = "failed":**
```json
{
  "success": false,
  "data": {
    "report_id": "uuid",
    "status": "failed",
    "error_message": "AI generation timed out. Report saved without AI insights."
  }
}
```

**Response 404:** Report not found

---

### GET /reports/{report_id}/download
Downloads the completed report PDF (proxied through the backend).

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:** `application/pdf`, `Content-Disposition: attachment; filename="naxely_report_<id8>.pdf"`
**Response 404:** Report not found
**Response 409:** Report not yet completed
**Response 502:** Signed URL / PDF retrieval failed

---

### GET /reports/{report_id}/export/pptx
Generates and downloads a PPTX export (regenerates charts + KPIs on the fly).

**Auth:** `Authorization: Bearer <jwt>` — **Agency only** (else 403)
**Response 200:** `application/vnd.openxmlformats-officedocument.presentationml.presentation` attachment
**Response 404:** Report not found
**Response 422:** Report has no CSV upload / original CSV missing from storage

---

### GET /reports
List all reports for authenticated user.

**Auth:** `Authorization: Bearer <jwt>`
**Query params:**
- `limit`: int (default 20, max 50)
- `offset`: int (default 0)
- `workspace_id`: uuid (optional, filters on the stored `workspace_id` column)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "uuid",
        "title": "Q1 2024 Marketing Performance",
        "template_type": "marketing",
        "status": "completed",
        "row_count": 1250,
        "trend_pct": 18.5,
        "created_at": "2026-08-05T10:30:00+00:00",
        "generation_time_seconds": 42.3,
        "pdf_url": "https://signed-url..."
      }
    ],
    "total": 15,
    "limit": 20,
    "offset": 0
  }
}
```
> `pdf_url` is only present (signed) when `status == "completed"`, else `null`.

---

### GET /reports/{report_id}
Get single report with full details including AI content.

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Q1 2024 Marketing Performance",
    "status": "completed",
    "ai_summary": "Revenue grew 18% month-over-month...",
    "ai_insights": [
      {
        "kpi": "Revenue",
        "number": "Revenue reached $45,200 in March",
        "reason": "Enterprise tier drove 68% of growth",
        "action": "Double down on Enterprise sales motion",
        "sentiment": "positive",
        "priority": "high"
      }
    ],
    "ai_anomalies": [],
    "row_count": 1250,
    "column_count": 8,
    "trend_pct": 18.5,
    "generation_time_seconds": 42.3,
    "pdf_url": "https://signed-url...",
    "share_token": null,
    "share_view_count": 0,
    "created_at": "2026-08-05T10:30:00+00:00",
    "error_message": null,
    "ai_skipped": false,
    "data_source_stale": false
  }
}
```
**Response 404:** Report not found

---

### POST /reports/{report_id}/retry
Re-runs the pipeline for a failed report (resets to `pending`).

**Auth:** `Authorization: Bearer <jwt>` (any tier)
**Response 200:**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "processing",
    "poll_url": "/reports/uuid/status"
  }
}
```
**Response 400:** Report is not in `failed` status
**Response 404:** Report not found

---

### POST /reports/bulk-delete
Permanently deletes up to 50 reports (DB row + PDF from storage). Not a soft delete.

**Auth:** `Authorization: Bearer <jwt>`
**Request:**
```json
{"report_ids": ["uuid1", "uuid2"]}
```
**Response 200 (flat body):**
```json
{"deleted": 2, "ids": ["uuid1", "uuid2"]}
```
**Response 400:** More than 50 IDs

---

### DELETE /reports/{report_id}
Soft delete a report (`deleted_at` set; PDF remains in storage).

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:** `{"success": true, "data": {"deleted": true}}`
**Response 404:** Report not found (includes reports owned by another user — no 403)

---

### POST /reports/{report_id}/share
Create a shareable link (regenerates a new token each call).

**Auth:** `Authorization: Bearer <jwt>` — **Pro+** (else 403)
**Request:**
```json
{
  "expires_days": 30
}
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "share_url": "https://naxely.com/share/abc123xyz",
    "share_token": "abc123xyz",
    "expires_at": "2026-09-04T00:00:00Z"
  }
}
```
> ⚠️ **Password protection is not implemented.** A `password` field briefly
> existed on `ShareRequest` but was removed (Aug 7, 2026 — audit finding F-18);
> access control is the share token itself (384-bit `secrets.token_urlsafe(48)`),
> not a password. `expires_days` is bounded 1–365.

**Response 404:** Report not found

---

### DELETE /reports/{report_id}/share
Revoke the share link (clears token + expiry).

**Auth:** `Authorization: Bearer <jwt>` — Pro+
**Response 200:** `{"success": true, "data": {"revoked": true}}`
**Response 404:** Report not found

---

### POST /reports/{report_id}/send
Emails the report PDF to client recipients.

**Auth:** `Authorization: Bearer <jwt>` — **Pro+**
**Request:**
```json
{
  "recipients": ["client@example.com"],
  "message": "Please review Q1 numbers."
}
```
**Response 200:** `{"success": true, "data": {"sent": true, "recipients": 1}}`
**Response 404:** Report not found
**Response 409:** Report has no PDF to send
**Response 502:** Email delivery failed

---

### GET /share/{share_token}
Public endpoint — view a shared report (no auth required). Increments
`share_view_count`.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Q1 2024 Marketing Performance",
    "status": "completed",
    "template_type": "marketing",
    "ai_summary": "Revenue grew 18% month-over-month...",
    "ai_insights": [],
    "ai_anomalies": [],
    "pdf_url": "https://signed-url...",
    "created_at": "2026-08-05T10:30:00+00:00",
    "is_white_label": false
  }
}
```
> `is_white_label` is true when the report owner's tier is `agency`.
> No password protection exists on this endpoint (password field removed Aug 7, 2026 — see note on POST .../share).

**Response 404:** Token not found → message `"Shared report not found"` (exact string; `reports.py:1430`)
**Response 410:** Link expired (⚠️ quirk: the shared error handler has no mapping
for 410, so the envelope `code` reads `INTERNAL_ERROR` while the HTTP status is 410)

---

## 4. SETTINGS ENDPOINTS

### GET /settings/profile
Get current user's full settings.

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": {
    "email": "user@example.com",
    "full_name": "Sarah Johnson",
    "tier": "pro",
    "ai_provider": "openai",
    "has_api_key": true,
    "api_key_preview": "sk-proj-...abcd",
    "logo_url": "https://signed-logo-url...",
    "brand_color": "#6366F1",
    "reports_this_month": 2,
    "monthly_limit": null
  }
}
```
> `logo_url` here is a **signed URL** (contrast `GET /auth/verify`).

---

### PATCH /settings/profile
Update user's display name.

**Auth:** `Authorization: Bearer <jwt>`
**Request:** `{"full_name": "Sarah Johnson"}` (max 255 chars, trimmed)
**Response 200:**
```json
{
  "success": true,
  "data": {"full_name": "Sarah Johnson", "updated_at": "2026-08-05T10:30:00+00:00"}
}
```
**Response 400:** empty name

---

### POST /settings/api-key
Save the user's AI provider API key (encrypted at rest — BYOK).

**Rate limit:** 5/minute per IP
**Auth:** `Authorization: Bearer <jwt>` — **any tier**
**Request:**
```json
{"provider": "openai", "api_key": "sk-proj-..."}
```
**Valid providers:** `openai`, `claude`, `gemini`, `groq`, `deepseek`, `mistral`, `together`
**Validations** (failure → 400): provider must be in the list above; key must match
the provider's format regex (e.g. `sk-` for OpenAI, `sk-ant-` for Claude,
`AIza...`/`AQ....` for Gemini, `gsk_` for Groq); max 200 chars.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "provider": "openai",
    "key_preview": "...xxxx",
    "saved_at": "2026-08-05T10:30:00+00:00"
  }
}
```
> Full key is NEVER returned — only the last 4 chars. `key_preview` is stored
> server-side on save; older keys without a preview show a provider-derived
> placeholder.

---

### DELETE /settings/api-key
Remove stored API key.

**Auth:** `Authorization: Bearer <jwt>` — **Pro+** (asymmetric with POST, which is any tier)
**Response 200:** `{"success": true, "data": {"deleted": true}}`

---

### POST /settings/branding
Update brand settings (logo, brand color, company name).

**Auth:** `Authorization: Bearer <jwt>`, `Content-Type: multipart/form-data` — **Pro+**
**Request (form-data):**
```
logo: <image file> (optional, .png/.jpg/.svg, max 2MB)
brand_color: "#1F3864"   (optional, must match #RRGGBB)
company_name: "Acme Corp" (optional, max 255)
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "logo_url": "https://signed-logo-url...",
    "brand_color": "#1F3864",
    "company_name": "Acme Corp",
    "suggested_colors": ["#1F3864", "#2E4B8F", "#0E9F6E"]
  }
}
```
> `suggested_colors` is auto-extracted from an uploaded logo (up to 3 colors).
> `company_name` is stored on `users.company_name` and used as the default on
> report cover pages.

**Error responses:** 400 (bad extension / >2MB / bad hex / no fields), 500 (storage failure)

---

### POST /settings/theme
Set UI theme preference.

**Auth:** `Authorization: Bearer <jwt>`
**Request:** `{"theme": "light"}` or `{"theme": "dark"}`
**Response 200:** `{"success": true, "data": {"theme": "light"}}`

---

### DELETE /settings/account
Permanently delete the account (storage files, Supabase auth user, DB rows).

**Auth:** `Authorization: Bearer <jwt>`
**Request:** `{"email": "user@example.com"}` (must match account email)
**Response 200:** `{"success": true, "data": {"deleted": true}}`
**Response 400:** email mismatch
**Response 502:** auth-provider deletion failed

---

### POST /settings/api-keys (Agency API keys)
Create a public-API key. Returns the raw key **once**.

**Auth:** `Authorization: Bearer <jwt>` — **Agency only**
**Request:** `{"name": "CI pipeline"}` (required, max 100 chars)
**Response 201 (flat body):**
```json
{
  "id": "uuid",
  "name": "CI pipeline",
  "key": "nax_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "key_prefix": "nax_ab12",
  "key_suffix": "cd34",
  "created_at": "2026-08-05T10:30:00+00:00",
  "message": "Save this key now. It will not be shown again."
}
```
> Max 10 active keys. Keys are 36 chars starting `nax_`; only the hash is stored.

**Response 400:** missing/too-long name, or 10 active keys already

---

### GET /settings/api-keys
List public-API keys (raw keys never returned).

**Auth:** `Authorization: Bearer <jwt>` — Agency
**Response 200 (flat array):**
```json
[
  {
    "id": "uuid",
    "name": "CI pipeline",
    "key_display": "nax_ab12...cd34",
    "created_at": "2026-08-05T10:30:00+00:00",
    "last_used_at": null,
    "revoked": false
  }
]
```

---

### DELETE /settings/api-keys/{key_id}
Revoke a public-API key.

**Auth:** `Authorization: Bearer <jwt>` — Agency
**Response 200:** `{"success": true, "message": "API key revoked"}`
**Response 404:** Key not found or already revoked

---

### DELETE /settings/api-keys/{key_id}/permanent
Permanently delete a public-API key (no revocation tombstone).

**Auth:** `Authorization: Bearer <jwt>` — Agency
**Response 200:** `{"success": true}`

---

## 5. TEMPLATE ENDPOINTS

### GET /templates
List user's saved templates (newest first).

**Auth:** `Authorization: Bearer <jwt>` — **Pro+**
**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Monthly Marketing Report",
      "template_type": "marketing",
      "config": {},
      "is_default": false,
      "created_at": "2026-08-01T00:00:00+00:00"
    }
  ]
}
```

---

### POST /templates
Save a new template.

**Auth:** `Authorization: Bearer <jwt>` — **Pro+**
**Request:**
```json
{
  "name": "Monthly Marketing Report",
  "template_type": "marketing",
  "config": {}
}
```
**Response 200** (⚠️ not 201): Created template object (same shape as GET item,
with `config` echoed back).
**Response 400:** empty name
**Response 500:** insert failure

---

### PATCH /templates/{template_id}
Update a template.

**Auth:** `Authorization: Bearer <jwt>` — **Pro+**
**Request:** any of `{"name": "...", "is_default": true, "config": {}}`
> Setting `is_default: true` clears `is_default` on the user's other templates.

**Response 200:** Updated template object
**Response 400:** empty name
**Response 404:** Template not found

---

### DELETE /templates/{template_id}
Delete a template.

**Auth:** `Authorization: Bearer <jwt>` — **Pro+**
**Response 200:** `{"success": true, "data": {"deleted": true}}`
**Response 404:** Template not found

---

## 6. SCHEDULED REPORT ENDPOINTS (Agency)

> ⚠️ **Workspace endpoints do not exist.** The previously documented
> `GET/POST/PATCH/DELETE /workspaces` routes were never implemented — there is no
> workspace management API. A `workspace_id` column exists on
> `scheduled_reports`/`reports` and is accepted in request bodies, but nothing
> creates or manages workspaces. Replaced below with the real Agency feature:
> scheduled reports.

### POST /scheduled-reports
Create a recurring report that emails the PDF to recipients on a schedule.

**Auth:** `Authorization: Bearer <jwt>` — **Agency only** (else 403)
**Request:**
```json
{
  "upload_id": "uuid",
  "name": "Weekly Client Digest",
  "frequency": "weekly",
  "recipient_emails": ["client@example.com"],
  "template_id": null,
  "workspace_id": null,
  "config_json": null
}
```
**Validations** (failure → 422): `frequency` must be one of `daily`, `weekly`,
`monthly`; `recipient_emails` must be non-empty.

**Response 200 (flat body — the response model, not an envelope):**
```json
{
  "id": "uuid",
  "name": "Weekly Client Digest",
  "frequency": "weekly",
  "next_run_at": "2026-08-12T10:30:00+00:00",
  "last_run_at": null,
  "recipient_emails": ["client@example.com"],
  "csv_storage_path": "scheduled-sources/...",
  "config_json": null,
  "is_active": true,
  "created_at": "2026-08-05T10:30:00+00:00",
  "template_id": null,
  "workspace_id": null,
  "sheets_url": null
}
```
**Response 404:** Upload not found (or not owned by user)
**Response 500:** DB insert / CSV copy failure

---

### GET /scheduled-reports
List the user's scheduled reports (newest first).

**Auth:** `Authorization: Bearer <jwt>` — Agency
**Response 200:** flat array of scheduled-report objects (shape above)

---

### PATCH /scheduled-reports/{report_id}
Update a scheduled report. Changing `frequency` recomputes `next_run_at`.

**Auth:** `Authorization: Bearer <jwt>` — Agency
**Request:** any of `{"name", "frequency", "recipient_emails", "is_active", "template_id", "config_json"}`
**Response 200:** Updated scheduled-report object
**Response 404:** Not found

---

### DELETE /scheduled-reports/{report_id}
Delete a scheduled report.

**Auth:** `Authorization: Bearer <jwt>` — Agency
**Response 200:** `{"success": true, "message": "Scheduled report deleted"}`
**Response 404:** Not found

---

### POST /internal/scheduled-reports/run
Internal cron trigger. Runs all due scheduled reports (fetch latest sheet data,
generate PDF, email recipients) in the background.

**Headers:** `X-Cron-Secret: <secret>` (matches `CRON_SECRET`)
**Response 202:** `{"status": "accepted"}`
**Response 403:** Invalid secret

---

## 7. PAYMENT ENDPOINTS

### GET /payments/plans
Public — returns current pricing plans.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "plans": [
      {
        "id": "free",
        "name": "Free",
        "price_monthly": 0,
        "features": ["3 reports/month", "CSV upload", "Basic charts", "PDF with watermark"]
      },
      {
        "id": "pro",
        "name": "Pro",
        "price_monthly": 29,
        "dodo_product_id": "prod_xxx",
        "features": ["Unlimited reports", "AI insights", "Custom branding", "Google Sheets", "No watermark"]
      },
      {
        "id": "agency",
        "name": "Agency",
        "price_monthly": 79,
        "dodo_product_id": "prod_xxx",
        "features": ["Everything in Pro", "White-label", "Dedicated support"]
      }
    ]
  }
}
```

---

### POST /payments/checkout
Creates a Dodo checkout session, or changes the plan for existing subscribers.

**Rate limit:** 10/minute per IP
**Auth:** `Authorization: Bearer <jwt>`
**Request:** `{"plan": "pro"}` or `{"plan": "agency"}`
**Response 200 (flat body):**
```json
{"checkout_url": "https://checkout.dodopayments.com/..."}
```
- Existing subscriber, same tier → **400** "Already subscribed to this plan"
- Existing subscriber, different tier → plan changed in place; returns `{"checkout_url": ""}`
- On-hold subscriber with a customer reference → customer portal session link

**Error responses:** 400 (invalid plan), 500 (product not configured), 502 (Dodo API failure)

---

### POST /payments/webhook
Dodo Payments webhook receiver. Verifies the Standard Webhooks signature, then
records the event and updates tier state.

**Rate limit:** 20/minute per IP
**Headers (Standard Webhooks):**
```
webhook-id: <id>
webhook-signature: <base64 sig>
webhook-timestamp: <unix ts>
```
> ⚠️ The previously documented `X-Dodo-Signature` header is wrong — verification
> uses Standard Webhooks headers via `standardwebhooks` library.

**Event → tier effect:**
| Event | Effect |
|---|---|
| `subscription.created` / `subscription.renewed` / `subscription.active` / `subscription.plan_changed` / `dunning.recovered` | Set tier (`pro`/`agency` from product), store `tier_expires_at`, `dodo_subscription_id`, `dodo_customer_id` |
| `subscription.on_hold` | Downgrade to `free`, clear `tier_expires_at` |
| `subscription.cancelled` / `subscription.failed` / `subscription.expired` / `refund.succeeded` / `dispute.opened` / `dispute.lost` / `dispute.accepted` / `dispute.expired` | Downgrade to `free`, clear expiry + subscription id |
| `payment.failed` | Email the user a payment-failure notice |

Idempotency: duplicate `webhook-id`s return
`{"success": true, "data": {"status": "already_processed"}}`.

**Response 200:** `{"success": true, "data": {"status": "processed"}}`
**Response 400:** invalid signature, unparseable JSON, or missing `webhook-id`

---

### POST /payments/downgrade
Schedule a downgrade (never immediate).

**Rate limit:** 10/minute per IP
**Auth:** `Authorization: Bearer <jwt>`
**Request:** `{"plan": "pro"}` (Agency→Pro) or `{"plan": "free"}` (any paid → Free)
**Response 200:**
```json
{
  "success": true,
  "data": {
    "planned_tier": "free",
    "effective_date": "2026-09-04T00:00:00+00:00",
    "message": "Your Pro access continues until September 4, 2026. After that, you'll move to the Free plan.",
    "scheduled_change_id": null
  }
}
```
(`scheduled_change_id` present only for Agency→Pro changes.)

**Error responses:**
- **400** no active subscription / already free / invalid plan / already on requested plan
- **400** with `detail.code` = `PENDING_SCHEDULED_CHANGE` or `PENDING_CANCELLATION` (resolve via `POST /payments/cancel-scheduled-change` first)
- **500** product not configured
- **502** Dodo API failure

---

### GET /payments/subscription
Returns live subscription state from Dodo.

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": {
    "has_subscription": true,
    "subscription_id": "sub_xxx",
    "status": "active",
    "next_billing_date": "2026-09-01T00:00:00+00:00",
    "cancel_at_next_billing_date": false,
    "scheduled_change": null
  }
}
```
`has_subscription: false` when the user has no `dodo_subscription_id`.
**Response 502:** Dodo retrieval failure

---

### POST /payments/cancel-scheduled-change
Cancels a pending plan change or a pending cancellation.

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{"success": true, "data": {"cancelled": true, "type": "plan_change"}}
```
`type` is `plan_change` or `cancellation`.
**Response 400:** no subscription / nothing scheduled
**Response 502:** Dodo API failure

---

### POST /payments/cancel
Schedules subscription cancellation at the next billing date (access continues
until period end).

**Auth:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": {
    "cancelled": true,
    "access_until": "2026-09-04T00:00:00+00:00",
    "message": "Your Pro access continues until September 4, 2026"
  }
}
```
**Response 400:** no active subscription
**Response 502:** Dodo API failure

---

## 8. PUBLIC API (v1)

Machine-to-machine API. **Auth:** `X-API-Key: <key>` (keys created via
`POST /settings/api-keys`). Invalid/missing/revoked key → **401**; non-Agency
account → **403**. Key `last_used_at` is updated on every call.

### POST /v1/reports
Create a report from a CSV/XLSX upload.

**Request (multipart/form-data):**
```
file: <CSV or XLSX>
title: "Q3 Revenue"
sections: '["kpi","charts","ai_insights","anomalies"]'   (optional JSON string)
tone: "professional"                                      (optional)
```
**Response 202 (flat body):**
```json
{
  "report_id": "uuid",
  "status": "processing",
  "status_url": "/v1/reports/uuid",
  "message": "Report generation started. Poll status_url for completion."
}
```
**Response 422:** unparseable file / fewer than 2 columns
**Response 401/403:** API-key errors

---

### GET /v1/reports/{report_id}
Poll status.

**Auth:** `X-API-Key`
**Response 200 (flat body):**
```json
{
  "report_id": "uuid",
  "status": "completed",
  "pdf_url": "https://signed-url...",
  "download_url": "/v1/reports/uuid/download"
}
```
(`pdf_url`/`download_url` only when completed; `error` field when failed.)
**Response 404:** Report not found

---

### GET /v1/reports/{report_id}/download
Download the report PDF.

**Auth:** `X-API-Key`
**Response 200:** `application/pdf` attachment
**Response 404:** Report not found
**Response 409:** Not yet completed
**Response 502:** Signed URL / PDF retrieval failed

---

## 9. HEALTH ENDPOINT

### GET /health
Public. Used by Uptime Robot + Render health checks.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-08-05T10:00:00+00:00"
}
```

---

## 10. TIER ENFORCEMENT RULES

> 402 = `MONTHLY_LIMIT_REACHED` (free monthly cap). 403 = `UPGRADE_REQUIRED`
> (feature gated by plan).

| Endpoint | Free | Pro | Agency |
|---|---|---|---|
| POST /reports/upload | ✅ (402 at 3/month) | ✅ | ✅ |
| POST /reports/sample-upload | ✅ | ✅ | ✅ |
| POST /reports/generate (no AI sections) | ✅ (402 at 3/month) | ✅ | ✅ |
| POST /reports/generate (AI sections) | ❌ 403 | ✅ | ✅ |
| POST /reports/preview-charts | ✅ | ✅ | ✅ |
| GET /reports, GET /reports/{id}, /status, /download, DELETE, /retry, /bulk-delete | ✅ | ✅ | ✅ |
| POST /reports/upload-sheets | ❌ 403 | ✅ | ✅ |
| GET /reports/sheets-config | ❌ 403 | ✅ | ✅ |
| POST /reports/{id}/share, DELETE .../share, POST .../send | ❌ 403 | ✅ | ✅ |
| GET /reports/{id}/export/pptx | ❌ 403 | ❌ 403 | ✅ |
| POST /settings/api-key (save) | ✅ | ✅ | ✅ |
| DELETE /settings/api-key | ❌ 403 | ✅ | ✅ |
| POST /settings/branding | ❌ 403 | ✅ | ✅ |
| GET/PATCH /settings/profile, POST /settings/theme, DELETE /settings/account | ✅ | ✅ | ✅ |
| POST /settings/api-keys, GET, DELETE (Agency API keys) | ❌ 403 | ❌ 403 | ✅ |
| GET/POST/PATCH/DELETE /templates | ❌ 403 | ✅ | ✅ |
| /scheduled-reports (all) | ❌ 403 | ❌ 403 | ✅ |
| /v1/* (X-API-Key auth) | ❌ 401/403 | ❌ 403 | ✅ |
| GET /payments/plans, GET /health, GET /share/{token} | Public | Public | Public |

---

## 11. RATE LIMITING

Keyed **per IP address** (slowapi `get_remote_address`), not per user. All limits
are per minute. Exceeding any limit → **429** with slowapi's default body:
`{"error": "Rate limit exceeded: <limit>"}`.

| Endpoint | Limit |
|---|---|
| POST /reports/upload | 10/minute |
| POST /reports/generate | 10/minute |
| POST /payments/checkout | 10/minute |
| POST /payments/downgrade | 10/minute |
| POST /payments/webhook | 20/minute |
| POST /settings/api-key | 5/minute |
| All other endpoints | No limit |

---

*End of ASD*
