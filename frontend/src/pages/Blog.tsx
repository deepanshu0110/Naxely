import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'

interface Post {
  slug: string
  title: string
  excerpt: string
  date?: string
  label?: string
  routePrefix?: string
}

const posts: Post[] = [
  {
    slug: 'two-weeks-building-naxely',
    title: 'What Two Weeks of Building a Client-Reporting Tool Actually Looked Like',
    excerpt: 'The real bugs, numbers, and decisions from the first two weeks after Naxely\'s Product Hunt launch — no polish, no inflated stats.',
    date: 'July 17, 2026',
  },
  {
    slug: 'python-csv-to-pdf-reports',
    title: 'Python CSV to PDF Reports: The DIY Script vs. Just Using a Tool',
    excerpt: 'A practical look at building CSV-to-PDF reports in Python vs. using a report generator tool — for freelance analysts and agencies sending client reports regularly.',
    date: 'July 14, 2026',
  },
  {
    slug: 'client-reporting-software-guide',
    title: 'How to Choose Client Reporting Software',
    excerpt: 'A practical guide to choosing client reporting software: map your data sources, evaluate AI and automation, pick the right delivery method, and check white-label options before you commit.',
    label: 'Guide',
  },
  {
    slug: 'byok-ai-reporting-tool',
    title: 'Why Naxely Uses BYOK: Bring Your Own AI Key for Client Reports',
    excerpt: 'Most AI reporting tools bundle markups into your subscription. Naxely lets you bring your own key — you pay the provider directly, at cost, with zero markup.',
    date: 'July 4, 2026',
  },
  {
    slug: 'agencyanalytics',
    title: 'Naxely vs AgencyAnalytics: Which Client Reporting Tool Fits Your Workflow?',
    excerpt: 'Naxely is an AI-powered CSV-to-PDF report generator for freelancers and small agencies. AgencyAnalytics is a live marketing dashboard for multi-channel campaigns.',
    label: 'Comparison',
    routePrefix: '/compare/',
  },
  {
    slug: 'databox',
    title: 'Naxely vs Databox: Which Reporting Tool Fits Your Workflow?',
    excerpt: 'Naxely turns uploaded data into branded PDF reports in under a minute. Databox is a live KPI dashboard platform with 100+ integrations.',
    label: 'Comparison',
    routePrefix: '/compare/',
  },
  {
    slug: 'powerdrill',
    title: 'Naxely vs Powerdrill: Purpose-Built Client Reports vs. AI Data Analysis Platform',
    excerpt: 'Compare Naxely and Powerdrill. Naxely is a purpose-built AI PDF report generator for client deliverables. Powerdrill Bloom is a broader AI data analysis workspace with natural-language BI.',
    label: 'Comparison',
    routePrefix: '/compare/',
  },
  {
    slug: 'dashthis',
    title: 'Naxely vs DashThis: Simple Client Reports vs. Marketing Dashboards',
    excerpt: 'Naxely turns uploaded data into branded PDF reports in under a minute. DashThis is a customizable marketing-dashboard platform with 40+ integrations for live campaign reporting.',
    label: 'Comparison',
    routePrefix: '/compare/',
  },
  {
    slug: 'csv-to-pdf-report-generator',
    title: 'CSV to PDF Report Generator: Turn Spreadsheet Data Into Client-Ready Reports',
    excerpt: 'Not all CSV-to-PDF tools are the same. Naxely reads your data, identifies trends, builds charts, and writes plain-English insights — automatically.',
    date: 'July 4, 2026',
  },
  {
    slug: 'white-label-client-reporting-agencies',
    title: 'White-Label Client Reporting for Agencies: Why "Any-Data" Beats Another Marketing Connector',
    excerpt: 'Why agency reporting tools built for marketing connectors miss the mark for any-data client reporting — and what BYOK, white-label pricing actually looks like.',
    date: 'July 5, 2026',
  },
  {
    slug: 'automating-client-reports',
    title: 'Automating Client Reports: The Complete Guide for Freelancers and Agencies',
    excerpt: 'How to automate client reporting — from CSV exports to AI-generated insights, BYOK pricing, and choosing the right tool for freelance analysts and agencies.',
    label: 'Guide',
  },
  {
    slug: 'what-should-client-report-include-checklist',
    title: 'What Should a Client Report Actually Include? (Checklist)',
    excerpt: 'A practical checklist for what belongs in a client-facing data report — from executive summary to next steps — and what to leave out.',
    label: 'Guide',
  },
  {
    slug: 'client-reporting-for-freelance-consultants',
    title: 'Client Reporting for Freelance Consultants (Not Just Marketers)',
    excerpt: 'Most client reporting tools are built for marketing agencies with live ad accounts. Here\'s what data analysts and consultants working from spreadsheets actually need.',
    label: 'Guide',
  },
  {
    slug: 'client-reporting-tools-for-upwork-freelancer',
    title: 'Client Reporting Tools for Upwork & Freelancer.com Analysts',
    excerpt: 'Freelance platform work means switching between clients and data formats constantly. Here\'s what to look for in a reporting tool when every contract is different.',
    label: 'Guide',
  },
  {
    slug: 'client-reporting-tools-flat-pricing',
    title: 'Reporting Tools With Flat Pricing (Not Per-Client)',
    excerpt: 'Some reporting tools price by dashboard or client count, which gets expensive as you scale. Here\'s how flat-rate pricing works instead, and when each model makes sense.',
    label: 'Guide',
  },
]

export default function Blog() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Blog — Naxely</title>
        <meta name="description" content="Learn about AI-powered PDF report generation, BYOK pricing, and tips for automating client reports on the Naxely blog." />
        <link rel="canonical" href="https://www.naxely.com/blog" />
        <meta property="og:url" content="https://www.naxely.com/blog" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Blog — Naxely" />
        <meta property="og:description" content="Learn about AI-powered PDF report generation, BYOK pricing, and tips for automating client reports." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Blog — Naxely" />
        <meta name="twitter:description" content="Learn about AI-powered PDF report generation, BYOK pricing, and tips for automating client reports." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
      </Head>
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-2">Blog</h1>
        <p className="text-ink/55 dark:text-paper/45 text-sm mb-12">Product updates, guides, and thoughts on AI-powered reporting.</p>
        <div className="space-y-6">
          {posts.map((post) => (
            <Link
              key={post.slug}
              to={`${post.routePrefix || '/blog/'}${post.slug}`}
              className="block rounded-xl border border-gray-200 bg-paper p-6 transition-colors hover:border-amber-500/40 dark:border-gray-700 dark:bg-gray-800"
            >
              <p className="text-xs text-gray-400 mb-1.5">{post.label ?? post.date}</p>
              <h2 className="font-display text-lg font-semibold text-ink dark:text-paper mb-1.5">{post.title}</h2>
              <p className="text-sm text-ink/55 dark:text-paper/45 leading-relaxed">{post.excerpt}</p>
            </Link>
          ))}
        </div>
      </div>
      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs text-gray-600">Naxely © 2026</p>
        </div>
      </footer>
    </div>
  )
}
