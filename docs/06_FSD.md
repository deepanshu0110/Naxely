
# FSD — Frontend Specification Document
## Databrief: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final

---

## 1. DESIGN SYSTEM

### 1.1 Colours
```css
/* Primary Palette */
--color-bg:           #FFFFFF;
--color-bg-subtle:    #F9FAFB;
--color-bg-muted:     #F3F4F6;
--color-border:       #E5E7EB;
--color-border-hover: #D1D5DB;

/* Text */
--color-text-primary:   #111827;
--color-text-secondary: #6B7280;
--color-text-muted:     #9CA3AF;

/* Accent (Indigo) */
--color-accent:         #6366F1;
--color-accent-hover:   #4F46E5;
--color-accent-light:   #EEF2FF;

/* Semantic */
--color-success:  #10B981;
--color-warning:  #F59E0B;
--color-error:    #EF4444;
--color-info:     #3B82F6;

/* Chart Palette (8 colours for auto charts) */
--chart-1: #6366F1;
--chart-2: #10B981;
--chart-3: #F59E0B;
--chart-4: #EF4444;
--chart-5: #3B82F6;
--chart-6: #8B5CF6;
--chart-7: #EC4899;
--chart-8: #14B8A6;
```

### 1.2 Typography
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

--text-xs:   0.75rem;   /* 12px — labels, captions */
--text-sm:   0.875rem;  /* 14px — body small, table */
--text-base: 1rem;      /* 16px — body */
--text-lg:   1.125rem;  /* 18px — subheadings */
--text-xl:   1.25rem;   /* 20px — section titles */
--text-2xl:  1.5rem;    /* 24px — page titles */
--text-3xl:  1.875rem;  /* 30px — hero */
--text-4xl:  2.25rem;   /* 36px — landing hero */
```

### 1.3 Spacing (Tailwind scale)
- Use 4px base unit (Tailwind default)
- Consistent padding: p-4 (16px) for cards, p-6 (24px) for sections
- Gap between elements: gap-4 or gap-6

### 1.4 Border Radius
- Cards: rounded-xl (12px)
- Buttons: rounded-lg (8px)
- Inputs: rounded-md (6px)
- Badges: rounded-full

### 1.5 Shadows
```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
```

---

## 2. ROUTES MAP

```
/                          → Landing page (public)
/login                     → Login page (public)
/signup                    → Signup page (public)
/auth/callback             → OAuth callback handler (public) ← REQUIRED for Google OAuth
/share/:token              → Shared report view (public)

