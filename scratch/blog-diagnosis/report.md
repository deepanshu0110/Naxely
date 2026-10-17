# Naxely Blog Diagnosis - Phase 1 (read-only)

Date: 2026-10-17 | Scope: all 12 blog posts + /blog index + feeds + robots/llms/sitemap + entity surfaces
Method: live HTTP checks via curl (PowerShell), source review of git history/commits where relevant, comparison against the site's own pricing research CSV. No site changes were made.
Raw data: `scratch/blog-diagnosis/raw/` (live_posts.json, article_summary.json, inbound_content_map.json, entity_check.txt, links_and_timing.txt, psi/ empty - see Section 8).
Labels: **Observed** = file/command evidence cited; **Inference** = my reading of that evidence.

---

## 1. What I received

**No exports were provided.** `scratch/blog-diagnosis/exports/` was empty (the folder did not exist). The full list of what is still needed is written to `scratch/blog-diagnosis/exports/notes.txt`:

- GSC: `gsc_blog_6m`, `gsc_blog_28d_compare`, `gsc_all_6m`, `gsc_blog_16m`, `gsc_indexing`, `gsc_cwv`, `gsc_links`, `gsc_crawl_stats.png`, `gsc_query_page_pairs.csv`
- GA4: `ga4_blog_landing.csv`, `ga4_blog_sources.csv`, `ga4_blog_paths.png`, signup key-event answer
- Clarity: `clarity_blog.png` + 3 recordings
- Ahrefs: `ahrefs_backlinks.csv`, `ahrefs_top_pages.csv`
- Bing: `bing_performance.csv`, index status for 3 posts, `bing_ai.csv`
- Other: `cloudflare_ai_crawlers.png`, `ai_answers.csv`, `serp_notes.csv`

Consequence per the brief: Parts 4 and 5 (query-level and page-level performance, off-site/backlinks), Bing data, GA4/Clarity conversion data, and AI-answer citations are only described in Section 8. Everything below is what CAN be established from the live site, its files, and the repo. The CSV (42 columns per post) carries "no export / not checked" in every performance column.

## 2. Issues by severity

### High

1. **Stale competitor price on a protected page.** `/blog/client-reporting-software-guide` says "Whatagraph from €699/mo (billed annually, shown in EUR)" (Observed - article text extraction, `raw/articles/client-reporting-software-guide.txt`). Current Whatagraph Max = **€999 / from $1,118** (Observed - `frontend/public/research/client-reporting-tool-pricing-2026.csv` row 4, captured 2026-10-11; commit `496684b` updated the research page from $812 to $1,118). The post still shows the pre-increase number.
2. **Unsupported industry claim contradicted by Naxely's own research.** `/blog/white-label-client-reporting-agencies` states white-label is "often north of $150/month" and that platforms gate it behind their highest tier (Observed - article text). Naxely's own CSV contradicts this: DashThis includes white-label on all plans from $44/mo, Swydo's single plan (€69) includes full white-label, and Bonsai removes branding at $29 (Observed - CSV rows 22-31, 55-62). Inference: this is a trust and AI-citation risk - an engine that cross-checks the claim against the site's own research page finds a contradiction.
3. **Freshness signals are missing or wrong almost everywhere.** `dateModified` is absent from BlogPosting JSON-LD on 10 of 12 posts; only guide and freelancers have it (2026-08-11) - and even those do not reflect the 11 Sep edit (bf012ba). Visible "Updated" date exists on only those same 2 posts (Observed - `raw/live_posts.json`, `raw/inbound_content_map.json`). Sitemap `lastmod` is stale against actual edits: automating-client-reports 2026-08-08 (edited 14+16 Sep), guide 2026-07-20 (edited 11 Sep) (Observed - `frontend/public/sitemap.xml` vs git log). Neither Google nor AI engines have a reliable signal that these pages are maintained.
4. **No performance data exists for this diagnosis** (all Part 0 exports missing). Per the brief's small-data rule, I made no query-level claims at all. The only query-level data referenced anywhere in this report is from the earlier, separate 18 Sep-5 Oct dip investigation ("automated client reporting"), already delivered, which found no on-site cause.

### Medium

