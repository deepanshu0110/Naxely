import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'

const entries = [
  {
    date: 'September 25, 2026',
    title: 'Report Open Tracking',
    description: 'Shared report links now show an open count next to the Share button and on the dashboard card — an eye icon with the number of times a client has opened the link, so you can see at a glance whether your report has been read.',
  },
  {
    date: 'September 14, 2026',
    title: 'Lifecycle Re-engagement Emails',
    description: 'Naxely now sends occasional helpful emails to keep reporting on track — including a nudge when your report has gone stale. Expanded in September with stale-report reminders.',
  },
  {
    date: 'September 9, 2026',
    title: 'Clickable PDF Footer Links',
    description: 'Links in the PDF footer are now clickable, so clients reading a report on-screen can follow them directly instead of copying plain text.',
  },
  {
    date: 'September 5, 2026',
    title: 'Dashboard Data Warnings',
    description: 'The dashboard report list now flags reports built from stale Google Sheets data or multi-sheet Excel files, so data issues are visible before you even open the report.',
  },
  {
    date: 'September 3, 2026',
    title: 'Together AI + Live Key Validation',
    description: 'Together AI joins the supported bring-your-own-key providers, and API keys are now validated live when you save them — you know immediately whether a key works.',
  },
  {
    date: 'August 24, 2026',
    title: 'Stale-Data Banner',
    description: 'Reports generated from cached data — when a Google Sheet could not be refreshed at generation time — now show a clear banner in the report view, so you always know how fresh the underlying data is.',
  },
  {
    date: 'August 24, 2026',
    title: 'Mobile Navigation Drawer',
    description: 'Site navigation now collapses into a mobile drawer menu with Guides and Compare sections on small screens.',
  },
  {
    date: 'August 23, 2026',
    title: 'Excel Multi-Sheet Warning',
    description: 'Uploading an Excel workbook with more than one sheet now shows a notice naming which sheet was used, so no data is silently skipped.',
  },
  {
    date: 'August 1, 2026',
    title: 'Redesigned PDF Reports',
    description: 'Every generated report now uses a new visual system - cleaner charts, better-aligned data tables, and clearer typography throughout. You can also choose which charts appear in your report instead of Naxely picking a fixed set: Free includes 3, Pro up to 8, Agency unlimited.',
  },
  {
    date: 'July 29, 2026',
    title: 'Google Sheets Live Refresh',
    description: 'Previously, connecting a Google Sheet only pulled data once at import time — including for scheduled reports, which kept reusing that same snapshot even if the source Sheet changed. Reports now re-fetch the Sheet fresh at generation time (manual and scheduled), with a safe fallback to the last-known data if the live fetch fails.',
  },
  {
    date: 'July 8, 2026',
    title: 'Templates',
    description: 'Save and reuse report configurations. Create a template from any report\'s tone, section, and brand settings, then load it instantly when starting a new report — no need to reconfigure the same layout every time.',
  },
  {
    date: 'July 7, 2026',
    title: 'Send-to-Client Email',
    description: 'Email completed PDF reports directly to clients from inside Naxely. Add recipient email addresses and an optional message, and Naxely sends the report as a PDF attachment — no download-and-forward step needed.',
  },
  {
    date: 'June 24, 2026',
    title: 'PowerPoint Export',
    description: 'Agency-tier users can export any report as an editable PowerPoint (.pptx) presentation, with the cover, KPIs, charts, and insights carried over from the PDF.',
  },
  {
    date: 'June 24, 2026',
    title: 'Google Sheets Connector',
    description: 'Connect a Google Sheet directly as a report data source on Pro and above — paste a Sheet URL instead of exporting CSVs first.',
  },
  {
    date: 'June 24, 2026',
    title: 'Programmatic API Access',
    description: 'Agency-tier users can generate branded reports programmatically via the API, using a personal key managed from the new API Keys tab in Settings.',
  },
]

export default function Changelog() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <Head>
        <title>Changelog — Naxely</title>
        <meta name="description" content="See what's new at Naxely — the latest features, improvements, and product updates for AI-powered PDF report generation." />
        <link rel="canonical" href="https://www.naxely.com/changelog" />
        <meta property="og:url" content="https://www.naxely.com/changelog" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Changelog — Naxely" />
        <meta property="og:description" content="See what's new at Naxely — the latest features, improvements, and product updates for AI-powered PDF report generation." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Changelog — Naxely" />
        <meta name="twitter:description" content="See what's new at Naxely — the latest features, improvements, and product updates for AI-powered PDF report generation." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
      </Head>
      <Navbar />

      <section className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display mb-2 text-3xl font-bold text-ink">
          Changelog
        </h1>
        <p className="mb-14 text-sm text-gray-500">
          What's new at Naxely, in reverse chronological order.
        </p>

        <div className="space-y-10">
          {entries.map((entry) => (
            <div key={entry.title}>
              <p className="text-xs text-gray-400 mb-1">{entry.date}</p>
              <h2 className="font-display text-lg font-semibold text-ink mb-1">{entry.title}</h2>
              <p className="text-sm text-ink/55 leading-relaxed">{entry.description}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-5xl text-center">
          <p className="text-xs text-gray-600">
            Made in India 🇮🇳 · Naxely &copy; 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
