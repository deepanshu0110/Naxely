# Naxely — COMPLETE BUILD PROMPTS
> OpenCode Desktop App + NVIDIA NIM Provider | Version: FINAL (corrected) | June 2026
> 14 Prompts covering every section of the app from setup to deployment

---

## BEFORE YOU START — OpenCode Desktop Setup

### 1. Get Free NVIDIA API Key
- Go to **build.nvidia.com**
- Sign up free (no credit card)
- Click any model → "Get API Key"
- Copy your `nvapi-xxxxxxxxx` key
- You get 1,000 free credits (request 5,000 more from dashboard)

### 2. Connect in OpenCode Desktop
Type in OpenCode chat:
```
/connect
```
Search for **NVIDIA** → paste your `nvapi-` key → Enter

### 3. Add This Config File
File location:
- Windows: `C:\Users\YourName\.config\opencode\opencode.jsonc`
- Mac/Linux: `~/.config/opencode/opencode.jsonc`

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "nvidia/z-ai/glm-4.7",
  "provider": {
    "nvidia": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "NVIDIA NIM",
      "api": "https://integrate.api.nvidia.com/v1",
      "options": {
        "baseURL": "https://integrate.api.nvidia.com/v1",
        "apiKey": "nvapi-YOUR_KEY_HERE",
        "timeout": 600000,
        "chunkTimeout": 60000
      },
      "models": {
        "z-ai/glm-4.7": {
          "name": "GLM 4.7",
          "tool_call": true,
          "temperature": true,
          "limit": { "context": 131072, "output": 16384 }
        },
        "nvidia/nemotron-3-super-120b-a12b": {
          "name": "Nemotron 3 Super 120B",
          "tool_call": true,
          "temperature": true,
          "limit": { "context": 1000000, "output": 32768 }
        },
        "deepseek-ai/deepseek-v3.2": {
          "name": "DeepSeek V3.2",
          "tool_call": true,
          "temperature": true,
          "limit": { "context": 131072, "output": 16384 }
        },
        "moonshotai/kimi-k2.6": {
          "name": "Kimi K2.6",
          "reasoning": true,
          "tool_call": true,
          "temperature": true,
          "limit": { "context": 262144, "output": 65536 }
        }
      }
    }
  }
}
```

### 4. Place the Spec Documents in Your Project
Create a `docs/` folder in your project root and put all 8 files there:
`01_PRD.md`, `02_TRD.md`, `03_SDD.md`, `04_DSD.md`, `05_ASD.md`, `06_FSD.md`, `07_SEC.md`, `08_DEP.md`

Every prompt below now says **`READ: docs/0X_XXX.md — Section Y`** instead of
a paste placeholder. This means OpenCode reads the file itself with its own
file-read tool — you never need to copy-paste document content into a prompt
again. Just make sure the `docs/` folder exists with these 8 files before
running Prompt 1, and add this rule to your `AGENTS.md`:

```markdown
## Spec Documents
All product/technical specs live in docs/01_PRD.md through docs/08_DEP.md.
When a prompt says "READ: docs/X.md — Section Y", open that file yourself
with your file-read tool and find that section before writing any code.
Never ask the user to paste document content — it's already on disk.
```

### 5. Switch Models Per Task
Type `/models` in OpenCode chat → select from list

### ⚠️ AVOID These Models on NVIDIA NIM (Known Bug — Hang Forever)
- `deepseek-ai/deepseek-v4-flash` ← hangs, never responds
- `deepseek-ai/deepseek-v4-pro` ← same bug
Use `deepseek-v3.2` instead — works perfectly.

---

## MODEL SELECTION GUIDE

> ⚠️ Qwen3 Coder 480B hit end-of-life on NVIDIA NIM (June 11, 2026) and Devstral 2 123B is not available through OpenCode — both removed below. Everything they covered now runs on GLM-4.7 or DeepSeek V3.2.

| Task | Use This Model | Why |
|---|---|---|
| Prompts 1, 2, 4, 5, 7, 9, 14 | DeepSeek V3.2 | Fast generation, 685B reasoning, confirmed free endpoint |
| Prompts 3, 6, 8, 10, 11, 12, 13 | GLM 4.7 | Agentic coding, tool use, strong UI generation |
| Reading all 8 docs at once | Nemotron 3 Super (1M context) | ⚠️ Verify it appears in `/models` first — NVIDIA's catalog currently lists it as "Downloadable" rather than "Free Endpoint," which may mean self-hosting only. If it's not selectable, have it read only the relevant doc file instead of all 8 at once.

---

## GOLDEN RULES FOR ALL PROMPTS

1. **Never paste document content yourself** — every prompt lists `READ: docs/X.md — Section Y`; the agent opens that file with its own file-read tool. Your job is just to make sure `docs/` has all 8 files before Prompt 1.
2. **End every prompt with:** *"Follow the documents exactly. Do not add features not specified. Do not use different library versions than stated."*
3. **One prompt = one feature** — do not combine multiple prompts
4. **If rate limited (429 error):** wait 60 seconds or switch to another model
5. **After each prompt completes:** test it works before moving to the next

---

## PROMPT 1 — Project Setup & Folder Structure
**Model:** DeepSeek V3.2 | **Estimated time:** 5 minutes

```
You are building a SaaS app called Naxely — an AI-powered PDF report generator.

