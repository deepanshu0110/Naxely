import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useReportStore } from '@/store/reportStore'
import Sidebar from '@/components/layout/Sidebar'
import ReportCard from '@/components/dashboard/ReportCard'
import EmptyState from '@/components/ui/EmptyState'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'

export default function Dashboard() {
  const { reports, isLoading, error, fetchReports, deleteReport } = useReportStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  const EmptyIllustration = () => (
    <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="30" width="80" height="70" rx="6" fill="#F3F4F6" stroke="#D1D5DB" strokeWidth="2" />
      <rect x="30" y="45" width="40" height="4" rx="2" fill="#9CA3AF" />
      <rect x="30" y="55" width="55" height="4" rx="2" fill="#E5E7EB" />
      <rect x="30" y="65" width="45" height="4" rx="2" fill="#E5E7EB" />
      <rect x="30" y="75" width="35" height="4" rx="2" fill="#E5E7EB" />
      <circle cx="85" cy="35" r="15" fill="#FDF1E6" stroke="#D97A34" strokeWidth="2" />
      <path d="M80 35L85 30L90 35M85 30V42" stroke="#D97A34" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
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
              title="Generate your first report"
              description="Upload a CSV and get an AI-powered PDF in 2 minutes"
              action={
                <Button onClick={() => navigate('/report/new')}>Create Report</Button>
              }
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {reports.map((report) => (
                <ReportCard key={report.id} report={report} onDelete={deleteReport} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
