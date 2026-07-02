import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function Terms() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Terms of Service — Naxely</title>
        <meta name="description" content="Naxely Terms of Service. By using Naxely, you agree to these terms. AI-powered PDF report generation for lawful business purposes." />
        <meta property="og:title" content="Terms of Service — Naxely" />
        <meta property="og:description" content="Naxely Terms of Service — usage guidelines, AI content policy, and cancellation terms." />
        <meta property="og:image" content="/og-image.png" />
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Terms of Service</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-4">
          <p>By using Naxely, you agree to these terms. Naxely provides an AI-powered PDF report generation service.</p>
          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Usage</h2>
          <p>You may use Naxely for lawful business purposes only. You retain full ownership of your data and reports.</p>
          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">AI Content</h2>
          <p>AI-generated insights are provided as-is. Review all output before sharing with clients.</p>
          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Cancellation</h2>
          <p>You may cancel your subscription at any time. Access to Pro/Agency features continues until the end of your billing period.</p>
          <p className="mt-8 text-xs text-ink/40">Last updated: June 2026</p>
        </div>
      </div>
    </div>
  )
}
