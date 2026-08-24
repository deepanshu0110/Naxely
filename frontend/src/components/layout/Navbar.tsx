import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export default function Navbar() {
  const { isAuthenticated } = useAuthStore()
  return (
    <nav className="sticky top-0 z-50 border-b border-slate bg-paper/95 backdrop-blur dark:border-gray-700 dark:bg-darkBg/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to={isAuthenticated ? '/dashboard' : '/'} className="font-display text-xl font-bold text-ink dark:text-gray-100">
          Naxely
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
            Features
          </a>
          <a href="#pricing" className="text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
            Pricing
          </a>
          <a href="#how-it-works" className="text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
            How it works
          </a>
          <div className="relative group">
            <button className="flex items-center gap-1 text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
              Guides
              <svg className="h-3 w-3 text-gray-400 group-hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
            </button>
            <div className="absolute left-0 top-full mt-2 hidden w-72 rounded-xl border border-gray-200 bg-paper py-2 shadow-lg group-hover:block group-focus-within:block dark:border-gray-700 dark:bg-darkBg">
              <Link to="/blog/client-reporting-software-guide" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">How to Choose Client Reporting Software</Link>
              <Link to="/blog/best-client-reporting-software-freelancers" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Best for Freelancers (2026)</Link>
              <Link to="/blog/automating-client-reports" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Automated Client Reporting: Complete Guide</Link>
              <Link to="/blog/what-should-client-report-include-checklist" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">What Should a Client Report Include?</Link>
              <Link to="/blog/excel-to-pdf-report-generator" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Excel to PDF Report Generator</Link>
              <Link to="/blog/two-weeks-building-naxely" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Two Weeks Building Naxely</Link>
            </div>
          </div>
          <div className="relative group">
            <button className="flex items-center gap-1 text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
              Compare
              <svg className="h-3 w-3 text-gray-400 group-hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
            </button>
            <div className="absolute left-0 top-full mt-2 hidden w-64 rounded-xl border border-gray-200 bg-paper py-2 shadow-lg group-hover:block group-focus-within:block dark:border-gray-700 dark:bg-darkBg">
              <Link to="/compare/agencyanalytics" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">AgencyAnalytics</Link>
              <Link to="/compare/databox" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Databox</Link>
              <Link to="/compare/powerdrill" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Powerdrill</Link>
              <Link to="/compare/dashthis" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">DashThis</Link>
              <Link to="/compare/whatagraph" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Whatagraph</Link>
              <Link to="/compare/klipfolio" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Klipfolio</Link>
              <Link to="/compare/bonsai" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Bonsai</Link>
              <Link to="/compare/plutio" className="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100">Plutio</Link>
              <div className="my-1 border-t border-gray-100 dark:border-gray-700" />
              <Link to="/blog" className="block px-4 py-2 text-sm font-medium text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20">See all comparisons →</Link>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 transition-colors duration-150 ease-in-out hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            Log in
          </Link>
          <Link
            to="/signup"
            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors duration-150 ease-in-out hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:ring-offset-2"
          >
            Start Free
          </Link>
        </div>
      </div>
    </nav>
  )
}
