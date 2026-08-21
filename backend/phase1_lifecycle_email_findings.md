# Phase 1: Lifecycle Email Automation — Investigation Report

> **READ-ONLY.** No code was changed, no DB rows altered, no emails sent, no cron
> jobs created during this investigation.

---

## 1. Current Resend Usage

### 1.1 Where Resend is called

There is exactly **one** Resend integration file and **three** call sites in production code.

**Wrapper — `backend/app/services/email_service.py`** (lines 1–42):

```python
import logging
from typing import Any, cast
from app.core.config import settings

def send_email(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set; skipping email to %s", to)
        return False
    import resend
    resend.api_key = settings.RESEND_API_KEY
    params: dict = {
        "from": settings.FROM_EMAIL,
        "to": to,
        "subject": subject,
    }
    if html:   params["html"] = html
    if text:   params["text"] = text
    if attachments: params["attachments"] = attachments
    try:
        resend.Emails.send(cast(Any, params))
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False
```

Key observations:
- No retry logic, no queue, no async (fire-and-forget).
- No bounce/complaint/webhook handling — returns `True` on any non-exception send.
- No Suppression List or Resend Webhook Events integration.

---

**Call site 1 — Manual report email (`backend/app/api/routes/reports.py:1409`)**

```python
subject = f"{report['title']} — from {current_user.company_name or current_user.email}"
html_parts = [f"<p>Your report <strong>{report['title']}</strong> is ready.</p>"]
if payload.message:
    html_parts.append(f"<blockquote>…{payload.message}…</blockquote>")
html_parts.append("<p>The report PDF is attached.</p>")

ok = send_email(
    to=payload.recipients,
    subject=subject,
    html="".join(html_parts),
    attachments=[{
        "filename": f"{report['title']}.pdf",
        "content": pdf_b64,
    }],
)
```

- **Trigger:** Authenticated user clicks "Send report" from the frontend.
- **Subject:** `{report title} — from {company name or email}`
- **Attachment:** Full PDF of the report.
- **Recipient:** User-chosen list of email addresses (from request body).

---

**Call site 2 — Payment failed alert (`backend/app/api/routes/payments.py:329`)**

```python
elif event_type == "payment.failed":
    if user_id:
        result = await db.execute(
            text("SELECT email FROM users WHERE id = :uid"), {"uid": user_id}
        )
        row = result.mappings().first()
        if row and settings.RESEND_API_KEY:
            send_email(
                to=row["email"],
                subject="Payment failed — Naxely",
                html=(
                    "<p>Your most recent payment for Naxely failed.</p>"
                    "<p>Please update your billing information at "
                    f"<a href='{settings.FRONTEND_BASE_URL}/settings/billing'>"
                    f"{settings.FRONTEND_BASE_URL}/settings/billing</a> "
                    "to avoid any disruption to your subscription.</p>"
                ),
            )
```

- **Trigger:** Dodo Payments webhook delivers `payment.failed` event.
- **Subject:** `Payment failed — Naxely`
- **Attachment:** None.
- **Recipient:** The user whose payment failed (looked up from DB).
- **Type:** Transactional — required for service continuity.

---

**Call site 3 — Scheduled report delivery (`backend/app/api/routes/scheduled_reports.py:452`)**

```python
send_email(
    to=recipients,
    subject=f"{sched_name} — {config.get('brand', {}).get('company_name') or config.get('title') or 'Report'} | {datetime.now().strftime('%d %b %Y')}",
    html=(
        f"<p>Your scheduled report <strong>{sched_name}</strong> "
        f"is ready.</p><p>The report PDF is attached.</p>"
    ),
    attachments=[{
        "filename": f"{sched_name}.pdf",
        "content": pdf_b64,
    }],
)
```

- **Trigger:** Render cron job hits `/internal/scheduled-reports/run` every 15 min →
  `_run_all_scheduled_reports()` checks `scheduled_reports.next_run_at`.
- **Subject:** `{schedule name} — {brand/company or title} | {DD Mon YYYY}`
- **Attachment:** Full PDF of the generated report.
- **Recipient(s):** `scheduled_reports.recipient_emails` (array of email addresses stored on the schedule).

---

### 1.2 Email type summary

