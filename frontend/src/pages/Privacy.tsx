import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function Privacy() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Privacy Policy — Naxely</title>
        <meta name="description" content="Naxely Privacy Policy. How we collect, use, and protect your data when you use our AI-powered PDF report generation service." />
        <meta property="og:title" content="Privacy Policy — Naxely" />
        <meta property="og:description" content="Naxely Privacy Policy — data collection, AI processing, third-party services, and your rights." />
        <meta property="og:image" content="/og-image.png" />
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Privacy Policy</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-4">
          <p>Naxely is committed to protecting your privacy. This policy explains how we collect, use, and safeguard your data when you use our AI-powered PDF report generation service.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Information We Collect</h2>
          <p><strong>Account information:</strong> When you sign up, we collect your name, email address, and billing information (processed securely through Dodo Payments).</p>
          <p><strong>Report data:</strong> CSV files, Google Sheets data, and generated PDF reports you upload or create through the service.</p>
          <p><strong>AI API keys:</strong> If you bring your own API key (BYOK), it is encrypted and stored securely in our database.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">How We Use Your Data</h2>
          <p>We use your data solely to provide and improve the service: generate PDF reports, process AI insights, manage your account, and communicate with you about service-related updates.</p>
          <p>Your uploaded data is used only to generate the reports you request. AI analysis is performed on your data at the time of report generation and is not used to train or improve third-party AI models.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Data Storage & Security</h2>
          <p>Your reports and uploaded data are stored securely on Supabase (PostgreSQL) and Supabase Storage. We use encryption in transit (TLS) and at rest. API keys are encrypted using Fernet symmetric encryption before storage.</p>
          <p>We retain your data for as long as your account is active. You may request deletion at any time by contacting us.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Third-Party Services</h2>
          <p>Naxely integrates with the following third-party services:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Supabase</strong> — authentication, database, and file storage</li>
            <li><strong>Dodo Payments</strong> — payment processing (we do not store credit card details)</li>
            <li><strong>Google AI / OpenAI / Groq / etc.</strong> — AI analysis (only when you provide an API key or use the free tier)</li>
            <li><strong>Google Sheets</strong> — data import (read-only, with your explicit authorization)</li>
            <li><strong>Resend</strong> — transactional email delivery</li>
          </ul>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Your Rights</h2>
          <p>You may access, update, or delete your account data at any time through your account settings. To request full data deletion, email us at hello@naxely.com.</p>
          <p>You may export your reports and data at any time. We will respond to data requests within 30 days.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Cookies</h2>
          <p>We use essential cookies for authentication and session management. We do not use tracking cookies or third-party analytics cookies beyond what is necessary for service operation.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Changes to This Policy</h2>
          <p>We may update this policy from time to time. Material changes will be communicated via email or through the service.</p>

          <p className="mt-8 text-xs text-ink/40">Last updated: June 2026</p>
        </div>
      </div>
    </div>
  )
}
