
# DEP — Deployment & DevOps Document
## Databrief: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. INFRASTRUCTURE OVERVIEW

```
GitHub Repo (monorepo)
├── /frontend  → Vercel (auto-deploy on push to main)
└── /backend   → Render.com (auto-deploy on push to main)

External Services:
├── Supabase     → Database + Auth + Storage
├── Dodo Payments → Subscription billing
├── Resend       → Transactional email
├── Sentry       → Error monitoring
└── Uptime Robot → Uptime checks
```

---

## 2. REPOSITORY STRUCTURE

```
databrief/                         ← GitHub repo root
├── frontend/                      ← React app
├── backend/                       ← FastAPI app
├── .github/
│   └── workflows/
│       ├── frontend-ci.yml
│       └── backend-ci.yml
├── README.md
└── .gitignore
```

### .gitignore (Critical entries)
```
# Environment files — NEVER commit these
.env
.env.local
.env.production
backend/.env
frontend/.env

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/

# Node
node_modules/
dist/
.vite/

# Temp files
/tmp/
*.pdf
*.csv
```

---

## 3. CI/CD PIPELINE

### 3.1 Backend CI (/.github/workflows/backend-ci.yml)
```yaml
name: Backend CI

on:
  push:
    branches: [main]
    paths: ['backend/**']

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          
      - name: Run type check
        run: |
          cd backend
          python -m mypy app/ --ignore-missing-imports
          
      - name: Run tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          MASTER_ENCRYPTION_KEY: ${{ secrets.MASTER_ENCRYPTION_KEY }}
        run: |
          cd backend
          pytest tests/ -v --tb=short
          
      - name: Deploy to Render
        if: success()
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
```

### 3.2 Frontend CI (/.github/workflows/frontend-ci.yml)
```yaml
name: Frontend CI

on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
          
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          
      - name: TypeScript type check
        run: |
          cd frontend
          npm run type-check
          
      - name: Build
        env:
          VITE_SUPABASE_URL: ${{ secrets.VITE_SUPABASE_URL }}
          VITE_SUPABASE_ANON_KEY: ${{ secrets.VITE_SUPABASE_ANON_KEY }}
          VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
        run: |
          cd frontend
          npm run build
          
      # Vercel auto-deploys via GitHub integration (no manual step needed)
```

---

## 4. RENDER.COM CONFIGURATION

### 4.1 render.yaml (Backend)
```yaml
services:
  - type: web
    name: databrief-api
    runtime: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt && alembic upgrade head
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: MASTER_ENCRYPTION_KEY
        sync: false
      - key: DODO_API_KEY
        sync: false
      - key: DODO_WEBHOOK_SECRET
        sync: false
      - key: RESEND_API_KEY
        sync: false
      - key: SENTRY_DSN
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: ALLOWED_ORIGINS
        value: https://databrief.io,https://www.databrief.io
```

### 4.2 Render Free Tier Gotchas
| Issue | Solution |
|---|---|
| Service sleeps after 15 min inactivity | Uptime Robot pings /health every 14 minutes |
| Cold start ~30 seconds | Frontend shows "Waking up server..." message if health check fails |
| Ephemeral disk (resets on deploy) | All files written to Supabase Storage, not local disk |
| 512MB RAM limit | Stream large CSVs in chunks, limit DataFrame to 50K rows |
| Build timeout: 15 minutes | Keep requirements.txt lean, use pip cache |

---

## 5. VERCEL CONFIGURATION

