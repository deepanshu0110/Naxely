import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'

export default function BlogPostTwoWeeks() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>What Two Weeks of Building a Client-Reporting Tool Actually Looked Like | Naxely</title>
        <meta name="description" content="The real bugs, numbers, and decisions from the first two weeks after Naxely's Product Hunt launch — no polish, no inflated stats." />
        <link rel="canonical" href="https://www.naxely.com/blog/two-weeks-building-naxely" />
        <meta property="og:url" content="https://www.naxely.com/blog/two-weeks-building-naxely" />
        <meta property="og:type" content="article" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="What Two Weeks of Building a Client-Reporting Tool Actually Looked Like | Naxely" />
        <meta property="og:description" content="The real bugs, numbers, and decisions from the first two weeks after Naxely's Product Hunt launch — no polish, no inflated stats." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="What Two Weeks of Building a Client-Reporting Tool Actually Looked Like | Naxely" />
        <meta name="twitter:description" content="The real bugs, numbers, and decisions from the first two weeks after Naxely's Product Hunt launch — no polish, no inflated stats." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BlogPosting","headline":"What Two Weeks of Building a Client-Reporting Tool Actually Looked Like","description":"The real bugs, numbers, and decisions from the first two weeks after Naxely's Product Hunt launch — no polish, no inflated stats.","url":"https://www.naxely.com/blog/two-weeks-building-naxely","datePublished":"2026-07-17","author":{"@type":"Person","name":"Deepanshu Garg","url":"https://www.linkedin.com/in/deepanshu-datascientist"},"publisher":{"@type":"Organization","name":"Naxely","url":"https://www.naxely.com"},"image":"https://www.naxely.com/og-image.png"})}</script>
      </Head>
      <Navbar />
      <article className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/blog" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Blog</Link>

        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-2">What Two Weeks of Building a Client-Reporting Tool Actually Looked Like</h1>
        <p className="text-xs text-gray-400 mb-10">July 17, 2026</p>

        <div className="mx-auto max-w-xl text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-5">
          <p>Most "we launched!" posts skip the part where things break. Here's the actual record: bugs found, decisions made, and the real numbers from the first two weeks after Naxely went live.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">The launch numbers, unfiltered</h2>
          <p>Naxely launched on Product Hunt on July 1, 2026. Two weeks later, here's what happened, pulled straight from the database instead of a vanity dashboard:</p>

          <ul className="list-disc pl-5 space-y-2">
            <li>6 signups (excluding the founder account)</li>
            <li>5 of those 6 generated at least one report. A bounce isn't a signup. An activated user is.</li>
            <li>1 signup, 0 reports generated. I followed up individually instead of counting it as a win.</li>
          </ul>

          <p>No "hundreds of signups" number to inflate. Six people tried it, five got value out of it on day one. That's the actual top of the funnel, and I'd rather post that than round up.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">The bugs that shipped anyway</h2>
          <p>Software ships with bugs. The difference is whether you talk about them.</p>

          <p>A BYOK key-nulling bug silently cleared a user's saved AI provider key under certain conditions. Caught before it caused a support ticket, but it's the kind of thing that matters more in a bring-your-own-key product than most, since the entire pitch is "your key stays yours."</p>

          <p>A percentage misclassification bug had columns meant to show dollar amounts rendering as percentages instead. Not a cosmetic bug. The whole point of the tool is presenting a client's numbers correctly.</p>

          <p>The Templates feature, shipped July 9, brought its own mess: an axios interceptor mismatch, an "Invalid Date" bug from double-timezone handling, a dual-state overwrite bug, and the one that actually stung, four of seven report sections rendering regardless of whether the user had toggled them off. Caught by running a 9-combination PDF test matrix before calling it done, which is the only reason I know about it instead of a user telling me.</p>

          <p>A silent toast failure meant file upload errors sometimes failed without telling the user anything went wrong. That one bothers me the most. The system looks like it's working right up until it isn't.</p>

          <p>None of this is impressive. It's just what a two-week-old product's bug list looks like when you actually write it down.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">The GA4 incident nobody saw</h2>
          <p>On July 13 I added CookieYes for cookie consent, a normal addition for a product that had been running without a proper consent platform since launch. It broke Google Analytics completely. Zero <code className="text-ink/60 dark:text-paper/60">_ga</code> cookies. Zero <code className="text-ink/60 dark:text-paper/60">/collect</code> pings. For the whole window between install and fix.</p>

          <p>The cause: a legacy consent component had been the only consent UI since July 1, and GA4 loading was gated on a localStorage key CookieYes had never heard of. Two consent systems, two sources of truth, and one quietly broke the other.</p>

          <p>I fixed it the same day. Killed the old component, rebuilt GA4 loading around CookieYes's own consent event, checked all three consent states live before calling it closed. The real lesson wasn't about GA4 specifically. It's that this kind of failure is silent by nature, and the only way to catch it fast is to check the raw network requests yourself instead of trusting that a clean deploy means working code.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">The pricing decision I'm not walking back</h2>
          <p>Every tier of Naxely, including Free, requires the user's own AI API key. No server-side fallback. That's deliberate, not something to apologize for. It means no shared-quota throttling, no AI markup hiding in the price, and nothing on my end pushing users toward heavier API usage. It also means a Free tier user has to go get a Groq or Gemini key before they can generate anything, which is real friction I accepted on purpose.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Why bother writing this down</h2>
          <p>Two weeks doesn't make a growth story. It makes a bug list and a handful of decisions that might still turn out wrong. That's what building something from zero actually looks like, before the numbers get big enough to round off the edges.</p>

          <hr className="border-gray-200 dark:border-gray-700 my-8" />

          <p className="text-sm italic text-ink/45 dark:text-paper/45">Naxely turns CSV and Google Sheets data into branded, AI-narrated PDF client reports. Built by one person, in public, bugs included.</p>

          <hr className="border-gray-200 dark:border-gray-700 my-8" />

          <p className="text-xs text-gray-400 space-x-2">
            <span>Related reading:</span>
            <Link to="/blog/csv-to-pdf-report-generator" className="text-ink/55 dark:text-paper/45 hover:text-amber-600">CSV to PDF Report Generator: Turn Spreadsheet Data Into Client-Ready Reports</Link>
            <span className="text-gray-300">·</span>
            <Link to="/blog/automating-client-reports" className="text-ink/55 dark:text-paper/45 hover:text-amber-600">Automating Client Reports: The Complete Guide</Link>
            <span className="text-gray-300">·</span>
            <Link to="/blog/byok-ai-reporting-tool" className="text-ink/55 dark:text-paper/45 hover:text-amber-600">Why BYOK AI Reporting Beats Built-In AI Markup</Link>
          </p>
        </div>
      </article>
      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs text-gray-600">Naxely &copy; 2026</p>
        </div>
      </footer>
    </div>
  )
}
