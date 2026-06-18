# TRD — Technical Requirements Document
## Naxely: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. TECH STACK — COMPLETE

### 1.1 Frontend
| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Framework | React | 18.x | UI library |
| Language | TypeScript | 5.x | Type safety |
| Styling | Tailwind CSS | 3.x | Utility-first CSS |
| UI Components | shadcn/ui | Latest | Pre-built accessible components |
| Charts (UI) | Recharts | 2.x | Interactive charts in browser |
| Routing | React Router | 6.x | Client-side routing |
| State Management | Zustand | 4.x | Lightweight global state |
| Forms | React Hook Form | 7.x | Form handling + validation |
| Validation | Zod | 3.x | Schema validation |
| HTTP Client | Axios | 1.x | API calls to backend |
| File Upload | React Dropzone | 14.x | Drag-and-drop CSV upload |
| Notifications | React Hot Toast | 2.x | Toast notifications |
| Icons | Lucide React | Latest | Clean icon set |
| Date Handling | date-fns | 3.x | Date formatting |
| Build Tool | Vite | 5.x | Fast bundler |
| Hosting | Vercel | — | Free static hosting + CDN |

### 1.2 Backend
| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Framework | FastAPI | 0.111.x | Python API framework |
| Language | Python | 3.11+ | Backend language |
| Server | Uvicorn | 0.29.x | ASGI server |
| Data Processing | Pandas | 2.x | CSV/data manipulation |
| Data Processing | NumPy | 1.x | Numerical operations |
| PDF Generation | ReportLab | 4.x | PDF creation |
| PPT Generation | python-pptx | 0.6.x | PowerPoint export |
| Chart Generation | Matplotlib | 3.x | Chart images for PDF |
| Seaborn | Seaborn | 0.13.x | Chart styling |
| AI Integration | openai | 1.x | OpenAI API calls |
| AI Integration | anthropic | 0.26.x | Claude API calls |
| Google Sheets | gspread | 6.x | Google Sheets connector |
| Encryption | cryptography | 42.x | AES-256 API key encryption |
| Scheduling | APScheduler | 3.x | Scheduled report jobs |
| File Handling | python-multipart | 0.x | File upload handling |
| HTTP | httpx | 0.27.x | Async HTTP client |
| Env Variables | python-dotenv | 1.x | Environment config |
| Testing | pytest | 8.x | Unit + integration tests |
| Hosting | Render.com | — | Free Python hosting |

### 1.3 Database & Auth
| Layer | Technology | Purpose |
|---|---|---|
| Database | Supabase PostgreSQL | All app data |
| Auth | Supabase Auth | Email + Google OAuth |
| File Storage | Supabase Storage | CSV uploads, logos, PDFs |
| ORM | SQLAlchemy 2.x | DB queries from Python |
| Migrations | Alembic | Schema version control |
| DB Client (FE) | @supabase/supabase-js | Frontend auth + storage |

### 1.4 Payments
| Layer | Technology | Purpose |
|---|---|---|
| Payment Provider | Dodo Payments | Subscription billing, MoR |
| Webhook Handler | FastAPI endpoint | Process payment events |
| Subscription State | Supabase DB | Store tier + status |

### 1.5 Infrastructure & DevOps
| Tool | Purpose |
|---|---|
| GitHub | Version control |
| GitHub Actions | CI/CD pipeline |
| Vercel | Frontend hosting + auto-deploy |
| Render.com | Backend hosting + auto-deploy |
| Sentry (free) | Error monitoring |
| Uptime Robot (free) | Uptime monitoring |
| Resend (free tier) | Transactional emails |

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                        │
│              React + TypeScript (Vercel)                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS (Axios)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                         │
│                  (Render.com)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Auth    │ │  Report  │ │   AI     │ │ Payments │  │
│  │  Router  │ │  Router  │ │  Router  │ │  Router  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└──────┬───────────────┬──────────────┬───────────────────┘
       │               │              │
       ▼               ▼              ▼
