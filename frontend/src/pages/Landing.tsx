import { Link } from 'react-router-dom'
import {
  Upload,
  Settings,
  Download,
  Sparkles,
  Lightbulb,
  BarChart3,
  Palette,
  DownloadCloud,
  Link2,
  Star,
} from 'lucide-react'
import Navbar from '@/components/layout/Navbar'
import Button from '@/components/ui/Button'

const stepped = [
  {
    num: '1',
    icon: Upload,
    title: 'Upload your CSV or connect Google Sheets',
  },
  {
    num: '2',
    icon: Settings,
    title: 'Configure your report in seconds',
  },
  {
    num: '3',
    icon: Download,
    title: 'Download a professional PDF in under 2 minutes',
  },
]

const features = [
  {
    icon: Sparkles,
    title: 'AI Executive Summary',
    desc: 'Get a plain-English summary of your data, written by AI in seconds.',
  },
  {
    icon: Lightbulb,
    title: 'NRA Insight Cards',
    desc: 'Number + Reason + Action cards for every KPI your data reveals.',
  },
  {
    icon: BarChart3,
    title: 'Auto Chart Generation',
    desc: 'Bar, line, and pie charts auto-selected based on your data types.',
  },
  {
    icon: Palette,
    title: 'Custom Branding',
    desc: 'Add your logo and brand colour for professional, white-label reports.',
  },
  {
    icon: DownloadCloud,
    title: 'One-Click PDF Export',
    desc: 'Download a polished, client-ready PDF with a single click.',
  },
  {
    icon: Link2,
    title: 'Google Sheets Connector',
    desc: 'Paste a Sheets URL and Naxely pulls your data automatically.',
  },
]

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
      'Shareable links',
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
      'Full white-label reports — every trace of Naxely branding removed',
      'Priority support — direct, fast responses from the founder',
    ],
    cta: 'Upgrade to Agency',
    ctaVariant: 'ghost' as const,
    href: '/settings?tab=billing',
  },
]

