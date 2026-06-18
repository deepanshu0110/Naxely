# PRD — Product Requirements Document
## Naxely: AI-Powered Report Generator
> Version: 1.0 | Date: June 2026 | Status: Final | Owner: Deepanshu

---

## 1. EXECUTIVE SUMMARY

### 1.1 Product Overview
Naxely is a SaaS web application that transforms raw data (CSV, Excel, Google Sheets) into professionally designed, AI-powered PDF reports in under 2 minutes. No design skills. No data science knowledge. No manual formatting.

### 1.2 Problem Statement
Freelance consultants, digital marketing agencies, and corporate analysts spend 4–8 hours per week manually building client reports in PowerPoint, Canva, or Google Slides. The process involves:
- Copying data from spreadsheets into slides
- Manually creating charts
- Writing summaries and insights by hand
- Formatting everything to look professional
- Repeating this cycle every week or month per client

This is entirely automatable. No affordable tool does it end-to-end today.

### 1.3 Solution
Upload data → configure report → download polished PDF with AI-written insights and auto-generated charts. Done in 2 minutes.

### 1.4 Product Vision
"The fastest way for any consultant or agency to turn client data into a professional report — without touching design tools or writing a single insight manually."

---

## 2. TARGET USERS

### 2.1 Primary Personas

#### Persona 1 — The Freelance Marketing Consultant
- Name: Sarah, 29, London
- Manages 6–10 clients simultaneously
- Sends weekly/monthly performance reports to each client
- Currently spends 3–4 hours per client per month on reports
- Pain: "I copy numbers from Google Ads into a slide, make a chart, write what it means. Every. Single. Month."
- Willingness to pay: $29/month without hesitation if it saves 10+ hours/month

#### Persona 2 — The Digital Marketing Agency
- Name: PixelForge Agency, 8-person team, Berlin
- Manages 20+ clients, each needing monthly reports
- Has a junior analyst who spends 2 days/month just on reports
- Pain: "We need reports that look branded and professional, not like Excel screenshots"
- Willingness to pay: $79/month for white-label + team access

#### Persona 3 — The Corporate Business Analyst
- Name: Raj, 34, Singapore
- Internal analyst presenting to leadership weekly
- Uses Excel + PowerPoint manually today
- Pain: "I spend more time formatting than actually analysing"
- Willingness to pay: $29/month if company approves (often expense-able)

### 2.2 Anti-Personas (Who This Is NOT For)
- Data scientists who want full custom analysis (use Jupyter/Python)
- Enterprise companies needing BI platforms (use Tableau/Power BI)
- Developers who want raw API access only (use OpenAI directly)
- Users with no data — this is not a report writing tool, it's a data→report tool

---

## 3. MARKET CONTEXT

### 3.1 Market Size
- Global AI SaaS market: $367.6B by 2034 (36.59% CAGR)
- RAG/AI report generation segment: ~$9.86B by 2030
- Target beachhead: 50M+ freelance consultants and 500K+ marketing agencies globally

### 3.2 Competitive Landscape

| Competitor | What They Do | Why Users Leave |
|---|---|---|
| Canva | Design tool, no data processing | Manual chart creation, no AI insights |
| Power BI | BI dashboard, no PDF flow | Too complex, requires training |
| Google Looker Studio | Free dashboards | No AI narrative, ugly PDFs, no export |
| ChatGPT | AI writing | No structured PDF, unreliable charts |
| DashThis | Marketing dashboards | Dashboard not PDF, expensive ($49+) |
| AgencyAnalytics | Agency reporting | $149/month, complex, overkill for small agencies |

### 3.3 Unique Differentiator
Naxely is the only tool that combines:
1. Raw data input (CSV/Sheets)
2. Auto chart generation
3. AI-written executive summary
4. NRA (Number + Reason + Action) insights per KPI
5. Branded PDF output
6. In one workflow, under 2 minutes, at $29/month

---

## 4. PRODUCT GOALS & SUCCESS METRICS

### 4.1 Business Goals
- Month 1: 100 signups, 10 paying users
- Month 3: 500 signups, 50 paying users ($1,450 MRR)
- Month 6: 2,000 signups, 200 paying users ($6,000+ MRR)
- Month 12: $20,000+ MRR

### 4.2 Product KPIs
| Metric | Target (Month 3) |
|---|---|
| Free → Paid conversion rate | 10%+ |
| Report generation time | < 2 minutes |
| Report generation success rate | > 98% |
| Monthly active users (MAU) | 300+ |
| Churn rate (monthly) | < 5% |
| NPS score | 50+ |

