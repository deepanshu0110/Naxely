import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function CookiePolicy() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Cookie Policy — Naxely</title>
        <meta name="description" content="Naxely Cookie Policy. What cookies we use, the consent categories controlled by our cookie banner, and how to change your preferences." />
        <link rel="canonical" href="https://www.naxely.com/cookie-policy" />
        <meta property="og:url" content="https://www.naxely.com/cookie-policy" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Cookie Policy — Naxely" />
        <meta property="og:description" content="Naxely Cookie Policy — what cookies we use, consent categories, and how to manage your preferences." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Cookie Policy — Naxely" />
        <meta name="twitter:description" content="Naxely Cookie Policy — what cookies we use, consent categories, and how to manage your preferences." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"Cookie Policy","item":"https://www.naxely.com/cookie-policy"}]})}</script>
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Cookie Policy</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-4">
          <p>This policy explains what cookies Naxely uses and why, the categories our cookie consent banner lets you control, and how to change your preferences. It works together with our <Link to="/privacy" className="text-amber-600 hover:text-amber-700 underline">Privacy Policy</Link>.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">What Are Cookies?</h2>
          <p>Cookies are small text files stored on your device when you visit a website. They help the site work correctly, remember your preferences, and help us understand how the site is used.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Consent & Our Cookie Banner</h2>
          <p>When you first visit naxely.com, our cookie consent banner (powered by CookieYes) asks for your consent before any non-essential cookies are set. The banner lets you Accept All, Reject All, or Customise your preferences per category, and you can change your choices at any time (see below).</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">The Cookies We Use</h2>
          <p>Our banner controls the following categories. The descriptions match what the banner shows:</p>

          <h3 className="font-semibold text-ink dark:text-paper text-sm mt-6">Necessary (Always Active)</h3>
          <p>Necessary cookies are required to enable the basic features of this site, such as providing secure log-in or adjusting your consent preferences. These cookies do not store any personally identifiable data. This category includes Cloudflare's <strong>__cf_bm</strong> cookie (1 hour, used to support Cloudflare Bot Management) and our own session cookies used for authentication.</p>

          <h3 className="font-semibold text-ink dark:text-paper text-sm mt-6">Functional</h3>
          <p>Functional cookies help perform certain functionalities like sharing the content of the website on social media platforms, collecting feedback, and other third-party features. This category is currently not used — there are no functional cookies to display.</p>

          <h3 className="font-semibold text-ink dark:text-paper text-sm mt-6">Analytics</h3>
          <p>Analytical cookies are used to understand how visitors interact with the website. These cookies help provide information on metrics such as the number of visitors, bounce rate, traffic source, etc. When you consent to this category, we load Google Analytics (GA4) and Microsoft Clarity, which set analytics cookies (for example <strong>_ga</strong>, <strong>_ga_*</strong>, and <strong>_clck</strong>/<strong>_clsk</strong>), and Ahrefs site analytics.</p>

          <h3 className="font-semibold text-ink dark:text-paper text-sm mt-6">Performance</h3>
          <p>Performance cookies are used to understand and analyse the key performance indexes of the website which helps in delivering a better user experience for the visitors. This category is currently not used.</p>

          <h3 className="font-semibold text-ink dark:text-paper text-sm mt-6">Advertisement</h3>
          <p>Advertisement cookies are used to provide visitors with customised advertisements based on the pages you visited previously and to analyse the effectiveness of the ad campaigns. Naxely does not currently serve personalised advertising, and this category is not used.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">How to Change Your Consent</h2>
          <p>You can change or withdraw your consent at any time by opening the cookie banner again — click the floating cookie button at the bottom corner of the site — and using the Customise, Reject All, or Accept All options, then Save My Preferences. Your choice is stored on your device, and no non-essential cookies are set until you consent.</p>
          <p>You can also delete or block cookies through your browser's own settings, and opt out of Google Analytics using the official opt-out add-on.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Contact</h2>
          <p>Questions about this Cookie Policy or your consent choices? Email us at <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a>.</p>

          <p className="mt-8 text-xs text-ink/40">Last updated: August 2026</p>
        </div>
      </div>
    </div>
  )
}
