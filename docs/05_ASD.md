
# ASD — API Specification Document
## Naxely: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. API OVERVIEW

- Base URL (production): `https://api.Naxely.io`
- Base URL (development): `http://localhost:8000`
- All requests: `Content-Type: application/json` unless file upload
- All protected routes require: `Authorization: Bearer <supabase_jwt>`
- All responses follow standard envelope:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

---

## 2. AUTH ENDPOINTS

### POST /auth/verify
Verifies JWT token and returns user profile. Called on app load.

**Headers:** `Authorization: Bearer <jwt>`
**Request:** None
**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Sarah Johnson",
    "avatar_url": "https://...",
    "tier": "pro",
    "tier_expires_at": "2026-07-01T00:00:00Z",
    "has_api_key": true,
    "ai_provider": "openai",
    "logo_url": "https://...",
    "brand_color": "#6366F1",
    "reports_this_month": 2,
    "monthly_limit": null
  }
}
```

**Response 401:** Invalid or expired JWT

---

## 3. REPORT ENDPOINTS

### POST /reports/upload
Upload a CSV file. Returns file metadata + column preview.

**Headers:** `Authorization: Bearer <jwt>`, `Content-Type: multipart/form-data`
**Request (form-data):**
```
file: <CSV file>
```
**Validations:**
- File must be .csv or .xlsx
- Max size: 10MB
- Max rows: 50,000
- Must have at least 2 columns

**Response 200:**
```json
{
  "success": true,
  "data": {
    "upload_id": "uuid",
    "filename": "marketing_q1.csv",
    "file_url": "https://supabase.../uploads/...",
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
      {"col_1": "2024-01-01", "col_2": 4500, "col_3": "North"}
    ]
  }
}
```

**Response 400:** File too large / invalid format / too many rows
**Response 402:** Free user at monthly limit

---

### POST /reports/upload-sheets
Connect a Google Sheets URL as data source.

**Headers:** `Authorization: Bearer <jwt>` (Pro+ only)
**Request:**
```json
{
  "sheets_url": "https://docs.google.com/spreadsheets/d/...",
  "sheet_name": "Sheet1"
}
```
**Response 200:** Same structure as /reports/upload
**Response 400:** Invalid URL / sheet not publicly accessible
**Response 402:** Free tier (Sheets is Pro only)

---

### POST /reports/generate
Main endpoint. Triggers full report generation pipeline.

**Headers:** `Authorization: Bearer <jwt>`
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
    {
      "original_name": "col_1",
      "display_name": "Date",
      "type": "date",
      "include": true
    },
    {
      "original_name": "col_2",
      "display_name": "Revenue",
      "type": "metric",
      "include": true
    }
  ],
  "brand": {
    "company_name": "Acme Corp",
    "prepared_by": "Sarah Johnson"
  },
  "workspace_id": null
}
```

**Response 202 (Accepted — async generation):**
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

**Response 402:** Free user at limit / Pro feature accessed without Pro tier

---

### GET /reports/{report_id}/status
Poll for report generation progress.

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "processing",
    "progress_percent": 65,
    "current_step": "Generating AI insights...",
    "steps_completed": ["parsing", "charts"],
    "steps_remaining": ["ai_insights", "pdf_build"]
  }
}
```

**When status = "completed":**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "completed",
    "progress_percent": 100,
    "pdf_url": "https://supabase-signed-url-generated-fresh...",
    "generation_time_seconds": 42.3
  }
}
```
> ⚠️ `pdf_url` here is a **freshly generated signed URL** (1hr expiry) — the DB stores the storage path, the backend generates the URL on every response.

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

---

### GET /reports
List all reports for authenticated user.

**Headers:** `Authorization: Bearer <jwt>`
**Query params:**
- `limit`: int (default 20, max 50)
- `offset`: int (default 0)
- `workspace_id`: uuid (optional, filter by workspace)

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
        "pdf_url": "https://signed-url...",
        "created_at": "2026-06-01T10:30:00Z",
        "generation_time_seconds": 42.3
      }
    ],
    "total": 15,
    "limit": 20,
    "offset": 0
  }
}
```

---

### GET /reports/{report_id}
Get single report with full details including AI content.

**Headers:** `Authorization: Bearer <jwt>`
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
    "pdf_url": "https://signed-url...",
    "share_token": null,
    "share_view_count": 0,
    "created_at": "2026-06-01T10:30:00Z"
  }
}
```