### 4.3 North Star Metric
**Reports generated per week** — this directly measures product value delivery.

---

## 5. FEATURES — COMPLETE LIST

### 5.1 Feature Tiers

#### FREE TIER — 3 reports/month
| # | Feature | Description |
|---|---|---|
| F01 | Email signup | Register with email + password |
| F02 | Google OAuth | One-click signup via Google |
| F03 | CSV upload | Upload CSV file (max 10MB) |
| F04 | Column mapper | Rename columns, mark types, exclude columns |
| F05 | Auto chart generation | Bar, line, pie — auto-selected by data type |
| F06 | Basic PDF export | PDF with Naxely watermark, no branding |
| F07 | Report history | Last 5 reports saved and downloadable |
| F08 | Usage counter | Shows "X of 3 free reports used this month" |
| F09 | Upgrade prompts | Contextual prompts when hitting limits |

#### PRO TIER — $29/month
Includes everything in Free plus:
| # | Feature | Description |
|---|---|---|
| P01 | API key settings | Enter/update OpenAI or Claude API key (encrypted) |
| P02 | AI executive summary | 150–250 word plain English summary of dataset |
| P03 | NRA insight cards | Number + Reason + Action per detected KPI |
| P04 | Anomaly detection | Flags statistical outliers with callout boxes |
| P05 | Trend detection | Identifies up/down trends, colour-coded |
| P06 | Logo upload | Upload company logo, appears on PDF cover |
| P07 | Brand colour | Set primary brand colour for charts + headers |
| P08 | Watermark removed | Clean PDF with no Naxely branding |
| P09 | Unlimited reports | No monthly report limit |
| P10 | Google Sheets connector | Paste Google Sheets URL → auto-pulls data |
| P11 | Report templates | Save report config as reusable template |
| P12 | Shareable link | Password-protected URL to share report online |
| P13 | In-browser preview | Preview full report before downloading |

#### AGENCY TIER — $79/month
Includes everything in Pro plus:
| # | Feature | Description |
|---|---|---|
| A01 | PowerPoint export | Same report exported as editable .pptx |
| A02 | Client workspaces | Separate workspace per client with own branding |
| A03 | White-label | Remove all Naxely branding from reports + app |
| A04 | Team seats | Up to 5 team members per account |
| A05 | API access | POST endpoint to trigger report generation programmatically |
| A06 | Scheduled reports | Auto-generate + email report on schedule (weekly/monthly) |
| A07 | Multi-dataset merge | Join 2–3 CSVs on common column, single report |

### 5.2 Features Explicitly NOT in MVP
- Mobile app (web only)
- Data connectors (Salesforce, HubSpot, etc.) — Phase 3
- Custom chart builder — Phase 3
- Collaborative editing — Phase 3
- Report comments — Phase 3
- Video export — never (out of scope)
- SQL database connector — Phase 3

---

## 6. USER FLOWS

### 6.1 New User Flow (First Report)
```
Land on homepage
→ Click "Start Free"
→ Sign up (email or Google)
→ Onboarding screen: "Upload your first CSV"
→ Upload CSV
→ Column mapper screen
→ Report config screen (title, date range, template)
→ Generate report (loading screen with progress)
→ In-browser preview
→ Download PDF
→ Report saved to history
```

### 6.2 Upgrade Flow
```
User hits 3-report limit
→ "You've used all 3 free reports this month" banner
→ Click "Upgrade to Pro"
→ Pricing page
→ Dodo Payments checkout
→ Payment confirmed
→ Pro features unlocked immediately
→ API key prompt: "Add your OpenAI/Claude key to unlock AI features"
```

### 6.3 Returning User Flow (Template Reuse)
```
Login
→ Dashboard
→ Click saved template
→ Upload new CSV (or reconnect Google Sheets)
→ Same config auto-applied
→ Generate report
→ Download
```

### 6.4 Agency Client Workspace Flow
```
Login (Agency tier)
→ Dashboard → "Workspaces"
→ Create new workspace: "Client: PixelForge"
→ Upload client logo + set brand colour
→ Generate all reports for that client inside this workspace
→ All reports auto-branded with client identity
```

---

## 7. REPORT STRUCTURE

### 7.1 Marketing Performance Report (Template 1 — MVP)
Sections in order:
1. **Cover Page** — Logo, report title, date range, prepared by
2. **Table of Contents** — Auto-generated
3. **Executive Summary** — AI-written, 150–250 words (Pro)
4. **Key Metrics Overview** — Top 5 KPIs as big-number callouts
5. **Charts Section** — Auto-generated charts (3–6 charts)
6. **AI Insights** — NRA cards per KPI (Pro)
7. **Anomaly Flags** — Yellow callout boxes for outliers (Pro)
8. **Trend Analysis** — Up/down trend per metric (Pro)
9. **Data Table** — Clean formatted version of raw data
10. **Recommendations** — AI-generated, editable (Pro)
11. **Appendix** — Raw data (optional, user toggle)

