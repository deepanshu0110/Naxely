import { Link } from 'react-router-dom'
import Navbar from '@/components/layout/Navbar'

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    highlight: false,
    features: [
      '3 reports/month',
      'CSV upload',
      'Basic charts (bar, line, pie)',
      'PDF with watermark',
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
      'NRA Insight Cards',
      'Anomaly Detection',
      'Custom branding (logo + colour)',
      'No watermark',
      'Google Sheets connector',
      'Save templates',
      'Shareable links',
      'Priority support',
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
      'White-label reports',
      'Dedicated support',
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
    a: 'Yes — the Agency plan removes all Databrief branding.',
  },
]

export default function Pricing() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <Navbar />

      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-4 text-center text-3xl font-bold text-gray-900">
            Simple, transparent pricing
          </h1>
          <p className="mb-14 text-center text-lg text-gray-500">
            Start free. Upgrade when you need more.
          </p>

          <div className="grid gap-8 md:grid-cols-3">
            {plans.map((p) => (
              <div
                key={p.name}
                className={`relative rounded-xl bg-white p-8 shadow-sm ${
                  p.highlight
                    ? 'border-2 border-indigo-500'
                    : 'border border-gray-200'
                }`}
              >
                {p.badge && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-500 px-3 py-0.5 text-xs font-semibold text-white">
                    {p.badge}
                  </span>
                )}
                <h3 className="text-lg font-semibold text-gray-900">{p.name}</h3>
                <p className="mt-2">
                  <span className="text-3xl font-bold text-gray-900">{p.price}</span>
                  <span className="text-sm text-gray-500">{p.period}</span>
                </p>
                <ul className="mt-6 space-y-3">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="mt-0.5 text-indigo-500">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to={p.href}
                  className={`mt-8 block w-full rounded-lg py-2.5 text-center text-sm font-semibold transition ${
                    p.ctaVariant === 'filled'
                      ? 'bg-indigo-500 text-white hover:bg-indigo-600'
                      : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {p.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-gray-200 bg-gray-50 px-6 py-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-10 text-center text-2xl font-bold text-gray-900">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            {faqs.map((faq) => (
              <div key={faq.q} className="rounded-xl bg-white p-6 shadow-sm">
                <h3 className="text-base font-semibold text-gray-900">{faq.q}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-5xl text-center">
          <p className="text-xs text-gray-400">
            Made in India 🇮🇳 · Databrief © 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