---

### DELETE /reports/{report_id}
Soft delete a report.

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:** `{"success": true, "data": {"deleted": true}}`
**Response 403:** Report belongs to another user
**Response 404:** Report not found

---

### POST /reports/{report_id}/share
Generate a shareable link.

**Headers:** `Authorization: Bearer <jwt>` (Pro+ only)
**Request:**
```json
{
  "expires_days": 30,
  "password": null
}
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "share_url": "https://Naxely.io/share/abc123xyz",
    "share_token": "abc123xyz",
    "expires_at": "2026-07-15T00:00:00Z"
  }
}
```

---

### GET /share/{share_token}
Public endpoint — view a shared report (no auth required).

**Response 200:** Report data (limited fields, no user info)
**Response 404:** Token not found or expired
**Response 410:** Link expired

---

## 4. SETTINGS ENDPOINTS

### POST /settings/api-key
Save or update user's AI API key (encrypted).

**Headers:** `Authorization: Bearer <jwt>` (Pro+ only)
**Request:**
```json
{
  "provider": "openai",
  "api_key": "sk-proj-..."
}
```
**Validations:**
- provider must be "openai" or "claude"
- api_key must start with "sk-" (OpenAI) or "sk-ant-" (Claude)
- api_key max length: 200 chars

**Response 200:**
```json
{
  "success": true,
  "data": {
    "provider": "openai",
    "key_preview": "sk-proj-...xxxx",
    "saved_at": "2026-06-15T10:00:00Z"
  }
}
```
**Note:** Full key is NEVER returned. Only last 4 chars shown.

---

### DELETE /settings/api-key
Remove stored API key.

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:** `{"success": true, "data": {"deleted": true}}`

---

### POST /settings/branding
Update user's brand settings.

**Headers:** `Authorization: Bearer <jwt>`, `Content-Type: multipart/form-data` (Pro+)
**Request (form-data):**
```
logo: <image file> (optional, .png/.jpg/.svg, max 2MB)
brand_color: "#1F3864"
company_name: "Acme Corp"
```
> `company_name` stored in `users.company_name` column — used as default on report cover page
**Response 200:**
```json
{
  "success": true,
  "data": {
    "logo_url": "https://supabase.../logos/...",
    "brand_color": "#1F3864",
    "company_name": "Acme Corp"
  }
}
```

---

### GET /settings/profile
Get current user's full settings.

**Headers:** `Authorization: Bearer <jwt>`
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
    "logo_url": "https://...",
    "brand_color": "#6366F1",
    "reports_this_month": 2,
    "monthly_limit": null
  }
}
```

---

### PATCH /settings/profile
Update user's display name.

**Headers:** `Authorization: Bearer <jwt>`
**Request:**
```json
{
  "full_name": "Sarah Johnson"
}
```
**Validations:** full_name max 255 chars, stripped of whitespace
**Response 200:**
```json
{
  "success": true,
  "data": {
    "full_name": "Sarah Johnson",
    "updated_at": "2026-06-15T10:00:00Z"
  }
}
```

---

## 5. TEMPLATE ENDPOINTS

### GET /templates
List user's saved templates.

**Headers:** `Authorization: Bearer <jwt>` (Pro+)
**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Monthly Marketing Report",
      "template_type": "marketing",
      "is_default": true,
      "created_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

---

### POST /templates
Save a new template from report config.

**Headers:** `Authorization: Bearer <jwt>` (Pro+)
**Request:**
```json
{
  "name": "Monthly Marketing Report",
  "template_type": "marketing",
  "config": {}
}
```
**Response 201:** Created template object

---

### DELETE /templates/{template_id}
Delete a template.

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:** `{"success": true, "data": {"deleted": true}}`

---

### PATCH /templates/{template_id}
Rename or update a template.

**Headers:** `Authorization: Bearer <jwt>` (Pro+)
**Request:**
```json
{
  "name": "Q1 Marketing Report",
  "is_default": true
}
```
**Response 200:** Updated template object

---

## 6. WORKSPACE ENDPOINTS (Agency)

### GET /workspaces
List all workspaces owned by user.

**Headers:** `Authorization: Bearer <jwt>` (Agency only)
**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Client: Acme Corp",
      "client_name": "Acme Corp",
      "logo_url": "https://...",
      "brand_color": "#1F3864",
      "report_count": 12,
      "created_at": "2026-05-01T00:00:00Z"
    }
  ]
}
```

