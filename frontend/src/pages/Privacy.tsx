import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function Privacy() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Privacy Policy — Naxely</title>
        <meta name="description" content="Naxely Privacy Policy. How we collect, use, and protect your data when you use our AI-powered PDF report generation service." />
        <link rel="canonical" href="https://www.naxely.com/privacy" />
        <meta property="og:url" content="https://www.naxely.com/privacy" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Privacy Policy — Naxely" />
        <meta property="og:description" content="Naxely Privacy Policy — data collection, AI processing, third-party services, and your rights." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Privacy Policy — Naxely" />
        <meta name="twitter:description" content="Naxely Privacy Policy — data collection, AI processing, third-party services, and your rights." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"Privacy Policy","item":"https://www.naxely.com/privacy"}]})}</script>
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Privacy Policy</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-4">
          <p>Naxely is committed to protecting your privacy. This policy explains how we collect, use, and safeguard your data when you use our AI-powered PDF report generation service.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Data Controller</h2>
          <p>Naxely is operated by Deepanshu Garg, based in India. For any privacy questions or requests, contact <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a>.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Information We Collect</h2>
          <p><strong>Account information:</strong> When you sign up, we collect your name, email address, and billing information (processed securely through Dodo Payments).</p>
          <p><strong>Report data:</strong> CSV files, Google Sheets data, and generated PDF reports you upload or create through the service.</p>
          <p><strong>AI API keys:</strong> If you bring your own API key (BYOK), it is encrypted before storage.</p>
          <p><strong>Usage data:</strong> We use Google Analytics (GA4) to understand how the site is used — pages visited, general location (country-level), and device type. See the Cookies section below.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">How We Use Your Data</h2>
          <p>We use your data solely to provide and improve the service: generate PDF reports, process AI insights, manage your account, communicate with you about service-related updates, and understand product usage through analytics.</p>
          <p>Your uploaded data (CSV, Sheets, report content) is used only to generate the reports you request. We do not sell your data or your reports to third parties.</p>
          <p>When you use a BYOK AI provider (Groq, OpenAI, Gemini, Claude, DeepSeek, Mistral, or Together AI), your report data is sent to that provider to generate insights. Each provider has its own data usage and retention policy, which may differ from ours — we encourage you to review the policy of whichever provider you choose to connect, since Naxely cannot control or guarantee how a third-party AI provider uses data once it's sent to them.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Data Storage & Security</h2>
          <p>Your reports and uploaded data are stored securely on Supabase (PostgreSQL) and Supabase Storage. We use encryption in transit (TLS) and encrypt stored API keys at rest.</p>
          <p>We retain your data for as long as your account is active. You may request deletion at any time by contacting us.</p>
          <p>Naxely's infrastructure providers (Supabase, Render, Vercel) may process or store data outside your home country. By using Naxely, you consent to this transfer, which is protected by the security measures described above.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Third-Party Services</h2>
          <p>Naxely integrates with the following third-party services:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Supabase</strong> — authentication, database, and file storage</li>
            <li><strong>Dodo Payments</strong> — payment processing (we do not store credit card details)</li>
            <li><strong>Groq, OpenAI, Gemini, Claude, DeepSeek, Mistral, Together AI</strong> — AI analysis, only when you provide your own API key</li>
            <li><strong>Google Sheets</strong> — data import (read-only, with your explicit authorization)</li>
            <li><strong>Resend</strong> — transactional email delivery</li>
            <li><strong>Google Analytics (GA4)</strong> — site usage analytics</li>
          </ul>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Your Rights</h2>
          <p>You may access, update, or delete your account data at any time through your account settings. To request full data deletion, email us at <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a>.</p>
          <p>You may export your reports and data at any time. We will respond to data requests within 30 days.</p>
          <p>If you are located in the EU/EEA or UK, you have rights under GDPR including access, correction, deletion, and data portability. Contact <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a> to exercise these rights.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Grievance Officer</h2>
          <p>In accordance with the Digital Personal Data Protection Act, 2023 (India) and other applicable data protection laws, the Grievance Officer for Naxely is Deepanshu Garg, reachable at <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a>. If you have a complaint or concern about how your personal data is handled, please contact the Grievance Officer directly. We aim to acknowledge and resolve grievances within 90 days.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Cookies</h2>
          <p>We use essential cookies for authentication and session management. We also use Google Analytics (GA4), which sets analytics cookies to help us understand site usage. You can opt out of Google Analytics tracking using your browser settings or a browser extension such as Google's official opt-out add-on.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Data Breach Notification</h2>
          <p>In the event of a data breach affecting your personal data, we will notify affected users without undue delay, and in accordance with applicable law (for EU/EEA and UK users, within 72 hours of becoming aware of the breach where required).</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">We Do Not Sell Your Data</h2>
          <p>Naxely does not sell, rent, or trade your personal information to third parties for their own marketing purposes.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Children's Privacy</h2>
          <p>Naxely is not directed at children under 16, and we do not knowingly collect personal data from children. If you believe a child has provided us with personal data, please contact <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a> and we will delete it.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Changes to This Policy</h2>
          <p>We may update this policy from time to time. Material changes will be communicated via email or through the service.</p>

          <p className="mt-8 text-xs text-ink/40">Last updated: July 2026</p>
        </div>
      </div>
    </div>
  )
}
