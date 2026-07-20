import React, { Suspense, useEffect } from 'react'
import { HelmetProvider } from 'react-helmet-async'
import { Analytics } from '@vercel/analytics/react'
import { Navigate, Outlet } from 'react-router-dom'
import type { RouteRecord } from 'vite-react-ssg'
import { Toaster } from 'react-hot-toast'
import useCookieYesGA4 from '@/hooks/useCookieYesGA4'
import useCookieYesClarity from '@/hooks/useCookieYesClarity'
import Login from '@/pages/Login'
import Signup from '@/pages/Signup'
import AuthCallback from '@/pages/AuthCallback'
import ForgotPassword from '@/pages/ForgotPassword'
import ResetPassword from '@/pages/ResetPassword'
import Dashboard from '@/pages/Dashboard'
import NewReport from '@/pages/NewReport'
import ReportView from '@/pages/ReportView'
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
import BlogPostHub from '@/pages/BlogPostHub'
import BlogPostClientReporting from '@/pages/BlogPostClientReporting'
import BlogPostBestFreelanceReporting from '@/pages/BlogPostBestFreelanceReporting'
import BlogPostPythonCsvToPdf from '@/pages/BlogPostPythonCsvToPdf'
import BlogPostTwoWeeks from '@/pages/BlogPostTwoWeeks'
import ComparisonAgencyAnalytics from '@/pages/ComparisonAgencyAnalytics'
import ComparisonDatabox from '@/pages/ComparisonDatabox'
import ComparisonPowerdrill from '@/pages/ComparisonPowerdrill'
import ComparisonDashThis from '@/pages/ComparisonDashThis'
import ComparisonWhatagraph from '@/pages/ComparisonWhatagraph'
import Faq from '@/pages/Faq'
import Changelog from '@/pages/Changelog'

const LazyScheduledReports = React.lazy(() => import('@/pages/ScheduledReports'))
const LazyTemplates = React.lazy(() => import('@/pages/Templates'))
const ProtectedRoute = React.lazy(() => import('@/components/ProtectedRoute'))
const PublicOnlyRoute = React.lazy(() => import('@/components/PublicOnlyRoute'))

function Loading() {
  return (
    <div className="flex h-screen items-center justify-center bg-slate">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-amber-500" />
    </div>
  )
}

function AuthInitializer() {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const idle = window.requestIdleCallback || ((cb: IdleRequestCallback) => setTimeout(cb, 10000))
      idle(() => {
        import('@/store/authStore').then(({ useAuthStore }) => {
          useAuthStore.getState().initialize()
        })
      })
    }
  }, [])
  return null
}

function RootLayout() {
  useCookieYesGA4()
  useCookieYesClarity()
  return (
    <HelmetProvider>
      <Outlet />
      <AuthInitializer />
      <Toaster position="top-right" />
      <Analytics />
    </HelmetProvider>
  )
}

export const routes: RouteRecord[] = [
  {
    element: <RootLayout />,
    children: [
      { path: '/', element: <Landing /> },
      {
        element: <Suspense fallback={<Loading />}><PublicOnlyRoute /></Suspense>,
        children: [
          { path: '/login', element: <Login /> },
          { path: '/signup', element: <Signup /> },
        ],
      },
      { path: '/auth/callback', element: <AuthCallback /> },
      { path: '/forgot-password', element: <ForgotPassword /> },
      { path: '/auth/reset-password', element: <ResetPassword /> },
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
      { path: '/blog/automating-client-reports', element: <BlogPostHub /> },
      { path: '/blog/client-reporting-software-guide', element: <BlogPostClientReporting /> },
      { path: '/blog/best-client-reporting-software-freelancers', element: <BlogPostBestFreelanceReporting /> },
      { path: '/blog/python-csv-to-pdf-reports', element: <BlogPostPythonCsvToPdf /> },
      { path: '/blog/two-weeks-building-naxely', element: <BlogPostTwoWeeks /> },
      { path: '/compare/agencyanalytics', element: <ComparisonAgencyAnalytics /> },
      { path: '/compare/databox', element: <ComparisonDatabox /> },
      { path: '/compare/powerdrill', element: <ComparisonPowerdrill /> },
      { path: '/compare/dashthis', element: <ComparisonDashThis /> },
      { path: '/compare/whatagraph', element: <ComparisonWhatagraph /> },
      { path: '/faq', element: <Faq /> },
      { path: '/changelog', element: <Changelog /> },
      {
        element: <Suspense fallback={<Loading />}><ProtectedRoute /></Suspense>,
        children: [
          { path: '/dashboard', element: <Dashboard /> },
          { path: '/report/new', element: <NewReport /> },
          { path: '/report/:id', element: <ReportView /> },
          { path: '/scheduled-reports', element: <Suspense fallback={<Loading />}><LazyScheduledReports /></Suspense> },
          { path: '/templates', element: <Suspense fallback={<Loading />}><LazyTemplates /></Suspense> },
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