---

### GET /workspaces/{workspace_id}
Get single workspace detail.

**Headers:** `Authorization: Bearer <jwt>` (Agency only)
**Response 200:** Single workspace object with members list
**Response 403:** Not the workspace owner
**Response 404:** Not found

---

### POST /workspaces
Create a new client workspace.

**Headers:** `Authorization: Bearer <jwt>` (Agency only)
**Request:**
```json
{
  "name": "Client: Acme Corp",
  "client_name": "Acme Corp"
}
```
**Response 201:** Created workspace object

---

### PATCH /workspaces/{workspace_id}
Update workspace branding.

**Headers:** `Authorization: Bearer <jwt>`, `Content-Type: multipart/form-data` (Agency only)
**Request (form-data):**
```
name: "Client: Acme Corp Updated"
client_name: "Acme Corp"
logo: <image file> (optional)
brand_color: "#1F3864"
```
**Response 200:** Updated workspace object

---

### DELETE /workspaces/{workspace_id}
Delete workspace. Reports inside workspace lose workspace association (not deleted).

**Headers:** `Authorization: Bearer <jwt>` (Agency only)
**Response 200:** `{"success": true, "data": {"deleted": true}}`

---

## 7. PAYMENT ENDPOINTS

### GET /payments/plans
Public endpoint — returns current pricing plans.

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
        "features": ["Everything in Pro", "White-label", "5 team seats", "Client workspaces", "PPT export", "API access"]
      }
    ]
  }
}
```

---

### POST /payments/webhook
Dodo Payments webhook receiver. Processes subscription events.

**Headers:** `X-Dodo-Signature: <hmac>` (verified before processing)
**Events handled:**
- `subscription.created` → upgrade user tier
- `subscription.renewed` → extend tier_expires_at
- `subscription.cancelled` → schedule downgrade at period end
- `subscription.expired` → downgrade user to free
- `payment.failed` → send email, keep access for 3 days grace period

**Response:** Always 200 (Dodo retries on non-200)

---

### POST /payments/cancel
User cancels subscription (sets to cancel at period end, not immediate).

**Headers:** `Authorization: Bearer <jwt>`
**Response 200:**
```json
{
  "success": true,
  "data": {
    "cancelled": true,
    "access_until": "2026-07-15T00:00:00Z",
    "message": "Your Pro access continues until July 15, 2026"
  }
}
```

---

## 8. HEALTH ENDPOINT

### GET /health
Public. Used by Uptime Robot + Render health checks.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2026-06-15T10:00:00Z"
}
```

---

## 9. TIER ENFORCEMENT RULES

| Endpoint | Free | Pro | Agency |
|---|---|---|---|
| POST /reports/upload | ✅ (3/month limit) | ✅ | ✅ |
| POST /reports/generate (no AI) | ✅ | ✅ | ✅ |
| POST /reports/generate (with AI) | ❌ 402 | ✅ | ✅ |
| POST /reports/upload-sheets | ❌ 402 | ✅ | ✅ |
| POST /reports/{id}/share | ❌ 402 | ✅ | ✅ |
| POST /settings/api-key | ❌ 402 | ✅ | ✅ |
| POST /settings/branding | ❌ 402 | ✅ | ✅ |
| GET /templates | ❌ 402 | ✅ | ✅ |
| POST /templates | ❌ 402 | ✅ | ✅ |
| GET /workspaces | ❌ 402 | ❌ 402 | ✅ |
| POST /workspaces | ❌ 402 | ❌ 402 | ✅ |
| PPT export | ❌ 402 | ❌ 402 | ✅ |
| API access (/api/*) | ❌ 402 | ❌ 402 | ✅ |

---

## 10. RATE LIMITING

| Endpoint | Limit |
|---|---|
| POST /reports/generate | 5 requests/hour per user |
| POST /reports/upload | 20 requests/hour per user |
| POST /settings/api-key | 10 requests/hour per user |
| POST /auth/verify | 60 requests/minute per IP |
| POST /payments/webhook | No limit (Dodo IPs only) |
| All other endpoints | 100 requests/minute per user |

---

*End of ASD*


---
