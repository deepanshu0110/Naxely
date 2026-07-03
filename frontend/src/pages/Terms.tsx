import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function Terms() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Terms of Service — Naxely</title>
        <meta name="description" content="Naxely Terms of Service. The rules and conditions for using our AI-powered PDF report generation service." />
        <link rel="canonical" href="https://naxely.com/terms" />
        <meta property="og:url" content="https://naxely.com/terms" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Terms of Service — Naxely" />
        <meta property="og:description" content="Naxely Terms of Service — usage, payment, liability, and account terms." />
        <meta property="og:image" content="https://naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Terms of Service — Naxely" />
        <meta name="twitter:description" content="Naxely Terms of Service — usage, payment, liability, and account terms." />
        <meta name="twitter:image" content="https://naxely.com/og-image.png" />
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Terms of Service</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-4">
          <p>By using Naxely, you agree to these terms. Naxely provides an AI-powered PDF report generation service ("Service"), operated by [Deepanshu Garg], based in India ("Naxely," "we," "us").</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Usage</h2>
          <p>You may use Naxely for lawful business purposes only. You retain full ownership of your data and the reports you generate. You are responsible for maintaining the confidentiality of your account and for all activity under it.</p>
          <p>You agree not to use Naxely to upload unlawful content, attempt to disrupt or reverse-engineer the Service, or violate any third party's rights.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Payment & Billing</h2>
          <p>Pro and Agency tier subscriptions are billed on a recurring basis through Dodo Payments. By subscribing, you authorize recurring charges until you cancel. See our Refund Policy for details on refund eligibility.</p>
          <p>We may change pricing with reasonable advance notice. Continued use of a paid tier after a price change takes effect constitutes acceptance of the new pricing.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">AI Content</h2>
          <p>AI-generated insights, summaries, and recommendations are provided as-is and may contain errors or inaccuracies. Review all AI-generated output before sharing it with clients or relying on it for business decisions. Naxely is not responsible for decisions made based on AI-generated content.</p>
          <p>If you connect your own AI provider (BYOK), your data is sent to that provider to generate output. Naxely is not responsible for the availability, accuracy, or data practices of third-party AI providers.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Intellectual Property</h2>
          <p>You retain full ownership of the data you upload and the reports you generate. Naxely retains all rights, title, and interest in the Service itself, including its software, design, and branding. Nothing in these Terms transfers any Naxely intellectual property to you beyond a limited license to use the Service as intended.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Disclaimer of Warranties</h2>
          <p>The Service is provided "as is" and "as available," without warranties of any kind, express or implied, including implied warranties of merchantability, fitness for a particular purpose, and non-infringement. We do not guarantee that the Service will be uninterrupted, error-free, or free of harmful components. You are responsible for backing up any data or reports important to you.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Limitation of Liability</h2>
          <p>To the fullest extent permitted by law, Naxely's total liability arising out of or related to these Terms or your use of the Service will not exceed the total fees you paid to Naxely in the 12 months preceding the claim. Naxely will not be liable for any indirect, incidental, consequential, or special damages, including lost profits or lost business opportunities, even if advised of the possibility of such damages.</p>
          <p>This limitation applies regardless of the legal theory of the claim, to the maximum extent permitted by applicable law.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Indemnification</h2>
          <p>You agree to indemnify and hold Naxely harmless from any claims, damages, or expenses (including reasonable legal fees) arising from your use of the Service, your violation of these Terms, or your violation of any third party's rights.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Cancellation & Termination</h2>
          <p>You may cancel your subscription at any time. Access to Pro/Agency features continues until the end of your current billing period.</p>
          <p>We may suspend or terminate your account if you violate these Terms, misuse the Service, or fail to pay applicable fees. Where reasonably possible, we will attempt to notify you before doing so.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Governing Law & Disputes</h2>
          <p>These Terms are governed by the laws of India. Before pursuing a formal claim, you agree to first contact us at hello@naxely.com so we can attempt to resolve the dispute informally.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Changes to These Terms</h2>
          <p>We may update these Terms from time to time. Material changes will be communicated via email or through the Service. Continued use after a change takes effect constitutes acceptance of the updated Terms.</p>

          <h2 className="font-semibold text-ink dark:text-paper text-base mt-6">Contact</h2>
          <p>Questions about these Terms? Email us at hello@naxely.com.</p>

          <p className="mt-8 text-xs text-ink/40">Last updated: July 2026</p>
        </div>
      </div>
    </div>
  )
}
