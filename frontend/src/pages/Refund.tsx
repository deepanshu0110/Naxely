import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function Refund() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Refund Policy — Naxely</title>
        <meta name="description" content="Naxely Refund Policy. 14-day money-back guarantee for Pro and Agency subscriptions." />
        <link rel="canonical" href="https://www.naxely.com/refund" />
        <meta property="og:url" content="https://www.naxely.com/refund" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Refund Policy — Naxely" />
        <meta property="og:description" content="Naxely Refund Policy — eligibility, how to request a refund, and exceptions." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Refund Policy — Naxely" />
        <meta name="twitter:description" content="Naxely Refund Policy — eligibility, how to request a refund, and exceptions." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"Refund Policy","item":"https://www.naxely.com/refund"}]})}</script>
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Refund Policy</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-4">
          <p>We offer a 14-day money-back guarantee on all paid subscriptions (Pro and Agency tiers). If you are not satisfied with Naxely for any reason, you may request a full refund within 14 days of purchase.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">What's Covered</h2>
          <p>Any first-time purchase of a monthly or annual plan is eligible for a full refund within the first 14 days. No questions asked.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">What's Not Covered</h2>
          <p>After the 14-day window, refunds are not available. However, you may cancel your subscription at any time, and you will retain access to paid features until the end of your current billing period.</p>
          <p>Renewal charges (payments made after the first 14 days for continued service) are generally non-refundable. If you believe an error occurred, contact hello@naxely.com and we will review your case.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">How to Request a Refund</h2>
          <p>Email us at <strong>hello@naxely.com</strong> from the email address associated with your Naxely account. Include your account name and the reason for your request. We will process your refund within 5-10 business days.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Payment Processor</h2>
          <p>All payments are processed by Dodo Payments. Refunds are issued through Dodo Payments and will be credited to the original payment method used at purchase.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Questions?</h2>
          <p>If you have any questions about this Refund Policy, contact us at hello@naxely.com.</p>

          <p className="mt-8 text-xs text-ink/40">Last updated: July 2026</p>
        </div>
      </div>
    </div>
  )
}