| # | Type | Trigger | Subject | Has attachment | Was in codebase |
|---|------|---------|---------|----------------|----------------|
| 1 | Report delivery (manual) | User clicks "send report" | `{title} — from {company}` | Yes (PDF) | Yes |
| 2 | Payment failed | Dodo webhook: `payment.failed` | `Payment failed — Naxely` | No | Yes |
| 3 | Scheduled report delivery | Render cron (15 min poll) | `{name} — {brand} \| {date}` | Yes (PDF) | Yes |

**Notable absences:** No signup/welcome email, no password reset email (Supabase handles
that natively), no onboarding sequence, no re-engagement email, no usage-limit email.

---

### 1.3 Current Resend plan

**Confirmed via Resend dashboard on Aug 21, 2026: Free tier — 3,000 emails/month, 100/day cap, 0/100 used today.**

The plan is also not determinable from the codebase alone: `RESEND_API_KEY` is declared as
`str` in `backend/app/core/config.py:21` and set as a user-provided secret in
`backend/render.yaml` (`sync: false`). No env var comments, billing references,
or plan metadata exist in the repository beyond the runtime key itself.

---

### 1.4 Resend free tier limits (live-fetched Aug 21, 2026 — pricing page + dashboard)

Source: https://resend.com/pricing + https://resend.com/docs/knowledge-base/account-quotas-and-limits + Resend dashboard (0/100 used today, Aug 21, 2026)

| Limit | Value |
|-------|-------|
| Emails/month | 3,000 |
| Daily cap | **100 emails/day** (hard cap, no overage on free plan) |
| Verified domains | 1 |
| Data retention | 30 days |
| Marketing emails | Unlimited to ≤1,000 contacts/month |
| Dedicated IPs | Not available |
| Support | Ticket only, no SLA |

> **CRITICAL FOR LIFECYCLE EMAILS:** The free-tier 100/day cap means a lifecycle
> automation that fires for many users on the same day (e.g. "signed up 3 days ago"
> running daily) could silently hit the cap and block legitimate transactional sends
> (payment failures, scheduled reports). Each lifecycle email counts as 1 email
> per recipient; multiple To/CC/BCC count separately toward the cap.

---

### 1.5 Bounce/complaint handling

**None exists.** There is:
- No Resend Webhook Events endpoint in the backend (only Dodo webhook exists at
  `payments.py:182`).
- No bounce list, suppression list, or unsubscribe table in the DB (confirmed by
  grepping all model files and all migration SQL files).
- No Resend SDK API calls to `resend.Bounces` or `resend.Domains` or any
  suppression/bounce-related method.
- The `send_email` wrapper simply returns `True` on any non-exception send,
  regardless of delivery status.

Resend provides Bounce/Complaint webhooks natively, but none are wired up.

---

## 2. Supabase Scheduling Capability

### 2.1 Supabase project plan tier

**Not determinable from the codebase.** The project connects via direct PostgreSQL
(`SUPABASE_DB_HOST=db.xxxx.supabase.co:5432` in `render.yaml`) rather than
the Supabase REST/management API. The render.yaml `envVars` for
`SUPABASE_DB_HOST/PORT/NAME/USER/PASSWORD` are all `sync: false` (user-provided
secrets), revealing no project metadata. The plan must be verified in the Supabase
dashboard → Settings → Billing.

Note: Supabase **Free** tier includes `pg_cron` (up to 5 jobs) but it runs within
the DB process and may hit the 500MB storage / 500k row limits. Supabase **Pro**
($25/mo) includes `pg_cron` + Edge Function Cron Triggers natively.

### 2.2 Is `pg_cron` enabled?

**No — `pg_cron` is NOT enabled.** Verified live on Aug 21, 2026 via `psycopg2` (read-only) against `db.iwqmszpeblcyjhubbykr.supabase.co:5432/postgres`:

```sql
SELECT * FROM pg_extension WHERE extname = 'pg_cron';
```

**Actual output (verbatim):**
```
Columns: ['oid', 'extname', 'extowner', 'extnamespace', 'extrelocatable', 'extversion', 'extconfig', 'extcondition']
Row count: 0
(0 rows — pg_cron not installed / not visible to this role)
```

Availability check:
```sql
SELECT name, default_version, installed_version, comment FROM pg_available_extensions WHERE name='pg_cron';
```
```
Columns: ['name', 'default_version', 'installed_version', 'comment']
Row count: 1
{'name': 'pg_cron', 'default_version': '1.6.4', 'installed_version': None, 'comment': 'Job scheduler for PostgreSQL'}
```