5. **Five posts under 800 article-body words** (Observed - word counts in `raw/article_summary.json`): checklist 645, google-sheets 668, two-weeks 714, python 725, anomaly 795. The other seven range 813-5,407.
6. **Five posts have no in-article CTA** (anchors to /signup or Naxely pricing inside the article body): python, two-weeks, anomaly, google-sheets, excel-to-pdf (Observed - `raw/article_summary.json`; all still have nav/footer signup links).
7. **Zero product visuals on every post.** Each post's only images are the three third-party directory badges in the shared footer; no screenshots of Naxely, no sample report images, no charts (Observed - `img_count`/images in `raw/live_posts.json`). The money pages sell a visual product while showing none of it.
8. **No blog post links to the pricing research page.** 0 of 12 (Observed - link extraction across all article bodies). Four posts quote competitor prices in text but not a single "here is our pricing study" link. The research page's only inbound links are from itself (2 nav/duplicate) and the 8 compare pages (1 each) (Observed - `raw/inbound_content_map.json`).
9. **Two near-orphan posts: 0 editorial inbound links from other posts** - `two-weeks-building-naxely` and `excel-to-pdf-report-generator` (Observed - post-to-post matrix, 65 links total). They are also the only two that appear in neither navbar nor footer (Observed - nav links 7 posts, footer 6; see baseline).
10. **Two SERP-truncation risks:** `/blog/automating-client-reports` title = 62 chars; `/blog/csv-to-pdf-report-generator` meta description = 162 chars (Observed - live HTML).
11. **Overlap pairs** (Observed - titles/H2 overlap; traffic data unavailable): (a) guide vs freelancers both carry the "best client reporting software" head term; (b) csv-to-pdf vs excel-to-pdf vs python share the file-to-PDF intent and even share page-pattern copy.
12. **Trailing-slash duplicates:** `/blog/<slug>/` returns 200 with no redirect on all 12 (canonical still points to the clean URL) (Observed - variants in `raw/live_posts.json`). Minor duplicate-URL surface.
13. **One two-hop redirect:** `http://naxely.com/...` -> 308 -> `https://naxely.com/...` -> 308 -> `https://www.naxely.com/...`; other variants are single-hop (Observed - variants). Low impact, trivial to collapse.

### Low

14. **AI-bot allowlist gaps in robots.txt** (Observed): GPTBot, Google-Extended, ChatGPT-User, PerplexityBot, ClaudeBot, Bingbot, anthropic-ai, Applebot(+-Extended) are explicitly allowed; OAI-SearchBot, Perplexity-User, Claude-SearchBot, Claude-User, CCBot and meta-externalagent are not named but are allowed by the `User-agent: *` Allow: / wildcard. No action is blocking anything today.
15. **RSS is unusual but valid:** `/rss.xml` returns 200 with 20 items - all 12 posts **and** 8 `/compare/` pages (Observed). Every post is listed; no posts missing.
16. **Entity surfaces don't share one description**, and Organization JSON-LD has no `description`/`founder` (Observed - `raw/entity_check.txt`): homepage meta says "AI client report generator...", llms.txt says "AI-powered PDF report generator...", /about says built by one person. Inference: minor entity-clarity drag for AI answers; cheap to align.
17. **sameAs profiles are mostly bot-blocked:** Product Hunt 200; LinkedIn 999; Crunchbase/G2/Trustpilot 403 to curl (Observed - anti-bot responses, not 404s). Inference: these are fine for humans but weak corroboration for AI crawlers that would otherwise verify the entity.

## 3. Opportunities by effect

Query-level opportunity sizing needs GSC (Section 8), so these are structural opportunities, ordered by expected effect per unit of effort:

