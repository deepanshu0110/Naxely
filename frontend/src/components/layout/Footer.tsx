import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 px-6 py-12">
      <div className="mx-auto max-w-2xl text-center">
        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-gray-600">
          <Link to="/blog/client-reporting-software-guide" className="hover:text-ink">How to Choose Client Reporting Software</Link>
          <span className="text-gray-300">·</span>
          <Link to="/blog/best-client-reporting-software-freelancers" className="hover:text-ink">Best for Freelancers (2026)</Link>
          <span className="text-gray-300">·</span>
          <Link to="/blog/automating-client-reports" className="hover:text-ink">Automated Client Reporting</Link>
          <span className="text-gray-300">·</span>
          <Link to="/blog/what-should-client-report-include-checklist" className="hover:text-ink">What Should a Client Report Include?</Link>
          <span className="text-gray-300">·</span>
          <Link to="/blog/excel-to-pdf-report-generator" className="hover:text-ink">Excel to PDF Report Generator</Link>
          <span className="text-gray-300">·</span>
          <Link to="/blog/two-weeks-building-naxely" className="hover:text-ink">Two Weeks Building Naxely</Link>
        </div>
        <p className="mt-4 text-xs text-gray-600">Naxely © 2026</p>
        <div className="mt-4 flex justify-center gap-4">
          <a href="https://toolfio.com" target="_blank" rel="noopener"><img src="https://toolfio.com/toolfio-dark-badge.png" alt="Featured on Toolfio" width="200" height="54" /></a>
          <a href="https://ideakiln.com/ideas/naxely" target="_blank" rel="noopener"><img src="https://ideakiln.com/light.svg" alt="Featured on Idea Kiln" width="200" height="54" /></a>
        </div>
      </div>
    </footer>
  )
}
