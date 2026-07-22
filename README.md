# Naxely — AI-Powered PDF Report Generator

**Live:** https://naxely.com

Turn raw data into client-ready PDF reports in 2 minutes. AI-powered insights, auto charts, custom branding.

## Tech Stack
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python 3.11 + SQLAlchemy + Supabase PostgreSQL
- **AI**: OpenAI GPT-4/Claude 3.5 (user's own API key)
- **Charts**: Matplotlib (PDF) + Recharts (browser)
- **PDF**: ReportLab
- **Hosting**: Vercel (frontend) + Render.com (backend)

## Quick Start

### 1. Clone repository
```bash
git clone https://github.com/deepanshu0110/Naxely.git
cd Naxely
```

### 2. Backend setup
```bash
cd backend
cp .env.example .env
# Edit .env with your Supabase and API keys
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Frontend setup
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 4. Database setup
```bash
cd backend
alembic upgrade head
```

## Deployment
- Frontend auto-deploys to Vercel on push to `main`
- Backend auto-deploys to Render.com on push to `main`

## Environment Variables
See `backend/.env.example` and `frontend/.env.example` for required variables.