Read the TRD using your file-read tool before writing anything. *(Don't wait for pasted content — open the file listed below directly.)*

READ: `docs/02_TRD.md` — Sections 3, 4, 5 only

Your task is to create the complete monorepo folder structure. Do NOT write any application logic yet.

CREATE THESE FILES AND FOLDERS EXACTLY:

1. Root level:
   - /frontend/ folder
   - /backend/ folder
   - .gitignore (with all entries from DEP Section 2 — Python, Node, env files, temp files)
   - README.md (simple: project name, stack, setup instructions)

2. /frontend/:
   - package.json (use EXACT versions from TRD Section 5.2 — all dependencies and devDependencies)
   - vite.config.ts (exact content from DEP Section 17)
   - tailwind.config.ts (exact content from DEP Section 18)
   - tsconfig.json (standard React + Vite TypeScript config)
   - postcss.config.js (autoprefixer only)
   - index.html (exact content from DEP Section 15 — includes Inter font Google Fonts link and meta tags)
   - .env.example (exact content from DEP Section 14 frontend section)
   - src/ with ALL subfolders: components/, pages/, hooks/, store/, lib/, types/, assets/
   - src/components/ with subfolders: ui/, layout/, landing/, auth/, dashboard/, report/, settings/

3. /backend/:
   - requirements.txt (EXACT versions from TRD Section 5.1 — every package listed)
   - .env.example (exact content from DEP Section 14 backend section)
   - Dockerfile (exact content from DEP Section 12)
   - render.yaml (exact content from DEP Section 4.1)
   - alembic.ini (exact content from DEP Section 13)
   - app/ with subfolders: api/routes/, core/, services/, models/, schemas/, utils/
   - migrations/ with versions/ subfolder
   - tests/ folder
   - app/__init__.py, app/main.py (stub only — just the imports and app = FastAPI())

4. GitHub Actions:
   - .github/workflows/backend-ci.yml (exact content from DEP Section 3.1)
   - .github/workflows/frontend-ci.yml (exact content from DEP Section 3.2)

Do not write any logic. Stubs and empty files only. Structure only.

Follow the documents exactly. Do not add files not specified. Do not change folder names.
```

---

## PROMPT 2 — Database Schema & Migrations
**Model:** DeepSeek V3.2 | **Estimated time:** 20 minutes

```
You are building Naxely. Read the complete database schema document yourself using your file-read tool. *(Don't wait for pasted content — open the file listed below directly.)*

READ: `docs/04_DSD.md` (full file)

Your task is to write all database-related files:

1. Run the auth trigger SQL FIRST (DSD Section 2 — top of tables section):
   - File: migrations/000_create_auth_trigger.sql
   - This is raw SQL for Supabase SQL editor, not an Alembic file
   - Use EXACT SQL from DSD including COALESCE for Google name/picture
   - Use raw_app_meta_data NOT app_metadata (critical — wrong field causes Google signup to fail)

2. SQLAlchemy models (one file per table):
   - app/models/base.py — Base = declarative_base(), shared updated_at mixin
   - app/models/user.py — User model matching DSD 2.1 exactly including company_name column
   - app/models/upload.py — Upload model matching DSD 2.0 exactly
   - app/models/report.py — Report model matching DSD 2.2 exactly (pdf_url stores PATH not signed URL)
   - app/models/template.py — Template model matching DSD 2.3
   - app/models/workspace.py — Workspace model matching DSD 2.4
   - app/models/workspace_member.py — WorkspaceMember model matching DSD 2.5
   - app/models/payment_event.py — PaymentEvent model matching DSD 2.6
   - app/models/scheduled_report.py — ScheduledReport model matching DSD 2.7

3. app/core/database.py:
   - Async SQLAlchemy engine using asyncpg: postgresql+asyncpg://
   - AsyncSession factory
   - get_db() async dependency for FastAPI

4. Alembic migration files (001 through 010):
   - migrations/001_create_users.sql through 010_create_indexes.sql
   - Each as proper Alembic migration using SQLAlchemy 2.0 op.* syntax
   - Include updated_at triggers from DSD (update_updated_at_column function)
   - Migration order EXACTLY as DSD Section 6

5. migrations/env.py — EXACT content from DEP Section 19:
   - Uses SYNC psycopg2 driver (postgresql+psycopg2://) for Alembic migrations
   - Imports all models so Alembic detects schema
   - NOT asyncpg (Alembic is sync only)

6. RLS policies file:
   - migrations/009_add_rls_policies.sql
   - Include RLS for ALL 8 tables as specified in DSD Section 4

Use SQLAlchemy 2.0 syntax throughout. Use UUID primary keys everywhere. All timestamps UTC.

Follow the documents exactly. Do not add columns not specified. Do not change table names.
```

---

## PROMPT 3 — FastAPI Core, Security & Config
**Model:** GLM 4.7 | **Estimated time:** 20 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/02_TRD.md` — Sections 2, 3, 6, 7, 10
READ: `docs/07_SEC.md` (full file)

Your task is to build the FastAPI backend core:

1. app/core/config.py:
   - Pydantic Settings class (pydantic-settings)
   - Load ALL environment variables listed in TRD Section 3.1
   - Include: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_JWT_SECRET, MASTER_ENCRYPTION_KEY,
     DODO_API_KEY, DODO_WEBHOOK_SECRET, DODO_PRO_PRODUCT_ID, DODO_AGENCY_PRODUCT_ID,
     RESEND_API_KEY, FROM_EMAIL, ENVIRONMENT, ALLOWED_ORIGINS, SECRET_KEY, TEMP_DIR,
     GOOGLE_SERVICE_ACCOUNT_JSON, SENTRY_DSN, SUPABASE_DB_HOST, SUPABASE_DB_PORT,
     SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD
   - settings = Settings() singleton at bottom of file

2. app/core/security.py — JWT verification:
   - Use python-jose library
   - Algorithm: HS256 (NOT RS256 — Supabase uses HS256 with shared secret)
   - Function: verify_supabase_jwt(token: str) -> dict
   - Decode with: jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
   - Raise HTTPException 401 on any JWTError

3. app/utils/encryption.py — AES-256-GCM encryption:
   - Exact implementation from SEC Section 2.2
   - get_master_key() → bytes: use bytes.fromhex(settings.MASTER_ENCRYPTION_KEY)
     Validate length is exactly 64 hex chars (32 bytes) or raise ValueError
   - encrypt_api_key(plaintext, master_key) → tuple[str, str]: returns (encrypted_b64, iv_b64)
   - decrypt_api_key(encrypted_b64, iv_b64, master_key) → str: returns plaintext
   - NEVER log the key anywhere

4. app/core/exceptions.py:
   - Custom exception handlers for FastAPI
   - All errors return format from TRD Section 7.2:
     {"error": true, "code": "ERROR_CODE", "message": "...", "detail": null}
   - Handle: HTTPException, RequestValidationError, Exception (catch-all → 500)

5. app/api/deps.py — FastAPI dependencies:
   - get_current_user(token from Authorization header) → User:
     Call verify_supabase_jwt() → get user from DB by id → return User model
     Raise 401 if token missing or invalid
   - check_report_limit(current_user) → None:
     Exact implementation from SDD Section 7
     Raise 402 if free user has used 3+ reports this month
   - check_pro_tier(current_user) → None:
     Raise 402 if user.tier not in ('pro', 'agency')
   - check_agency_tier(current_user) → None:
     Raise 402 if user.tier != 'agency'
   - increment_report_count(user_id, db) — from SDD Section 7, uses text() wrapper
   - mark_upload_used(upload_id, db) — from SDD Section 7, uses text() wrapper
   - reset_monthly_usage(db) — from SDD Section 7, uses text() wrapper

6. app/main.py:
   - FastAPI app with title="Naxely API", version="1.0.0"
   - CORS middleware: allowed_origins from settings.ALLOWED_ORIGINS (split by comma)
   - Security headers middleware (X-Content-Type-Options, X-Frame-Options etc from SEC 4.3)
   - slowapi rate limiter (Limiter from slowapi)
   - Sentry init from settings.SENTRY_DSN (only if ENVIRONMENT == "production")
   - Register all exception handlers from exceptions.py
   - Include routers: /auth, /reports, /settings, /payments, /health
   - GET /health endpoint returning {"status": "ok", "version": "1.0.0", "environment": ..., "timestamp": ...}

Use from sqlalchemy import text everywhere you write raw SQL. Never use raw strings in db.execute().

Follow the documents exactly. Do not add middleware or endpoints not specified.
```

---

## PROMPT 4 — File Upload & CSV Processing
**Model:** DeepSeek V3.2 | **Estimated time:** 25 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/05_ASD.md` — Section 3, POST /reports/upload and POST /reports/upload-sheets
READ: `docs/04_DSD.md` — Section 2.0 uploads table only
READ: `docs/07_SEC.md` — Sections 6.1 and 6.2
READ: `docs/03_SDD.md` — Section 3, CSV upload memory stream pattern

Your task is to build the file upload system:

1. app/services/data_service.py:

   parse_csv(content: bytes) → pd.DataFrame:
   - Use io.BytesIO(content) — NEVER write to disk (Render.com has no persistent disk)
   - Handle both .csv (pd.read_csv) and .xlsx (pd.read_excel with openpyxl)
   - Raise ValueError if file cannot be parsed

   validate_csv(df: pd.DataFrame) → None:
   - Max 50,000 rows → raise ValueError("Too many rows. Maximum is 50,000.")
   - Min 2 columns → raise ValueError("File must have at least 2 columns.")

   validate_for_injection(df: pd.DataFrame) → None:
   - Scan all string cells for values starting with =, +, -, @
   - Raise ValueError("File contains potentially dangerous formula content.")

   detect_column_types(df: pd.DataFrame) → list[dict]:
   - For each column return:
     {"original_name": str, "suggested_name": str, "suggested_type": "date"|"metric"|"dimension",
      "sample_values": list (first 3 non-null values as strings),
      "null_count": int, "unique_count": int}
   - Type detection rules:
     date: column name contains 'date'/'time'/'month'/'year' OR values parse as datetime
     metric: column is numeric (int or float)
     dimension: everything else (categorical strings)
   - suggested_name: capitalize and clean the column name (replace _ with space, title case)

   apply_column_config(df: pd.DataFrame, column_config: list[dict]) → pd.DataFrame:
   - Rename columns using display_name from config
   - Drop columns where include=False
   - Return clean DataFrame

   compute_column_stats(df: pd.DataFrame) → dict:
   - Build exact column_stats_json format from SDD Section 4.1
   - For each metric column: mean, min, max, latest_value, trend (increasing/decreasing/flat), trend_pct_change
   - Include date_column name and date_range

2. app/api/routes/reports.py — POST /reports/upload:
   - Accept: UploadFile = File(...)
   - Read entire file: content = await file.read() — bytes in memory, never disk
   - Validate MIME type (text/csv or xlsx MIME) from SEC 6.1
   - Validate file size < 10MB
   - Call data_service.parse_csv(content)
   - Call data_service.validate_csv(df)
   - Call data_service.validate_for_injection(df)
   - Call data_service.detect_column_types(df)
   - Upload to Supabase Storage:
     upload_id = str(uuid.uuid4())
     storage_path = f"uploads/{current_user.id}/{upload_id}/raw.csv"
     supabase_client.storage.from_("uploads").upload(storage_path, content)
   - Insert row into uploads table (file_url=storage_path, columns_meta as JSON, etc.)
   - Return EXACT response schema from ASD POST /reports/upload

3. app/api/routes/reports.py — POST /reports/upload-sheets (Pro only):
   - Accept JSON: {"sheets_url": str, "sheet_name": str}
   - Validate URL starts with https://docs.google.com/spreadsheets/
   - Use gspread to open sheet and get all records as DataFrame
   - Run same validation/detection as CSV upload
   - Store as CSV in uploads bucket
   - Return same response schema as CSV upload

Return EXACT error codes from ASD: 400 for invalid file, 402 for free tier limit.
Follow the documents exactly. Do not add validation not specified.
```

---

## PROMPT 5 — Chart Generation Service
**Model:** DeepSeek V3.2 | **Estimated time:** 15 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/01_PRD.md` — Section 7.2 chart type selection rules only
READ: `docs/02_TRD.md` — Section 6.4 PDF generation constraints only
READ: `docs/03_SDD.md` — Section 2, chart service step in pipeline

Your task is to build app/services/chart_service.py:

CRITICAL FIRST LINES (mandatory — without these the server crashes):
import matplotlib
matplotlib.use('Agg')  # Must be BEFORE any other matplotlib import
# Do NOT import matplotlib.pyplot or seaborn here — import them INSIDE each
# function, after this line has already run. See the rule at the bottom of
# this prompt: pyplot must never be imported at module level in this file.

Chart colors to use (from FSD design system):
CHART_COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6', '#EC4899', '#14B8A6']

Functions to implement:

select_chart_type(df: pd.DataFrame, column_name: str, date_column: str = None) → str:
Apply EXACT rules from PRD Section 7.2:
- Has date_column AND numeric column → "line"
- Categorical column AND numeric column → "bar"
- Single numeric column → "histogram"
- Values sum to ~100 (percentages) → "pie"
- Two numeric columns (no date) → "scatter"
- Multiple numeric columns with date → "multi_line"

generate_chart(df: pd.DataFrame, column_name: str, chart_type: str,
               report_id: str, chart_index: int, brand_color: str = '#6366F1') → str:
- Create /tmp/Naxely/{report_id}/ directory if not exists
- Save chart to /tmp/Naxely/{report_id}/chart_{chart_index}.png
- Resolution: 150 DPI (TRD Section 6.4)
- Figure size: (10, 5) inches
- Use tight_layout()
- No chart title (titles go in PDF section headers)
- Clear axis labels using display column name
- Use brand_color for primary series
- Return full file path

generate_sync(df: pd.DataFrame, report_id: str, config: dict,
              brand_color: str = '#6366F1') → list[str]:
THIS MUST BE A SYNC FUNCTION (called via run_in_executor — do NOT make it async)
- Identify date column from config
- For each metric column (max 8 total):
  - Call select_chart_type()
  - Call generate_chart()
  - Append path to list
- Return list of chart file paths

cleanup_charts(report_id: str) → None:
- Delete entire /tmp/Naxely/{report_id}/ directory
- Use shutil.rmtree() with ignore_errors=True

Do NOT make generate_sync async. It runs in a thread pool executor.
Do NOT import matplotlib.pyplot at module level — only inside functions after matplotlib.use('Agg').
Follow the documents exactly.
```

---

## PROMPT 6 — AI Service (Summary, NRA Insights, Anomaly Detection)
**Model:** GLM 4.7 | **Estimated time:** 25 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/03_SDD.md` — Section 4 (AI prompts + column_stats format)
READ: `docs/01_PRD.md` — Section 8 (content rules)
READ: `docs/02_TRD.md` — Section 6.3 (AI error handling)
READ: `docs/07_SEC.md` — Section 2 (API key encryption)

Your task is to build app/services/ai_service.py:

1. get_user_api_key(user: User) → tuple[str, str]:
   - Decrypt using decrypt_api_key() from encryption.py
   - master_key = get_master_key() — calls bytes.fromhex(MASTER_ENCRYPTION_KEY)
   - Return (provider, plaintext_key)
   - Raise HTTPException 402 if user has no API key stored

2. call_openai(prompt: str, system: str, api_key: str, timeout: int = 25) → str:
   - Use openai.OpenAI(api_key=api_key)
   - Model: "gpt-4o-mini" (cheapest, fast)
   - Wrap in try/except:
     AuthenticationError → raise HTTPException 400 "Invalid API key — please update in Settings"
     RateLimitError → raise HTTPException 429 "AI rate limit — try again in 60 seconds"
     APITimeoutError → raise HTTPException 504 "AI timed out — report saved without AI insights"
     Any other error → raise HTTPException 500
   - NEVER log api_key in any error message
   - After call: del api_key (discard from memory)

3. call_claude(prompt: str, system: str, api_key: str, timeout: int = 25) → str:
   - Use anthropic.Anthropic(api_key=api_key)
   - Model: "claude-haiku-4-5-20251001" (cheapest Claude)
   - Same error handling as call_openai but for Anthropic exceptions
   - NEVER log api_key

4. generate_summary(df: pd.DataFrame, config: dict, user: User) → str:
   - Build column_stats_json from df using EXACT format from SDD Section 4.1
   - Build executive summary prompt EXACTLY as written in SDD Section 4.1
   - Call appropriate AI function based on user.ai_provider
   - Return summary text (150-250 words per PRD Section 8.1)
   - On any AI failure: return None (report continues without summary)

5. generate_nra_insights(df: pd.DataFrame, config: dict, user: User) → list[dict]:
   - Build NRA insights prompt EXACTLY as written in SDD Section 4.2
   - Call AI and parse JSON response:
     raw = call_openai/call_claude(...)
     cleaned = raw.strip().lstrip('```json').rstrip('```').strip()
     insights = json.loads(cleaned)
   - Validate each insight has: kpi, number, reason, action, sentiment, priority
   - Return empty list on ANY parse failure (never crash report generation)
   - Max 5 insights

6. detect_anomalies(df: pd.DataFrame) → list[dict]:
   - Pure Pandas — NO AI call
   - For each numeric column:
     mean = col.mean(), std = col.std()
     z_scores = (col - mean) / std
     anomalies = rows where abs(z_score) > 2
   - Return list in exact format from DSD Section 3.3
   - Max 5 anomalies total

7. detect_trends(df: pd.DataFrame, date_col: str = None) → list[dict]:
   - Pure Pandas — NO AI call
   - For each numeric column: calculate slope using numpy.polyfit
   - trend = "increasing" if slope > 0.01, "decreasing" if slope < -0.01, else "flat"
   - pct_change = ((last_value - first_value) / first_value) * 100
   - Return list with column, trend, pct_change

Follow the documents exactly. Never expose API keys in logs or error messages.
```

---

## PROMPT 7 — PDF Generation Service
**Model:** DeepSeek V3.2 | **Estimated time:** 30 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/01_PRD.md` — Sections 7.1 and 8
READ: `docs/02_TRD.md` — Section 6.4
READ: `docs/03_SDD.md` — Section 2, PDF service step

Your task is to build app/services/pdf_service.py using ReportLab:

THIS ENTIRE FILE MUST USE SYNC FUNCTIONS ONLY.
It is called via asyncio.run_in_executor — do NOT use async/await anywhere.

build_sync(df: pd.DataFrame, chart_paths: list[str], ai_content: dict,
           config: dict, user_data: dict) → str:
Returns path to generated PDF file.

The PDF must contain ALL sections in EXACT ORDER from PRD Section 7.1:

SECTION 1 — Cover Page:
- Logo: if user_data['logo_url'], download and embed (max 120px height using Pillow to resize)
- Report title (large, bold, brand_color)
- Date range: "From {from} to {to}"
- Company name: user_data.get('company_name', '')
- Prepared by: config.get('brand', {}).get('prepared_by', '')
- Prepared date: today's date
- Naxely watermark if user_data['tier'] == 'free':
  Diagonal "Generated by Naxely" text across every page using canvas.saveState/restoreState

SECTION 2 — Table of Contents:
- Auto-generated with page numbers
- List all sections included in config['sections']

SECTION 3 — Executive Summary (only if 'executive_summary' in config['sections'] AND ai_content['summary'] is not None):
- Section header in brand_color
- AI summary text in normal body font

SECTION 4 — Key Metrics Overview:
- Top 5 numeric KPIs as large-number callouts
- Each: metric name, big number, trend arrow (↑ green / ↓ red / → grey)

SECTION 5 — Charts:
- Embed each PNG from chart_paths as ReportLab Image
- Centre each chart on the page
- Caption below each chart: column name

SECTION 6 — AI Insight Cards (only if 'insights' in config['sections'] AND ai_content['insights'] not empty):
- For each NRA insight:
  - Coloured left border (green=positive, red=negative, grey=neutral)
  - KPI name header (bold)
  - "📊 " + insight['number'] (bold)
  - "▶ " + insight['reason'] (normal)
  - "✓ " + insight['action'] (italic)

SECTION 7 — Anomaly Flags (only if ai_content['anomalies'] not empty):
- Yellow background boxes for each anomaly
- "⚠️ " + anomaly['message']

SECTION 8 — Data Table:
- ReportLab Table with TableStyle
- Alternating row colours: white / #F9FAFB
- Header row: brand_color background, white text
- All column values as strings

SECTION 9 — Recommendations:
- Compile all 'action' fields from NRA insights
- Numbered list

SECTION 10 — Appendix (only if 'appendix' in config['sections']):
- Raw data table (same as Section 8)

Style rules:
- Font: Helvetica (built into ReportLab, no embedding needed)
- Brand color from user_data['brand_color'] (default '#6366F1')
- Chart image DPI: 150 (match what chart_service saves)
- Page size: A4
- Margins: 72pt (1 inch) all sides

Save to: /tmp/Naxely/{report_id}/report.pdf
Return the full file path.

Follow the documents exactly. Build all 10 sections. Do not skip any section.
```

---

## PROMPT 8 — Report Generation Orchestrator & API Endpoints
**Model:** GLM 4.7 | **Estimated time:** 30 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/03_SDD.md` — Sections 2, 3, 6, 7
READ: `docs/05_ASD.md` — Section 3 fully (all report endpoints)
READ: `docs/04_DSD.md` — uploads table and reports table only

Your task is to build the complete report generation system:

1. app/services/report_service.py — run_report_pipeline():

EXACT implementation from SDD Section 6:
- Import matplotlib and call matplotlib.use('Agg') at TOP of file
- run_report_pipeline is an ASYNC function
- Chart and PDF generation use run_in_executor (both are sync functions):
  loop = asyncio.get_event_loop()
  chart_paths = await loop.run_in_executor(None, chart_service.generate_sync, df, report_id, config, brand_color)
  pdf_path = await loop.run_in_executor(None, pdf_service.build_sync, df, chart_paths, ai_content, config, user_data)

Pipeline steps in exact order from SDD Section 2:
  a. update_status(report_id, 'processing', step='data')
  b. Fetch upload row from DB using config.upload_id → get file_url (storage path)
  c. Download CSV bytes from Supabase Storage: supabase.storage.from_("uploads").download(file_url)
  d. df = data_service.parse_csv(content)
  e. df = data_service.apply_column_config(df, config.column_config)
  f. update_status(report_id, 'processing', step='charts')
  g. chart_paths = await loop.run_in_executor(None, chart_service.generate_sync, ...)
  h. Delete CSV from storage after charts done
  i. If config has AI sections and user has API key:
     update_status(report_id, 'processing', step='ai')
     summary = await ai_service.generate_summary(df, config, user)
     insights = await ai_service.generate_nra_insights(df, config, user)
     anomalies = ai_service.detect_anomalies(df)
     trends = ai_service.detect_trends(df)
  j. update_status(report_id, 'processing', step='pdf')
  k. pdf_path = await loop.run_in_executor(None, pdf_service.build_sync, ...)
  l. Upload PDF to Supabase Storage: storage_path = f"reports/{user_id}/{report_id}/report.pdf"
     supabase.storage.from_("reports").upload(storage_path, open(pdf_path, 'rb').read())
  m. chart_service.cleanup_charts(report_id) — delete /tmp files
  n. mark_upload_used(upload_id, db) — set uploads.used = TRUE
  o. increment_report_count(user_id, db) — only on SUCCESS
  p. Update report row: status='completed', pdf_url=storage_path (PATH not signed URL),
     ai_summary, ai_insights, ai_anomalies, generation_time_seconds
  - On ANY exception: update status='failed', error_message=str(e), capture to Sentry

2. app/api/routes/reports.py — ALL endpoints:

POST /reports/generate:
  - Depends: get_current_user, check_report_limit
  - Validate upload_id exists and belongs to current_user (fetch from uploads table)
  - Check if AI features requested → check_pro_tier if so
  - Create report row (status='pending', user_id, config as JSON)
  - background_tasks.add_task(run_report_pipeline, ...)
  - Return 202 with report_id, status='processing', poll_url, estimated_seconds=45
  - Return EXACT schema from ASD POST /reports/generate

GET /reports/{report_id}/status:
  - Fetch report from DB
  - Verify report.user_id == current_user.id (403 if not)
  - If status='completed': generate FRESH signed URL from report.pdf_url (storage path):
    signed = supabase.storage.from_("reports").create_signed_url(report.pdf_url, 3600)
    Return pdf_url = signed['signedURL']
  - Return exact schemas from ASD for each status (processing/completed/failed)

GET /reports:
  - List with pagination (limit, offset query params)
  - Filter by current_user.id (users only see own reports)
  - For each completed report: generate fresh signed URL
  - Return exact schema from ASD GET /reports

GET /reports/{report_id}:
  - Fetch single report + verify ownership
  - Generate fresh signed URL if completed
  - Return exact schema from ASD GET /reports/{report_id}

DELETE /reports/{report_id}:
  - Verify ownership
  - Soft delete: UPDATE reports SET deleted_at = NOW() WHERE id = :id
  - Return {"success": true, "data": {"deleted": true}}

POST /reports/{report_id}/share (Pro only):
  - Generate random 64-char token (secrets.token_urlsafe(48))
  - Set share_token, share_expires_at in DB
  - Return share_url = f"https://Naxely.io/share/{token}"

GET /share/{share_token} (PUBLIC — no auth):
  - Look up report by share_token
  - Check share_expires_at > now (return 410 if expired)
  - Increment share_view_count
  - Generate fresh signed URL for PDF
  - Return limited report data (no user info)

Follow the documents exactly. Always generate fresh signed URLs, never return stored signed URLs.
```

---

## PROMPT 9 — Payments, Settings & Templates
**Model:** DeepSeek V3.2 | **Estimated time:** 20 minutes

```
You are building Naxely. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/05_ASD.md` — Sections 4, 5, 7
READ: `docs/07_SEC.md` — Sections 2, 5, 6
READ: `docs/04_DSD.md` — users table and payment_events table only

Your task is to build three route files:

1. app/api/routes/settings.py:

GET /settings/profile:
  - Return full user profile matching ASD schema
  - api_key_preview: if user.encrypted_api_key, return last 4 chars of a stored preview
    (store the preview separately or derive: "*..."+original[-4:] during save)
  - monthly_limit: None for pro/agency, 3 for free

PATCH /settings/profile:
  - Accept: {"full_name": str}
  - Validate: max 255 chars, strip whitespace
  - UPDATE users SET full_name = :name, updated_at = NOW() WHERE id = :uid
  - Return updated profile

POST /settings/api-key (Pro+ only via check_pro_tier dependency):
  - Accept: {"provider": str, "api_key": str}
  - Validate provider is "openai" or "claude"
  - Validate key pattern using regex from SEC 6.3:
    openai: ^sk-[a-zA-Z0-9\-_]{20,}$
    claude: ^sk-ant-[a-zA-Z0-9\-_]{20,}$
  - Encrypt: master_key = get_master_key(); encrypted, iv = encrypt_api_key(api_key, master_key)
  - Store encrypted_api_key, api_key_iv, ai_provider in users table
  - Return: {"provider": ..., "key_preview": "..."+api_key[-4:], "saved_at": ...}
  - NEVER return the full key or log it

DELETE /settings/api-key:
  - Set encrypted_api_key=NULL, api_key_iv=NULL, ai_provider=NULL
  - Return {"success": true, "data": {"deleted": true}}

POST /settings/branding (Pro+ only, multipart/form-data):
  - Accept: logo file (optional), brand_color, company_name
  - If logo provided:
    Validate: .png/.jpg/.svg only, max 2MB
    Upload to Supabase Storage: logos/{user_id}/logo.{ext}
    Update users.logo_url
  - Validate brand_color matches #RRGGBB pattern
  - UPDATE users: brand_color, company_name
  - Return: {"logo_url": ..., "brand_color": ..., "company_name": ...}

2. app/api/routes/payments.py:

GET /payments/plans (PUBLIC — no auth):
  - Return static pricing data with DODO product IDs from settings
  - Exact response schema from ASD GET /payments/plans

POST /payments/webhook:
  - Get raw request body BEFORE JSON parsing: body = await request.body()
  - Verify HMAC: verify_dodo_webhook(body, request.headers.get("X-Dodo-Signature"), settings.DODO_WEBHOOK_SECRET)
  - If invalid signature: return 400
  - Parse JSON: payload = json.loads(body)
  - Check idempotency: if payload['id'] already in payment_events table, return 200 immediately
  - Insert into payment_events table
  - Handle event types:
    "subscription.created" / "subscription.renewed": 
      UPDATE users SET tier='pro' or 'agency', tier_expires_at=..., dodo_subscription_id=...
    "subscription.cancelled": set flag (keep access until period end)
    "subscription.expired": UPDATE users SET tier='free'
    "payment.failed": send email via Resend
  - ALWAYS return 200 (Dodo retries on non-200)

POST /payments/cancel (authenticated):
  - Call Dodo API to cancel subscription
  - Return access_until date
  - Exact schema from ASD POST /payments/cancel

3. app/api/routes/templates.py:

GET /templates (Pro+): List user's templates
POST /templates (Pro+): Create new template
PATCH /templates/{id} (Pro+): Update template name/is_default
DELETE /templates/{id}: Delete template

All templates: filter by current_user.id only.

Follow the documents exactly. Use text() wrapper for all raw SQL.
```

---

## PROMPT 10 — React Frontend: Auth, Layout & Core
**Model:** GLM 4.7 | **Estimated time:** 30 minutes

```
You are building the Naxely React frontend. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/06_FSD.md` — Sections 1, 2, 3.2, 3.3, 4, 5, 6, 7
READ: `docs/02_TRD.md` — Section 5.2 (package.json)

Your task is to build the core frontend infrastructure:

1. src/lib/supabase.ts:
   import { createClient } from '@supabase/supabase-js'
   export const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY)

2. src/lib/axios.ts:
   - Axios instance with baseURL: import.meta.env.VITE_API_BASE_URL
   - Request interceptor: get JWT from authStore → set Authorization: Bearer {token}
   - Response interceptor: 401 → navigate to /login; 402 → emit 'upgrade-needed' event

3. src/types/user.ts, report.ts, api.ts:
   - TypeScript interfaces matching ALL response schemas from ASD
   - User interface: id, email, full_name, avatar_url, tier, tier_expires_at, has_api_key, ai_provider, logo_url, brand_color, company_name, reports_this_month, monthly_limit
   - Report interface: id, title, template_type, status, row_count, pdf_url, ai_summary, ai_insights, ai_anomalies, share_token, share_view_count, created_at
   - UploadResult interface: upload_id, filename, row_count, column_count, columns, preview_rows

4. src/store/authStore.ts — Zustand store:
   - State: user (User | null), isLoading, isAuthenticated, session
   - Actions:
     initialize(): check supabase.auth.getSession() on app load
     loginWithGoogle(): supabase.auth.signInWithOAuth({provider: 'google', options: {redirectTo: window.location.origin+'/auth/callback'}})
     loginWithEmail(email, password): supabase.auth.signInWithPassword()
     logout(): supabase.auth.signOut() + clear store
     fetchProfile(): call GET /auth/verify → set user
   - Token stored in memory only — NEVER localStorage (SEC Section 1.1)

5. src/store/reportStore.ts — Zustand store:
   - State: reports, uploadedFile, generationStatus, isGenerating
   - Actions: fetchReports, uploadFile, generateReport, pollStatus, deleteReport

6. src/App.tsx — React Router with ALL routes from FSD Section 2:
   - Public: /, /login, /signup, /auth/callback, /share/:token, /pricing, /404
   - Protected (redirect to /login if not authenticated):
     /dashboard, /report/new, /report/:id, /settings, /settings/api-key, /settings/billing, /settings/branding
   - Agency-only (redirect to /pricing if tier != 'agency'):
     /workspaces, /workspaces/:id
   - ProtectedRoute wrapper component that checks authStore.isAuthenticated

7. src/pages/AuthCallback.tsx:
   Exact implementation from FSD Section 2 route guards:
   useEffect: supabase.auth.onAuthStateChange((event) => { if (event === 'SIGNED_IN') navigate('/dashboard') })
   Show: "Signing you in..." text while waiting

8. src/pages/Login.tsx — EXACT spec from FSD Section 3.2:
   - Google button: calls authStore.loginWithGoogle()
   - Email/password form: react-hook-form + zod validation (email format, password min 8 chars)
   - Inline errors below each field (not toast)
   - On success: navigate to /dashboard
   - Design: centered card max-w-md, Inter font, indigo accent from FSD Section 1.1

9. src/pages/Signup.tsx — EXACT spec from FSD Section 3.3:
   - Same as login but with full_name field
   - supabase.auth.signUp() for email registration
   - Password strength indicator

10. src/components/layout/Sidebar.tsx — EXACT spec from FSD Section 3.4:
    - Logo top
    - Navigation items with tier-based visibility:
      Dashboard: always shown
      New Report: always shown
      Templates: shown with lock icon if free, shown normally if pro+
      Workspaces: HIDDEN completely if not agency tier
      Settings: always shown
    - Usage bar (only for free tier): "X of 3 reports used" — red when at limit
    - Upgrade banner (free tier only)
    - User avatar + name at bottom

11. src/components/layout/Navbar.tsx — Landing page navbar (sticky):
    - Logo left, links centre, CTA buttons right
    - "Log in" ghost button + "Start Free" filled indigo button

Use EXACT colours from FSD Section 1.1 as Tailwind classes.
Use Inter font (loaded via Google Fonts in index.html — already set up in Prompt 1).
Every loading state shows skeleton loader. Every error state shows retry button. Never blank screen.

Follow the documents exactly. Do not add features not specified.
```

---

## PROMPT 11 — React Frontend: Report Wizard & Dashboard
**Model:** GLM 4.7 | **Estimated time:** 35 minutes

```
You are building the Naxely React frontend. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/06_FSD.md` — Sections 3.4, 3.5, 3.6, 4
READ: `docs/05_ASD.md` — Section 3 schemas
READ: `docs/03_SDD.md` — Section 5 polling pattern

Your task is to build the report creation UI:

1. src/pages/Dashboard.tsx — EXACT spec from FSD Section 3.4:
   - Header: "Your Reports" + "+ New Report" button (→ /report/new)
   - Empty state: SVG illustration + "Create your first report" + CTA button
   - Report grid: 2 columns desktop, 1 column mobile
   - ReportCard for each report

2. src/components/dashboard/ReportCard.tsx:
   - Title (truncated at 50 chars)
   - Template type badge (Marketing / Financial / etc.)
   - Status badge: green=Completed, yellow=Processing, red=Failed
   - "1,250 rows" info
   - Created date formatted with date-fns
   - Three-dot menu: Download PDF | View | Delete
   - On delete: confirmation dialog → call DELETE /reports/{id}

3. src/components/dashboard/UsageBar.tsx:
   - Progress bar: reports_this_month / monthly_limit
   - Label: "2 of 3 free reports used this month"
   - Color: grey normally, red (#EF4444) when at limit
   - "Upgrade for unlimited →" link when at limit

4. src/pages/NewReport.tsx — 4-step wizard from FSD Section 3.5:
   - Step indicator: 4 circles with labels (Upload, Map, Configure, Generate)
   - Active step highlighted in indigo
   - "Back" and "Next" buttons
   - State: currentStep (1-4), uploadResult, columnConfig, reportConfig

5. src/components/report/FileUpload.tsx — Step 1:
   - react-dropzone: accept .csv and .xlsx only
   - Drag zone with cloud upload icon
   - Show "or click to browse" text
   - On file drop: call POST /reports/upload via axios
   - Loading spinner during upload
   - Success state: filename, row count, column count
   - Error state: clear error message

6. src/components/report/ColumnMapper.tsx — Step 2:
   - Table: one row per column from upload result
   - Columns: Original Name | Display Name (editable input) | Type (dropdown) | Include (toggle)
   - Type dropdown options: date, metric, dimension
   - Sample values: show first 3 as small grey chips
   - Pre-filled with suggested_name and suggested_type from upload response

7. src/components/report/ReportConfig.tsx — Step 3:
   - Title input (required, max 255 chars)
   - Date range: two date inputs (from / to) using date-fns formatting
   - Tone selector: 4 radio cards side by side
     Professional (briefcase icon) | Casual (chat icon) | Data-heavy (chart icon) | Story-driven (book icon)
   - Sections checklist:
     Free users: Charts ✅ | Key Metrics ✅ | Data Table ✅ | Executive Summary 🔒 | AI Insights 🔒
     Pro users: all enabled
   - Locked sections show UpgradePrompt component with "Upgrade to Pro" button

8. src/components/report/GeneratingLoader.tsx — Step 4 (shown during generation):
   - Full-screen overlay (white background)
   - 4 step indicators:
     1. "Parsing your data..." 
     2. "Generating charts..."
     3. "Writing AI insights..."
     4. "Building your PDF..."
   - Current step shows spinner, completed steps show green checkmark
   - "Usually takes 30–90 seconds" subtitle
   - Estimated time countdown

9. src/hooks/useReportStatus.ts — polling hook:
   EXACT implementation from SDD Section 5:
   MAX_POLLS = 30, POLL_INTERVAL = 3000ms
   - Sleep 3s → GET /reports/{id}/status → check status
   - Update progress state on each poll
   - On 'completed': navigate to /report/{id}
   - On 'failed': show error toast + navigate back to dashboard
   - After 30 polls (90s): show "taking longer than expected" message

10. src/pages/ReportView.tsx — EXACT spec from FSD Section 3.6:
    - Header: title + Download PDF button (opens signed URL) + Share button (Pro) + Delete button
    - Left panel: PDF viewer using pdfjs-dist (render the signed PDF URL)
    - Right panel: generation time, source file info, AI summary card, NRA insight cards, anomaly alerts

11. src/components/report/InsightCard.tsx:
    - Border colour: green (#10B981) for positive, red (#EF4444) for negative, grey for neutral
    - KPI name header
    - 📊 Number (bold)
    - ▶ Reason (normal text)
    - ✓ Action (italic)
    - Priority badge: HIGH / MEDIUM / LOW

Use FSD Section 4 component specs for Button, Badge, Modal, Spinner, EmptyState, UpgradePrompt.
Every async action shows loading state. Every error shows user-friendly message.
Follow the documents exactly.
```

---

## PROMPT 12 — Landing Page
**Model:** GLM 4.7 | **Estimated time:** 25 minutes

```
You are building the Naxely landing page. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/06_FSD.md` — Section 3.1 (landing page spec)
READ: `docs/06_FSD.md` — Section 1 (design system)
READ: `docs/01_PRD.md` — Sections 3.3 and 5.1

Your task is to build src/pages/Landing.tsx with ALL sections from FSD 3.1 in order:

1. Sticky Navbar (src/components/layout/Navbar.tsx — already built in Prompt 10):
   Import and use it here

2. Hero Section:
   - Headline: "Turn raw data into a client-ready report in 2 minutes"
   - Subheadline: "Upload a CSV, get an AI-powered PDF report with insights, charts, and recommendations. No design skills needed."
   - Primary CTA button: "Start Free — No credit card required" → navigate to /signup
   - Social proof text below button: "Join consultants and agencies worldwide"
   - Background: white with very subtle dot grid pattern (CSS background-image)
   - Clean, lots of whitespace — Notion style

3. How It Works (3 steps horizontal):
   - Step 1: Upload icon + "Upload your CSV or connect Google Sheets"
   - Step 2: Settings icon + "Configure your report in seconds"
   - Step 3: Download icon + "Download a professional PDF in under 2 minutes"
   - Each: large number, icon, title, one-line description

4. Features Grid (6 cards, 3x2 grid):
   - AI Executive Summary (Sparkles icon)
   - NRA Insight Cards (Lightbulb icon)
   - Auto Chart Generation (BarChart icon)
   - Custom Branding (Palette icon)
   - One-Click PDF Export (Download icon)
   - Google Sheets Connector (Link icon)
   - Each card: icon in indigo, title, 2-line description
   - Card style: white, rounded-xl, subtle shadow, hover lifts slightly

5. Pricing Section (3 columns):
   Free column ($0/month):
   - 3 reports/month, CSV upload, Basic charts (bar, line, pie), PDF with watermark, Email support
   - CTA: "Start Free" (ghost button) → /signup

   Pro column ($29/month — HIGHLIGHTED with indigo border + "Most Popular" badge):
   - Unlimited reports, AI Executive Summary, NRA Insight Cards, Anomaly Detection
   - Custom branding (logo + colour), No watermark, Google Sheets connector
   - Save templates, Shareable links, Priority support
   - CTA: "Upgrade to Pro" (filled indigo) → opens Dodo Payments checkout

   Agency column ($79/month):
   - Everything in Pro + White-label reports, 5 team seats, Client workspaces
   - PowerPoint export, API access, Scheduled reports, Dedicated support
   - CTA: "Upgrade to Agency" → Dodo Payments checkout

6. Testimonials (3 placeholder cards):
   - Each: star rating (5 stars), quote text, name, role, company
   - Use placeholder text "Coming soon — be the first to review"
   - Style: white cards, rounded-xl, shadow-sm

7. Final CTA Banner:
   - Dark background (bg-gray-900)
   - Headline: "Ready to stop spending hours on reports?"
   - Subtext: "Join thousands of consultants and agencies saving time with Naxely."
   - Button: "Get started free" → /signup

8. Footer:
   - Logo + tagline: "Turn data into insights, instantly."
   - Links: Features, Pricing, Privacy Policy, Terms of Service, Contact
   - "Made in India 🇮🇳 · Naxely © 2026"
   - Subtle top border

Design rules — STRICTLY from FSD Section 1.1:
- Background: #FFFFFF, text: #111827, accent: #6366F1
- Font: Inter (loaded in index.html)
- Cards: rounded-xl, shadow-sm
- Buttons: rounded-lg
- Lots of padding and white space — clean minimal Notion style
- NO dark backgrounds except final CTA banner
- Use lucide-react for all icons

Follow the documents exactly. Build all 8 sections. Do not add sections not specified.
```

---

## PROMPT 13 — Settings Pages & Final Polish
**Model:** GLM 4.7 | **Estimated time:** 20 minutes

```
You are building the Naxely React frontend. Read these documents yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/06_FSD.md` — Section 3.7 (Settings page spec)
READ: `docs/06_FSD.md` — Section 3.8 (Pricing page spec)
READ: `docs/05_ASD.md` — Section 4 (settings endpoints)

Your task is to build the settings and pricing pages:

1. src/pages/Settings.tsx — 4 tabs (Profile | API Key | Branding | Billing):
   Use tab component from shadcn/ui

   Profile Tab:
   - Full name input (pre-filled from user.full_name)
   - Email field (read-only, from auth)
   - Save button → PATCH /settings/profile
   - Success toast on save

   API Key Tab:
   - Current status: "Connected (OpenAI)" / "Connected (Claude)" / "Not configured"
   - Key preview: "sk-proj-...abcd" (last 4 chars only)
   - Provider dropdown: OpenAI | Claude (Anthropic)
   - API key input: password type, paste-only
   - Warning: "Your key is encrypted with AES-256 and only used during report generation. It is never stored in plain text."
   - Save button → POST /settings/api-key
   - Delete button (with confirmation modal) → DELETE /settings/api-key
   - If free tier: show UpgradePrompt instead of the form

   Branding Tab (Pro+ only — show UpgradePrompt for free):
   - Logo upload: show current logo (if set), drag-drop to replace
     Max 2MB, PNG/JPG/SVG only
   - Brand colour picker: hex input + colour swatch preview
   - Company name input
   - Preview section: mini PDF cover page mockup that updates live as user types
   - Save button → POST /settings/branding

   Billing Tab:
   - Current plan display: "Free" / "Pro — $29/month" / "Agency — $79/month"
   - Next billing date (if subscribed)
   - For free users: upgrade cards for Pro and Agency (same as pricing page but compact)
   - For paid users: "Cancel Subscription" button → confirmation modal → POST /payments/cancel
   - After cancel: "Your access continues until {date}"

2. src/pages/Pricing.tsx — standalone page (also accessible from /)
   - Same 3-column pricing table as landing page Section 5
   - But with full FAQ section below:
     Q: Can I cancel anytime? A: Yes, cancel any time — access until end of billing period.
     Q: Do I need a credit card for the free plan? A: No.
     Q: What AI providers are supported? A: OpenAI and Anthropic Claude — bring your own API key.
     Q: Is my data secure? A: Yes — files are encrypted in transit and at rest. CSV files are deleted immediately after your report is generated.
     Q: Can agencies white-label reports? A: Yes — the Agency plan removes all Naxely branding.

3. src/pages/NotFound.tsx:
   - Simple 404 page
   - "Page not found" heading
   - "Go back to dashboard" link

4. src/components/settings/ApiKeyForm.tsx:
   - Standalone component for the API Key tab
   - Handles all state, validation, API calls internally
   - Shows success/error states cleanly

5. Final check — add these to every page that shows user data:
   - Loading skeleton while fetching
   - Empty state if no data
   - Error state with retry button
   - Never show a blank white screen

Follow the documents exactly. All forms use react-hook-form + zod validation.
```

---

## PROMPT 14 — CI/CD & Deployment Configuration
**Model:** DeepSeek V3.2 | **Estimated time:** 10 minutes

```
You are finalizing Naxely for deployment. Read these sections yourself using your file-read tool before writing anything. *(Don't wait for pasted content — open each file listed below directly.)*

READ: `docs/08_DEP.md` — Sections 3, 4, 5, 6, 7, 12, 13, 19, 20

Your task is to create all deployment configuration files exactly as documented:

Files to create:

1. .github/workflows/backend-ci.yml
   EXACT content from DEP Section 3.1
   Uses: Python 3.11, pytest, mypy, Render deploy hook

2. .github/workflows/frontend-ci.yml
   EXACT content from DEP Section 3.2
   Uses: Node 20, npm ci, TypeScript check, Vite build

3. backend/render.yaml
   EXACT content from DEP Section 4.1
   Service name: Naxely-api, Python runtime, free plan
   buildCommand must run: pip install -r requirements.txt && alembic upgrade head

4. frontend/vercel.json
   EXACT content from DEP Section 5.1
   Includes: SPA rewrite rule, security headers, cache headers for assets

5. backend/Dockerfile
   EXACT content from DEP Section 12
   Uses python:3.11-slim, installs system deps for matplotlib/reportlab/cryptography,
   creates /tmp/Naxely directory

6. backend/alembic.ini
   EXACT content from DEP Section 13
   Uses postgresql+psycopg2:// URL (SYNC driver for Alembic)

7. backend/migrations/env.py
   EXACT content from DEP Section 19
   Uses SYNC psycopg2 connection, imports all models, builds URL from env vars

After creating all files, also create:

8. DEPLOYMENT_CHECKLIST.md — GitHub Issue template:
   Convert the pre-launch checklist from DEP Section 11 into a GitHub Issue template
   with checkboxes for every item. Include the auth trigger setup step:
   "[ ] Run 000_create_auth_trigger.sql in Supabase SQL editor before any users sign up"

9. GITHUB_SECRETS.md — reference file:
   Table of all GitHub secrets from DEP Section 20
   Include: what each secret is, where to find it, which workflow uses it
   Add warning: NEVER commit these to git

Follow the documents exactly. Do not modify any configuration values.
```

---

## QUICK REFERENCE — Prompts vs Models

| Prompt | What Gets Built | Model |
|---|---|---|
| 1 | Folder structure, package.json, config files | DeepSeek V3.2 |
| 2 | DB schema, migrations, SQLAlchemy models | DeepSeek V3.2 |
| 3 | FastAPI core, JWT, encryption, deps | GLM 4.7 |
| 4 | CSV upload, data service, column detection | DeepSeek V3.2 |
| 5 | Chart generation (matplotlib) | DeepSeek V3.2 |
| 6 | AI service, NRA insights, anomaly detection | GLM 4.7 |
| 7 | PDF generation (ReportLab, all 10 sections) | DeepSeek V3.2 |
| 8 | Report orchestration, all report API endpoints | GLM 4.7 |
| 9 | Payments, settings, templates endpoints | DeepSeek V3.2 |
| 10 | React auth, layout, sidebar, Zustand stores | GLM 4.7 |
| 11 | Report wizard, dashboard, polling hook | GLM 4.7 |
| 12 | Landing page (all 8 sections) | GLM 4.7 |
| 13 | Settings pages, pricing page, 404 | GLM 4.7 |
| 14 | CI/CD, Dockerfile, render.yaml, vercel.json | DeepSeek V3.2 |

---

## TROUBLESHOOTING

**Model hangs with no response:**
- Avoid `deepseek-v4-flash` and `deepseek-v4-pro` on NVIDIA NIM — known bug
- Use `deepseek-v3.2` instead

**429 Rate Limit error (40 RPM):**
- Wait 60 seconds
- Or switch to a different model (each has its own RPM bucket)

**AI gives wrong code:**
- Tell it to re-read the relevant `docs/X.md` file with its file-read tool — it may have skimmed or misread the section
- Say: "Read the document again. Your code does not match Section X. Rewrite it to match exactly."

**Context too long:**
- Try Nemotron 3 Super (1M context) if it shows up in `/models` — see the caveat in the Model Selection Guide above
- Otherwise tell it to read only the specific section named in the prompt, not the entire file
- GLM-4.7 (128K) and DeepSeek V3.2 (128K) both comfortably fit any single document section used in these prompts

**Credits running out:**
- Request 5,000 more at: build.nvidia.com → Account → Request Credits (free)
- Or add Gemini API as backup provider (1,000 req/day free at aistudio.google.com)