┌──────────┐    ┌──────────┐   ┌──────────────┐
│ Supabase │    │  OpenAI  │   │ Dodo Payments│
│ (DB+Auth │    │ /Claude  │   │  (Webhooks)  │
│ +Storage)│    │   API    │   └──────────────┘
└──────────┘    └──────────┘
```

### 2.2 Report Generation Pipeline
```
CSV Upload (Frontend)
       │
       ▼
Supabase Storage (raw file saved)
       │
       ▼
FastAPI: Parse CSV → Pandas DataFrame
       │
       ▼
Column Mapper → Clean DataFrame
       │
       ├──────────────────────────────┐
       ▼                              ▼
Matplotlib: Generate chart images    AI Layer (if Pro):
(PNG, saved to /tmp)                 - Detect KPIs
                                     - Generate summary
                                     - Generate NRA insights
                                     - Detect anomalies
                                     - Detect trends
       │                              │
       └──────────────┬───────────────┘
                      ▼
              ReportLab: Build PDF
              (charts embedded as images)
                      │
                      ▼
              Supabase Storage: Save PDF
                      │
                      ▼
              Frontend: Download URL returned
```

### 2.3 Authentication Flow
```
User clicks "Sign in with Google"
       │
       ▼
Supabase Auth → Google OAuth 2.0
       │
       ▼
Supabase returns JWT token
       │
       ▼
Frontend stores token in memory (not localStorage)
       │
       ▼
Every API request: Authorization: Bearer <JWT>
       │
       ▼
FastAPI validates JWT with Supabase public key
       │
       ▼
Extract user_id → use for all DB queries
```

### 2.4 API Key Encryption Flow
```
User enters API key in Settings
       │
       ▼
Frontend sends key to FastAPI via HTTPS (POST /settings/api-key)
       │
       ▼
FastAPI: AES-256-GCM encrypt using MASTER_ENCRYPTION_KEY (env var)
       │
       ▼
Store encrypted_key in users table (Supabase)
       │
       ▼
On report generation:
FastAPI decrypts key in memory → passes to OpenAI/Claude → never logs it
       │
       ▼
Key is never returned to frontend in any response
```

---

## 3. ENVIRONMENT VARIABLES

### 3.1 Backend (.env — Render.com)
```bash
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # Service role key (never expose to frontend)
SUPABASE_JWT_SECRET=your-jwt-secret

# Encryption
MASTER_ENCRYPTION_KEY=32-byte-hex-string  # AES-256 key for API key encryption
ENCRYPTION_SALT=16-byte-hex-string

# Dodo Payments
DODO_API_KEY=your-dodo-api-key
DODO_WEBHOOK_SECRET=your-webhook-secret
DODO_PRO_PRODUCT_ID=prod_xxx
DODO_AGENCY_PRODUCT_ID=prod_xxx

# Email (Resend)
RESEND_API_KEY=re_xxx
FROM_EMAIL=hello@Naxely.io

# App
ENVIRONMENT=production
ALLOWED_ORIGINS=https://Naxely.io,https://www.Naxely.io
SECRET_KEY=random-64-char-string
TEMP_DIR=/tmp/Naxely

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### 3.2 Frontend (.env — Vercel)
```bash
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...  # Anon key only (safe for frontend)
VITE_API_BASE_URL=https://api.Naxely.io
VITE_DODO_CLIENT_TOKEN=dodo_client_xxx
VITE_ENVIRONMENT=production
```

**⚠️ CRITICAL RULE:** SUPABASE_SERVICE_KEY and MASTER_ENCRYPTION_KEY must NEVER appear in frontend code or git history. Backend only.

---

## 4. FOLDER STRUCTURE

