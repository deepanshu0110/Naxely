import { HelmetProvider } from 'react-helmet-async'
import { Analytics } from '@vercel/analytics/react'
import { Navigate, Outlet } from 'react-router-dom'
import type { RouteRecord } from 'vite-react-ssg'
import { useAuthStore } from '@/store/authStore'
import { Toaster } from 'react-hot-toast'
import CookieConsent from '@/components/CookieConsent'
import Login from '@/pages/Login'
import Signup from '@/pages/Signup'
import AuthCallback from '@/pages/AuthCallback'
import Dashboard from '@/pages/Dashboard'
import NewReport from '@/pages/NewReport'
import ReportView from '@/pages/ReportView'
import ScheduledReports from '@/pages/ScheduledReports'
import Landing from '@/pages/Landing'
import Settings from '@/pages/Settings'
import Pricing from '@/pages/Pricing'
import NotFound from '@/pages/NotFound'
import SharedReportView from '@/pages/SharedReportView'
import Contact from '@/pages/Contact'
import Terms from '@/pages/Terms'
import Privacy from '@/pages/Privacy'
import Refund from '@/pages/Refund'
import Blog from '@/pages/Blog'
import BlogPostByok from '@/pages/BlogPostByok'
import BlogPostCsvToPdf from '@/pages/BlogPostCsvToPdf'
import BlogPostWhiteLabel from '@/pages/BlogPostWhiteLabel'

function RootLayout() {
  return (
    <HelmetProvider>
      <Outlet />
      <CookieConsent />
      <Toaster position="top-right" />
      <Analytics />
    </HelmetProvider>
  )
}

function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-pulse rounded bg-gray-200" />
          <div className="h-5 w-32 animate-pulse rounded bg-gray-200" />
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

function PublicOnlyRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-5 w-32 animate-pulse rounded bg-gray-200" />
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}

export const routes: RouteRecord[] = [
  {
    element: <RootLayout />,
    children: [
      { path: '/', element: <Landing /> },
      {
        element: <PublicOnlyRoute />,
        children: [
          { path: '/login', element: <Login /> },
          { path: '/signup', element: <Signup /> },
        ],
      },
      { path: '/auth/callback', element: <AuthCallback /> },
      { path: '/share/:token', element: <SharedReportView /> },
      { path: '/pricing', element: <Pricing /> },
      { path: '/contact', element: <Contact /> },
      { path: '/terms', element: <Terms /> },
      { path: '/privacy', element: <Privacy /> },
      { path: '/refund', element: <Refund /> },
      { path: '/blog', element: <Blog /> },
      { path: '/blog/byok-ai-reporting-tool', element: <BlogPostByok /> },
      { path: '/blog/csv-to-pdf-report-generator', element: <BlogPostCsvToPdf /> },
      { path: '/blog/white-label-client-reporting-agencies', element: <BlogPostWhiteLabel /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/dashboard', element: <Dashboard /> },
          { path: '/report/new', element: <NewReport /> },
          { path: '/report/:id', element: <ReportView /> },
          { path: '/scheduled-reports', element: <ScheduledReports /> },
          { path: '/settings', element: <Settings /> },
          { path: '/settings/api-key', element: <Navigate to="/settings" replace /> },
          { path: '/settings/billing', element: <Navigate to="/settings" replace /> },
          { path: '/settings/branding', element: <Navigate to="/settings" replace /> },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
]
