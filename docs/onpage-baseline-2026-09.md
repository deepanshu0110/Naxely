# On-Page Baseline — 2026-09-07

**Source:** live fetch `https://www.naxely.com<route>` via `requests.get` with desktop User-Agent, `200` for all 21 routes. **Method:** full-HTML counts vs article-body (`<article>`). Title/meta from `<title>` and `meta[name=description]` exact, character counts via `len(string)`. Headings/images/links via regex `<h1|h2|h3|img|a>`. Canonical via `link[rel=canonical]`. Date: 2026-09-07.

**Routes audited:** 21 = 13 blog (`/blog` + 12 posts) + 8 compare. Excludes `/login`, `/signup`, `/pricing`, `/faq`, `/terms`, etc. per scope. Full route table from `frontend/src/App.tsx:103-158` — 58 paths, filtered to blog/compare.

| Route | Title (chars) | Meta desc (chars) | H1 | H2 | H3 | Images | Internal links (art / full) | Word count (art / full) | Canonical OK | Target keyword (if known) | GSC position (if known) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| /blog | Blog — Naxely (13) | Learn about AI-powered PDF report generation, BYOK pricing, and tips for automat… (118) | 1 | 20 | 0 | 0 | 39 / 39 | 1024 / 1024 | yes | blog hub | — |
| /blog/byok-ai-reporting-tool | BYOK AI Reporting Tool: Bring Your Own Key Explained (52) | What BYOK means for AI reporting tools, why it saves money, and how Naxely lets … (157) | 1 | 6 | 0 | 3 | 6 / 31 | 808 / 1215 | yes | byok ai reporting | — |
| /blog/csv-to-pdf-report-generator | CSV to PDF Report Generator with AI Insights \| Naxely (53) | Convert CSV files into branded PDF reports with AI-written insights and charts … (160) | 1 | 7 | 0 | 3 | 12 / 37 | 855 / 1262 | yes | csv to pdf | — |
| /blog/white-label-client-reporting-agencies | White Label Client Reporting for Agencies \| Naxely (50) | Why agency reporting tools built for ad-platform connectors don't fit any-data client reporting — and what BYOK, white-label pricing looks like instead. (152) | 1 | 7 | 1 | 3 | 8 / 33 | 1213 / 1664 | yes | white label reporting | — |
| /blog/automating-client-reports | Automated Client Reporting for Freelancers \| CSV to PDF in 60s (62) | Upload a CSV or Google Sheet, get a branded AI-narrated PDF client report in und… (159) | 1 | 10 | 8 | 3 | 15 / 40 | 2308 / 3283 | yes | automated client reporting | — |
| /blog/client-reporting-software-guide | Best Client Reporting Software: Compare 6 Tools for Agencies (60) | Compare 6 client reporting tools: file-based vs connector-based, pricing, AI ins… (140) | 1 | 13 | 13 | 3 | 25 / 50 | 5492 / 7040 | yes | client reporting software | — |
| /blog/best-client-reporting-software-freelancers | Best Client Reporting Software for Freelancers (2026) (53) | Best client reporting software for freelancers depends on your data source. Comp… (157) | 1 | 10 | 10 | 3 | 10 / 35 | 3466 / 4659 | yes | best client reporting software freelancers | — |
| /blog/python-csv-to-pdf-reports | Python CSV to PDF Reports: DIY vs. Using a Tool (47) | Practical look at building CSV-to-PDF reports in Python vs. using a report gener… (154) | 1 | 4 | 0 | 3 | 4 / 29 | 749 / 1159 | yes | python csv to pdf | — |
| /blog/two-weeks-building-naxely | Two Weeks Building a Client-Reporting Tool \| Naxely (51) | The real bugs, numbers, and decisions from the first two weeks after Naxely … (75) | 1 | 5 | 0 | 3 | 4 / 29 | 750 / 1152 | yes | — | — |
| /blog/what-should-client-report-include-checklist | What Should a Client Report Include? (Checklist) — Naxely (57) | A practical checklist for what belongs in a client-facing data report — from exe… (133) | 1 | 8 | 4 | 3 | 5 / 30 | 665 / 1314 | yes | what should client report include | — |
| /blog/anomaly-detection-in-client-reports | What Naxely's Anomaly Detection Catches (And What Doesn't) (58) | How Naxely's anomaly detection flags outliers using z-score thresholds, the filtering that keeps flags useful, and the honest limitations. (138) | 1 | 4 | 0 | 3 | 5 / 30 | 852 / 1263 | yes | anomaly detection | — |
| /blog/google-sheets-client-reports | How Naxely Keeps Google Sheets Reports Current (46) | How Naxely keeps recurring client reports current from a connected Google Sheet … (142) | 1 | 4 | 0 | 3 | 5 / 30 | 705 / 1116 | yes | google sheets client reports | — |
| /blog/excel-to-pdf-report-generator | Excel to PDF Report Generator with AI Insights \| Naxely (55) | Convert Excel workbooks into branded PDF reports with AI-written insights and ch… (151) | 1 | 5 | 3 | 3 | 5 / 30 | 1083 / 1702 | yes | excel to pdf | — |
| /compare/agencyanalytics | Naxely: The Free Alternative to AgencyAnalytics for Client Reporting (68) | Looking for an agency analytics alternative? Naxely is a free CSV-to-PDF report … (159) | 1 | 6 | 4 | 3 | 16 / 41 | 967 / 1507 | yes | agency analytics alternative | — |
| /compare/databox | Naxely vs Databox: Which Reporting Tool Fits Your Workflow? (59) | Naxely vs Databox: Naxely turns uploaded data into branded PDFs in under a minut… (138) | 1 | 4 | 3 | 3 | 4 / 29 | 511 / 976 | yes | databox alternative | — |
| /compare/powerdrill | Naxely vs Powerdrill: Purpose-Built Client Reports vs. AI Data Analysis Platform (80) | Compare Naxely and Powerdrill. Naxely is a PDF generator for client deliverables… (150) | 1 | 4 | 4 | 3 | 5 / 30 | 730 / 1259 | yes | powerdrill alternative | — |
| /compare/dashthis | Naxely vs DashThis: Simple Client Reports vs. Marketing Dashboards (66) | Compare Naxely and DashThis. Naxely turns uploaded CSVs into branded PDFs in und… (154) | 1 | 4 | 4 | 3 | 4 / 29 | 732 / 1323 | yes | dashthis alternative | — |
| /compare/whatagraph | Naxely vs Whatagraph: CSV-to-PDF Reports vs. Multi-Channel Dashboard (68) | Compare Naxely and Whatagraph. Naxely turns CSVs into branded PDFs in under a mi… (153) | 1 | 4 | 5 | 3 | 4 / 29 | 931 / 1532 | yes | whatagraph alternative | — |
| /compare/klipfolio | Naxely vs Klipfolio: PDF Reports vs. Live Dashboards (52) | Naxely vs Klipfolio: Naxely turns uploaded data into branded PDFs in under a min… (149) | 1 | 4 | 3 | 3 | 4 / 29 | 507 / 967 | yes | klipfolio alternative | — |
| /compare/bonsai | Naxely vs Bonsai: PDF Reports vs. Business Suite (48) | Naxely vs Bonsai: Naxely turns uploaded data into branded PDFs in under a minute… (147) | 1 | 5 | 3 | 3 | 4 / 29 | 702 / 1204 | yes | bonsai alternative | — |
| /compare/plutio | Naxely vs Plutio: PDF Reports vs. All-in-One Platform (53) | Naxely vs Plutio: Naxely turns uploaded data into branded PDFs in under a minute… (153) | 1 | 5 | 3 | 3 | 4 / 29 | 706 / 1205 | yes | plutio alternative | — |

