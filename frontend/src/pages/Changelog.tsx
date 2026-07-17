import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'

const entries = [
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
          <p className="text-xs text-gray-400">
            Made in India 🇮🇳 · Naxely &copy; 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
