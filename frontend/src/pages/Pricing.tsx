import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import Navbar from '@/components/layout/Navbar'
import Button from '@/components/ui/Button'
import api from '@/lib/axios'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    highlight: false,
    features: [
      '3 reports/month',
      'CSV upload',
      'Google Sheets connector',
      'Basic charts (bar, line, pie)',
      'PDF with watermark',
      'BYOK AI key (bring your own)',
      'Email support',
    ],
    cta: 'Start Free',
    ctaVariant: 'ghost' as const,
    href: '/signup',
  },
  {
    name: 'Pro',
    price: '$29',
    period: '/month',
    highlight: true,
    badge: 'Most Popular',
    features: [
      'Unlimited reports',
      'AI Executive Summary',
      'AI Insight Cards',
      'Anomaly Detection',
      '16 chart types',
      'Custom branding (logo + colour)',
      'No watermark',
      'Google Sheets connector',
      'Scheduled reports',
      'Shareable links',
      'BYOK AI key',
    ],
    cta: 'Upgrade to Pro',
    ctaVariant: 'filled' as const,
    href: '/settings?tab=billing',
  },
  {
    name: 'Agency',
    price: '$79',
    period: '/month',
    highlight: false,
    features: [
      'Everything in Pro',
      'PowerPoint export',
      'Full white-label reports — every trace of Naxely branding removed',
      'Programmatic API access',
      'Priority support — direct, fast responses from the founder',
    ],
    cta: 'Upgrade to Agency',
    ctaVariant: 'ghost' as const,
    href: '/settings?tab=billing',
  },
]

const faqs = [
  {
    q: 'Can I cancel anytime?',
    a: 'Yes, cancel any time — access continues until the end of your billing period.',
  },
  {
    q: 'Do I need a credit card for the free plan?',
    a: 'No. The free plan requires no payment information.',
  },
  {
    q: 'What AI providers are supported?',
    a: 'OpenAI and Anthropic Claude — bring your own API key.',
  },
  {
    q: 'Is my data secure?',
    a: 'Yes — files are encrypted in transit and at rest. CSV files are deleted immediately after your report is generated.',
  },
  {
    q: 'Can agencies white-label reports?',
    a: 'Yes — the Agency plan removes all Naxely branding.',
  },
]

export default function Pricing() {
  const { isAuthenticated } = useAuthStore()
  const [loading, setLoading] = useState<'pro' | 'agency' | null>(null)

  const handleCheckout = async (plan: 'pro' | 'agency') => {
    setLoading(plan)
    try {
      const resp = await api.post('/payments/checkout', { plan })
      const data = resp.data as { checkout_url: string }
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      } else {
        toast.success(`Upgraded to ${plan === 'pro' ? 'Pro' : 'Agency'}`)
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } }
      if (axiosErr.response?.status === 401) {
        window.location.href = '/settings?tab=billing'
        return
      }
      toast.error('Failed to start checkout. Please try again.')
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <Head>
        <title>Pricing — Naxely</title>
        <meta name="description" content="Simple, transparent pricing for Naxely. Start free, upgrade when you need more. Plans from $0 to $79/month." />
        <link rel="canonical" href="https://www.naxely.com/pricing" />
        <meta property="og:url" content="https://www.naxely.com/pricing" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Pricing — Naxely" />
        <meta property="og:description" content="Simple, transparent pricing for Naxely — Free, Pro ($29/mo), and Agency ($79/mo) plans." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Pricing — Naxely" />
        <meta name="twitter:description" content="Simple, transparent pricing for Naxely — Free, Pro ($29/mo), and Agency ($79/mo) plans." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"Pricing","item":"https://www.naxely.com/pricing"}]})}</script>
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"Can I cancel anytime?","acceptedAnswer":{"@type":"Answer","text":"Yes, cancel any time — access continues until the end of your billing period."}},{"@type":"Question","name":"Do I need a credit card for the free plan?","acceptedAnswer":{"@type":"Answer","text":"No. The free plan requires no payment information."}},{"@type":"Question","name":"What AI providers are supported?","acceptedAnswer":{"@type":"Answer","text":"OpenAI and Anthropic Claude — bring your own API key."}},{"@type":"Question","name":"Is my data secure?","acceptedAnswer":{"@type":"Answer","text":"Yes — files are encrypted in transit and at rest. CSV files are deleted immediately after your report is generated."}},{"@type":"Question","name":"Can agencies white-label reports?","acceptedAnswer":{"@type":"Answer","text":"Yes — the Agency plan removes all Naxely branding."}}]})}</script>
      </Head>
      <Navbar />

      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h1 className="font-display mb-4 text-center text-3xl font-bold text-ink">
            Simple, transparent pricing
          </h1>
          <p className="mb-14 text-center text-lg text-gray-500">
            Start free. Upgrade when you need more.
          </p>

          <div className="grid gap-8 md:grid-cols-3">
            {plans.map((p) => {
              const planKey = p.name.toLowerCase() as 'pro' | 'agency'
              return (
              <div
                key={p.name}
                className={`relative rounded-xl bg-paper p-8 shadow-sm ${
                  p.highlight
                    ? 'border-2 border-amber-500'
                    : 'border border-gray-200'
                }`}
              >
                {p.badge && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-amber-500 px-3 py-0.5 text-xs font-semibold text-white">
                    {p.badge}
                  </span>
                )}
                <h3 className="font-body text-lg font-semibold text-ink">{p.name}</h3>
                <p className="mt-2">
                  <span className="font-mono tabular-nums text-3xl font-bold text-ink">{p.price}</span>
                  <span className="text-sm text-gray-500">{p.period}</span>
                </p>
                <ul className="mt-6 space-y-3">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="mt-0.5 text-amber-500">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                {p.name === 'Free' ? (
                  <Link to={p.href} className="mt-8 block w-full rounded-lg border border-gray-300 bg-paper py-2.5 text-center text-sm font-semibold text-gray-700 transition-colors duration-150 ease-in-out hover:bg-slate focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
                    {p.cta}
                  </Link>
                ) : isAuthenticated ? (
                  <Button
                    variant="primary"
                    size="md"
                    className="mt-8 w-full justify-center"
                    loading={loading === planKey}
                    onClick={() => handleCheckout(planKey)}
                  >
                    {p.cta}
                  </Button>
                ) : (
                  <Link to="/signup" className="mt-8 block w-full rounded-lg bg-amber-500 py-2.5 text-center text-sm font-semibold text-white transition-colors duration-150 ease-in-out hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
                    {p.cta}
                  </Link>
                )}
              </div>
            )})}
          </div>
        </div>
      </section>

      <section className="border-t border-gray-200 bg-slate px-6 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="font-display mb-10 text-center text-2xl font-bold text-ink">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            {faqs.map((faq) => (
              <div key={faq.q} className="rounded-xl bg-paper p-6 shadow-sm">
                <h3 className="font-body text-base font-semibold text-ink">{faq.q}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-5xl text-center">
          <p className="text-xs text-gray-400">
            Made in India 🇮🇳 · Naxely © 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