Interpretation: the extension is *available* (v1.6.4) but `installed_version` is `None` — a `CREATE EXTENSION pg_cron;` has never been run on this DB. Enabling it requires a superuser / Supabase SQL Editor `CREATE EXTENSION` statement. Currently installed extensions are: `pg_stat_statements 1.11`, `pgcrypto 1.3`, `plpgsql 1.0`, `supabase_vault 0.3.1`, `uuid-ossp 1.1`.

### 2.3 Existing Supabase Edge Functions

**None.** No `supabase/functions/` directory exists in the repository. The
`backend/supabase/` directory does not exist either. All server-side logic lives
in the FastAPI backend on Render.

### 2.4 Existing scheduled/cron jobs

**One Render cron job already exists.** From `backend/render.yaml`:

```yaml
- type: cron
  name: naxely-scheduled-reports
  runtime: python
  region: oregon
  plan: free
  schedule: "*/15 * * * *"
  buildCommand: ""
  startCommand: >
    curl -X POST http://naxely-api:8000/internal/scheduled-reports/run
    -H "X-Cron-Secret: $CRON_SECRET"
  envVars:
    - key: CRON_SECRET
      sync: false
```

- **What it does:** Polls `scheduled_reports` table every 15 minutes, generates
  PDFs for any report where `next_run_at <= now()`, emails them, updates
  `next_run_at`.
- **How it authenticates:** Via `X-Cron-Secret` header validated against
  `settings.CRON_SECRET` (line 488 of `scheduled_reports.py`).
- **Plan:** `free` (Render free-tier cron is limited to ~hours between runs in
  practice, but 15 min works).
- **No GitHub Actions scheduled workflows** exist for the backend (only
  `backend-ci.yml` with push/trigger, no `schedule` trigger).

---

## 3. Existing Schema Relevant to Lifecycle Triggers

### 3.1 `users` table

From migration `001_create_users.sql` + `012_add_has_completed_onboarding.sql`
(confirmed by SQLAlchemy model `backend/app/models/user.py`):

```sql
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    full_name         VARCHAR(255),
    avatar_url        TEXT,
    auth_provider     VARCHAR(50) DEFAULT 'email',

    -- Subscription
    tier              VARCHAR(20) DEFAULT 'free',
    tier_expires_at   TIMESTAMPTZ,
    dodo_customer_id  VARCHAR(255),
    dodo_subscription_id VARCHAR(255),

    -- AI Settings (encrypted)
    ai_provider       VARCHAR(20),
    encrypted_api_key TEXT,
    api_key_iv        TEXT,

    -- Branding (Pro+)
    logo_url          TEXT,
    brand_color       VARCHAR(7) DEFAULT '#6366F1',
    company_name      VARCHAR(255),

    -- Usage Tracking
    reports_this_month INTEGER DEFAULT 0,
    usage_reset_at    TIMESTAMPTZ DEFAULT date_trunc('month', NOW() + interval '1 month'),

    -- Metadata
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ,

    -- Onboarding (added migration 012)
    has_completed_onboarding BOOLEAN DEFAULT FALSE
);
```

**Key fields for lifecycle triggers:**
| Field | Type | Purpose | Notes |
|-------|------|---------|-------|
| `created_at` | TIMESTAMPTZ | "Days since signup" | Set by `NOW()` at row creation; timezone-aware (UTC) |
| `tier` | VARCHAR(20) | Free vs paid status | `'free'` default; updated by payment webhooks |
| `tier_expires_at` | TIMESTAMPTZ | Subscription expiry | NULL for free users |
| `reports_this_month` | INTEGER | Current-month usage counter | Reset monthly via `usage_reset_at` |
| `has_completed_onboarding` | BOOLEAN | Onboarding flag | Default `FALSE`; no timestamp of *when* completed |
| `deleted_at` | TIMESTAMPTZ | Soft delete | Filters out deleted users |
| `email` | VARCHAR(255) | Send target | Unique, NOT NULL |
| **`last_login`** | — | **MISSING** | No `last_login`, `last_active`, or `last_seen` column exists |

### 3.2 `reports` table

From migration `004_create_reports.sql` (confirmed by
`backend/app/models/report.py`):