/dashboard                 → Report history (protected)
/report/new                → New report wizard (protected)
/report/:id                → Report detail + preview (protected)
/settings                  → Settings (protected)
/settings/api-key          → API key management (protected)
/settings/billing          → Billing + upgrade (protected)
/settings/branding         → Brand settings (Pro, protected)
/workspaces                → Workspace list (Agency, protected)
/workspaces/:id            → Workspace detail (Agency, protected)
/pricing                   → Pricing page (public)
/404                       → Not found page
```

**Route Guards:**
- `/dashboard` and all `/report/*` → redirect to `/login` if not authenticated
- `/settings/branding` → redirect to pricing if not Pro+
- `/workspaces` and `/workspaces/:id` → redirect to pricing if not Agency
- `/` → redirect to `/dashboard` if already authenticated
- `/auth/callback` → Supabase handles the OAuth token exchange here, then redirects to `/dashboard`

**⚠️ /auth/callback Implementation (CRITICAL for Google OAuth):**
```tsx
// src/pages/AuthCallback.tsx
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'

export default function AuthCallback() {
  const navigate = useNavigate()
  useEffect(() => {
    supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') navigate('/dashboard')
    })
  }, [navigate])
  return <div>Signing you in...</div>
}
```

---

## 3. PAGE SPECIFICATIONS

### 3.1 Landing Page (/)

**Sections (top to bottom):**

#### Navbar
- Logo (left): "Databrief" wordmark
- Links (centre): Features, Pricing, How it works
- CTA (right): "Log in" (ghost) + "Start Free" (filled indigo button)
- Sticky on scroll

#### Hero Section
- Headline: "Turn raw data into a client-ready report in 2 minutes"
- Subheadline: "Upload a CSV, get an AI-powered PDF report with insights, charts, and recommendations. No design skills needed."
- CTA: "Start Free — No credit card required" (large indigo button)
- Social proof: "Join 1,000+ consultants and agencies" (update with real numbers)
- Hero visual: Animated screenshot/mockup of a generated PDF report
- Background: White with subtle grid pattern

#### How It Works (3 steps)
- Step 1: Upload your CSV or connect Google Sheets
- Step 2: Configure your report (title, branding, sections)
- Step 3: Download your professional PDF in under 2 minutes
- Each step has icon + title + 1-line description

#### Features Grid (6 cards)
- AI Executive Summary
- NRA Insight Cards
- Auto Chart Generation
- Custom Branding
- One-Click PDF Export
- Google Sheets Connector

#### Pricing Section
(Same as /pricing page — full 3-tier table)

#### Testimonials
- 3 placeholder cards (fill with real ones post-launch)

#### Final CTA Banner
- "Ready to stop spending hours on reports?"
- Button: "Get started free"

#### Footer
- Logo, tagline
- Links: Privacy Policy, Terms of Service, Contact
- "Made in India 🇮🇳" (builds trust + community)

---

### 3.2 Login Page (/login)

**Layout:** Centered card, max-width 400px, white background

**Elements:**
- Databrief logo (top)
- Heading: "Welcome back"
- Google OAuth button (primary, full width): "Continue with Google"
- Divider: "or"
- Email input
- Password input (with show/hide toggle)
- "Forgot password?" link
- Submit button: "Log in"
- Footer: "Don't have an account? Sign up"

**Validation:**
- Email: valid format required
- Password: min 8 chars required
- Show inline errors (not toast) below each field

**On success:** Redirect to /dashboard

---

### 3.3 Signup Page (/signup)

**Same layout as login, elements:**
- Heading: "Create your account"
- Google OAuth button (primary)
- Divider: "or"
- Full name input
- Email input
- Password input (with strength indicator)
- Terms: "By signing up, you agree to our Terms of Service and Privacy Policy"
- Submit button: "Create account"
- Footer: "Already have an account? Log in"

**On success:** Show onboarding modal → redirect to /dashboard

---

### 3.4 Dashboard (/dashboard)

**Layout:** Sidebar (left, 240px) + Main content area

**Sidebar:**
- Databrief logo
- Navigation:
  - Dashboard (all tiers)
  - New Report (all tiers)
  - Templates (Pro+ only — hidden with lock icon for free)
  - Workspaces (Agency only — completely hidden for Free/Pro)
  - Settings (all tiers)
- Usage bar: "2 of 3 free reports used" (progress bar, red when at 3) — Free tier only
- Upgrade banner (if free tier): "Upgrade to Pro — Unlimited reports + AI insights"
- User avatar + name (bottom)

**Main Content:**

*Header row:*
- Title: "Your Reports"
- Button: "+ New Report" (indigo)

*If no reports (empty state):*
- Illustration (simple SVG)
- "Generate your first report"
- "Upload a CSV and get an AI-powered PDF in 2 minutes"
- Button: "Create Report"

*If reports exist:*
- Grid of ReportCards (2 columns on desktop, 1 on mobile)

**ReportCard component:**
- Title
- Template type badge (e.g., "Marketing")
- Status badge (Completed / Processing / Failed)
- Row count: "1,250 rows"
- Created date: "June 1, 2026"
- Actions: Download PDF | View | Delete (three-dot menu)

---

### 3.5 New Report Wizard (/report/new)

**Multi-step wizard with progress indicator (4 steps)**

#### Step 1: Upload Data
- Tab: "Upload CSV" | "Google Sheets" | "Paste Data"
- CSV: Drag-and-drop zone + file browser button
- Sheets: Text input for URL + "Connect" button
- Progress bar during upload
- On success: Shows file stats ("1,250 rows × 8 columns")
- "Next" button activates after successful upload

#### Step 2: Map Columns
- Table with one row per column:
  | Original Name | Display Name | Type | Include |
  |---|---|---|---|
  | col_1 | [editable input] | [dropdown: date/metric/dimension] | [toggle] |
- Sample values shown per column (3 examples)
- Auto-detected type shown with confidence indicator
- "Preview Data" section: shows first 5 rows with mapped names
- "Next" button

#### Step 3: Configure Report
- Report title input (required)
- Date range picker (from / to)
- Tone selector: Professional / Casual / Data-heavy / Story-driven (4 radio cards)
- Sections checklist (with lock icons on Pro sections for free users):
  - ✅ Key Metrics Overview (free)
  - ✅ Charts (free)
  - 🔒 Executive Summary (Pro)
  - 🔒 AI Insights (Pro)
  - 🔒 Anomaly Detection (Pro)
  - ✅ Data Table (free)
- "Next" button

#### Step 4: Branding (Pro) / Generate (Free)
- Free users: Skip branding, show "Generate Report" button directly
- Pro users:
  - Logo upload (drag-drop, max 2MB)
  - Brand colour picker
  - Company name input
  - Prepared by input
  - Preview: Mini cover page mockup updates live as they type
- "Generate Report" button (large, indigo)

**Generation Loading Screen:**
- Full-page loading with animated steps:
  1. "Parsing your data..." ✅
  2. "Generating charts..." ✅
  3. "Writing AI insights..." (spinner)
  4. "Building your PDF..." (pending)
- Estimated time countdown
- "This usually takes 30–90 seconds"
- Cancel button (if <10 seconds elapsed, warn user)

---

### 3.6 Report View (/report/:id)

**Layout:** Header + Two-panel (preview left, details right on desktop)

**Header:**
- Report title
- Status badge
- Actions: Download PDF | Download PPT (Agency) | Share | Delete

**Left Panel — Report Preview:**
- Embedded PDF viewer using `pdfjs-dist` (add to package.json: `"pdfjs-dist": "^4.4.0"`)
- Use `<iframe src={signedPdfUrl}>` as fallback on browsers where PDF.js isn't loaded
- Signed URL refreshed on page load (call GET /reports/{id} to get fresh url)

**Right Panel — Details:**
- Generation time: "Generated in 42 seconds"
- Data source: "marketing_q1.csv — 1,250 rows"
- AI Summary (if Pro): Text block
- Insight Cards (if Pro): NRA cards list
- Anomaly Alerts (if Pro): Yellow alert boxes
- Share link section (if Pro): Generate + copy link

---

### 3.7 Settings (/settings)

**Tabs:** Profile | API Key | Branding | Billing

**Profile Tab:**
- Full name input
- Email (read-only, from auth)
- Save button

**API Key Tab:**
- Current provider: "OpenAI" / "Claude" / "Not set"
- Key preview: "sk-proj-...abcd"
- Provider dropdown: OpenAI | Claude
- Key input (password field, paste only, never shows full key again)
- Save + Delete buttons
- Info box: "Your key is encrypted with AES-256. It's only used during report generation and never stored in plain text."

**Branding Tab (Pro only — locked with upgrade prompt for free):**
- Logo upload (shows current logo + replace button)
- Brand colour picker (hex input + colour swatch)
- Company name
- Save button

**Billing Tab:**
- Current plan: "Pro — $29/month"
- Next billing date: "July 15, 2026"
- Button: "Cancel Subscription" → confirmation modal
- For free users: Upgrade to Pro card + Upgrade to Agency card

---

### 3.8 Pricing Page (/pricing)

**Layout:** 3-column pricing table

**Free Column:**
- $0/month
- 3 reports/month
- CSV upload
- Basic charts (bar, line, pie)
- PDF with watermark
- Email support
- CTA: "Start Free"

**Pro Column (highlighted):**
- $29/month
- "Most Popular" badge
- Unlimited reports
- AI Executive Summary
- NRA Insight Cards
- Anomaly Detection
- Custom branding (logo + colour)
- No watermark
- Google Sheets connector
- Save templates
- Shareable links
- Priority support
- CTA: "Upgrade to Pro" → Dodo Payments checkout

**Agency Column:**
- $79/month
- Everything in Pro
- White-label reports
- 5 team seats
- Client workspaces
- PowerPoint export
- API access
- Scheduled reports
- Dedicated support
- CTA: "Upgrade to Agency" → Dodo Payments checkout

**FAQ Section below table:**
- Can I cancel anytime? Yes, cancel any time, access until end of billing period.
- Do I need a credit card for the free plan? No.
- What AI providers are supported? OpenAI and Anthropic Claude (bring your own key).
- Is my data secure? Yes — files are encrypted in transit and at rest.

---

### 3.9 Shared Report View (/share/:token)

**Public page — no auth required**
- Databrief minimal header (logo only, "Create your own report" link)
- Report title
- PDF viewer (read-only)
- Report metadata: Generated by [company name], [date]
- "Create your own report" CTA at bottom

---

## 4. COMPONENT LIBRARY

### 4.1 Shared Components

| Component | Props | Notes |
|---|---|---|
| `Button` | variant (primary/ghost/danger), size, loading, disabled | Loading state shows spinner |
| `Input` | label, error, hint, type | Always shows label above |
| `Badge` | variant (success/warning/error/info/neutral), text | Pill shape |
| `Card` | children, padding, shadow | White, rounded-xl |
| `Modal` | isOpen, onClose, title, children | Backdrop blur |
| `Tooltip` | content, children | Hover trigger |
| `Progress` | value (0-100), label, colour | Used for usage bar |
| `Spinner` | size, colour | Loading indicator |
| `EmptyState` | illustration, title, description, action | For empty lists |
| `UpgradePrompt` | feature, tier | Shows lock icon + upgrade CTA |

### 4.2 NRA Insight Card
```
┌─────────────────────────────────────────┐
│  📊 Churn Rate            HIGH PRIORITY  │
│                                          │
│  #  "Churn rate reached 8.3% in March"  │
│                                          │
│  ▶  "SMB accounts drove 73% of churns"  │
│                                          │
│  ✓  "Trigger re-engagement for SMBs     │
│      inactive 14+ days"                  │
│                                    🔴    │
└─────────────────────────────────────────┘
```
- Border colour: green (positive), red (negative), grey (neutral)
- Priority badge: high/medium/low

### 4.3 Usage Bar Component
```
Free Plan: 2 of 3 reports used this month
[████████████████░░░░░░░░] 67%
                    Upgrade for unlimited →
```
- Turns red at 3/3
- Upgrade link shown when at limit

---

## 5. STATE MANAGEMENT

### 5.1 authStore (Zustand)
```typescript
interface AuthStore {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
}
```

### 5.2 reportStore (Zustand)
```typescript
interface ReportStore {
  reports: Report[];
  currentReport: Report | null;
  uploadedFile: UploadResult | null;
  generationStatus: GenerationStatus | null;
  isGenerating: boolean;
  fetchReports: () => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  generateReport: (config: ReportConfig) => Promise<void>;
  pollStatus: (reportId: string) => Promise<void>;
  deleteReport: (reportId: string) => Promise<void>;
}
```

---

## 6. RESPONSIVE BREAKPOINTS

| Breakpoint | Width | Layout changes |
|---|---|---|
| Mobile | < 768px | Sidebar collapses to bottom nav, single column, wizard stacks |
| Tablet | 768–1024px | Sidebar icon-only, 2-col grid |
| Desktop | > 1024px | Full sidebar, 3-col grid, split panels |

---

## 7. LOADING & ERROR STATES

Every data-fetching component must show:
1. **Loading:** Skeleton loader (not spinner) for lists and cards
2. **Empty:** EmptyState component with relevant illustration
3. **Error:** Error card with retry button
4. **Success:** The actual data

Rule: Never show a blank white screen. Always show one of the 4 states above.

---

*End of FSD*


---
