# SDD — System Design Document
## Databrief: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. COMPONENT MAP

```
┌─────────────────────── DATABRIEF SYSTEM ──────────────────────────┐
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    FRONTEND (Vercel)                          │  │
│  │  Pages: Landing | Auth | Dashboard | Wizard | Settings       │  │
│  │  State: Zustand (auth + report store)                        │  │
│  │  Charts: Recharts (interactive, browser only)                │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                           │ HTTPS / Axios                           │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │                   BACKEND (Render.com)                        │  │
│  │                                                               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐  │  │
│  │  │  Auth   │  │ Reports │  │Settings │  │  Payments     │  │  │
│  │  │ Router  │  │ Router  │  │ Router  │  │  Router       │  │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └───────┬───────┘  │  │
│  │       │             │             │               │           │  │
│  │  ┌────▼─────────────▼─────────────▼───────────────▼──────┐  │  │
│  │  │                  SERVICE LAYER                          │  │  │
│  │  │  data_service → chart_service → ai_service             │  │  │
│  │  │             ↓               ↓             ↓             │  │  │
│  │  │         pdf_service ← ── ── ── ── ──────┘              │  │  │
│  │  │  payment_service | email_service | sheets_service       │  │  │
│  │  └──────────────────────┬──────────────────────────────────┘  │  │
│  └─────────────────────────┼──────────────────────────────────────┘  │
│                             │                                         │
│  ┌──────────────────────────▼──────────────────────────────────────┐ │
│  │              EXTERNAL SERVICES                                   │ │
│  │  Supabase (DB + Auth + Storage) | OpenAI/Claude | Dodo          │ │
│  │  Resend (Email) | Sentry (Errors) | Google Sheets API           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. REPORT GENERATION — DETAILED FLOW

```
User clicks "Generate Report"
          │
          ▼
POST /reports/generate
          │
          ▼
┌─── VALIDATION ──────────────────────────┐
│ 1. JWT valid?                           │
│ 2. User within monthly limit?           │
│ 3. Upload ID exists + belongs to user?  │
│ 4. Pro features requested → check tier? │
└─────────────────┬───────────────────────┘
                  │
                  ▼
Create report row (status='pending') in DB
                  │
                  ▼
Return 202 + report_id to frontend (async)
                  │
                  ▼ (background task)
┌─── DATA SERVICE ────────────────────────┐
│ 1. Fetch CSV from Supabase Storage      │
│ 2. pd.read_csv() → DataFrame            │
│ 3. Apply column renames + exclusions    │
│ 4. Detect KPIs (numeric columns)        │
│ 5. Detect date column                   │
│ 6. Calculate descriptive stats          │
│ Update status='processing', step='data' │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─── CHART SERVICE ───────────────────────┐
│ ⚠️  FIRST LINE of chart_service.py:     │
│  import matplotlib                       │
│  matplotlib.use('Agg')  ← CRITICAL      │
│  Without this, matplotlib tries to open │
│  a GUI display → crashes on Render.com  │
│                                          │
│ For each KPI × date combination:        │
│   1. Select chart type (rule-based)     │
│   2. plt.figure() → plot → save PNG     │
│   3. Save to /tmp/{report_id}/chart_N.png│
│ Max 8 charts total                      │
│ Delete raw CSV from Supabase Storage    │
│ Update status='processing', step='charts'│
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─── AI SERVICE (Pro only) ───────────────┐
│ 1. Decrypt user's API key               │
│ 2. Build prompt with:                   │
│    - Column names + types               │
│    - Key stats (mean, min, max, trend)  │
│    - Anomaly candidates                 │
│    - Requested tone                     │
│ 3. Call OpenAI/Claude API               │
│ 4. Parse response → summary + insights  │
│ 5. Run anomaly detection (z-score > 2)  │
│ 6. Run trend detection (slope of values)│
│ 7. Discard decrypted key from memory    │
│ Update status='processing', step='ai'  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─── PDF SERVICE ─────────────────────────┐
│ ReportLab SimpleDocTemplate:            │
│ 1. Cover page (logo, title, date range) │
│ 2. Table of contents                    │
│ 3. Executive summary (AI text)          │
│ 4. KPI overview (big number callouts)   │
│ 5. Charts (embed PNG images)            │
│ 6. NRA insight cards                    │
│ 7. Anomaly flags (yellow boxes)         │
│ 8. Data table (TableStyle)              │
│ 9. Recommendations                      │
│ 10. Appendix (if enabled)               │
│ Build PDF → save to /tmp/{report_id}/   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
Upload PDF to Supabase Storage
reports/{user_id}/{report_id}/report.pdf
                  │
                  ▼
Delete /tmp/{report_id}/ entirely
                  │
                  ▼
Update report row:
- status='completed'
- pdf_url = STORAGE PATH (e.g. "reports/{user_id}/{report_id}/report.pdf")
- ai_summary, ai_insights, ai_anomalies
- generation_time_seconds

