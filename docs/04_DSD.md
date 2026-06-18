# DSD — Database Schema Document
## Naxely: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. DATABASE OVERVIEW
- Engine: PostgreSQL (via Supabase)
- ORM: SQLAlchemy 2.x
- Migrations: Alembic
- All tables use UUID primary keys
- All timestamps in UTC
- Soft deletes on users and reports (deleted_at column)

---

## 2. TABLES

### ⚠️ SUPABASE AUTH TRIGGER — MUST CREATE ON SETUP
When a user signs up via Supabase Auth (email or Google), Supabase creates
a record in `auth.users` (its internal table). Our custom `users` table needs
a matching row automatically. Without this trigger, every user gets a 403 on
their first API request because RLS finds no matching row.

```sql
-- Run in Supabase SQL editor BEFORE any users sign up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, avatar_url, auth_provider)
  VALUES (
    NEW.id,
    NEW.email,
    -- raw_user_meta_data contains OAuth profile data (name, picture from Google)
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
    COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture'),
    -- raw_app_meta_data contains provider info (NOT app_metadata — that column doesn't exist)
    CASE
      WHEN NEW.raw_app_meta_data->>'provider' = 'google' THEN 'google'
      ELSE 'email'
    END
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
```

---

### 2.0 uploads (CRITICAL — missing from original, required by ASD)
```sql
-- This table bridges POST /reports/upload → POST /reports/generate
-- ASD returns upload_id from /upload, backend uses it in /generate to find file
CREATE TABLE uploads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- File info
    filename        VARCHAR(255) NOT NULL,
    file_url        TEXT NOT NULL,      -- Supabase Storage path
    file_size_bytes INTEGER,
    source_type     VARCHAR(20) DEFAULT 'csv',  -- 'csv' | 'xlsx' | 'paste'

    -- Parsed metadata (returned to frontend for column mapper)
    row_count       INTEGER,
    column_count    INTEGER,
    columns_meta    JSONB DEFAULT '[]',
    -- columns_meta structure:
    -- [{"original_name":"col_1","suggested_name":"Date",
    --   "suggested_type":"date","sample_values":["2024-01-01"],
    --   "null_count":0,"unique_count":90}]

    -- Lifecycle
    expires_at      TIMESTAMPTZ DEFAULT NOW() + interval '24 hours',
    used            BOOLEAN DEFAULT FALSE,  -- True after report generated

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_expires_at ON uploads(expires_at) WHERE used = FALSE;

-- Cleanup job: delete expired unused uploads daily (also delete from Storage)
```

### 2.1 users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    avatar_url      TEXT,
    auth_provider   VARCHAR(50) DEFAULT 'email',  -- 'email' | 'google'
    
    -- Subscription
    tier            VARCHAR(20) DEFAULT 'free',   -- 'free' | 'pro' | 'agency'
    tier_expires_at TIMESTAMPTZ,
    dodo_customer_id VARCHAR(255),                -- Dodo Payments customer ID
    dodo_subscription_id VARCHAR(255),            -- Dodo Payments subscription ID
    
    -- AI Settings (encrypted)
    ai_provider     VARCHAR(20),                  -- 'openai' | 'claude'
    encrypted_api_key TEXT,                       -- AES-256-GCM encrypted
    api_key_iv      TEXT,                         -- Initialisation vector
    
    -- Branding (Pro+)
    logo_url        TEXT,                         -- Supabase Storage URL
    brand_color     VARCHAR(7) DEFAULT '#6366F1', -- Hex colour
    company_name    VARCHAR(255),                 -- Default company name for reports

    -- Usage Tracking
    reports_this_month INTEGER DEFAULT 0,
    usage_reset_at  TIMESTAMPTZ DEFAULT date_trunc('month', NOW() + interval '1 month'),

    -- Metadata
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                   -- Soft delete
);

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER reports_updated_at
  BEFORE UPDATE ON reports
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER templates_updated_at
  BEFORE UPDATE ON templates
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_dodo_customer ON users(dodo_customer_id);
```

### 2.2 reports
```sql
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    
    -- Report Identity
    title           VARCHAR(255) NOT NULL,
    template_type   VARCHAR(50) DEFAULT 'marketing',  -- 'marketing' | 'financial' | 'survey' | 'sales' | 'custom'
    status          VARCHAR(20) DEFAULT 'pending',    -- 'pending' | 'processing' | 'completed' | 'failed'
    
    -- Input Data
    source_type     VARCHAR(20) DEFAULT 'csv',        -- 'csv' | 'sheets' | 'paste'
    source_url      TEXT,                             -- Supabase Storage URL for CSV, or Google Sheets URL
    source_filename VARCHAR(255),
    row_count       INTEGER,
    column_count    INTEGER,
    
    -- Report Config (stored as JSON)
    config          JSONB DEFAULT '{}',
    /*
    config structure:
    {
      "date_range": {"from": "2024-01-01", "to": "2024-03-31"},
      "tone": "professional",
      "sections": ["executive_summary", "charts", "insights", "table"],
      "excluded_columns": ["id", "row_number"],
      "column_renames": {"col_1": "Revenue", "col_2": "Churn Rate"},
      "column_types": {"Revenue": "metric", "Date": "date", "Region": "dimension"},
      "brand": {"logo_url": "...", "color": "#1F3864"}
    }
    */
    
    -- Output
    -- IMPORTANT: store STORAGE PATH not signed URL (signed URLs expire in 1hr and go stale)
    -- Backend generates fresh signed URL on every GET /reports or GET /reports/{id} request
    pdf_url         TEXT,                             -- Storage PATH: reports/{user_id}/{report_id}/report.pdf
    ppt_url         TEXT,                             -- Storage PATH: reports/{user_id}/{report_id}/report.pptx
    share_token     VARCHAR(64),                      -- Random token for shareable link
    share_expires_at TIMESTAMPTZ,
    share_view_count INTEGER DEFAULT 0,
    
    -- AI Content (cached)
    ai_summary      TEXT,                             -- Generated executive summary
    ai_insights     JSONB DEFAULT '[]',               -- Array of NRA insight objects
    ai_anomalies    JSONB DEFAULT '[]',               -- Array of anomaly objects
    
    -- Performance
    generation_time_seconds FLOAT,
    error_message   TEXT,                             -- If status = 'failed'
    
    -- Metadata
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                       -- Soft delete
);