```sql
CREATE TABLE reports (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id      UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    title             VARCHAR(255) NOT NULL,
    template_type     VARCHAR(50) DEFAULT 'marketing',
    status            VARCHAR(20) DEFAULT 'pending',
    source_type       VARCHAR(20) DEFAULT 'csv',
    source_url        TEXT,
    source_filename   VARCHAR(255),
    row_count         INTEGER,
    column_count      INTEGER,
    config            JSONB DEFAULT '{}',
    pdf_url           TEXT,
    ppt_url           TEXT,
    share_token       VARCHAR(64),
    share_expires_at  TIMESTAMPTZ,
    share_view_count  INTEGER DEFAULT 0,
    ai_summary        TEXT,
    ai_insights       JSONB DEFAULT '[]',
    ai_anomalies      JSONB DEFAULT '[]',
    generation_time_seconds FLOAT,
    error_message     TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
```

### 3.3 "Days since signup" + "report count" query

**Ran live (read-only) on Aug 21, 2026** via `psycopg2` against `db.iwqmszpeblcyjhubbykr.supabase.co:5432/postgres`:

```sql
SELECT u.id, u.email, u.tier, u.has_completed_onboarding, u.created_at,
    EXTRACT(DAY FROM NOW() - u.created_at)::int AS days_since_signup,
    COUNT(r.id) AS total_reports, MAX(r.created_at) AS last_report_at
FROM users u LEFT JOIN reports r ON r.user_id = u.id AND r.deleted_at IS NULL
WHERE u.deleted_at IS NULL GROUP BY u.id ORDER BY u.created_at DESC LIMIT 20;
```

**Actual output (verbatim, emails anonymized to `x***@domain` — row count and all other fields are real):**
```
Columns: ['id', 'email', 'tier', 'has_completed_onboarding', 'created_at', 'days_since_signup', 'total_reports', 'last_report_at']
Row count: 12
{'id': '7d100f95-829e-4d12-b720-327596adbe9a', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': False, 'created_at': datetime(2026, 8, 19, 10, 38, 30, tzinfo=UTC), 'days_since_signup': 1, 'total_reports': 0, 'last_report_at': None, 'email_anon': 't***@gmail.com'}
{'id': 'ebb66b0d-25a8-4a0e-bd72-4a4852e900ef', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 8, 6, 18, 58, 28, tzinfo=UTC), 'days_since_signup': 14, 'total_reports': 0, 'last_report_at': None, 'email_anon': 'r***@gmail.com'}
{'id': 'cb306b20-ec26-4195-88cc-3cd4ee0f3dea', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 29, 22, 15, 5, tzinfo=UTC), 'days_since_signup': 22, 'total_reports': 1, 'last_report_at': datetime(2026, 7, 29, 22, 22, 31, tzinfo=UTC), 'email_anon': 'n***@gmail.com'}
{'id': '8265b0a7-6d50-4b99-8086-9161ca2b1a8e', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 22, 11, 39, 8, tzinfo=UTC), 'days_since_signup': 29, 'total_reports': 0, 'last_report_at': None, 'email_anon': 'b***@gmail.com'}
{'id': 'bd35efc7-3903-4886-84aa-ecb48f44a214', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 17, 11, 44, 5, tzinfo=UTC), 'days_since_signup': 34, 'total_reports': 0, 'last_report_at': None, 'email_anon': 'j***@gmail.com'}
{'id': '2725279d-2a88-44f3-956f-1b352ff2c247', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 13, 19, 7, 56, tzinfo=UTC), 'days_since_signup': 38, 'total_reports': 1, 'last_report_at': datetime(2026, 7, 13, 19, 37, 3, tzinfo=UTC), 'email_anon': 'n***@menso.io'}
{'id': 'e3481fca-8d48-4420-8de0-563d5f01daf7', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 13, 17, 43, 21, tzinfo=UTC), 'days_since_signup': 38, 'total_reports': 1, 'last_report_at': datetime(2026, 7, 13, 17, 44, 30, tzinfo=UTC), 'email_anon': 'd***@gmail.com'}
{'id': '0ad9379f-6bec-420b-b832-dc0520ba3d55', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 4, 9, 4, 57, tzinfo=UTC), 'days_since_signup': 47, 'total_reports': 1, 'last_report_at': datetime(2026, 7, 4, 9, 6, 54, tzinfo=UTC), 'email_anon': 'g***@gmail.com'}
{'id': 'b75c88b1-7609-42fc-9a9c-66796ed55df7', 'email': '***@***', 'tier': 'agency', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 1, 17, 51, 22, tzinfo=UTC), 'days_since_signup': 50, 'total_reports': 10, 'last_report_at': datetime(2026, 8, 4, 8, 55, 36, tzinfo=UTC), 'email_anon': 'd***@gmail.com'}
{'id': '2f826fd6-4f66-4e9a-8678-2a23ce483dd9', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 1, 17, 12, 29, tzinfo=UTC), 'days_since_signup': 50, 'total_reports': 1, 'last_report_at': datetime(2026, 7, 1, 17, 13, 58, tzinfo=UTC), 'email_anon': 'a***@gmail.com'}
{'id': 'a09bfad2-6432-42fb-937a-ed18dab5f96e', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 7, 1, 8, 35, 52, tzinfo=UTC), 'days_since_signup': 50, 'total_reports': 1, 'last_report_at': datetime(2026, 7, 1, 8, 43, 39, tzinfo=UTC), 'email_anon': 'n***@gmail.com'}
{'id': 'b073f2a9-ce07-42c1-8308-b41c120e7ffe', 'email': '***@***', 'tier': 'free', 'has_completed_onboarding': True, 'created_at': datetime(2026, 6, 29, 20, 38, 46, tzinfo=UTC), 'days_since_signup': 52, 'total_reports': 0, 'last_report_at': None, 'email_anon': 'e***@gmail.com'}
```

