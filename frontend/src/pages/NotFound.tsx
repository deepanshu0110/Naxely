import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-paper dark:bg-darkBg">
      <Head>
        <title>Page Not Found — Naxely</title>
        <meta name="robots" content="noindex, nofollow" />
      </Head>
      <h1 className="font-display text-4xl font-bold text-ink dark:text-gray-100">Page not found</h1>
      <p className="text-gray-500 dark:text-gray-400">The page you are looking for does not exist.</p>
      <Link
        to="/dashboard"
        className="mt-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors duration-150 ease-in-out hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
      >
        Go back to dashboard
      </Link>
    </div>
  )
}
