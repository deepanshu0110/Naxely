# Naxely Blog - Baseline, October 2026

Captured: 2026-10-17 (UTC), read-only. Re-run on 2026-11-02 and in January 2027.
Method: live HTTP checks (curl) per post + source review. Collected data in
`scratch/blog-diagnosis/raw/` (live_posts.json, article_summary.json,
inbound_content_map.json, entity_check.txt, links_and_timing.txt).

## Blog inventory

| Metric | Value |
|---|---|
| Blog posts | 12 |
| Posts reachable / in sitemap / in llms.txt / on /blog index | 12 / 12 / 12 / 12 |
| All-agree check (router, sitemap, llms.txt, index) | Yes |
| Missing from any source | None |
| `/rss.xml` | 200, valid-looking XML, 20 items = 12 posts + 8 compare pages |

## Content depth (article body words, extracted from live HTML between H1 and footer)

| Slug | Words |
|---|---|
| byok-ai-reporting-tool | 813 |
| csv-to-pdf-report-generator | 838 |
| white-label-client-reporting-agencies | 1144 |
| automating-client-reports | 2632 |
| client-reporting-software-guide | 5407 |
| best-client-reporting-software-freelancers | 3287 |
| python-csv-to-pdf-reports | 725 |
| two-weeks-building-naxely | 714 |
| what-should-client-report-include-checklist | 645 |
| anomaly-detection-in-client-reports | 795 |
| google-sheets-client-reports | 668 |
| excel-to-pdf-report-generator | 1086 |
| **Total / average** | **18754 / 1563** |
| Posts under 800 words | 5 (python, two-weeks, checklist, anomaly, google-sheets) |

## Technical health

| Metric | Value |
|---|---|
| Posts with HTTP 200 | 12/12 |
| Self-canonical | 12/12 |
| robots meta tags on posts | 0 |
| H1 count | 1 on all 12 |
| Heading skips | 0 |
| Images missing alt / dimensions | 0 / 0 |
| Mixed content | 0 |
| Broken links in article bodies | 0 (21 unique hrefs checked, all 200) |
| JSON-LD blocks invalid | 0 |
| Posts with dateModified | 2/12 (guide + freelancers, both 2026-08-11) |
| Posts with visible "Updated" date | 2/12 |
| Posts with FAQPage schema + FAQ section | 6/12 (white-label, automating, guide, freelancers, checklist, excel-to-pdf) |
| Product screenshots inside posts | 0 (each post has 3 external directory badge images in the footer) |
| og:image | og-image.png 200, 1200x630, 35885 bytes, same for all posts |
| Trailing-slash URL (`/blog/x/`) | 200 with no redirect on 12/12 (canonical still clean) |
| Uppercase path (`/Blog/x`) | 404 (acceptable) |
| Redirect chains | `http://naxely.com/...` = 2 hops (308 -> https non-www -> https www); others 1 hop |
| Soft 404 | Works (`/blog/this-does-not-exist` -> 404) |
| Sitemap lastmod staleness | automating-client-reports lastmod 2026-08-08 (edited 14+16 Sep); guide 2026-07-20 (edited 11 Sep) |
| TTFB proxy (curl, my network, Cloudflare edge) | 0.34s-0.50s across /blog + 4 sampled posts |
| HTML weight (sampled) | 24.8KB-77.6KB |
| PSI / Core Web Vitals | NOT CHECKED - free PSI API returned 429 quota exceeded on 2026-10-17 |

## Titles / descriptions

| Slug | title_len | meta_len | Flag |
|---|---|---|---|
| byok-ai-reporting-tool | 52 | 159 | - |
| csv-to-pdf-report-generator | 53 | 162 | meta >160 chars |
| white-label-client-reporting-agencies | 50 | 154 | - |
| automating-client-reports | 62 | 159 | title >60 chars |
| client-reporting-software-guide | 60 | 140 | - |
| best-client-reporting-software-freelancers | 60 | 143 | - |
| python-csv-to-pdf-reports | 47 | 156 | - |
| two-weeks-building-naxely | 51 | 131 | - |
| what-should-client-report-include-checklist | 59 | 137 | - |
| anomaly-detection-in-client-reports | 58 | 138 | - |
| google-sheets-client-reports | 46 | 144 | - |
| excel-to-pdf-report-generator | 55 | 153 | - |

## Internal links (editorial, from article bodies)

