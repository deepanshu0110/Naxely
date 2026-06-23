import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useReportStore } from '@/store/reportStore'
import { useAuthStore } from '@/store/authStore'
import WelcomeModal from '@/components/onboarding/WelcomeModal'
import Sidebar from '@/components/layout/Sidebar'
import ReportCard from '@/components/dashboard/ReportCard'
import EmptyState from '@/components/ui/EmptyState'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'

export default function Dashboard() {
  const { reports, isLoading, error, fetchReports, deleteReport } = useReportStore()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const fetchProfile = useAuthStore((s) => s.fetchProfile)
  const [showWelcome, setShowWelcome] = useState(false)

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  useEffect(() => {
    if (user && !user.has_completed_onboarding) {
      setShowWelcome(true)
    }
  }, [user])

  const handleWelcomeClose = () => {
    setShowWelcome(false)
    fetchProfile()
  }

  const EmptyIllustration = () => (
    <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="18" y="22" width="72" height="62" rx="5" stroke="#D97A34" stroke-width="1.5" />
      <line x1="30" y1="36" x2="68" y2="36" stroke="#D97A34" stroke-width="1.5" stroke-linecap="round" />
      <line x1="30" y1="44" x2="78" y2="44" stroke="#D97A34" stroke-width="1.5" stroke-linecap="round" />
      <line x1="30" y1="51" x2="72" y2="51" stroke="#D97A34" stroke-width="1.5" stroke-linecap="round" />
      <rect x="32" y="68" width="8" height="8" rx="1" stroke="#D97A34" stroke-width="1.5" />
      <rect x="46" y="58" width="8" height="18" rx="1" stroke="#D97A34" stroke-width="1.5" />
      <rect x="60" y="48" width="8" height="28" rx="1" stroke="#D97A34" stroke-width="1.5" />
      <circle cx="88" cy="34" r="13" stroke="#D97A34" stroke-width="1.5" />
      <line x1="97" y1="43" x2="106" y2="52" stroke="#D97A34" stroke-width="1.5" stroke-linecap="round" />
    </svg>
  )

  return (
    <div className="flex h-screen bg-slate dark:bg-darkBg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="mb-8 flex items-center justify-between">
            <h1 className="font-display text-2xl font-bold text-ink dark:text-gray-100">Your Reports</h1>
            <Button onClick={() => navigate('/report/new')}>+ New Report</Button>
          </div>

          {isLoading && reports.length === 0 ? (
            <div className="flex items-center justify-center py-20">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/30">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              <Button variant="ghost" size="sm" className="mt-3" onClick={() => fetchReports()}>
                Retry
              </Button>
            </div>
          ) : reports.length === 0 ? (
            <EmptyState
              illustration={<EmptyIllustration />}
              title="No reports yet"
              description="Upload a CSV to generate your first client-ready PDF report in minutes."
              action={
                <Button onClick={() => navigate('/report/new')}>Create Report</Button>
              }
            />
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <ReportCard key={report.id} report={report} onDelete={deleteReport} />
              ))}
            </div>
          )}
        </div>
      </main>
      {showWelcome && <WelcomeModal onClose={handleWelcomeClose} />}
    </div>
  )
}