### 5.1 vercel.json (Frontend)
```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    },
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

### 5.2 Custom Domain Setup
1. Buy `databrief.io` (Namecheap or Cloudflare)
2. In Vercel: Add domain → get CNAME/A records
3. In Namecheap: Add DNS records from Vercel
4. In Render: Add custom domain `api.databrief.io` → get CNAME
5. In Namecheap: Add CNAME `api → xxxx.onrender.com`
6. SSL: Auto-provisioned by both Vercel and Render (Let's Encrypt)

---

## 6. SUPABASE SETUP

### 6.1 Project Creation
1. Create project at supabase.com
2. Region: Southeast Asia (Singapore) — closest to India + good global latency
3. Database password: 32+ char random string (save securely)
4. Copy: Project URL, anon key, service key

### 6.2 Auth Configuration
```
Supabase Dashboard → Auth → Settings:
- Site URL: https://databrief.io
- Redirect URLs: https://databrief.io/auth/callback
- Email confirmations: ON
- Google OAuth: Enable → add Client ID + Secret from Google Cloud Console
```

### 6.3 Storage Buckets
```sql
-- Run in Supabase SQL editor
INSERT INTO storage.buckets (id, name, public) VALUES ('uploads', 'uploads', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('reports', 'reports', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('logos', 'logos', false);

-- Storage policies (backend service key bypasses these)
CREATE POLICY "Users can upload their own files"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'uploads' AND auth.uid()::text = (storage.foldername(name))[1]);
```

### 6.4 Database Migrations
```bash
# Run locally first (dev), then production
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "add_scheduled_reports_table"

# Rollback
alembic downgrade -1
```

---

## 7. DODO PAYMENTS SETUP

### 7.1 Account Setup
1. Create account at dodopayments.com
2. Complete KYC verification (Indian founder — provide PAN + bank details)
3. Add bank account for INR settlement
4. Enable test mode for development

### 7.2 Product Configuration
```
Create 2 products in Dodo dashboard:

Product 1: Databrief Pro
- Name: Databrief Pro
- Price: $29/month
- Billing: Monthly recurring
- Trial: None
- Copy product ID → DODO_PRO_PRODUCT_ID env var

Product 2: Databrief Agency
- Name: Databrief Agency
- Price: $79/month
- Billing: Monthly recurring
- Trial: None
- Copy product ID → DODO_AGENCY_PRODUCT_ID env var
```

### 7.3 Webhook Configuration
```
Dodo Dashboard → Webhooks:
- Endpoint URL: https://api.databrief.io/payments/webhook
- Events to subscribe:
  ✅ subscription.created
  ✅ subscription.renewed
  ✅ subscription.cancelled
  ✅ subscription.expired
  ✅ payment.failed
  ✅ payment.succeeded
- Copy webhook secret → DODO_WEBHOOK_SECRET env var
```

---

## 8. EMAIL SETUP (Resend)

### 8.1 Configuration
1. Create account at resend.com
2. Add domain: resend.com → Add `databrief.io`
3. Add DNS records (SPF, DKIM, DMARC) in Namecheap
4. Create API key → RESEND_API_KEY env var
5. From address: `hello@databrief.io`

### 8.2 Email Templates (Transactional)
| Template | Trigger | Subject |
|---|---|---|
| Welcome | New signup | "Welcome to Databrief 👋" |
| Report Ready | Report generation completes | "Your report is ready — download now" |
| Upgrade Confirmation | Successful payment | "You're now on Databrief Pro 🎉" |
| Payment Failed | Failed charge | "Action required: Update your payment method" |
| Cancellation | Subscription cancelled | "You've cancelled Databrief Pro" |
| Scheduled Report | Auto-generated report | "[Report Name] — Your scheduled report" |

---

## 9. MONITORING

### 9.1 Sentry (Error Monitoring)
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    environment=settings.ENVIRONMENT,
    before_send=scrub_sensitive_data  # Remove API keys from events
)
```

### 9.2 Uptime Robot
```
Create 2 monitors:
1. Frontend: https://databrief.io — HTTP, every 5 min
2. Backend: https://api.databrief.io/health — HTTP, every 5 min

Alert: Email notification if down for 2+ consecutive checks
```

### 9.3 Render.com Logs
```bash
# View live logs
render logs --service databrief-api --tail

# Key log lines to watch:
# ERROR — needs immediate attention
# WARNING — AI timeouts, rate limits
# INFO — normal report generation activity
```

---

## 10. LOCAL DEVELOPMENT SETUP

### 10.1 Prerequisites
```bash
node >= 20.0.0
python >= 3.11
git
```

### 10.2 Setup Steps
```bash
# Clone repo
git clone https://github.com/deepanshu0110/databrief.git
cd databrief

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your dev Supabase + test Dodo keys
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env
# Fill in .env with VITE_SUPABASE_URL etc.
npm run dev  # Runs on http://localhost:5173
```

### 10.3 Development vs Production Differences
| Setting | Development | Production |
|---|---|---|
| CORS origins | localhost:5173 added | Only databrief.io |
| AI calls | Real (use test key) | Real (user's key) |
| Dodo Payments | Test mode | Live mode |
| Sentry | Disabled | Enabled |
| Log level | DEBUG | INFO |
| HTTPS | HTTP (localhost) | HTTPS enforced |

---

## 11. DEPLOYMENT CHECKLIST (Pre-Launch)

- [ ] All 8 env vars set on Render.com
- [ ] All 4 env vars set on Vercel
- [ ] Database migrations run on production Supabase
- [ ] Auth trigger (`000_create_auth_trigger.sql`) confirmed active
- [ ] Storage buckets created + policies set
- [ ] Google OAuth redirect URI set to production URL
- [ ] Dodo Payments webhook pointing to production URL
- [ ] Custom domain `databrief.io` connected to Vercel
- [ ] Custom domain `api.databrief.io` connected to Render
- [ ] SSL certificates active on both domains
- [ ] Uptime Robot monitors active
- [ ] Sentry project created + DSN set
- [ ] Resend domain verified + email templates created
- [ ] CI/CD pipelines tested with a dummy commit
- [ ] /health endpoint returning 200
- [ ] End-to-end test: signup → upload → generate → download PDF
- [ ] Payment test: upgrade to Pro → verify tier changes → cancel

---

## 12. DOCKERFILE (Backend)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for matplotlib, reportlab, cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libfreetype6-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create temp directory
RUN mkdir -p /tmp/databrief

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 13. ALEMBIC.INI

```ini
[alembic]
script_location = migrations
prepend_sys_path = .

# SQLAlchemy async URL — reads from env
sqlalchemy.url = postgresql+asyncpg://%(SUPABASE_DB_USER)s:%(SUPABASE_DB_PASSWORD)s@%(SUPABASE_DB_HOST)s:%(SUPABASE_DB_PORT)s/%(SUPABASE_DB_NAME)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Add these to backend .env for Alembic direct DB access:
```bash
SUPABASE_DB_HOST=db.xxxx.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-db-password
```

---

## 14. ENV EXAMPLE FILES

### backend/.env.example
```bash
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_DB_HOST=db.xxxx.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-db-password

# Encryption (generate with: python -c "import secrets; print(secrets.token_hex(32))")
MASTER_ENCRYPTION_KEY=64-hex-char-string-here

# Dodo Payments
DODO_API_KEY=your-dodo-api-key
DODO_WEBHOOK_SECRET=your-webhook-secret
DODO_PRO_PRODUCT_ID=prod_xxx
DODO_AGENCY_PRODUCT_ID=prod_xxx

# Email
RESEND_API_KEY=re_xxx
FROM_EMAIL=hello@databrief.io

# App
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
SECRET_KEY=random-64-char-string
TEMP_DIR=/tmp/databrief

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Sentry (leave blank in dev)
SENTRY_DSN=
```

### frontend/.env.example
```bash
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
VITE_API_BASE_URL=http://localhost:8000
VITE_DODO_CLIENT_TOKEN=dodo_client_xxx
VITE_ENVIRONMENT=development
```

---

## 15. FRONTEND INDEX.HTML (Inter Font + Meta Tags)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Databrief — AI Report Generator</title>
  <meta name="description" content="Turn raw data into client-ready PDF reports in 2 minutes. AI-powered insights, auto charts, custom branding." />
  <meta property="og:title" content="Databrief — AI Report Generator" />
  <meta property="og:description" content="Upload CSV → AI insights + charts → branded PDF. In 2 minutes." />
  <meta property="og:image" content="/og-image.png" />
  <link rel="icon" type="image/svg+xml" href="/favicon.ico" />

  <!-- Inter font from Google Fonts (covers all weights needed) -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

---

## 16. PYTEST CONFTEST.PY

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.core.config import settings

TEST_USER_ID = "test-user-uuid-1234"
TEST_USER_EMAIL = "test@databrief.io"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def client():
    """Async test client — no real DB, mocked Supabase"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def auth_headers():
    """Returns headers with a mock JWT for testing protected endpoints"""
    # In tests, mock the JWT verification dependency
    return {"Authorization": "Bearer test-jwt-token"}

@pytest.fixture
def sample_csv_path(tmp_path):
    """Creates a sample CSV file for upload tests"""
    csv_content = "date,revenue,churn_rate,region\n2024-01-01,45000,0.05,North\n2024-02-01,52000,0.08,North\n"
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)
```
*End of DEP*

---

## 17. VITE.CONFIG.TS (Frontend)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
          supabase: ['@supabase/supabase-js'],
        },
      },
    },
  },
})
```

---

## 18. TAILWIND.CONFIG.TS (Frontend)

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Match FSD design system exactly
        accent: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          light: '#EEF2FF',
        },
        brand: {
          bg: '#FFFFFF',
          subtle: '#F9FAFB',
          muted: '#F3F4F6',
          border: '#E5E7EB',
        },
        chart: {
          1: '#6366F1',
          2: '#10B981',
          3: '#F59E0B',
          4: '#EF4444',
          5: '#3B82F6',
          6: '#8B5CF6',
          7: '#EC4899',
          8: '#14B8A6',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
```