1. **Freshness wiring (largest cheap win).** One mechanism change gives every future edit a correct `dateModified` + visible "updated" line + accurate sitemap `lastmod`. Effect: pages currently look untouched since Jul/Aug; after this, every edit is legible to Google and AI engines.
2. **Research-page wiring.** The pricing research page (67-row CSV, updated 11 Oct) is exactly the "evidence" asset AI engines quote - and no post links to it while 4 posts quote prices in prose. Adding contextual links from freelancers, guide, white-label, csv-to-pdf converts existing accuracy into citation surface. 0/12 today.
3. **Fix the two accuracy defects** (Whatagraph €699 -> €999/$1,118 on the guide; the $150+ claim in white-label). Small edits, removes trust/citation risk.
4. **Orphan repair + targeted internal links.** two-weeks and excel-to-pdf have 0 editorial inlinks; checklist only 2; python 3. The blog already has 65 post-to-post links, so a handful of contextual links fixes the matrix.
5. **Extractability uplift on 5 weak posts.** Average heuristic score is 5.1/10 (Section 4). Question-form H2s, real lists, one dated update line, and price-source links lift every post most cheaply.
6. **Conversion surfaces.** 5 posts with zero in-article CTA; 8/12 have no link to /pricing or the research page. For posts that already receive impressions, this is free conversion surface.
7. **Product proof.** 0 screenshots across 12 posts. One real sample-report image per money post is the single largest content-quality gap.
8. **Cluster consolidation.** The file-to-PDF trio (csv/excel/python) currently overlaps instead of interlinking as a hub-and-spokes; converting the overlap into intentional cross-links protects all three.

## 4. GEO / AEO readiness

