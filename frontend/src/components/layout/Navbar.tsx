import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate bg-paper/95 backdrop-blur dark:border-gray-700 dark:bg-darkBg/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="font-display text-xl font-bold text-ink dark:text-gray-100">
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
          <Link to="/blog/automating-client-reports" className="text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
            Guides
          </Link>
          <Link to="/compare/agencyanalytics" className="text-sm font-medium text-gray-600 transition-colors duration-150 ease-in-out hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2">
            Compare
          </Link>
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