### 4.1 Frontend (/frontend)
```
frontend/
├── public/
│   ├── favicon.ico
│   └── og-image.png
├── src/
│   ├── assets/
│   │   └── logo.svg
│   ├── components/
│   │   ├── ui/                    # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── landing/
│   │   │   ├── Hero.tsx
│   │   │   ├── Features.tsx
│   │   │   ├── Pricing.tsx
│   │   │   ├── Testimonials.tsx
│   │   │   └── CTA.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── SignupForm.tsx
│   │   │   └── GoogleButton.tsx
│   │   ├── dashboard/
│   │   │   ├── ReportCard.tsx
│   │   │   ├── UsageBar.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── report/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ColumnMapper.tsx
│   │   │   ├── ReportConfig.tsx
│   │   │   ├── GeneratingLoader.tsx
│   │   │   ├── ReportPreview.tsx
│   │   │   └── InsightCard.tsx
│   │   └── settings/
│   │       ├── ApiKeyForm.tsx
│   │       ├── BrandingForm.tsx
│   │       └── BillingSection.tsx
│   ├── pages/
│   │   ├── Landing.tsx
│   │   ├── Login.tsx
│   │   ├── Signup.tsx
│   │   ├── Dashboard.tsx
│   │   ├── NewReport.tsx
│   │   ├── ReportView.tsx
│   │   ├── Settings.tsx
│   │   ├── Pricing.tsx
│   │   └── NotFound.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useReports.ts
│   │   ├── useUpload.ts
│   │   └── useSubscription.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   └── reportStore.ts
│   ├── lib/
│   │   ├── supabase.ts
│   │   ├── axios.ts
│   │   └── utils.ts
│   ├── types/
│   │   ├── report.ts
│   │   ├── user.ts
│   │   └── api.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env
├── .env.example
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
└── package.json
```

### 4.2 Backend (/backend)
```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── reports.py
│   │   │   ├── settings.py
│   │   │   ├── payments.py
│   │   │   └── health.py
│   │   └── deps.py              # Shared dependencies (auth, DB)
│   ├── core/
│   │   ├── config.py            # Settings from env vars
│   │   ├── security.py          # JWT validation, encryption
│   │   └── exceptions.py        # Custom exception handlers
│   ├── services/
│   │   ├── report_service.py    # Orchestrates full report generation
│   │   ├── ai_service.py        # AI summary + NRA insights
│   │   ├── chart_service.py     # Matplotlib chart generation
│   │   ├── pdf_service.py       # ReportLab PDF building
│   │   ├── ppt_service.py       # python-pptx export
│   │   ├── data_service.py      # CSV parsing + Pandas processing
│   │   ├── sheets_service.py    # Google Sheets connector
│   │   ├── payment_service.py   # Dodo Payments + webhooks
│   │   └── email_service.py     # Resend transactional emails
│   ├── models/
│   │   ├── user.py              # SQLAlchemy User model
│   │   ├── report.py            # SQLAlchemy Report model
│   │   ├── template.py          # SQLAlchemy Template model
│   │   └── workspace.py         # SQLAlchemy Workspace model
│   ├── schemas/
│   │   ├── report.py            # Pydantic request/response schemas
│   │   ├── user.py
│   │   └── payment.py
│   ├── utils/
│   │   ├── encryption.py        # AES-256 encrypt/decrypt
│   │   ├── file_handler.py      # Upload/delete temp files
│   │   └── validators.py        # CSV validation
│   └── main.py                  # FastAPI app entry point
├── migrations/
│   └── versions/                # Alembic migration files
├── tests/
│   ├── test_reports.py
│   ├── test_ai_service.py
│   ├── test_pdf_service.py
│   └── test_payments.py
├── .env
├── .env.example
├── requirements.txt
├── alembic.ini
├── Dockerfile
└── render.yaml
```

---

## 5. DEPENDENCIES — COMPLETE

### 5.1 Backend requirements.txt
> ✅ CONFLICT-TESTED: All versions verified with pip dry-run — zero conflicts

