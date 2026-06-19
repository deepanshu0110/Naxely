import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate bg-paper/95 backdrop-blur dark:border-gray-700 dark:bg-ink/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/" className="font-display text-xl font-bold text-ink dark:text-gray-100">
          Naxely
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900">
            Features
          </a>
          <a href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900">
            Pricing
          </a>
          <a href="#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900">
            How it works
          </a>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Log in
          </Link>
          <Link
            to="/signup"
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
          >
            Start Free
          </Link>
        </div>
      </div>
    </nav>
  )
}