⚠️ NEVER store signed URLs in the DB — they expire in 1hr.
   Generate fresh signed URL on EVERY GET /reports or GET /reports/{id}:
   ```python
   signed_url = supabase.storage.from_("reports").create_signed_url(
       report.pdf_url,  # storage path from DB
       expires_in=3600  # 1 hour
   )
   ```
                  │
                  ▼
Frontend polls GET /reports/{id}/status
→ Receives 'completed' + download URL
→ Shows preview + download button
```

---

## 3. DATA FLOW — FRONTEND TO BACKEND

```
User Action              Frontend                    Backend
─────────────────────────────────────────────────────────────
1. Drop CSV file    → FileUpload component      → POST /reports/upload
                                                  ↓ File arrives as SpooledTempFile
                                                  ↓ Read into memory (io.BytesIO)
                                                  ↓ pd.read_csv(BytesIO(content))
                                                  ↓ Validate rows/cols/size
                                                  ↓ Upload to Supabase Storage:
                                                    supabase.storage.from_("uploads")
                                                    .upload(path, content, {"content-type":"text/csv"})
                                                  ↓ Create uploads row in DB
                    ← Upload ID + column preview ←
                    ← (file_url stored server-side only)

2. Map columns      → ColumnMapper form         → (local state only)

3. Configure report → ReportConfig form         → (local state only)

4. Generate         → POST to /reports/generate → Validate upload_id
                                                  ↓ Fetch upload row → get file_url
                                                  ↓ Download CSV from Storage into memory
                                                  ↓ Background task starts
                    ← 202 + report_id           ←

5. Poll status      → GET /reports/{id}/status  → Return progress %
   (every 3 sec)    ← {status, step, percent}   ←
                    → Repeat until 'completed'
                    ← On completed: generate fresh signed URL from storage_path

6. Download PDF     → Link to signed URL        → Supabase signed URL (generated fresh)
                    ← PDF file download         ←