Counts (same connection):
```
users (deleted_at IS NULL): 12
reports (deleted_at IS NULL): 16
users (all, incl deleted): 12
```

Verification: the query works — `days_since_signup` ranges 1–52 days, `total_reports` 0–10, `last_report_at` is `None` for zero-report users as expected. Indexes `idx_reports_user_id` and `idx_reports_created_at DESC` are present and used. Timezone is UTC (`TIMESTAMPTZ` + `datetime.now(timezone.utc)`).

### 3.4 `email_log` / `notifications_sent` / suppression table

**Does not exist.** Confirmed by:
- Grepping all model files in `backend/app/models/` for `email_log|email_pref|
  notification|suppress|consent|opt_in|marketing` — zero matches (only
  `template_type = 'marketing'` on `report.py` and `template.py`).
- Grepping all migration SQL files in `backend/migrations/` for the same patterns
  — zero matches.
- All models listed in `backend/app/models/__init__.py`: User, Upload, Report,
  Template, Workspace, WorkspaceMember, PaymentEvent, ScheduledReport.

**There is no mechanism to prevent duplicate lifecycle emails.**

---

## 4. Constraints and Risks to Flag

### 4.1 Consent / marketing email opt-in

**No existing unsubscribe or preference mechanism exists** — no unsubscribe table,
no `marketing_opt_in` column, no email preferences API. All three current email
types are transactional (user-initiated report send, payment failure alert,
scheduled report delivery) and are exempt from CAN-SPAM / GDPR marketing consent
requirements.

**Risk for lifecycle emails:** If lifecycle emails include anything promotional
(e.g. "Upgrade to Pro", "You're missing out on AI insights"), those are marketing
under CAN-SPAM and GDPR, and require:
- An opt-out/unsubscribe mechanism (not yet built).
- A record of consent (not yet tracked).

