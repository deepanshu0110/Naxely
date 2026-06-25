import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useReportStore } from '@/store/reportStore'
import { useAuthStore } from '@/store/authStore'
import WelcomeModal from '@/components/onboarding/WelcomeModal'
import Sidebar from '@/components/layout/Sidebar'
import ReportCard from '@/components/dashboard/ReportCard'
import EmptyState from '@/components/ui/EmptyState'
import { NaxelyMark } from '@/components/ui/NaxelyMark'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import Modal from '@/components/ui/Modal'

export default function Dashboard() {
  const { reports, isLoading, error, fetchReports, deleteReport, bulkDeleteReports } = useReportStore()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const fetchProfile = useAuthStore((s) => s.fetchProfile)
  const [showWelcome, setShowWelcome] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [showBulkConfirm, setShowBulkConfirm] = useState(false)

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

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }, [])

  const selectAll = useCallback(() => setSelectedIds(new Set(reports.map((r) => r.id))), [reports])
  const clearSelection = useCallback(() => setSelectedIds(new Set()), [])

  const handleBulkDelete = async () => {
    setBulkDeleting(true)
    try {
      await bulkDeleteReports(Array.from(selectedIds))
      clearSelection()
      setShowBulkConfirm(false)
      toast.success(`Deleted ${selectedIds.size} report${selectedIds.size !== 1 ? 's' : ''}`)
    } catch {
      toast.error('Failed to delete reports')
    } finally {
      setBulkDeleting(false)
    }
  }

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
              illustration={<NaxelyMark size={48} />}
              title="No reports yet"
              description="Upload a CSV to generate your first client-ready PDF report in minutes."
              action={
                <Button onClick={() => navigate('/report/new')}>Create Report</Button>
              }
            />
          ) : (
            <div>
              {selectedIds.size > 0 && (
                <div className="mb-4 flex items-center gap-3 rounded-xl bg-ink px-4 py-3 dark:bg-gray-100">
                  <span className="flex-1 text-sm font-medium text-white dark:text-ink">
                    {selectedIds.size} selected
                  </span>
                  <button
                    onClick={selectAll}
                    className="text-sm text-gray-300 underline underline-offset-2 transition hover:text-white dark:text-gray-600 dark:hover:text-ink"
                  >
                    Select all ({reports.length})
                  </button>
                  <button
                    onClick={clearSelection}
                    className="text-sm text-gray-300 underline underline-offset-2 transition hover:text-white dark:text-gray-600 dark:hover:text-ink"
                  >
                    Clear
                  </button>
                  <Button variant="danger" size="sm" onClick={() => setShowBulkConfirm(true)}>
                    Delete {selectedIds.size}
                  </Button>
                </div>
              )}
              <div className="space-y-3">
                {reports.map((report) => (
                  <ReportCard
                    key={report.id}
                    report={report}
                    onDelete={deleteReport}
                    isSelected={selectedIds.has(report.id)}
                    onToggleSelect={toggleSelect}
                  />
                ))}
              </div>
            </div>
          )}

          <Modal
            isOpen={showBulkConfirm}
            onClose={() => setShowBulkConfirm(false)}
            title={`Delete ${selectedIds.size} report${selectedIds.size !== 1 ? 's' : ''}?`}
          >
            <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
              This will permanently delete {selectedIds.size} report{selectedIds.size !== 1 ? 's' : ''}
              and their PDFs. This cannot be undone.
            </p>
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setShowBulkConfirm(false)}>
                Cancel
              </Button>
              <Button variant="danger" className="flex-1" onClick={handleBulkDelete} loading={bulkDeleting}>
                Delete
              </Button>
            </div>
          </Modal>
        </div>
      </main>
      {showWelcome && <WelcomeModal onClose={handleWelcomeClose} />}
    </div>
  )
}