**Method notes:** counts via `re.findall(r'<h2[^>]*>', html)` etc.; word count via `re.findall(r'\w+', re.sub(r'<[^>]+>',' ', html))`; internal links = `href` starting with `/` or containing `naxely.com`. All 21 fetched `200`. No `404`.

### Task 5 — Flags (not fixes)

- **Missing/empty meta:** none — all 21 have non-empty `<title>` and `meta description`.
- **0 internal links (article):** none — min is `4` (`/blog/python-csv-to-pdf-reports`, `/compare/*` pages).
- **Title >60 chars:** 6 flagged — `/blog/automating-client-reports` 62, `/compare/agencyanalytics` 68, `/compare/powerdrill` 80, `/compare/dashthis` 66, `/compare/whatagraph` 68 (already reviewed in prior phase, `Automated Client Reporting for Freelancers | CSV to PDF in 60s` intentionally 62 for CTR, `Powerdrill` 80 is long but descriptive — not urgent).
- **Description >155 chars:** 6 flagged — `/blog/byok-ai-reporting-tool` 157, `/blog/csv-to-pdf-report-generator` 160, `/blog/best-client-reporting-software-freelancers` 157, `/blog/automating-client-reports` 159, `/compare/agencyanalytics` 159, `/blog/white-label` 152 (borderline) — all previously reviewed, `byok` 157 and `csv-to-pdf` 160 are 2-5 chars over, not urgent.
- **Failed fetch:** none.

**Full fetch logs saved via `temp_baseline.py` output — word counts above are article-body / full-HTML pair for transparency (prior report confusion was full-HTML 7k vs article 5k).**

**GSC columns left blank — no GSC export provided in this env; to be filled when available.**

*Saved: `docs/onpage-baseline-2026-09.md` — dated 2026-09-07, re-fetch to refresh.*
