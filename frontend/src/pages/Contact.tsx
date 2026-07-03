import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function Contact() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>Contact — Naxely</title>
        <meta name="description" content="Have a question or need help with Naxely? Reach out to us at hello@naxely.com and we'll get back to you within 24 hours." />
        <link rel="canonical" href="https://naxely.com/contact" />
        <meta property="og:url" content="https://naxely.com/contact" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="Contact — Naxely" />
        <meta property="og:description" content="Get in touch with the Naxely team. We respond within 24 hours." />
        <meta property="og:image" content="https://naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Contact — Naxely" />
        <meta name="twitter:description" content="Get in touch with the Naxely team. We respond within 24 hours." />
        <meta name="twitter:image" content="https://naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://naxely.com/"},{"@type":"ListItem","position":2,"name":"Contact","item":"https://naxely.com/contact"}]})}</script>
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">Contact Us</h1>
        <p className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed mb-8">
          Have a question or need help? Reach out to us at{' '}
          <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a>
          {' '}and we&apos;ll get back to you within 24 hours.
        </p>
      </div>
    </div>
  )
}