```

### ⚠️ File Upload on Render.com Free Tier (No Persistent Disk)
```python
# app/api/routes/reports.py
@router.post("/reports/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Read entire file into memory — Render has no persistent disk
    content = await file.read()  # bytes in memory

    # Parse to DataFrame for validation (don't write to disk)
    import io
    df = pd.read_csv(io.BytesIO(content))

    # Upload to Supabase Storage (memory → network, never touches disk)
    upload_id = str(uuid.uuid4())
    storage_path = f"uploads/{current_user.id}/{upload_id}/raw.csv"
    supabase.storage.from_("uploads").upload(storage_path, content)

    # Store metadata in uploads table
    # ... create uploads row ...
    return {"upload_id": upload_id, "columns": [...], ...}
```

---

## 4. AI PROMPT DESIGN

### 4.1 Executive Summary Prompt
```
System: You are a professional business analyst writing executive summaries for client reports.
Write concisely and authoritatively. Never fabricate numbers — only reference data provided.

User: Write an executive summary for a {tone} marketing performance report.

Dataset statistics:
{column_stats_json}

Key findings:
- Best performing metric: {top_kpi}
- Worst performing metric: {bottom_kpi}
- Date range: {from} to {to}
- Total rows: {row_count}

Requirements:
- Exactly 150-250 words
- Third person ("Revenue increased..." not "Your revenue...")
- Mention: top performer, biggest concern, one recommended action
- Tone: {tone}
- Return ONLY the summary text, no headers or bullets
```

### column_stats_json Format (what to pass to AI)
```json
{
  "columns": [
    {
      "name": "Monthly Revenue",
      "type": "metric",
      "mean": 42500.0,
      "min": 31200.0,
      "max": 58900.0,
      "latest_value": 58900.0,
      "trend": "increasing",
      "trend_pct_change": 18.4,
      "null_count": 0,
      "row_count": 12
    },
    {
      "name": "Churn Rate",
      "type": "metric",
      "mean": 0.063,
      "min": 0.041,
      "max": 0.083,
      "latest_value": 0.083,
      "trend": "increasing",
      "trend_pct_change": 31.7,
      "null_count": 0,
      "row_count": 12
    }
  ],
  "date_column": "Date",
  "date_range": {"from": "2024-01-01", "to": "2024-12-31"}
}
```

### 4.2 NRA Insights Prompt
```
System: You are a data analyst generating actionable business insights.
Return ONLY valid JSON. No preamble, no explanation.

User: Generate NRA insights for these KPIs:
{kpi_stats_json}

Return a JSON array where each object has:
{
  "kpi": "metric name",
  "number": "one specific number-led observation",
  "reason": "one specific cause or explanation",
  "action": "one specific recommended action",
  "sentiment": "positive|negative|neutral",
  "priority": "high|medium|low"
}

Rules:
- Every "number" field MUST start with an actual number from the data
- Every "action" must be specific and executable
- Maximum 5 insights
- Return ONLY the JSON array
```

---

## 5. POLLING PATTERN (Frontend)

```typescript
// hooks/useReportStatus.ts
const pollReportStatus = async (reportId: string) => {
  const MAX_POLLS = 30;       // 30 × 3s = 90s max
  const POLL_INTERVAL = 3000; // 3 seconds

  for (let i = 0; i < MAX_POLLS; i++) {
    await sleep(POLL_INTERVAL);

    const { data } = await api.get(`/reports/${reportId}/status`);

    if (data.status === 'completed') {
      setReport(data);
      return;
    }

    if (data.status === 'failed') {
      setError(data.error_message);
      return;
    }

    setProgress(data.progress_percent);
    setCurrentStep(data.current_step);
  }

  // Timeout after 90 seconds
  setError('Report is taking longer than expected. Check back in a few minutes.');
};
```

---

## 6. BACKGROUND TASK PATTERN (Backend)

```python
# FastAPI background tasks (no Celery needed for MVP)
from fastapi import BackgroundTasks
from sqlalchemy import text  # REQUIRED for raw SQL in SQLAlchemy 2.0
import asyncio
import matplotlib
matplotlib.use('Agg')  # MUST be set before any other matplotlib import

@router.post("/reports/generate")
async def generate_report(
    config: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    report = await create_report_record(config, current_user.id)
    background_tasks.add_task(
        run_report_pipeline,
        report_id=report.id,
        user_id=current_user.id,
        config=config
    )
    return {"report_id": report.id, "status": "processing"}

async def run_report_pipeline(report_id, user_id, config):
    try:
        await update_status(report_id, 'processing', step='data')
        # Look up upload file_url from uploads table
        upload = await get_upload(config.upload_id)
        df = await data_service.process(upload.file_url, config)

        await update_status(report_id, 'processing', step='charts')
        # ⚠️ Matplotlib is NOT async — run in thread pool executor to avoid blocking
        loop = asyncio.get_event_loop()
        chart_paths = await loop.run_in_executor(
            None,  # Default thread pool
            chart_service.generate_sync,  # Sync function
            df, report_id
        )

        if config.ai_enabled:
            await update_status(report_id, 'processing', step='ai')
            ai_content = await ai_service.generate(df, config, user_id)

        await update_status(report_id, 'processing', step='pdf')
        # PDF generation also blocking — run in executor
        pdf_path = await loop.run_in_executor(
            None,
            pdf_service.build_sync,
            df, chart_paths, ai_content, config
        )

        storage_path = await upload_to_storage(pdf_path, user_id, report_id)
        cleanup_temp_files(report_id)

        # Mark upload as used + increment report counter
        await mark_upload_used(config.upload_id)
        await increment_report_count(user_id)

        await update_report_completed(report_id, storage_path, ai_content)

    except Exception as e:
        await update_report_failed(report_id, str(e))
        sentry_sdk.capture_exception(e)
```

---

## 7. FREEMIUM ENFORCEMENT

```python
# app/api/deps.py
from sqlalchemy import text  # REQUIRED for raw SQL in SQLAlchemy 2.0

async def check_report_limit(current_user: User = Depends(get_current_user)):
    """Dependency — inject into report generation endpoint"""
    if current_user.tier == 'free':
        if current_user.reports_this_month >= 3:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "MONTHLY_LIMIT_REACHED",
                    "message": "You've used all 3 free reports this month.",
                    "upgrade_url": "https://databrief.io/pricing"
                }
            )

async def check_pro_tier(current_user: User = Depends(get_current_user)):
    """Dependency — inject into Pro-only endpoints"""
    if current_user.tier not in ('pro', 'agency'):
        raise HTTPException(
            status_code=402,
            detail={
                "code": "PRO_REQUIRED",
                "message": "This feature requires a Pro subscription.",
                "upgrade_url": "https://databrief.io/pricing"
            }
        )

# Called after SUCCESSFUL report completion (not on start — failed reports don't count)
async def increment_report_count(user_id: str, db: AsyncSession):
    await db.execute(
        text("UPDATE users SET reports_this_month = reports_this_month + 1 WHERE id = :uid"),
        {"uid": user_id}
    )
    await db.commit()

# Monthly usage reset cron — runs daily at 00:01 UTC via APScheduler
async def reset_monthly_usage(db: AsyncSession):
    now = datetime.utcnow()
    await db.execute(
        text(
            "UPDATE users SET reports_this_month = 0, "
            "usage_reset_at = date_trunc('month', NOW() + interval '1 month') "
            "WHERE usage_reset_at <= :now"
        ),
        {"now": now}
    )
    await db.commit()

# Called after report generation completes — marks upload as consumed
async def mark_upload_used(upload_id: str, db: AsyncSession):
    await db.execute(
        text("UPDATE uploads SET used = TRUE WHERE id = :uid"),
        {"uid": upload_id}
    )
    await db.commit()
```

---

*End of SDD*


---
