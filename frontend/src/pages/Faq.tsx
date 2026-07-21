import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'

const faqs = [
  {
    q: 'Can ChatGPT create a report?',
    a: 'ChatGPT can help write report text if you paste in your data manually, but it won\'t generate charts, pull structured data from a CSV, or produce a branded PDF you can hand to a client. Naxely connects directly to your CSV or Google Sheet, builds the charts and analysis automatically, and outputs a finished PDF — no copy-pasting data into a chat window.',
  },
  {
    q: 'How do I generate a report with AI?',
    a: 'Upload a CSV or connect a Google Sheet, map your columns, and Naxely\'s AI writes the executive summary, flags anomalies, and generates chart recommendations automatically. You review and adjust before exporting to PDF. Most reports take under a minute.',
  },
  {
    q: 'Which AI tool is free to generate reports?',
    a: 'Naxely\'s free tier includes 3 reports a month with no AI markup — you bring your own API key (BYOK), and Groq offers a free API key with no credit card required, so you can run the whole thing at zero cost.',
  },
  {
    q: 'Is there a free AI tool to generate reports without a credit card?',
    a: 'Yes. Naxely\'s free tier doesn\'t require a credit card, and if you use Groq as your AI provider, their free tier doesn\'t either. You\'ll need a Groq account to get an API key, but there\'s no payment info involved.',
  },
  {
    q: 'How can I tell if a report is AI-generated?',
    a: 'Naxely\'s reports are AI-assisted, not AI-invented — the charts and data come directly from your uploaded file, and the AI writes the narrative (executive summary, insights, recommendations) based on that real data. Nothing is fabricated; the AI is interpreting numbers you provided, not generating fictional content.',
  },
  {
    q: 'What\'s the best AI for creating client reports?',
    a: 'It depends on what you\'re optimizing for. General AI chat tools like ChatGPT are flexible but require manual data entry and don\'t produce branded PDFs. Purpose-built tools like Naxely are narrower — they\'re built specifically for turning spreadsheet data into a polished client-ready report, with charts and analysis handled automatically.',
  },
  {
    q: 'Do I need to pay for the AI, or does Naxely charge for it?',
    a: 'Naxely uses a bring-your-own-key model — you connect your own API key from a provider like Groq, OpenAI, or Gemini, and Naxely never marks up or charges extra on top of what your AI provider charges you. Most freelancers and small agencies pay very little to nothing per report, since AI providers like Groq offer generous free tiers.',
  },
  {
    q: 'Can I use AI to write a report from a Google Sheet?',
    a: 'Yes — connect your Google Sheet directly, no need to export to CSV first. Naxely reads the data, generates charts, and writes the report the same way it would from an uploaded file.',
  },
]

const faqSchemaLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqs.map(({ q, a }) => ({
    '@type': 'Question',
    name: q,
    acceptedAnswer: { '@type': 'Answer', text: a },
  })),
}

export default function Faq() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <Head>
        <title>Frequently Asked Questions — Naxely</title>
        <meta name="description" content="Answers to common questions about AI report generation, Naxely's free tier, BYOK pricing, Google Sheets integration, and more." />
        <link rel="canonical" href="https://www.naxely.com/faq" />
        <meta property="og:url" content="https://www.naxely.com/faq" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Frequently Asked Questions — Naxely" />
        <meta property="og:description" content="Answers to common questions about AI report generation, Naxely's free tier, BYOK pricing, Google Sheets integration, and more." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Frequently Asked Questions — Naxely" />
        <meta name="twitter:description" content="Answers to common questions about AI report generation, Naxely's free tier, BYOK pricing, Google Sheets integration, and more." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify(faqSchemaLd)}</script>
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"FAQ","item":"https://www.naxely.com/faq"}]})}</script>
      </Head>
      <Navbar />

      <section className="mx-auto max-w-2xl px-6 py-24">
        <h1 className="font-display mb-2 text-center text-3xl font-bold text-ink">
          Frequently Asked Questions
        </h1>
        <p className="mb-14 text-center text-sm text-gray-500">
          Everything you need to know about AI report generation and Naxely.
        </p>

        <div className="space-y-3">
          {faqs.map((faq) => (
            <details key={faq.q} className="group cursor-pointer rounded-xl border border-gray-200 bg-paper p-5">
              <summary className="flex items-center justify-between text-sm font-semibold text-ink list-none">
                {faq.q}
                <span className="text-amber-500 transition-transform group-open:rotate-180">▼</span>
              </summary>
              <p className="mt-3 text-sm text-ink/55 leading-relaxed">{faq.a}</p>
            </details>
          ))}
        </div>
      </section>

      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-5xl text-center">
          <p className="text-xs text-gray-600">
            Made in India 🇮🇳 · Naxely © 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
