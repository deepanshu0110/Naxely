import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'

const CANONICAL = 'https://www.naxely.com/research/client-reporting-tool-pricing-2026'
const TITLE = 'Client Reporting Tool Pricing: 5, 12, 25 Clients (Oct 2026)'
const DESCRIPTION =
  "We priced 6 client reporting tools for agencies with 5, 12 and 25 clients, using each vendor's own pricing page on 7 October 2026. Three can't be priced at 25 clients without a sales call."
const H1 = 'What client reporting tools cost for 5, 12 and 25 clients'

export default function ResearchPricing2026() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>{TITLE}</title>
        <meta name="description" content={DESCRIPTION} />
        <link rel="canonical" href={CANONICAL} />
        <meta property="og:url" content={CANONICAL} />
        <meta property="og:type" content="article" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content={TITLE} />
        <meta property="og:description" content={DESCRIPTION} />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={TITLE} />
        <meta name="twitter:description" content={DESCRIPTION} />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"Client Reporting Tool Pricing (October 2026)","item":CANONICAL}]})}</script>
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"Article","headline":H1,"datePublished":"2026-10-07","dateModified":"2026-10-07","author":{"@type":"Person","name":"Deepanshu Garg","url":"https://www.naxely.com/about"}})}</script>
      </Head>
      <Navbar />
      <article className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/blog" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Blog</Link>

        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-2">{H1}</h1>
        <p className="text-xs text-gray-500 mb-6">By <Link to="/about" className="text-amber-600 hover:text-amber-700 underline">Deepanshu Garg</Link>. Prices checked on each vendor's own pricing page on 7 October 2026.</p>

        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-5">
          <p>Pricing pages show a starting price. Agencies need a different number: what the tool costs for the clients they actually have. We priced 6 client reporting tools for three agency sizes, using only what each vendor publishes.</p>

          <p><strong>Disclosure:</strong> I build Naxely, which competes with these tools. Naxely is not in the main table, because it works differently. It has its own section below, with its trade-offs.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Key findings</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li><strong>At 12 clients, the effective monthly cost on annual billing runs from $240 to $310</strong> for the three tools priced in dollars that we could compute (AgencyAnalytics, DashThis and Klipfolio). Swydo comes in at €179. Whatagraph starts at $812.</li>
            <li><strong>At 25 clients, 3 of the 6 tools cannot be priced from their public pricing page.</strong> AgencyAnalytics moves to volume pricing, Whatagraph's included credits run out, and Databox needs a custom quote.</li>
            <li><strong>The pricing model matters more than the starting price.</strong> Per-client pricing grows in a straight line. Per-dashboard pricing jumps in steps. Per-source pricing depends on how many platforms each client uses.</li>
            <li><strong>Annual billing saves 10% to 20%</strong> across the tools that offer both.</li>
          </ul>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">The assumptions</h2>
          <p>Every tool counts usage differently, so we fixed one simple agency setup:</p>
          <ul className="list-disc pl-5 space-y-2">
            <li>1 client = 1 report or dashboard per month</li>
            <li>3 data sources per client (for example GA4, Google Ads and Meta Ads)</li>
            <li>1 user seat</li>
            <li>White-label not required</li>
            <li>The cheapest plan that fits, at list price</li>
          </ul>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Effective monthly cost, billed annually</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">Tool</th>
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">Pricing model</th>
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">5 clients</th>
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">12 clients</th>
                  <th className="py-2 font-semibold text-ink dark:text-paper">25 clients</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">AgencyAnalytics</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Per client</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$100</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$240</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">Volume pricing, contact sales</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">DashThis</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Per dashboard (tiers)</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$139</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$279</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">$279</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Klipfolio</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Per dashboard (tiers)</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$190</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$310</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">$600</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Swydo</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Per data source</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">€84.50</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">€179</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">€354.50</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Databox</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Users and data sources (tiers)</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$319</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Custom quote</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">Custom quote</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Whatagraph</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Source credits</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">From $812</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">From $812</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">Not public above 50 credits</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Cost per month, billed monthly</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">Tool</th>
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">5 clients</th>
                  <th className="py-2 pr-4 font-semibold text-ink dark:text-paper">12 clients</th>
                  <th className="py-2 font-semibold text-ink dark:text-paper">25 clients</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">AgencyAnalytics</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$125</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$300</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">Volume pricing, contact sales</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">DashThis</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$164</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$324</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">$324</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Klipfolio</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$220</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$350</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">$690</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Swydo</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">€91.50</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">€186</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">€361.50</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Databox</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">$399</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">Custom quote</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">Custom quote</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-ink/80 dark:text-paper/80 font-medium">Whatagraph</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">No monthly billing</td>
                  <td className="py-2 pr-4 text-ink/55 dark:text-paper/45">No monthly billing</td>
                  <td className="py-2 text-ink/55 dark:text-paper/45">No monthly billing</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">How each number was worked out</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li><strong>AgencyAnalytics:</strong> $20 per client per month billed annually, $25 billed monthly. Unlimited data sources. Agencies with 25 or more clients get volume pricing through sales, so no public price exists at 25.</li>
            <li><strong>DashThis:</strong> 5 clients fit the Professional plan (10 dashboards, 40 sources). 12 and 25 clients fit the Business plan (25 dashboards, 100 sources). 25 clients sits exactly at the Business limit.</li>
            <li><strong>Klipfolio:</strong> 5 clients need Grow (10 dashboards), 12 need Team (20), 25 need Team+ (40). Users are unlimited on every plan.</li>
            <li><strong>Swydo:</strong> €69 a month (€62 billed annually) includes 10 data sources. Each extra source costs €4.50. 5 clients use 15 sources, so 5 extra. We assumed the same €4.50 rate under annual billing, because the page does not split it. Swydo prices in EUR for EU countries and USD elsewhere, so you may see the same numbers in dollars.</li>
            <li><strong>Databox:</strong> 15 data sources exceed Team Core (10), so 5 clients need Team Scale (30 sources, $319 billed annually). 36 sources exceed Team Scale, and the next step is a custom quote. Databox also has an Agency plan from $79 a month plus $20 per client pack. It may cost less, but the page does not say how many clients the base plan covers, so we did not price it.</li>
            <li><strong>Whatagraph:</strong> the Max plan starts at $812 a month (€699), billed annually, with 50 source credits. One credit covers one connected source. 5 and 12 clients fit inside 50 credits. 25 clients need 75, and the price of extra credits is not public.</li>
          </ul>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Where Naxely fits</h2>
          <p>Naxely costs $29 a month on Pro, with unlimited reports. That number is not comparable to the table, for three reasons:</p>
          <ol className="list-decimal pl-5 space-y-2">
            <li><strong>No live connectors.</strong> Naxely turns a CSV, Excel file or Google Sheet into a branded PDF report. You export the data from each platform yourself. The tools above pull it for you.</li>
            <li><strong>Your own AI key.</strong> Paid plans use your own key from an AI provider such as Groq, OpenAI or Gemini. Any cost from that provider is extra.</li>
            <li><strong>Branding, not full white-label, on Pro.</strong> Full white-label is on the $79 Agency plan.</li>
          </ol>
          <p>If your clients' data already lives in spreadsheets, Naxely costs less. If you want data pulled automatically from ad platforms, the tools above do something Naxely does not.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Tools we left out of the table</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li><strong>Powerdrill</strong> sells AI credits per seat, not per client or per source. Its Pro plan is $19.90 a month billed monthly. We could not turn credits into a per-client cost without guessing.</li>
          </ul>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-8">Method</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>Prices come only from each vendor's own pricing page, loaded on 7 October 2026 in a browser set to a US locale. We saved a screenshot and the page text for every figure.</li>
            <li>No review sites, aggregators or sales quotes.</li>
            <li>Promotional prices are excluded. Where a page showed a limited-time discount, we used the regular price.</li>
            <li>Where a cost needed a number the vendor does not publish, we wrote "contact sales", "custom quote" or "not public" instead of estimating.</li>
          </ul>

          <p><strong>Download the data:</strong> <a href="/research/client-reporting-tool-pricing-2026.csv" className="text-amber-600 hover:text-amber-700 underline">CSV of every plan and price</a></p>

          <p><strong>Spotted a mistake?</strong> Pricing changes often. Email <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a> and I will check it against the vendor's page and correct it within a week.</p>

          <p>Next update: January 2027.</p>

          <div className="pt-6">
            <Link to="/signup" className="inline-block rounded-lg bg-amber-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-amber-600 transition-colors">Generate your first report &mdash; free &rarr;</Link>
          </div>
        </div>
      </article>

      <Footer />
    </div>
  )
}
