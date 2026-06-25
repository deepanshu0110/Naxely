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
import { NaxelyMark } from '@/components/ui/NaxelyMark'
import { useAuthStore } from '@/store/authStore'

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

function PDFMockupCard() {
  return (
    <div className="relative w-[340px] h-[460px]
      bg-white dark:bg-[#1e1c18]
      rounded-2xl
      shadow-[0_24px_64px_rgba(0,0,0,0.10)]
      dark:shadow-[0_24px_64px_rgba(0,0,0,0.45)]
      overflow-hidden
      border border-black/5 dark:border-white/5
      flex-shrink-0">

      {/* Top brand bar */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-amber-500" />

      {/* Header row */}
      <div className="flex items-center justify-between px-6 pt-7 pb-0">
        <div className="flex items-center gap-1.5">
          <NaxelyMark size={14} color="#D97A34" />
          <span className="text-[10px] text-ink/30 dark:text-paper/25">Naxely</span>
        </div>
        <span className="text-[10px] text-ink/30 dark:text-paper/25">Acme Corp</span>
      </div>

      {/* Hero stat */}
      <div className="px-6 pt-8 pb-5 text-center">
        <p className="font-display text-xl font-semibold text-amber-500">
          Revenue: +24.6% ▲
        </p>
      </div>

      {/* Rule */}
      <div className="mx-6 h-px bg-amber-500/25" />

      {/* Report title */}
      <div className="px-6 pt-5">
        <h2 className="font-display text-[22px] font-semibold
          text-ink dark:text-paper leading-tight mb-0.5">
          Q2 Sales Report
        </h2>
        <p className="text-[10px] text-ink/35 dark:text-paper/25">Acme Corp</p>
      </div>

      {/* KPI mini-row */}
      <div className="flex gap-2.5 px-6 pt-4">
        {[
          { label: 'Revenue', value: '$440K', trend: '+24.6%', up: true },
          { label: 'Units',   value: '3.2K',  trend: '−3.1%',  up: false },
          { label: 'Regions', value: '4',     trend: 'stable', up: null },
        ].map((kpi) => (
          <div key={kpi.label}
            className="flex-1 bg-amber-500/6 dark:bg-amber-500/10 rounded-lg p-2.5">
            <p className="text-[8px] text-ink/35 dark:text-paper/25 mb-0.5">
              {kpi.label}
            </p>
            <p className="text-[13px] font-semibold text-ink dark:text-paper font-mono">
              {kpi.value}
            </p>
            <p className={`text-[8px] font-mono ${
              kpi.up === true  ? 'text-emerald-600 dark:text-emerald-400' :
              kpi.up === false ? 'text-red-500 dark:text-red-400' :
                                 'text-ink/25 dark:text-paper/20'
            }`}>
              {kpi.trend}
            </p>
          </div>
        ))}
      </div>

      {/* Mini bar chart */}
      <div className="px-6 pt-4">
        <div className="flex items-end gap-[3px] h-10">
          {[35,52,41,68,45,72,58,80,63,88,71,95].map((h, i) => (
            <div key={i}
              className="flex-1 rounded-[2px] bg-amber-500/65 dark:bg-amber-500/55"
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
        <p className="text-[8px] font-mono text-ink/20 dark:text-paper/15 mt-1">
          Monthly Revenue Trend
        </p>
      </div>

      {/* Metadata footer */}
      <div className="absolute bottom-5 left-0 right-0
        flex justify-between px-6">
        <span className="text-[8px] font-mono text-ink/20 dark:text-paper/15">
          Jun 2026
        </span>
        <span className="text-[8px] font-mono text-ink/20 dark:text-paper/15">
          Prepared by Acme Corp
        </span>
      </div>

      {/* Bottom brand bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-amber-500" />
    </div>
  );
}

export default function Landing() {
  const { isAuthenticated } = useAuthStore();

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
        {/* ── Hero inner layout ── */}
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">

          {/* Left column — copy */}
          <div className="flex-1 text-center lg:text-left">

            {/* Eyebrow tag */}
            <div className="inline-flex items-center gap-2 mb-6
              bg-amber-500/10 dark:bg-amber-500/15
              text-amber-700 dark:text-amber-400
              text-xs font-medium tracking-widest uppercase
              px-3 py-1.5 rounded-full
              border border-amber-500/20 dark:border-amber-500/25">
              <NaxelyMark size={11} color="currentColor" />
              CSV → Branded PDF in under 60 seconds
            </div>

            {/* H1 */}
            <h1 className="font-display text-5xl lg:text-[3.5rem] font-semibold
              text-ink dark:text-paper
              leading-[1.1] tracking-tight mb-6">
              Turn raw data into{' '}
              <span className="text-amber-600 dark:text-amber-400">
                client-ready reports
              </span>
              {' '}— automatically
            </h1>

            {/* Subheadline */}
            <p className="text-ink/60 dark:text-paper/50 text-lg leading-relaxed
              max-w-lg mx-auto lg:mx-0 mb-10">
              Upload a CSV or connect Google Sheets. Naxely generates a branded PDF
              with AI insights, charts, and recommendations in under a minute.
              No design skills needed.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center
              justify-center lg:justify-start gap-4 mb-10">
              {isAuthenticated ? (
                <Link to="/dashboard"
                  className="bg-amber-500 hover:bg-amber-600 text-white
                    font-medium px-7 py-3 rounded-lg transition-colors text-base
                    inline-block">
                  Go to Dashboard →
                </Link>
              ) : (
                <>
                  <Link to="/signup"
                    className="bg-amber-500 hover:bg-amber-600 text-white
                      font-medium px-7 py-3 rounded-lg transition-colors text-base
                      inline-block">
                    Generate your first report — free
                  </Link>
                  <Link to="/login"
                    className="text-ink/60 dark:text-paper/50
                      hover:text-ink dark:hover:text-paper
                      font-medium text-base transition-colors">
                    Sign in →
                  </Link>
                </>
              )}
            </div>

            {/* Social proof */}
            <div className="flex flex-wrap items-center
              justify-center lg:justify-start
              gap-x-6 gap-y-2
              text-sm text-ink/35 dark:text-paper/25">
              <span>✓ No credit card required</span>
              <span>✓ Free tier available</span>
              <span>✓ PDF ready in under 60s</span>
            </div>

          </div>

          {/* Right column — PDF mockup */}
          <div className="hidden lg:flex flex-1 justify-center items-center">
            <PDFMockupCard />
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