Add `tailwindcss-animate` to package.json devDependencies:
```json
"tailwindcss-animate": "^1.0.7"
```

---

## 19. ALEMBIC MIGRATIONS/ENV.PY

```python
# backend/migrations/env.py
# Uses SYNC psycopg2 driver — Alembic does not support asyncpg without complex setup
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import load_dotenv

load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build SYNC connection URL for Alembic (psycopg2, not asyncpg)
DB_URL = (
    f"postgresql+psycopg2://"
    f"{os.environ['SUPABASE_DB_USER']}:{os.environ['SUPABASE_DB_PASSWORD']}"
    f"@{os.environ['SUPABASE_DB_HOST']}:{os.environ['SUPABASE_DB_PORT']}"
    f"/{os.environ['SUPABASE_DB_NAME']}"
)
config.set_main_option("sqlalchemy.url", DB_URL)

# Import all models so Alembic detects them
from app.models.user import User
from app.models.report import Report
from app.models.template import Template
from app.models.workspace import Workspace
from app.core.database import Base
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## 20. GITHUB ACTIONS SECRETS — COMPLETE LIST

Configure ALL of these in GitHub → Settings → Secrets → Actions:

| Secret Name | Value | Used By |
|---|---|---|
| `SUPABASE_URL` | https://xxxx.supabase.co | Backend CI tests |
| `SUPABASE_SERVICE_KEY` | eyJhbGc... | Backend CI tests |
| `MASTER_ENCRYPTION_KEY` | 64 hex chars | Backend CI tests |
| `RENDER_DEPLOY_HOOK_URL` | https://api.render.com/deploy/srv-xxx?key=xxx | Backend deploy trigger |
| `VITE_SUPABASE_URL` | https://xxxx.supabase.co | Frontend CI build |
| `VITE_SUPABASE_ANON_KEY` | eyJhbGc... | Frontend CI build |
| `VITE_API_BASE_URL` | https://api.databrief.io | Frontend CI build |

**How to get RENDER_DEPLOY_HOOK_URL:**
Render.com → Your Service → Settings → Deploy Hook → Copy URL
