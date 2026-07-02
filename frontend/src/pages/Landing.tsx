import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import {
  Upload,
  Settings,
  Download,
  Sparkles,
  BarChart3,
  Palette,
  Link2,
} from 'lucide-react'
import Navbar from '@/components/layout/Navbar'
import { NaxelyMark } from '@/components/ui/NaxelyMark'
import { useAuthStore } from '@/store/authStore'
import { useInView } from '@/hooks/useInView'

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
      'AI insight cards — auto-written summary for every KPI',
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

const productStats = [
  {
    value: '6,000+',
    label: 'rows processed per report',
  },
  {
    value: '< 30s',
    label: 'average generation time',
  },
  {
    value: '16',
    label: 'chart types supported',
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
            <div
              key={i}
              className="flex-1 rounded-[2px] bg-amber-500/65 dark:bg-amber-500/55 nax-bar-grow"
              style={{
                height: `${h}%`,
                transformOrigin: 'bottom',
                animation: `nax-grow-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) both`,
                animationDelay: `${400 + i * 40}ms`,
              }}
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

  const { ref: howItWorksRef, inView: howItWorksInView } = useInView();
  const { ref: pricingRef, inView: pricingInView } = useInView();
  const { ref: testimonialsRef, inView: testimonialsInView } = useInView();
  const { ref: finalCtaRef, inView: finalCtaInView } = useInView();
  const { ref: featureHeaderRef, inView: featureHeaderInView } = useInView();
  const { ref: bentoRef, inView: bentoInView } = useInView();
  const { ref: sampleRef, inView: sampleInView } = useInView();

  return (
    <div className="min-h-screen bg-paper text-ink">
      <Head>
        <title>Naxely — AI-Powered PDF Report Generator</title>
        <meta name="description" content="Turn raw data into client-ready PDF reports in under 60 seconds. Upload CSV or connect Google Sheets — AI writes insights, builds charts, and brands every page." />
        <meta property="og:title" content="Naxely — AI-Powered PDF Report Generator" />
        <meta property="og:description" content="Upload CSV or connect Google Sheets. Naxely generates a branded PDF with AI insights, charts, and recommendations in under a minute." />
        <meta property="og:image" content="/og-image.png" />
      </Head>
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

            {/* Eyebrow tag — appears first */}
            <div className="inline-flex items-center gap-2 mb-6
              bg-amber-500/10 dark:bg-amber-500/15
              text-amber-700 dark:text-amber-400
              text-xs font-medium tracking-widest uppercase
              px-3 py-1.5 rounded-full
              border border-amber-500/20 dark:border-amber-500/25
              nax-animate-fade-up"
              style={{ animationDelay: '0ms' }}>
              <NaxelyMark size={11} color="currentColor" />
              CSV → Branded PDF in under 60 seconds
            </div>

            {/* H1 */}
            <h1 className="font-display text-5xl lg:text-[3.5rem] font-semibold
              text-ink dark:text-paper
              leading-[1.1] tracking-tight mb-6
              nax-animate-fade-up"
              style={{ animationDelay: '80ms' }}>
              Turn raw data into{' '}
              <span className="text-amber-600 dark:text-amber-400">
                client-ready reports
              </span>
              {' '}— automatically
            </h1>

            {/* Subheadline */}
            <p className="text-ink/60 dark:text-paper/50 text-lg leading-relaxed
              max-w-lg mx-auto lg:mx-0 mb-10
              nax-animate-fade-up"
              style={{ animationDelay: '160ms' }}>
              Upload a CSV or connect Google Sheets. Naxely generates a branded PDF
              with AI insights, charts, and recommendations in under a minute.
              No design skills needed.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center
              justify-center lg:justify-start gap-4 mb-10
              nax-animate-fade-up"
              style={{ animationDelay: '240ms' }}>
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
                    className="
                      relative overflow-hidden
                      bg-amber-500 hover:bg-amber-600
                      text-white font-medium px-7 py-3 rounded-lg
                      transition-colors text-base inline-block
                      group
                    ">
                    <span className="relative z-10">
                      Generate your first report — free
                    </span>
                    {/* Shimmer layer */}
                    <span className="
                      absolute inset-0
                      bg-gradient-to-r from-transparent via-white/20 to-transparent
                      -translate-x-full group-hover:translate-x-full
                      transition-transform duration-700 ease-in-out
                    " />
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
              text-sm text-ink/35 dark:text-paper/25
              nax-animate-fade-up"
              style={{ animationDelay: '320ms' }}>
              <span>✓ No credit card required</span>
              <span>✓ Free tier available</span>
              <span>✓ PDF ready in under 60s</span>
            </div>

          </div>

          {/* Right column — PDF mockup */}
          <div className="hidden lg:flex flex-1 justify-center items-center">
            <div className="nax-animate-float">
              <PDFMockupCard />
            </div>
          </div>

        </div>
      </section>

      {/* ── How It Works ── */}
      <section
        ref={howItWorksRef}
        id="how-it-works"
        className={`bg-slate px-6 py-20 ${howItWorksInView ? 'nax-animate-fade-in' : 'opacity-0'}`}
        style={{
          backgroundImage: 'radial-gradient(circle, #D97A3411 1px, transparent 1px)',
          backgroundSize: '28px 28px',
          animationDelay: '0ms',
        }}
      >
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

      {/* ── Features Bento ── */}
      <section id="features" className="py-24 px-6 md:px-12 lg:px-20">
        <div className="max-w-7xl mx-auto">

          {/* Section header */}
          <div
            ref={featureHeaderRef}
            className={`text-center mb-16 transition-all duration-500
              ${featureHeaderInView
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-4'
              }`}
          >
            <p className="text-amber-600 dark:text-amber-400
              text-xs font-medium tracking-widest uppercase mb-3">
              Everything you need
            </p>
            <h2 className="font-display text-4xl font-semibold
              text-ink dark:text-paper">
              From raw data to client-ready PDF
            </h2>
          </div>

          {/* Bento grid */}
          <div
            ref={bentoRef}
            className={`grid grid-cols-1 lg:grid-cols-3 gap-4 auto-rows-auto
              transition-all duration-700
              ${bentoInView
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-6'
              }`}
          >

            {/* ── Card 1: CSV → PDF (hero, wide) lg:col-span-2 ── */}
            <div className="relative overflow-hidden rounded-2xl p-7
              bg-white dark:bg-[#1e1c18]
              border border-black/5 dark:border-white/5
              hover:border-amber-500/30 dark:hover:border-amber-500/25
              transition-colors duration-300
              lg:col-span-2">

              {/* Top accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-amber-500 rounded-t-2xl" />

              <div className="flex items-start justify-between mb-6">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/15
                  flex items-center justify-center">
                  <Upload className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                <span className="text-xs font-mono text-amber-600 dark:text-amber-400
                  bg-amber-500/8 dark:bg-amber-500/12 px-2.5 py-1 rounded-full">
                  Core feature
                </span>
              </div>

              <h3 className="font-display text-2xl font-semibold
                text-ink dark:text-paper mb-3">
                Upload a CSV.<br />Get a branded PDF.
              </h3>
              <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed max-w-md mb-8">
                Drop in any CSV or connect a Google Sheet and Naxely generates a
                fully branded, client-ready PDF report in under 60 seconds — with
                charts, KPI cards, and AI-written insights included.
              </p>

              {/* Pipeline visual */}
              <div className="flex items-center gap-3">
                {[
                  { label: 'CSV Upload', emoji: '📄' },
                  { label: 'AI Analysis', emoji: '✦' },
                  { label: 'PDF Report', emoji: '📊' },
                ].map((step, i) => (
                  <div key={step.label} className="flex items-center gap-3">
                    <div className="flex flex-col items-center gap-1.5">
                      <div className="w-10 h-10 rounded-lg
                        bg-amber-500/10 dark:bg-amber-500/15
                        flex items-center justify-center text-lg">
                        {step.emoji}
                      </div>
                      <span className="text-[10px] font-mono text-ink/40 dark:text-paper/30">
                        {step.label}
                      </span>
                    </div>
                    {i < 2 && (
                      <div className="w-8 h-px bg-amber-500/30 mb-4 flex-shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* ── Card 2: AI Insights (tall, right) lg:col-span-1 lg:row-span-2 ── */}
            <div className="relative overflow-hidden rounded-2xl p-7
              bg-white dark:bg-[#1e1c18]
              border border-black/5 dark:border-white/5
              hover:border-amber-500/30 dark:hover:border-amber-500/25
              transition-colors duration-300
              lg:col-span-1 lg:row-span-2">

              <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/15
                flex items-center justify-center mb-6">
                <Sparkles className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>

              <h3 className="font-display text-xl font-semibold
                text-ink dark:text-paper mb-3">
                AI insights, auto-written
              </h3>
              <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed mb-8">
                Naxely identifies trends, flags anomalies, and writes plain-English
                insights for every metric — ready to share with clients, no editing needed.
              </p>
              <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed mb-8">
                AI-generated insights are included in every report — review them in the web app before downloading your PDF.
              </p>

              {/* Sample insight cards */}
              <div className="space-y-3">
                {[
                  {
                    label: 'HIGH',
                    text: 'Revenue up 33.9% — strongest month in Q2',
                    color: 'text-amber-600 dark:text-amber-400',
                    bg: 'bg-amber-500/8 dark:bg-amber-500/12',
                  },
                  {
                    label: 'MEDIUM',
                    text: 'Units Sold trending flat over the last 30 days',
                    color: 'text-ink/50 dark:text-paper/40',
                    bg: 'bg-black/4 dark:bg-white/5',
                  },
                  {
                    label: 'FLAG',
                    text: 'Anomaly: Revenue spike 2.1× std deviation',
                    color: 'text-red-500 dark:text-red-400',
                    bg: 'bg-red-500/6 dark:bg-red-500/10',
                  },
                ].map((insight) => (
                  <div key={insight.label} className={`rounded-xl p-3.5 ${insight.bg}`}>
                    <span className={`text-[9px] font-mono font-semibold ${insight.color} block mb-1`}>
                      {insight.label}
                    </span>
                    <p className="text-[11px] text-ink/65 dark:text-paper/55 leading-snug">
                      {insight.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Card 3: 16 Chart Types (small) ── */}
            <div className="relative overflow-hidden rounded-2xl p-7
              bg-white dark:bg-[#1e1c18]
              border border-black/5 dark:border-white/5
              hover:border-amber-500/30 dark:hover:border-amber-500/25
              transition-colors duration-300">

              <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/15
                flex items-center justify-center mb-5">
                <BarChart3 className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>

              <h3 className="font-display text-xl font-semibold
                text-ink dark:text-paper mb-2">
                16 chart types
              </h3>
              <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed mb-5">
                Line, bar, scatter, pie, heatmap, waterfall, and more.
                AI picks the right chart for your data automatically.
              </p>

              {/* Chart type icon grid */}
              <div className="grid grid-cols-4 gap-1.5">
                {['▦','▤','◉','▲','▬','◈','▩','◐'].map((glyph, i) => (
                  <div key={i}
                    className="aspect-square rounded-lg
                      bg-amber-500/8 dark:bg-amber-500/12
                      flex items-center justify-center
                      text-amber-600 dark:text-amber-400 text-sm">
                    {glyph}
                  </div>
                ))}
              </div>
            </div>

            {/* ── Card 4: Scheduled Reports (small) ── */}
            <div className="relative overflow-hidden rounded-2xl p-7
              bg-white dark:bg-[#1e1c18]
              border border-black/5 dark:border-white/5
              hover:border-amber-500/30 dark:hover:border-amber-500/25
              transition-colors duration-300">

              <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/15
                flex items-center justify-center mb-5">
                <Download className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>

              <h3 className="font-display text-xl font-semibold
                text-ink dark:text-paper mb-2">
                Scheduled delivery
              </h3>
              <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed mb-5">
                Set it once. Naxely emails your client a fresh PDF daily,
                weekly, or monthly — automatically.
              </p>

              {/* Cadence pills */}
              <div className="flex flex-wrap gap-2">
                {['Daily', 'Weekly', 'Monthly'].map((cadence) => (
                  <span key={cadence}
                    className="text-xs font-mono
                      bg-amber-500/8 dark:bg-amber-500/12
                      text-amber-700 dark:text-amber-400
                      px-3 py-1 rounded-full border border-amber-500/15">
                    {cadence}
                  </span>
                ))}
              </div>
            </div>

            {/* ── Card 5: Brand Customization (wide) lg:col-span-2 ── */}
            <div className="relative overflow-hidden rounded-2xl p-7
              bg-white dark:bg-[#1e1c18]
              border border-black/5 dark:border-white/5
              hover:border-amber-500/30 dark:hover:border-amber-500/25
              transition-colors duration-300
              lg:col-span-2">

              <div className="flex items-start gap-5">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/15
                  flex items-center justify-center flex-shrink-0">
                  <Palette className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-display text-xl font-semibold
                    text-ink dark:text-paper mb-2">
                    Fully branded — your logo, your colors
                  </h3>
                  <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed mb-5">
                    Upload your logo, set your brand color, add your company name.
                    Every PDF looks like it came from your studio, not a SaaS tool.
                    Agency accounts get full white-label — no Naxely branding anywhere.
                  </p>

                  {/* Color swatch row */}
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-ink/35 dark:text-paper/25 font-mono">
                      Brand color
                    </span>
                    <div className="flex gap-2">
                      {['#D97A34','#6366F1','#0E9F6E','#EF4444','#14131F'].map((hex) => (
                        <div
                          key={hex}
                          className="w-6 h-6 rounded-full
                            border-2 border-white dark:border-[#1e1c18]
                            shadow-sm hover:scale-110 transition-transform cursor-default"
                          style={{ backgroundColor: hex }}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-ink/25 dark:text-paper/20 font-mono">
                      + any custom hex
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* ── Card 6: Google Sheets (with Live badge) ── */}
            <div className="relative overflow-hidden rounded-2xl p-7
              bg-white dark:bg-[#1e1c18]
              border border-black/5 dark:border-white/5
              hover:border-amber-500/30 dark:hover:border-amber-500/25
              transition-colors duration-300">

              <div className="flex items-start justify-between mb-5">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 dark:bg-amber-500/15
                  flex items-center justify-center">
                  <Link2 className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                {/* Live badge */}
                <span className="text-xs font-mono text-ink/40 dark:text-paper/30
                  bg-black/5 dark:bg-white/8
                  px-2.5 py-1 rounded-full border border-black/8 dark:border-white/10">
                  Live
                </span>
              </div>

              <h3 className="font-display text-xl font-semibold
                text-ink dark:text-paper mb-2">
                Connect Google Sheets
              </h3>
              <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed">
                Paste a Sheet URL and Naxely reads it directly.
                No CSV export needed — your data stays where it already lives.
              </p>
            </div>

          </div>{/* end bento grid */}
        </div>
      </section>

      {/* ── Sample Report ── */}
      <section
        ref={sampleRef}
        className={`px-6 py-20 ${sampleInView ? 'nax-animate-fade-in' : 'opacity-0'}`}
        style={{ animationDelay: '0ms' }}
      >
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">
            See a Real Sample — No Cherry-Picking
          </h2>
          <p className="text-ink/60 dark:text-paper/50 text-base leading-relaxed mb-10 max-w-2xl mx-auto">
            This is the unedited input and output. Download the raw CSV, then view
            the exact PDF Naxely generated from it — nothing edited, nothing staged.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="/sample/agency_billable_hours.csv"
              download
              className="bg-amber-500 hover:bg-amber-600 text-white font-medium px-7 py-3 rounded-lg transition-colors text-base inline-block"
            >
              Download Sample CSV
            </a>
            <a
              href="/sample/report.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ink/60 dark:text-paper/50 hover:text-ink dark:hover:text-paper font-medium text-base transition-colors inline-block"
            >
              View Sample PDF Report →
            </a>
          </div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section
        ref={pricingRef}
        id="pricing"
        className={`bg-slate px-6 py-20 ${pricingInView ? 'nax-animate-fade-in' : 'opacity-0'}`}
        style={{ animationDelay: '0ms' }}
      >
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
                {p.name === 'Pro' && (
                  <p className="mt-2 text-xs text-gray-500 leading-relaxed">
                    If one report takes you 2 hours, this pays for itself in a single client deliverable.
                  </p>
                )}
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
      <section
        ref={testimonialsRef}
        className={`px-6 py-20 ${testimonialsInView ? 'nax-animate-fade-in' : 'opacity-0'}`}
        style={{ animationDelay: '0ms' }}
      >
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display mb-14 text-center text-2xl font-bold text-ink">
            Built for serious reporting work
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            {productStats.map((s, i) => (
              <div
                key={i}
                className="rounded-xl bg-paper p-6 text-center shadow-sm"
              >
                <p className="font-display text-3xl font-bold text-ink">
                  {s.value}
                </p>
                <p className="mt-2 text-sm text-gray-500">
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA Banner ── */}
      <section
        ref={finalCtaRef}
        className={`bg-ink px-6 py-20 ${finalCtaInView ? 'nax-animate-fade-in' : 'opacity-0'}`}
        style={{ animationDelay: '0ms' }}
      >
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold text-white">
            Ready to stop spending hours on reports?
          </h2>
          <p className="mt-4 text-gray-400">
            Join consultants and agencies saving time with
            Naxely.
          </p>
          <Link
            to="/signup"
            className="mt-8 inline-block rounded-lg bg-white px-8 py-3 text-sm font-semibold text-ink hover:bg-gray-100"
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
              <a href="#features" className="hover:text-ink">
                Features
              </a>
              <a href="#pricing" className="hover:text-ink">
                Pricing
              </a>
              <Link to="/privacy" className="hover:text-ink">
                Privacy Policy
              </Link>
              <Link to="/terms" className="hover:text-ink">
                Terms of Service
              </Link>
              <Link to="/contact" className="hover:text-ink">
                Contact
              </Link>
              <Link to="/refund" className="hover:text-ink">
                Refund Policy
              </Link>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 mt-8 pt-8 border-t border-gray-200">
            <a
              href="https://www.producthunt.com/products/naxely?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-naxely"
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                alt="Naxely - CSV and Google Sheets to branded PDF reports with AI | Product Hunt"
                width="250"
                height="54"
                src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1181500&theme=neutral&t=1782573416777"
              />
            </a>
            <a href="https://www.uneed.best/tool/naxely" target="_blank" rel="noopener noreferrer">
              <img src="https://www.uneed.best/EMBED3.png" alt="Uneed Embed Badge" height="54" />
            </a>
            <a href="https://fazier.com/launches/naxely.com" target="_blank" rel="noopener noreferrer">
              <img src="https://fazier.com/api/v1//public/badges/launch_badges.svg?badge_type=launched&theme=neutral" width="120" alt="Fazier badge" />
            </a>
            <a href="https://dang.ai" target="_blank" rel="dofollow noopener" style={{display:'inline-block', textDecoration:'none'}}>
              <img
                src="https://assets.dang.ai/badges/dang-verified-dark.png"
                alt="Verified on DANG!"
                width="260"
                height="94"
                style={{display:'block', width:'260px', maxWidth:'100%', height:'auto', border:0, outline:'none', textDecoration:'none'}}
              />
            </a>
            <a href="https://www.shipit.buzz/products/naxely?ref=badge" target="_blank" rel="noopener noreferrer">
              <img src="https://www.shipit.buzz/api/products/naxely/badge?theme=light" alt="Featured on Shipit" />
            </a>
            <a href="https://smollaunch.com" target="_blank" rel="noopener">
              <img src="https://smollaunch.com/badges/featured.svg" alt="Naxely — Featured on Smol Launch" loading="lazy" width="250" height="60" />
            </a>
          </div>
          <p className="mt-4 text-center text-xs text-gray-400">
            Made in India 🇮🇳 · Naxely © 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
