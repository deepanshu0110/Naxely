import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-white dark:bg-gray-900">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">Page not found</h1>
      <p className="text-gray-500 dark:text-gray-400">The page you are looking for does not exist.</p>
      <Link
        to="/dashboard"
        className="mt-2 rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-600"
      >
        Go back to dashboard
      </Link>
    </div>
  )
}
