import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { format } from 'date-fns'
import { FileText, Clock, RefreshCw } from 'lucide-react'
import api from '@/lib/axios'

interface SharedReportData {
  id: string
  title: string
  status: string
  template_type: string
  ai_summary: string | null
  ai_insights: unknown[]
  ai_anomalies: unknown[]
  pdf_url: string | null
  created_at: string | null
  is_white_label?: boolean
}

export default function SharedReportView() {
  const { token } = useParams<{ token: string }>()
  const [report, setReport] = useState<SharedReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ type: 'expired' | 'not_found' | 'generic'; message: string } | null>(null)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    setError(null)
    api
      .get(`/share/${token}`)
      .then((res) => setReport(res.data))
      .catch((err) => {
        const status = err.response?.status
        if (status === 410) {
          setError({ type: 'expired', message: 'This link has expired or has been revoked.' })
        } else if (status === 404) {
          setError({ type: 'not_found', message: 'This link has expired or is invalid.' })
        } else {
          setError({ type: 'generic', message: 'Something went wrong. Please try again.' })
        }
      })
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <div data-testid="shared-report-skeleton" className="flex h-screen animate-pulse flex-col bg-paper dark:bg-darkBg">
        <header className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-7 w-64 rounded bg-gray-200 dark:bg-gray-700" />
          </div>
          <div className="h-5 w-32 rounded bg-gray-200 dark:bg-gray-700" />
        </header>
        <main className="flex-1 overflow-hidden bg-slate p-4 dark:bg-darkBg">
          <div className="h-full w-full rounded-lg border border-gray-200 bg-paper dark:border-gray-700 dark:bg-darkBg" />
        </main>
        <footer className="border-t border-gray-200 py-3 dark:border-gray-700">
          <div className="mx-auto h-4 w-28 rounded bg-gray-200 dark:bg-gray-700" />
        </footer>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-paper dark:bg-darkBg">
        <p className="text-sm text-gray-500 dark:text-gray-400">{error.message}</p>
        {error.type === 'generic' && (
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-2 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
        )}
      </div>
    )
  }

  if (!report) {
    return (
      <div className="flex h-screen items-center justify-center bg-paper dark:bg-darkBg">
        <p className="text-sm text-gray-500 dark:text-gray-400">Report not found.</p>
      </div>
    )
  }

  const showFooter = report.is_white_label !== true

  return (
    <div data-testid="shared-report-container" className="flex h-screen flex-col bg-paper dark:bg-darkBg">
      <header data-testid="shared-report-header" className="flex items-center justify-between border-b border-gray-200 px-6 py-4 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          <h1 data-testid="report-title" className="font-display text-xl font-bold text-ink dark:text-gray-100">
            {report.title}
          </h1>
        </div>
        {report.created_at && (
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Clock className="h-4 w-4" />
            {format(new Date(report.created_at), 'MMM d, yyyy')}
          </div>
        )}
      </header>

      <main data-testid="shared-report-main" className="flex-1 overflow-hidden bg-slate p-4 dark:bg-darkBg">
        {report.pdf_url ? (
          <iframe
            src={report.pdf_url}
            title="Report PDF"
            className="h-full w-full rounded-lg border border-gray-200 bg-paper dark:border-gray-700 dark:bg-darkBg"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">PDF preview not available</p>
          </div>
        )}
      </main>

      {showFooter && (
        <footer
          data-testid="powered-by-footer"
          className="border-t border-gray-200 py-3 text-center text-xs text-gray-400 dark:border-gray-700 dark:text-gray-500"
        >
          Powered by Naxely
        </footer>
      )}
    </div>
  )
}
