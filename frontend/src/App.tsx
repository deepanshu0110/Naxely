import { Suspense, lazy } from 'react'
import { HelmetProvider } from 'react-helmet-async'
import { Analytics } from '@vercel/analytics/react'
import { Navigate, Outlet } from 'react-router-dom'
import type { RouteRecord } from 'vite-react-ssg'
import { Toaster } from 'react-hot-toast'
import useCookieYesGA4 from '@/hooks/useCookieYesGA4'
import useCookieYesClarity from '@/hooks/useCookieYesClarity'

const AuthCallback = lazy(() => import('@/pages/AuthCallback'))
const ForgotPassword = lazy(() => import('@/pages/ForgotPassword'))
const ResetPassword = lazy(() => import('@/pages/ResetPassword'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const NewReport = lazy(() => import('@/pages/NewReport'))
const ReportView = lazy(() => import('@/pages/ReportView'))
const Landing = lazy(() => import('@/pages/Landing'))
const Settings = lazy(() => import('@/pages/Settings'))
const Pricing = lazy(() => import('@/pages/Pricing'))
const NotFound = lazy(() => import('@/pages/NotFound'))
const SharedReportView = lazy(() => import('@/pages/SharedReportView'))
const Contact = lazy(() => import('@/pages/Contact'))
const Terms = lazy(() => import('@/pages/Terms'))
const Privacy = lazy(() => import('@/pages/Privacy'))
const Refund = lazy(() => import('@/pages/Refund'))
const Blog = lazy(() => import('@/pages/Blog'))
const BlogPostByok = lazy(() => import('@/pages/BlogPostByok'))
const BlogPostCsvToPdf = lazy(() => import('@/pages/BlogPostCsvToPdf'))
const BlogPostWhiteLabel = lazy(() => import('@/pages/BlogPostWhiteLabel'))
const BlogPostHub = lazy(() => import('@/pages/BlogPostHub'))
const BlogPostClientReporting = lazy(() => import('@/pages/BlogPostClientReporting'))
const BlogPostBestFreelanceReporting = lazy(() => import('@/pages/BlogPostBestFreelanceReporting'))
const BlogPostPythonCsvToPdf = lazy(() => import('@/pages/BlogPostPythonCsvToPdf'))
const BlogPostTwoWeeks = lazy(() => import('@/pages/BlogPostTwoWeeks'))
const ComparisonAgencyAnalytics = lazy(() => import('@/pages/ComparisonAgencyAnalytics'))
const ComparisonDatabox = lazy(() => import('@/pages/ComparisonDatabox'))
const ComparisonPowerdrill = lazy(() => import('@/pages/ComparisonPowerdrill'))
const ComparisonDashThis = lazy(() => import('@/pages/ComparisonDashThis'))
const ComparisonWhatagraph = lazy(() => import('@/pages/ComparisonWhatagraph'))
const Faq = lazy(() => import('@/pages/Faq'))
const Changelog = lazy(() => import('@/pages/Changelog'))
const Login = lazy(() => import('@/pages/Login'))
const Signup = lazy(() => import('@/pages/Signup'))

const LazyScheduledReports = lazy(() => import('@/pages/ScheduledReports'))
const LazyTemplates = lazy(() => import('@/pages/Templates'))
const ProtectedRoute = lazy(() => import('@/components/ProtectedRoute'))
const PublicOnlyRoute = lazy(() => import('@/components/PublicOnlyRoute'))

function Loading() {
  return (
    <div className="flex h-screen items-center justify-center bg-slate">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-amber-500" />
    </div>
  )
}

function RootLayout() {
  useCookieYesGA4()
  useCookieYesClarity()
  return (
    <HelmetProvider>
      <Suspense fallback={<Loading />}>
        <Outlet />
      </Suspense>
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
        element: <PublicOnlyRoute />,
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
        element: <ProtectedRoute />,
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
