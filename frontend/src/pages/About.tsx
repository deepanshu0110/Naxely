import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function About() {
  return (
    <div className="min-h-screen bg-paper dark:bg-darkBg">
      <Head>
        <title>About Naxely | Built by Deepanshu Garg</title>
        <meta name="description" content="Naxely is built by Deepanshu Garg, a freelance data analyst in India. Who builds it, why, and how to reach the founder directly." />
        <link rel="canonical" href="https://www.naxely.com/about" />
        <meta property="og:url" content="https://www.naxely.com/about" />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_US" />
        <meta property="og:title" content="About Naxely | Built by Deepanshu Garg" />
        <meta property="og:description" content="Naxely is built by Deepanshu Garg, a freelance data analyst in India. Who builds it, why, and how to reach the founder directly." />
        <meta property="og:image" content="https://www.naxely.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="About Naxely | Built by Deepanshu Garg" />
        <meta name="twitter:description" content="Naxely is built by Deepanshu Garg, a freelance data analyst in India. Who builds it, why, and how to reach the founder directly." />
        <meta name="twitter:image" content="https://www.naxely.com/og-image.png" />
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"https://www.naxely.com/"},{"@type":"ListItem","position":2,"name":"About","item":"https://www.naxely.com/about"}]})}</script>
        <script type="application/ld+json">{JSON.stringify({"@context":"https://schema.org","@type":"Person","name":"Deepanshu Garg","url":"https://www.naxely.com/about","jobTitle":"Founder, Naxely","sameAs":["https://www.linkedin.com/in/deepanshu-datascientist"]})}</script>
      </Head>
      <div className="mx-auto max-w-2xl px-6 py-24">
        <Link to="/" className="text-sm text-amber-600 hover:text-amber-700 mb-8 inline-block">&larr; Back to Home</Link>
        <h1 className="font-display text-3xl font-bold text-ink dark:text-paper mb-6">About Naxely</h1>
        <div className="text-ink/55 dark:text-paper/45 text-sm leading-relaxed space-y-5">
          <p>Naxely is built and run by one person, Deepanshu Garg, a freelance data analyst and data scientist based in India.</p>
          <p>I built Naxely after spending too many hours turning client spreadsheets into reports by hand. You upload a CSV, Excel file or Google Sheet, and Naxely turns it into a branded PDF or PPTX report with charts and a written summary.</p>
          <p>I work in Python, SQL, Excel, Power BI and Tableau. If you have a question about Naxely or a report that did not come out right, email me at <a href="mailto:hello@naxely.com" className="text-amber-600 hover:text-amber-700 underline">hello@naxely.com</a>. I read and answer every message myself.</p>
          <p><a href="https://www.linkedin.com/in/deepanshu-datascientist" target="_blank" rel="noopener noreferrer" className="text-amber-600 hover:text-amber-700 underline">Deepanshu Garg on LinkedIn</a></p>
        </div>
      </div>
      <footer className="border-t border-gray-200 px-6 py-12">
        <div className="mx-auto max-w-5xl text-center">
          <p className="text-xs text-gray-600">
            Made in India 🇮🇳 · Naxely © 2026
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-gray-600">
            <Link to="/about" className="hover:text-ink">About</Link>
            <span className="text-gray-300">·</span>
            <Link to="/contact" className="hover:text-ink">Contact</Link>
            <span className="text-gray-300">·</span>
            <Link to="/privacy" className="hover:text-ink">Privacy</Link>
            <span className="text-gray-300">·</span>
            <Link to="/terms" className="hover:text-ink">Terms</Link>
            <span className="text-gray-300">·</span>
            <Link to="/refund" className="hover:text-ink">Refund Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