**Crawl policy (Observed):** robots.txt allows everything public and explicitly welcomes the major AI crawlers (list in Section 2 #14). No blocking issue. CCBot (Common Crawl) is implicitly allowed - that is a licensing decision, not a bug (see Section 7).

**llms.txt (Observed):** exists, comprehensive, lists all 12 posts with one-line descriptions, all 8 compares, the research page, current pricing ($0/$29/$79). Best-in-class surface for this site size. Two nits: "AI-powered PDF report generator" vs homepage "AI client report generator" wording (entity inconsistency), and the file names 12 guides while 2 are launch/feature stories (minor).

**Extractability (heuristic 0-10, Inference from Observed signals):** average **5.1**. Per-post: freelancers 7; byok/white-label/automating/guide 6; csv-to-pdf/checklist/excel 5; python/two-weeks/anomaly 4; google-sheets 3.

Recurring blockers behind those scores:
- No visible "Updated" line: 10/12 (the 2 that have it are the 2 best-kept pages).
- Question-form H2s: strong on byok, csv-to-pdf, white-label, automating (>5 each); essentially absent on guide, freelancers, python, two-weeks, checklist, anomaly, google-sheets, excel-to-pdf - so most pages are not shaped like the questions buyers ask AI engines.
- No named external sources in any post body (Inference: external price claims are text-only; only freelancers links vendor pricing pages - 7 links).
- No FAQ content on 6 posts (present: white-label, automating, guide, freelancers, checklist, excel). Per the brief: do NOT add FAQPage schema for rich results; these are content blocks only.
- No product screenshots anywhere (Section 2 #7).
- Checklist post renders no `<ul>/<ol>` at all despite being a checklist (Observed).
- First paragraph length: csv-to-pdf 64w, guide 79w, freelancers 86w, google-sheets 68w - over the ~60-word extractability target; the rest pass (byok 45, white-label 40, automating 60, python 44, two-weeks 31, checklist 54, anomaly 50, excel 60).

**Entity (Observed, `raw/entity_check.txt`):** consistent author (Deepanshu Garg -> /about, visible byline + JSON-LD on all 12); one name/URL; but three different one-line descriptions across homepage/meta, llms.txt, /about, and Organization JSON-LD lacks `description` and `founder`. sameAs: 5 profiles, mostly anti-bot (Section 2 #17).

**AI-answer measurement (manual, pending).** `ai_answers.csv` was not provided, so I wrote the 10 buyer prompts below, derived from the posts' own question H2s (the closest available proxy to GSC question queries, per the brief's fallback). Run each in ChatGPT, Perplexity, Gemini, Copilot, and Claude, log: does Naxely appear, is it cited with a URL, is the fact correct - then repeat monthly.

1. "What's the best client reporting software for freelancers in 2026?"
2. "What should I include in a monthly client report?"
3. "How do I automate client reports from CSV files without a developer?"
4. "Is there a CSV to PDF report generator with AI insights?"
5. "How can I turn an Excel workbook into a branded PDF client report?"
6. "What's the cheapest white-label client reporting tool for a small agency?"
7. "Do client reporting tools mark up AI usage, or can I bring my own API key?"
8. "How do I keep a Google Sheets client report up to date automatically?"
9. "What is anomaly detection in a client report, and is it reliable?"
10. "Should I write a Python script or use a tool for recurring PDF client reports?"

## 5. Conversion path

Observed: 7 of 12 posts contain one in-article CTA (freelancers has two - a Naxely pricing link and a signup CTA); 5 posts (python, two-weeks, anomaly, google-sheets, excel-to-pdf) have **none** inside the body. Only 1 post (freelancers) links to /pricing from the body; 0 link to the research page; 4 link to any /compare page (guide 12 links, freelancers 2, white-label 1, automating 1). The free tier hook ("3 reports/month, no credit card") appears in the automating meta description and in freelancers; it is not a repeated pattern.

`cta_above_median_scroll` could not be assessed: Clarity screenshots/recordings and GA4 landing-page data were not provided (Section 8). Inference: the natural first CTA opportunities are (a) the checklist post's "Turning this into a repeatable process" section, (b) python's "Where a tool like Naxely fits" H2 - both currently end without a link.

## 6. Proposed action plan (max 10; nothing here has been done - Phase 1 is read-only)

Each item: effort (S/M/L) - evidence - success metric - re-check date - kill switch. Items touching protected pages are marked **[PROTECTED - needs Deepanshu ok]**.

1. **Freshness mechanism: emit `dateModified` + visible "Updated <date>" + correct sitemap lastmod.** M. Evidence: 10/12 missing, 2 stale, sitemap stale on the two Sep-edited posts. Metric: 12/12 posts show dateModified >= last content edit; sitemap lastmod matches. Check 2026-11-02. Kill switch: if JSON-LD validation breaks (schema tests) revert emit-block.
2. **Refresh the stale Whatagraph price wherever quoted.** S. Evidence: guide €699 vs current €999/$1,118 (CSV 2026-10-11). Metric: zero price strings older than the research CSV capture. Check 2026-11-02. Kill switch: revert to previous string if the research CSV changes again before launch. **[PROTECTED page (guide) - needs ok]**
3. **Correct the $150+ white-label claim** to match research (e.g. cite DashThis $44 / Swydo €69 / add-on prices). S. Evidence: Section 2 #2. Metric: claim now traceable to research CSV rows. Check 2026-11-02. Kill switch: if Deepanshu prefers to keep positioning language, replace with "add-on" wording only.
4. **Add research-page links where competitor prices appear** (freelancers first, then guide, white-label, csv-to-pdf). S. Evidence: 0/12 today; 4 posts quote prices in prose. Metric: >=4 posts link /research/client-reporting-tool-pricing-2026 in context. Check 2026-11-02. Kill switch: none needed (pure additive link) unless anchor feels forced - then skip that post.
5. **Add one in-article CTA to the 5 CTA-less posts** (natural spots: python "tool route", checklist "repeatable process", anomaly "what to do next", google-sheets "connecting a sheet", excel "What Naxely does"). S. Evidence: Section 5. Metric: 12/12 posts have >=1 in-body CTA. Check 2026-11-02. Kill switch: revert any CTA that reads promotional in context.
6. **Fix the two truncation risks** - csv-to-pdf meta to <=155 chars; automating title to <=60 chars. S. Evidence: 162 chars / 62 chars. Metric: lengths in range. Check 2026-11-02. Kill switch: keep old strings if GSC CTR (once available) worsens. **[automating is PROTECTED - needs ok]**
7. **Repair the link matrix:** add contextual links (guide/automating -> excel-to-pdf, two-weeks; csv-to-pdf <-> excel cross-links; python -> csv-to-pdf already exists). S-M. Evidence: two-weeks and excel-to-pdf have 0 editorial inlinks. Metric: 0 posts with <2 editorial inlinks. Check 2026-11-02. Kill switch: n/a (additive). **[links from guide/automating are PROTECTED - needs ok]**
8. **Extractability pass on the 5 weakest posts** (google-sheets 3, python/anomaly/two-weeks 4, checklist 5): question-form H2s, render the checklist as a real list, add one concrete sourced fact each. M. Evidence: Section 4. Metric: average extractability >= 6.5 on re-score; checklist has real ul/ol markup. Check 2026-11-30. Kill switch: keep edits additive; revert any heading change that drops an existing anchor (`#why-agencies...` anchor is in a protected page's inbound link - do not touch that heading).
9. **Add one real product screenshot per money post** (guide, freelancers, automating, csv-to-pdf; sample report + UI). M/L (assets needed). Evidence: 0 images today. Metric: >=1 in-article image on those 4; images have alt + dimensions. Check 2026-11-30. Kill switch: skip if screenshots expose client data or look unpolished.
10. **Widen explicit AI-bot allowlist** (OAI-SearchBot, Perplexity-User, Claude-SearchBot, Claude-User, meta-externalagent) and leave CCBot for a decision. S. Evidence: Section 2 #14. Metric: named in robots.txt. Check 2026-11-02. Kill switch: trivially revert; wildcard already allows everything, so no behavior change expected.

Deferred to a second wave (not in the 10): trailing-slash redirect, two-hop redirect collapse, RSS scope decision, Organization JSON-LD `description`/`founder`, description alignment across entity surfaces.

## 7. Needs Deepanshu's decision

1. **Approve edits to the three protected pages where this diagnosis found issues:** guide (Whatagraph price, research link, updated date), automating (title length, dateModified/updated line, inbound links), compare/agencyanalytics (no issues found this round - nothing proposed). Reporting only, per the rules.
2. **CCBot (Common Crawl):** currently allowed by wildcard. Allow (default) or disallow? It is a data-licensing choice, not an SEO bug.
3. **Provide the Part 0 exports** (list in `exports/notes.txt`): without GSC/GA4/Clarity/Ahrefs/Bing, no post can be ranked, no "decaying/invisible/close" verdict is possible, and the CSV's performance columns stay empty.
4. **Run the 10 AI buyer prompts** (Section 4) in the 5 chat engines and return `ai_answers.csv` - that is the only way to measure AI citations this month.
5. **GSC URL-inspection for the 12 posts** (index status + last crawl) - 5 minutes in the GSC UI, fills the `indexed_google` column.
6. **sameAs corroboration:** decide whether to add one or two openly-fetchable profile URLs (Product Hunt is already fetchable; G2/Trustpilot/Crunchbase/LinkedIn block bots) - affects how AI engines verify the entity.

## 8. Not checked (and why)

- **Google index status, impressions, clicks, positions, CTR, query-page pairs, crawl stats** - no GSC export; no GSC API access from this environment. No query-level statement is made anywhere in this report per the <20-impressions rule.
- **Bing index/performance** - no export; no API key.
- **Core Web Vitals / PSI** - attempted via the free PSI API on 2026-10-17; Google returned HTTP 429 "Quota exceeded... Queries per day" for all 5 URLs. Recorded as not checked. (Curl TTFB proxy recorded in baseline: 0.34-0.50s.) If Deepanshu wants CWV, either retry a PSI run another day or export `gsc_cwv`.
- **GA4 traffic/engagement/signup key event, Clarity scroll depth + recordings** - no export. `cta_above_median_scroll` therefore unknown.
- **Backlink domains, referring pages** - no Ahrefs export (`backlink_domains` = not checked on all rows). This also means the "AI referral sessions" column is empty.
- **AI-answer citations** - no `ai_answers.csv`; the 10 prompts in Section 4 are the substitute until then.
- **Vercel deploy history** (would have helped correlate the Sep dip) - no CLI/token in this environment; git push times remain the proxy.
- **Live AI-crawler access logs (Cloudflare)** - no screenshot provided.

## 9. Bottom line

**Biggest problem:** 10 of 12 posts carry no freshness or sourcing signals (no `dateModified`, no updated date, stale sitemap lastmods, zero links to the site's own 67-row pricing research) - so both Google and AI engines are looking at pages that claim to be July/August documents, quoting prices with no evidence trail, and five of them still end without a single CTA.

**Biggest opportunity:** everything needed to fix that is already on the site - the research page, the compare pages, the badges, the free tier - and none of it is wired into the blog; the cheapest wins (dates, research links, 5 CTAs, 2 accuracy fixes) are small, additive, and verifiable by a curl re-run on 2 Nov 2026.