### 7.2 Chart Types Auto-Selected By Data
| Data Pattern | Chart Type |
|---|---|
| Date column + numeric column | Line chart |
| Categorical column + numeric column | Bar chart |
| Percentages that sum to ~100% | Pie / Donut chart |
| Two numeric columns | Scatter plot |
| One numeric column | Histogram |
| Multiple numeric columns over time | Multi-line chart |

---

## 8. CONTENT & COPY RULES

### 8.1 AI Summary Rules
- Always 150–250 words
- Written in third person ("Revenue increased..." not "Your revenue...")
- Always mentions: top performer, biggest concern, and one recommended action
- Never hallucinates — only references numbers actually in the data
- Tone matches user's selected tone (Professional / Casual / Data-heavy / Story-driven)

### 8.2 NRA Insight Format (Mandatory)
Every insight must follow exactly:
```
Number:  "Churn rate reached 8.3% in March — the highest in 6 months"
Reason:  "SMB accounts (under $500 MRR) drove 73% of all churns"
Action:  "Trigger re-engagement sequence for SMB accounts inactive 14+ days"
```

### 8.3 Anomaly Threshold
- Flag any value that is more than 2 standard deviations from the column mean
- Display as yellow callout box: "⚠️ Anomaly: [metric] on [date] was [X]x the average"

---

## 9. CONSTRAINTS

### 9.1 Hard Limits
| Constraint | Value | Reason |
|---|---|---|
| Max file upload size | 10MB | Supabase free tier storage limit |
| Max rows per CSV | 50,000 | Performance — AI processing time |
| Max columns mapped | 20 | PDF layout constraint |
| Max charts per report | 8 | PDF page count + readability |
| Max report pages | 20 | PDF generation time |
| Reports per month (Free) | 3 | Freemium conversion driver |
| Team seats (Agency) | 5 | Pricing + support complexity |
| API key length | Max 200 chars | OpenAI/Claude key standard length |
| Shareable link expiry | 30 days default | Storage cost control |

### 9.2 Browser Support
- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅
- Mobile browsers: read-only (upload + download works, editor not optimised)
- IE: not supported

### 9.3 Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigable
- Screen reader compatible (ARIA labels on all interactive elements)
- Colour contrast ratio minimum 4.5:1

---

## 10. NON-FUNCTIONAL REQUIREMENTS

| Requirement | Target |
|---|---|
| Report generation time | < 90 seconds for 10,000 rows |
| Page load time | < 2 seconds (LCP) |
| API response time (non-AI) | < 500ms |
| AI endpoint response time | < 30 seconds |
| Uptime | 99.5%+ |
| Concurrent users (free tier) | 100+ without degradation |
| PDF quality | 150 DPI for charts (web-optimised, balances quality vs file size) |

---

## 11. LAUNCH REQUIREMENTS (Definition of Done for MVP)

MVP is ready to launch when ALL of the following are true:
- [ ] Landing page live with hero, features, pricing, sign up
- [ ] Email + Google OAuth working
- [ ] CSV upload + column mapper working
- [ ] At least 3 chart types auto-generating correctly
- [ ] PDF downloading with watermark (free tier)
- [ ] Dodo Payments checkout working for Pro upgrade
- [ ] AI summary + NRA insights working with user's API key (Pro)
- [ ] Branded PDF (logo + colour) working (Pro)
- [ ] Report history saving last 5 reports
- [ ] Usage counter enforcing 3-report free limit
- [ ] Deployed on Vercel (frontend) + Render.com (backend)
- [ ] Custom domain (naxely.io) connected
- [ ] SSL certificate active
- [ ] Error monitoring active (Sentry free tier)

---

## 12. FUTURE ROADMAP (Post-MVP)

### Phase 2 (Month 2–3 after launch)
- Google Sheets live connector
- Scheduled reports (weekly/monthly auto-send)
- PowerPoint export
- Client workspaces (Agency tier)
- Additional templates: Financial, Survey, Sales Pipeline

### Phase 3 (Month 4–6 after launch)
- Data connectors (Shopify, HubSpot, Google Analytics)
- Custom chart builder
- Multi-language reports
- Report embedding (iframe)
- Mobile-optimised editor

---

*End of PRD*


---