-- Indexes
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX idx_reports_share_token ON reports(share_token);
CREATE UNIQUE INDEX idx_reports_share_token_unique ON reports(share_token) WHERE share_token IS NOT NULL;
```

### 2.3 templates
```sql
CREATE TABLE templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    template_type   VARCHAR(50) DEFAULT 'marketing',
    config          JSONB NOT NULL DEFAULT '{}',      -- Same structure as reports.config
    is_default      BOOLEAN DEFAULT FALSE,            -- User's default template
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_templates_user_id ON templates(user_id);
```

### 2.4 workspaces (Agency tier)
```sql
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name            VARCHAR(255) NOT NULL,            -- e.g., "Client: Acme Corp"
    client_name     VARCHAR(255),
    logo_url        TEXT,
    brand_color     VARCHAR(7),
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workspaces_owner_id ON workspaces(owner_id);
```

### 2.5 workspace_members (Agency tier)
```sql
CREATE TABLE workspace_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) DEFAULT 'member',     -- 'owner' | 'admin' | 'member'
    invited_at      TIMESTAMPTZ DEFAULT NOW(),
    accepted_at     TIMESTAMPTZ,
    
    UNIQUE(workspace_id, user_id)
);
```

### 2.6 payment_events
```sql
CREATE TABLE payment_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    
    event_type      VARCHAR(100) NOT NULL,           -- 'subscription.created' | 'subscription.cancelled' etc.
    dodo_event_id   VARCHAR(255) UNIQUE,             -- Dodo Payments event ID (idempotency)
    payload         JSONB NOT NULL,                  -- Full webhook payload
    processed       BOOLEAN DEFAULT FALSE,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_events_user_id ON payment_events(user_id);
