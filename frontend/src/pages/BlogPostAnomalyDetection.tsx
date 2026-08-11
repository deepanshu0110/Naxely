import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'

export default function BlogPostAnomalyDetection() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>What Naxely's Anomaly Detection Actually Catches (And What It Doesn't) | Naxely</title>
        <meta name="description" content="How Naxely's anomaly detection flags outliers in client reports using z-score > 2, the filtering that keeps flags useful, and the honest limitations you should know about." />
        <link rel="canonical" href="https://www.naxely.com/blog/anomaly-detection-in-client-reports" />
        <meta property="og:url" content="https://www.naxely.com/blog/anomaly-detection-in-client-reports" />
        <meta property="og:type" content="article" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="What Naxely's Anomaly Detection Actually Catches (And What It Doesn't) | Naxely" />
        <meta property="og:description" content="How Naxely's anomaly detection flags outliers in client reports using z-score > 2, the filtering that keeps flags useful, and the honest limitations you should know about." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="What Naxely's Anomaly Detection Actually Catches (And What It Doesn't) | Naxely" />
        <meta name="twitter:description" content="How Naxely's anomaly detection flags outliers in client reports using z-score > 2, the filtering that keeps flags useful, and the honest limitations you should know about." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BlogPosting","headline":"What Naxely's Anomaly Detection Actually Catches (And What It Doesn't)","description":"How Naxely's anomaly detection flags outliers in client reports using z-score > 2, the filtering that keeps flags useful, and the honest limitations you should know about.","url":"https://www.naxely.com/blog/anomaly-detection-in-client-reports","datePublished":"2026-08-04T00:00:00Z","author":{"@type":"Person","name":"Deepanshu Garg","url":"https://www.linkedin.com/in/deepanshu-datascientist"},"publisher":{"@type":"Organization","name":"Naxely","url":"https://www.naxely.com","sameAs":["https://www.linkedin.com/company/naxely-app","https://www.crunchbase.com/organization/naxely","https://www.producthunt.com/products/naxely"]},"image":"https://www.naxely.com/og-image.png"})}</script>
      </Head>
      <Navbar />
      <article className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/blog" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Blog</Link>

        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-2">What Naxely's Anomaly Detection Actually Catches (And What It Doesn't)</h1>
        <p className="text-xs text-gray-400 mb-10">August 4, 2026</p>

        <div className="mx-auto max-w-xl text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-5">
          <p>If you've ever sent a client report and gotten a reply asking "wait, why did this number spike?" — you already know the problem this solves. A 40-row report has outliers buried in it that you won't catch skimming the PDF before you hit send, but your client's reader might.</p>

          <p>Naxely flags those automatically. Here's exactly how it works, including the parts we haven't built yet.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">What gets flagged</h2>
          <p>Every numeric column in your report gets checked against its own mean and standard deviation. Any value sitting more than 2 standard deviations away — outside the range where roughly 95% of typical values fall — gets flagged in the report as an anomaly.</p>

          <p>Here's a real example, run against Naxely's own demo dataset:</p>

          <blockquote className="border-l-4 border-amber-500 pl-4 my-4 text-ink/70 dark:text-paper/70 italic">
            <p><strong>Revenue value 1027.00 is 3.4x the standard deviation from the mean</strong></p>
            <p>(mean 571.33, expected band 302.41–840.26)</p>
          </blockquote>

          <blockquote className="border-l-4 border-amber-500 pl-4 my-4 text-ink/70 dark:text-paper/70 italic">
            <p><strong>Profit value 837.00 is 4.8x the standard deviation from the mean</strong></p>
          </blockquote>

          <blockquote className="border-l-4 border-amber-500 pl-4 my-4 text-ink/70 dark:text-paper/70 italic">
            <p><strong>Units Sold value 5.00 is 2.5x the standard deviation from the mean</strong></p>
          </blockquote>

          <p>That first one is the clearest case: a Revenue value of 1,027 against a typical range of roughly 302–840 isn't noise — it's a real standout worth a sentence of context in your client email, whether it's good news (a big deal closed) or something to explain (a one-off invoice, a data entry correction).</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Why 2 standard deviations, specifically</h2>
          <p>Two standard deviations is the standard statistical threshold for "outside the typical range" — about the top and bottom 2.5% of values under a normal distribution combined. It's a well-established cutoff, not an arbitrary number, and it's conservative enough that it won't flag ordinary week-to-week variation as an anomaly.</p>

          <p>What actually keeps the flags useful instead of noisy is the filtering built around that threshold:</p>

          <ul className="list-disc pl-5 space-y-2">
            <li>Only numeric columns are checked — no false flags on category or date fields</li>
            <li>A column needs at least 3 data points before anomaly detection runs at all</li>
            <li>Columns with zero variance (a constant value throughout) are skipped entirely</li>
            <li>Missing values are dropped before the calculation, so gaps in your data don't distort the mean</li>
            <li>Repeated outliers in the same column are deduplicated, so one recurring issue doesn't flood the report with the same flag over and over</li>
            <li>The report caps out at 10 flags total, so even a genuinely messy dataset doesn't turn the Anomaly Flags page into a wall of noise</li>
          </ul>

          <p>The real tradeoff this creates: on a small dataset, a value sitting just outside 2 standard deviations but well short of 3 might be a borderline call — arguably worth a second look, arguably just normal variance. We chose to accept that gray area rather than tighten the threshold and risk missing genuine outliers, or loosen it and bury every report in flags that don't mean anything.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">What it doesn't do yet</h2>
          <p>Right now, anomaly flags go straight from detection into your PDF, PowerPoint export, and the in-app report view — there's no step in between where you can dismiss a false positive or add your own context before a client sees it. If Naxely flags something you already know the explanation for, that flag ships in the report as-is; you'd explain it separately, outside the tool.</p>

          <p>This is a real limitation we're aware of, not a hidden one. If you've run into this — wanting to add a note to a flagged anomaly, or clear one you already understand — that's useful signal for us, so tell us.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">What to actually do when your report flags something</h2>
          <p>A few practical habits, since the flags are automatic but the judgment call is still yours:</p>

          <ul className="list-disc pl-5 space-y-3">
            <li>
              <strong>Treat it as a pre-send checklist, not an alarm.</strong> Skim the Anomaly Flags page before sending — it's faster than re-reading every chart yourself, and it's the same 2-minute check every time regardless of dataset size.
            </li>
            <li>
              <strong>When it's a real outlier, name it in one sentence.</strong> Clients don't need a paragraph — "Revenue includes a one-time Q1 contract renewal" closes the loop faster than letting them ask.
            </li>
            <li>
              <strong>When it's noise, you'll usually know immediately.</strong> A known data-entry fix, a one-off event you already flagged internally — these don't need explaining to the client at all, just a mental note that the flag was expected.
            </li>
          </ul>

          <p>Anomaly detection isn't meant to replace your judgment about what's worth mentioning to a client — it's meant to make sure you never miss something worth a second look before the report goes out.</p>

          <hr className="border-gray-200 dark:border-gray-700 my-8" />

          <p className="text-sm text-ink/55 dark:text-paper/45"><em>Naxely turns your CSV or Google Sheet into a branded, AI-narrated PDF report in under 60 seconds — including automatic anomaly detection on every numeric column. <Link to="/blog/automating-client-reports" className="text-amber-600 hover:text-amber-700 underline">Learn more about how the full pipeline works &rarr;</Link></em></p>

          <p className="text-sm text-ink/55 dark:text-paper/45"><em>Related reading: <Link to="/blog/csv-to-pdf-report-generator" className="text-amber-600 hover:text-amber-700 underline">Converting CSVs into client-ready PDF reports</Link> <span className="text-gray-300">·</span> <Link to="/blog/google-sheets-client-reports" className="text-amber-600 hover:text-amber-700 underline">How Naxely Keeps Your Google Sheets Reports Current</Link> <span className="text-gray-300">·</span> <Link to="/blog/python-csv-to-pdf-reports" className="text-amber-600 hover:text-amber-700 underline">Generating CSV-to-PDF reports with Python</Link></em></p>
        </div>
      </article>
      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs text-gray-600">Naxely © 2026</p>
        </div>
      </footer>
    </div>
  )
}