```
# Web Framework
fastapi==0.111.0
uvicorn[standard]==0.29.0

# Data Processing
pandas==2.2.0
numpy==1.26.4
openpyxl==3.1.2

# Visualisation (PDF charts only — not served to frontend)
matplotlib==3.8.4
seaborn==0.13.2
pillow==10.3.0

# PDF + PPT Generation
reportlab==4.2.0
python-pptx==0.6.23

# AI Integrations (user provides their own key)
openai==1.30.0
anthropic==0.26.0

# Google Sheets Connector
gspread==6.1.0
google-auth==2.29.0

# Security & Encryption
cryptography==42.0.8
python-jose[cryptography]==3.3.0  # JWT validation
slowapi==0.1.9                     # Rate limiting

# Database
sqlalchemy==2.0.30
asyncpg==0.29.0                    # PostgreSQL ASYNC driver (used by FastAPI at runtime)
psycopg2-binary==2.9.9             # PostgreSQL SYNC driver (used by Alembic for migrations ONLY)
alembic==1.13.1

# Supabase Client
# NOTE: supabase==2.9.1 required — 2.4.0 conflicts with httpx>=0.26
supabase==2.9.1

# HTTP & File Handling
httpx==0.27.2
python-multipart==0.0.9
aiofiles==23.2.1                   # Async file I/O

# Config & Validation
python-dotenv==1.0.1
pydantic==2.7.1
pydantic-settings==2.3.0

# Scheduling (Agency tier scheduled reports only — NOT used for report generation)
# Report generation uses FastAPI BackgroundTasks instead
apscheduler==3.10.4

# Email
resend==2.0.0

# Monitoring
sentry-sdk[fastapi]==2.5.0

# Testing & Type Checking
pytest==8.2.2
pytest-asyncio==0.23.7
mypy==1.10.0
```

### ⚠️ KEY CONFLICT THAT WAS FIXED
`supabase==2.4.0` requires `httpx<0.26`. `openai` and `anthropic` require `httpx>=0.23`. 
Using `supabase==2.9.1` resolves this — it accepts `httpx>=0.24,<1.0`.
Never downgrade supabase below 2.9.1.