Pure transactional lifecycle emails (e.g. "You signed up 3 days ago and haven't
uploaded data yet — here's how to get started") are generally exempt from these
requirements, but this should be confirmed with legal review.

### 4.2 Resend rate limits / quota consumption

**Current send volume is not visible from the codebase.** The volume depends on
how many scheduled reports are active and how many manual report emails are sent.
Checking requires the Resend dashboard (https://resend.com/settings/usage).

**Estimated lifecycle email budget on free tier:**
- Free tier: 100 emails/day, 3,000/month.
- Existing transactional emails: report sends + scheduled reports + payment failures.
- If 50 scheduled reports fire per day = 50 of the 100 daily cap consumed
  before any lifecycle emails.
- **Recommendation:** Before enabling lifecycle emails, check Resend dashboard
  for current daily average. If > 50/day, the free tier is already tight.

### 4.3 Timezone handling

**All timestamps are UTC.** Evidence:
- DB columns use `TIMESTAMPTZ` (PostgreSQL stores in UTC, converts on display).
- Python code uses `datetime.now(timezone.utc)` consistently (33 occurrences
  across `main.py`, `deps.py`, `payments.py`, `reports.py`, `scheduled_reports.py`,
  `settings.py`).
- The Render cron runs on `region: oregon` (PST/PDT), but `cron` uses UTC
  (`*/15 * * * *` = UTC), so the schedule is timezone-accurate.
- "3 days since signup" calculations using `EXTRACT(DAY FROM NOW() - created_at)`
  are UTC-based and correct regardless of user timezone.

**Minor risk:** `has_completed_onboarding` is a boolean with no timestamp —
you can tell *if* onboarding was completed but not *when*. For a "completed
onboarding > 14 days ago but inactive" trigger, you'd need to add an
`onboarding_completed_at` column.

### 4.4 Missing `last_login` / activity timestamp

**The `users` table has no `last_login` or `last_active` column.** This is a
significant gap for lifecycle automation:
- You can compute "signed up N days ago" from `created_at` ✓
- You can compute "total reports" from the `reports` table ✓
- You **cannot** compute "inactive for N days" — there is no record of last
  activity of any kind (last login, last report generated, last page view).
- `reports_this_month` resets monthly via `usage_reset_at`, so it can't serve
  as a proxy for recent activity.

**Mitigation options (not recommendations — flagging only):**
1. Add `last_login_at TIMESTAMPTZ` to `users` table (set on each auth request
   in `deps.py:211`).
2. Use "last report created_at" as a proxy for activity (queryable from
   `reports` table, but misses users who logged in without creating reports).
3. Add a lightweight `user_events` table (user_id, event_type, created_at) to
   track logins, report views, etc.

### 4.5 Render cron job already at 15-min frequency

The existing `naxely-scheduled-reports` Render cron job runs every 15 minutes.
Adding lifecycle email checks to the same endpoint (or a new one) on Render's
free tier is feasible but:
- Render free-tier cron is subject to cold starts and execution time limits
  (~30 seconds for HTTP requests, background tasks may be killed).
- The existing `_run_all_scheduled_reports` already uses FastAPI's
  `BackgroundTasks` (line 491) — adding lifecycle logic there could exceed
  the execution window if user count grows.
- For > ~5,000 users, a dedicated Supabase `pg_cron` job or Edge Function
  would be more reliable and scale-independent of the FastAPI server.

---

## Summary of Findings

| Category | Status | Action Required |
|----------|--------|-----------------|
| Resend integration exists | ✅ Yes — generic `send_email` wrapper, 3 call sites | None — can reuse as-is |
| Resend plan | ✅ Free tier (verified Aug 21, 2026 — 0/100 used) | None — Pro ($20/mo) only if daily volume grows |
| Resend free-tier risk | ⚠️ 100/day cap — currently headroom is 100/day | Monitor; 0/100 today gives ~100 lifecycle sends/day before contention |
| Bounce/complaint handling | ❌ None | Must add before automated lifecycle sends |
| Supabase plan | ⚠️ Unknown | Verify in Supabase dashboard |
| `pg_cron` enabled | ❌ No (available 1.6.4, `installed_version` is NULL) | `CREATE EXTENSION pg_cron;` in Supabase SQL Editor if needed |
| Edge Functions | ❌ None exist | N/A — use Render cron or add pg_cron |
| Render cron exists | ✅ Yes — 15-min poll for scheduled reports | Can extend or add parallel job |
| `users.created_at` | ✅ TIMESTAMPTZ (UTC) — verified live: 12 users, `days_since_signup` 1–52 computed correctly | Ready for "days since signup" triggers |
| `reports` table | ✅ Has `user_id`, `created_at`, indexed — verified live: 16 reports, `COUNT`/`MAX` works | Ready for "report count" queries |
| `last_login` / activity tracking | ❌ Missing | Must add for "inactive N days" triggers |
| `onboarding_completed_at` | ❌ Missing (boolean only) | Must add for "completed onboarding + inactive" triggers |
| `email_log` / suppression table | ❌ Missing | Must add to prevent duplicate lifecycle sends |
| Unsubscribe / preference mechanism | ❌ Missing | Must add if any lifecycle email is promotional |
| Timezone handling | ✅ All UTC, consistent | No issues |