const testimonials = [
  {
    quote: 'Coming soon — be the first to review',
    name: '—',
    role: '—',
    company: '—',
  },
  {
    quote: 'Coming soon — be the first to review',
    name: '—',
    role: '—',
    company: '—',
  },
  {
    quote: 'Coming soon — be the first to review',
    name: '—',
    role: '—',
    company: '—',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-paper text-ink">
      <Navbar />

      {/* ── Hero ── */}
      <section
        className="px-6 py-24 dark:[--dot-color:#D97A3410]"
        style={{
          backgroundImage:
            'radial-gradient(circle, var(--dot-color, #D97A3422) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
      >
        <div className="relative mx-auto flex max-w-6xl items-center gap-12">
          <div className="flex-1">
            <h1 className="font-display text-4xl font-bold leading-tight tracking-tight text-ink dark:text-gray-100 sm:text-5xl">
              Turn raw data into a client-ready report in 2&nbsp;minutes
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg text-gray-500 dark:text-gray-400">
              Upload a CSV, get an AI-powered PDF report with insights, charts,
              and recommendations. No design skills needed.
            </p>
            <Link to="/signup">
              <Button variant="primary" className="mt-10 px-8 py-3.5 text-base">
                Start Free — No credit card required
              </Button>
            </Link>
            <p className="mt-4 text-sm text-gray-400 dark:text-gray-500">
              Join consultants and agencies worldwide
            </p>
          </div>
          <div className="hidden flex-1 lg:block">
            <div className="rounded-xl border border-amber-200/40 dark:border-amber-900/40 bg-paper p-4 shadow-lg">
              <div className="mb-3 flex items-center gap-2 border-b border-amber-200/20 dark:border-amber-900/20 pb-3">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-red-400 dark:bg-red-600" />
                  <div className="h-2.5 w-2.5 rounded-full bg-yellow-400 dark:bg-yellow-600" />
                  <div className="h-2.5 w-2.5 rounded-full bg-green-400 dark:bg-green-600" />
                </div>
                <div className="text-xs font-medium text-gray-400 dark:text-gray-500">report_preview.pdf</div>
              </div>
              <div className="overflow-hidden rounded-md bg-paper">
                <div className="h-3 rounded-t-md bg-amber-500" />
                <div className="space-y-2.5 p-3">
                  <div className="flex h-7 items-end gap-1.5">
                    <div className="w-2.5 rounded-sm bg-amber-500" style={{ height: '37%' }} />
                    <div className="w-2.5 rounded-sm bg-amber-500" style={{ height: '60%' }} />
                    <div className="w-2.5 rounded-sm bg-amber-500" style={{ height: '83%' }} />
                  </div>
                  <div className="h-px bg-gray-300" />
                  <div className="font-display text-[10px] font-bold uppercase tracking-tight text-gray-500">Revenue</div>
                  <div className="font-display text-lg font-bold leading-tight text-ink">$1,900</div>
                  <div className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-mint">
                    <svg width="8" height="8" viewBox="0 0 10 10" fill="none"><path d="M5 1 L9 9 L1 9 Z" fill="#0E9F6E" /></svg>
                    +90%
                  </div>
                  <div className="flex h-6 items-end gap-1 pt-1">
                    <div className="flex-1 rounded-t-sm bg-amber-500/20" style={{ height: '40%' }} />
                    <div className="flex-1 rounded-t-sm bg-amber-500/30" style={{ height: '55%' }} />
                    <div className="flex-1 rounded-t-sm bg-amber-500/40" style={{ height: '70%' }} />
                    <div className="flex-1 rounded-t-sm bg-amber-500/50" style={{ height: '85%' }} />
                    <div className="flex-1 rounded-t-sm bg-amber-500/60" style={{ height: '100%' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how-it-works" className="bg-slate px-6 py-20" style={{ backgroundImage: 'radial-gradient(circle, #D97A3411 1px, transparent 1px)', backgroundSize: '28px 28px' }}>
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display mb-14 text-center text-2xl font-bold text-ink">
            How it works
          </h2>
          <div className="grid gap-10 md:grid-cols-3">
            {stepped.map((s) => (
              <div key={s.num} className="text-center">
                <span className="font-display text-5xl font-bold text-amber-200/60">
                  {s.num}
                </span>
                <div className="mx-auto mt-4 flex h-14 w-14 items-center justify-center rounded-xl bg-amber-50">
                  <s.icon className="h-7 w-7 text-amber-500" />
                </div>
                <h3 className="mt-4 text-base font-semibold text-ink">
                  {s.title}
                </h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Grid (bento) ── */}
      <section id="features" className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display mb-4 text-center text-3xl font-bold text-ink dark:text-gray-100">
            Everything you need to turn data into reports
          </h2>
          <p className="mb-16 text-center text-gray-500 dark:text-gray-400">
            Six capabilities, one seamless flow — from upload to polished PDF.
          </p>
          <div className="grid gap-4 lg:grid-cols-3">
            {features.map((f, i) => (
              <div
                key={f.title}
                className={`rounded-xl border border-amber-200/20 dark:border-amber-900/50 bg-paper dark:bg-darkBg shadow-sm ${
                  i === 0 ? 'lg:col-span-2 lg:row-span-2 p-6' : 'p-5'
                }`}
              >
                <div className="mb-3 flex items-start justify-between">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-500/10">
                    <f.icon className="h-5 w-5 text-amber-500" />
                  </div>
                  {i === 5 && (
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
                      Coming Soon
                    </span>
                  )}
                </div>
                <h3 className="font-display mb-1 text-base font-semibold text-ink dark:text-gray-100">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-gray-500 dark:text-gray-400">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing" className="bg-slate px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display mb-14 text-center text-2xl font-bold text-ink">
            Pricing
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {plans.map((p) => (
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
                <h3 className="text-lg font-semibold text-ink">
                  {p.name}
                </h3>
                <p className="mt-2">
                  <span className="font-display text-3xl font-bold tracking-tight text-ink">
                    {p.price}
                  </span>
                  <span className="text-sm text-gray-500">{p.period}</span>
                </p>
                <ul className="mt-6 space-y-3">
                  {p.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-start gap-2 text-sm text-gray-600"
                    >
                      <span className="mt-0.5 text-amber-500">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to={p.href}
                  className={`mt-8 block w-full rounded-lg py-2.5 text-center text-sm font-semibold transition ${
                    p.ctaVariant === 'filled'
                      ? 'bg-amber-500 text-white hover:bg-amber-600'
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

      {/* ── Testimonials ── */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display mb-14 text-center text-2xl font-bold text-ink">
            What our users say
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            {testimonials.map((t, i) => (
              <div
                key={i}
                className="rounded-xl bg-paper p-6 shadow-sm"
              >
                <div className="mb-3 flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <Star
                      key={j}
                      className="h-4 w-4 fill-amber-400 text-amber-400"
                    />
                  ))}
                </div>
                <p className="text-sm leading-relaxed text-gray-600">
                  "{t.quote}"
                </p>
                <div className="mt-4">
                  <p className="text-sm font-semibold text-gray-900">
                    {t.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {t.role}, {t.company}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA Banner ── */}
      <section className="bg-gray-900 px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold text-white">
            Ready to stop spending hours on reports?
          </h2>
          <p className="mt-4 text-gray-400">
            Join thousands of consultants and agencies saving time with
            Naxely.
          </p>
          <Link
            to="/signup"
            className="mt-8 inline-block rounded-lg bg-white px-8 py-3 text-sm font-semibold text-gray-900 hover:bg-gray-100"
          >
            Get started free
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-col items-center gap-6 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="font-display text-lg font-bold text-ink">Naxely</p>
              <p className="mt-1 text-sm text-gray-500">
                Turn data into insights, instantly.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-6 text-sm text-gray-500">
              <a href="#features" className="hover:text-gray-900">
                Features
              </a>
              <a href="#pricing" className="hover:text-gray-900">
                Pricing
              </a>
              <a href="#" className="hover:text-gray-900">
                Privacy Policy
              </a>
              <a href="#" className="hover:text-gray-900">
                Terms of Service
              </a>
              <a href="#" className="hover:text-gray-900">
                Contact
              </a>
            </div>
          </div>
          <p className="mt-8 text-center text-xs text-gray-400">
            Made in India 🇮🇳 · Naxely © 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