CREATE INDEX idx_payment_events_type ON payment_events(event_type);
CREATE UNIQUE INDEX idx_payment_events_dodo_id ON payment_events(dodo_event_id);
```

### 2.7 scheduled_reports (Agency tier)
```sql
CREATE TABLE scheduled_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id     UUID REFERENCES templates(id) ON DELETE SET NULL,
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    
    name            VARCHAR(255) NOT NULL,
    frequency       VARCHAR(20) NOT NULL,            -- 'weekly' | 'monthly'
    next_run_at     TIMESTAMPTZ NOT NULL,
    last_run_at     TIMESTAMPTZ,
    
    -- Data source for scheduled run
    sheets_url      TEXT,                            -- Must be Google Sheets (persistent connection)
    
    -- Email recipients
    recipient_emails TEXT[] NOT NULL,
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduled_reports_next_run ON scheduled_reports(next_run_at) WHERE is_active = TRUE;
```

---

## 3. JSONB SCHEMAS

### 3.1 reports.config
```json
{
  "title": "Q1 2024 Marketing Performance",
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-03-31"
  },
  "tone": "professional",
  "sections": [
    "executive_summary",
    "kpi_overview",
    "charts",
    "insights",
    "anomalies",
    "trends",
    "data_table",
    "recommendations",
    "appendix"
  ],
  "excluded_columns": ["id", "row_num"],
  "column_renames": {
    "col_revenue": "Monthly Revenue",
    "col_churn": "Churn Rate"
  },
  "column_types": {
    "Monthly Revenue": "metric",
    "Date": "date",
    "Region": "dimension",
    "Churn Rate": "metric"
  },
  "brand": {
    "logo_url": "https://xxxx.supabase.co/storage/v1/object/...",
    "color": "#1F3864",
    "company_name": "Acme Corp",
    "prepared_by": "Sarah Johnson"
  }
}
```

### 3.2 reports.ai_insights
```json
[
  {
    "kpi": "Churn Rate",
    "number": "Churn rate reached 8.3% in March — the highest in 6 months",
    "reason": "SMB accounts under $500 MRR drove 73% of all churns",
    "action": "Trigger re-engagement sequence for SMB accounts inactive for 14+ days",
    "sentiment": "negative",
    "priority": "high"
  }
]
```

### 3.3 reports.ai_anomalies
```json
[
  {
    "column": "Website Traffic",
    "date": "2024-03-15",
    "value": 45230,
    "mean": 12400,
    "std_dev": 2100,
    "z_score": 15.6,
    "message": "Website traffic on March 15 was 3.6x the monthly average"
  }
]
```

---

## 4. ROW LEVEL SECURITY (RLS) POLICIES

```sql
-- Enable RLS on ALL tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_reports ENABLE ROW LEVEL SECURITY;

-- users: can only access own row
CREATE POLICY users_own_data ON users
  FOR ALL USING (auth.uid() = id);

-- uploads: can only access own uploads
CREATE POLICY uploads_own_data ON uploads
  FOR ALL USING (auth.uid() = user_id);

-- reports: can only access own reports
CREATE POLICY reports_own_data ON reports
  FOR ALL USING (auth.uid() = user_id);

-- templates: can only access own templates
CREATE POLICY templates_own_data ON templates
  FOR ALL USING (auth.uid() = user_id);

-- workspaces: owner can access all, members can read
CREATE POLICY workspaces_owner ON workspaces
  FOR ALL USING (auth.uid() = owner_id);

-- workspace_members: members can see memberships they belong to
CREATE POLICY workspace_members_access ON workspace_members
  FOR SELECT USING (auth.uid() = user_id);

-- payment_events: users can only see own payment events
CREATE POLICY payment_events_own ON payment_events
  FOR SELECT USING (auth.uid() = user_id);

-- scheduled_reports: users can only access own schedules
CREATE POLICY scheduled_reports_own ON scheduled_reports
  FOR ALL USING (auth.uid() = user_id);

-- NOTE: Backend uses SUPABASE_SERVICE_KEY which BYPASSES RLS
-- RLS is a secondary defence layer for direct DB / Supabase client access
-- Never use anon key on backend — always service key
```

---

## 5. SUPABASE STORAGE BUCKETS

| Bucket | Purpose | Public? | Max File Size |
|---|---|---|---|
| `uploads` | Raw CSV files (temp) | No (private) | 10MB |
| `reports` | Generated PDFs + PPTs | No (private, signed URLs) | 15MB |
| `logos` | User/workspace logos | No (private) | 2MB |

### Storage Path Conventions
```
# IMPORTANT: uploads use upload_id (report doesn't exist yet at upload time)
uploads/{user_id}/{upload_id}/raw.csv      ← upload_id from uploads table
uploads/{user_id}/{upload_id}/raw.xlsx     ← Excel files

# Reports use report_id (created during generation)
reports/{user_id}/{report_id}/report.pdf
reports/{user_id}/{report_id}/report.pptx

# Logos use user/workspace id
logos/{user_id}/logo.{ext}
logos/workspaces/{workspace_id}/logo.{ext}
```

---

## 6. MIGRATIONS ORDER

```
000_create_auth_trigger.sql        ← FIRST — must exist before any user signs up
001_create_users.sql
002_create_uploads.sql             ← SECOND — needed before reports (foreign key)
003_create_workspaces.sql
004_create_reports.sql
005_create_templates.sql
006_create_workspace_members.sql
007_create_payment_events.sql
008_create_scheduled_reports.sql
009_add_rls_policies.sql
010_create_indexes.sql
```

---

*End of DSD*


---
