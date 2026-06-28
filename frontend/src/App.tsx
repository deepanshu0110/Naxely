import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useEffect } from 'react'
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
        <div className="h-5 w-32 animate-pulse rounded bg-gray-200" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}

function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Route>
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/share/:token" element={<SharedReportView />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="/terms" element={<Terms />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/report/new" element={<NewReport />} />
        <Route path="/report/:id" element={<ReportView />} />
        <Route path="/scheduled-reports" element={<ScheduledReports />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/settings/api-key" element={<Navigate to="/settings" replace />} />
        <Route path="/settings/billing" element={<Navigate to="/settings" replace />} />
        <Route path="/settings/branding" element={<Navigate to="/settings" replace />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  )
}