### 5.2 Frontend package.json (key dependencies)
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0",
    "typescript": "^5.4.0",
    "@supabase/supabase-js": "^2.43.0",
    "axios": "^1.7.0",
    "zustand": "^4.5.0",
    "react-hook-form": "^7.51.0",
    "zod": "^3.23.0",
    "@hookform/resolvers": "^3.4.0",
    "recharts": "^2.12.0",
    "react-dropzone": "^14.2.0",
    "react-hot-toast": "^2.4.0",
    "lucide-react": "^0.383.0",
    "date-fns": "^3.6.0",
    "tailwindcss": "^3.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    "pdfjs-dist": "^4.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/node": "^20.14.0",
    "tailwindcss-animate": "^1.0.7"
  }
}
```

### ⚠️ shadcn/ui is NOT an npm package
shadcn/ui components are installed via CLI, not npm install.
Run this ONCE after `npm install`:
```bash
npx shadcn-ui@latest init
# Choose: TypeScript=yes, Style=Default, Base colour=Slate, CSS variables=yes
# Then add individual components as needed:
npx shadcn-ui@latest add button input label card badge dialog
```
This copies component source files into `src/components/ui/` — they become YOUR code.

---

## 6. TECHNICAL CONSTRAINTS

### 6.1 Render.com Free Tier Limits
| Constraint | Limit | Mitigation |
|---|---|---|
| RAM | 512MB | Limit DataFrame size, stream large files |
| CPU | Shared | Queue heavy jobs, timeout at 60s |
| Cold start | ~30 seconds | Show "warming up" message on frontend |
| Disk | Ephemeral | Use /tmp for temp files, delete after use |
| Bandwidth | 100GB/month | Compress PDFs, limit file sizes |
| Sleep after inactivity | 15 minutes | Uptime Robot pings every 14 min |

### 6.2 Supabase Free Tier Limits
| Constraint | Limit | Mitigation |
|---|---|---|
| Storage | 1GB | Delete temp CSVs after processing, keep only PDFs |
| DB rows | 500MB | Lean schema, archive old reports after 90 days |
| Auth users | 50,000 | More than enough for MVP |
| Bandwidth | 5GB/month | Compress uploads, optimise PDF sizes |
| Edge functions | 500K/month | Not using (FastAPI handles logic) |

### 6.3 AI API Constraints (User's Own Key)
| Constraint | Behaviour |
|---|---|
| Invalid API key | Return 400 with "Invalid API key — please check Settings" |
| Rate limit hit | Return 429 with "AI service temporarily unavailable — try again in 60s" |
| API key not set | Return 402 with "Add your API key in Settings to use AI features" |
| Timeout (>30s) | Return 504 with "AI generation timed out — report saved without AI insights" |
| Token limit exceeded | Truncate DataFrame to 1000 rows before sending to AI |

### 6.4 PDF Generation Constraints
| Constraint | Value |
|---|---|
| Max charts per PDF | 8 (performance) |
| Max pages | 20 |
| Chart image resolution | 150 DPI (balance of quality vs file size) |
| Max PDF file size | 15MB |
| Temp chart storage | /tmp/Naxely/{report_id}/ — deleted after PDF built |
| Font | Helvetica (built into ReportLab, no font embedding needed) |

### 6.5 CORS Configuration
```python
# FastAPI CORS settings
allowed_origins = [
    "https://Naxely.io",
    "https://www.Naxely.io",
    "http://localhost:5173",  # Dev only
]
# NEVER allow "*" in production
```

---

## 7. ERROR HANDLING STANDARDS

### 7.1 HTTP Status Codes Used
| Code | When |
|---|---|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (invalid file, bad CSV) |
| 401 | Not authenticated |
| 402 | Payment required (Pro feature, no subscription) |
| 403 | Forbidden (wrong tier, not authorised) |
| 404 | Resource not found |
| 422 | Validation error (Pydantic) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 504 | Gateway timeout (AI took too long) |

### 7.2 Error Response Format (All Endpoints)
```json
{
  "error": true,
  "code": "INVALID_API_KEY",
  "message": "Your API key is invalid. Please update it in Settings.",
  "detail": null
}
```

### 7.3 Frontend Error Handling Rules
- Every API call wrapped in try/catch
- Network errors → "Connection error — please check your internet"
- 401 errors → redirect to login
- 402 errors → show upgrade modal
- 500 errors → show "Something went wrong — our team has been notified" + Sentry capture
- Never show raw Python tracebacks to users

---

## 8. PERFORMANCE REQUIREMENTS

### 8.1 Backend
| Endpoint | Max Response Time |
|---|---|
| GET /health | 100ms |
| GET /reports | 500ms |
| POST /reports/upload | 2000ms (file upload) |
| POST /reports/generate | 90,000ms (90s — AI + PDF) |
| GET /reports/{id}/status | 200ms |
| POST /settings/api-key | 300ms |
| POST /payments/webhook | 500ms |

> Note: PDF download happens via Supabase signed URL (direct from Storage) — not a FastAPI endpoint.

### 8.2 Frontend
| Metric | Target |
|---|---|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| Time to Interactive | < 3.5s |
| Bundle size (gzipped) | < 200KB |
| Lighthouse score | 85+ |

---

## 9. TESTING REQUIREMENTS

### 9.1 Backend Tests (pytest)
- Unit tests for: data_service, ai_service, pdf_service, encryption
- Integration tests for: all API endpoints
- Minimum coverage: 70%

### 9.2 Frontend Tests
- Manual testing checklist for each page before deploy
- Automated: not required for MVP (add Vitest in Phase 2)

### 9.3 CI Pipeline (GitHub Actions)
```yaml
On every push to main:
1. Run pytest (backend)
2. Run TypeScript type check (frontend)
3. Run Vite build (frontend)
4. If all pass → auto-deploy to Vercel (frontend) + Render (backend)
```

---

## 10. LOGGING STANDARDS

### 10.1 What to Log (Backend)
```python
# Log these:
logger.info(f"Report generated: user={user_id}, report={report_id}, time={elapsed}s")
logger.warning(f"AI timeout: user={user_id}, report={report_id}")
logger.error(f"PDF generation failed: {str(e)}", exc_info=True)

# NEVER log these:
# - API keys (encrypted or plain)
# - Passwords
# - JWT tokens
# - Full CSV data (privacy)
```

### 10.2 Sentry (Error Monitoring)
- All 500 errors auto-captured
- User ID attached to each event (not email — privacy)
- PII scrubbing enabled

---

*End of TRD*


---