| Slug | Inbound from posts | Outbound (internal) |
|---|---|---|
| automating-client-reports | 14 (+1 homepage body) | 13 |
| byok-ai-reporting-tool | 9 | 5 |
| client-reporting-software-guide | 9 | 25 |
| csv-to-pdf-report-generator | 8 | 9 |
| white-label-client-reporting-agencies | 7 | 6 |
| google-sheets-client-reports | 5 | 5 |
| best-client-reporting-software-freelancers | 4 | 8 |
| anomaly-detection-in-client-reports | 4 | 5 |
| python-csv-to-pdf-reports | 3 | 4 |
| what-should-client-report-include-checklist | 2 | 4 |
| two-weeks-building-naxely | 0 | 4 |
| excel-to-pdf-report-generator | 0 | 5 |
| Total editorial post-to-post links | 65 | - |

Site chrome: navbar links 7 posts (guide, freelancers, automating, checklist, excel-to-pdf, python, two-weeks);
footer links 6 (no python). 5 posts appear in neither navbar nor footer:
byok, csv-to-pdf, white-label, anomaly, google-sheets. Only /blog index links all 12.

Links to the research page from blog posts: 0/12. Links to /pricing from post bodies: 1 (freelancers).
Posts linking to /compare/*: 4 (guide 12 links, freelancers 2, white-label 1, automating 1).

## In-article CTAs (anchors to /signup or naxely pricing inside article body)

| With CTA (7) | CTA count |
|---|---|
| byok, csv-to-pdf, white-label, automating, guide, checklist | 1 each |
| freelancers | 2 (naxely.com/pricing + /signup) |

Without any in-article CTA (5): python-csv-to-pdf-reports, two-weeks-building-naxely,
anomaly-detection-in-client-reports, google-sheets-client-reports, excel-to-pdf-report-generator.
(Every post still has nav/footer signup links; this counts article-body CTAs only.)

## Extractability (heuristic 0-10, see report Part 7)

Scores: byok 6, csv-to-pdf 5, white-label 6, automating 6, guide 6, freelancers 7,
python 4, two-weeks 4, checklist 5, anomaly 4, google-sheets 3, excel-to-pdf 5.
**Average: 5.1/10.** (Heuristic - not externally benchmarked.)

## Entity consistency (observed 2026-10-17)

- Homepage title: "Naxely - AI Client Report Generator (CSV & Sheets to PDF)"
- Homepage meta: "Naxely is an AI client report generator that turns CSV or Google Sheets data into branded PDF reports in under a minute..."
- llms.txt summary: "AI-powered PDF report generator. Turn CSV files and Google Sheets into branded, professional PDF reports..."
- /about H1 "About Naxely"; first line: "Naxely is built and run by one person, Deepanshu Garg, a freelance data analyst and data scientist based in India."
- Footer tagline: "Turn data into insights, instantly."
- Organization JSON-LD: name Naxely, url, logo, contactPoint hello@naxely.com, sameAs 5 URLs (no `description`, no `founder` property)
- All 12 posts: author "Deepanshu Garg" -> /about, matching visible byline
- sameAs URL reachability from curl: Product Hunt 200; LinkedIn 999; Crunchbase 403; G2 403; Trustpilot 403 (all anti-bot responses, not 404s - but AI crawlers likely blocked too)

## Robots / AI crawlers (2026-10-17)

- `User-agent: *` Allow / ; Disallow /dashboard /report/ /settings /scheduled-reports /templates
- Explicit Allow: GPTBot, Google-Extended, ChatGPT-User, PerplexityBot, ClaudeBot, Bingbot, anthropic-ai, Applebot, Applebot-Extended
- Not explicitly named (allowed via wildcard): OAI-SearchBot, Perplexity-User, Claude-SearchBot, Claude-User, CCBot, meta-externalagent
- llms.txt: lists all 12 posts + 8 compares + research page + pricing. All 12 posts present.
- Sitemap: https://www.naxely.com/sitemap.xml declared in robots.txt

## Not available this month (GSC/GA4/Clarity/Ahrefs/Bing exports missing)

Blog clicks, impressions, average position, indexed-post count, AI-feature impressions,
AI referral sessions, scroll depth, backlink domains, Bing impressions, Naxely citations in AI answers.
All recorded as "no export / not checked" in blog_diagnosis.csv. Re-baseline these numbers
as soon as Deepanshu exports the Part 0 files (list in scratch/blog-diagnosis/exports/notes.txt).

## Re-run instructions

1. Re-run `scratch/blog-diagnosis/collect.ps1`..`collect7.ps1` (read-only) and diff raw JSON against this baseline.
2. Compare: word counts, dateModified/updated lines, inline research links, CTA counts,
   inbound-link matrix, robots.txt bot list, remote content checks.
3. With the GSC/GA4 exports present next time, fill the performance columns and re-assign
   the "Working/Decaying/Invisible/Close" verdict per post (this baseline's verdicts are structural only).
