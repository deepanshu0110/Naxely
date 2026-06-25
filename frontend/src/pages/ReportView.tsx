import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { Download, Share2, Trash2, Clock, FileText, AlertTriangle, X, Presentation } from 'lucide-react'
import toast from 'react-hot-toast'
import Sidebar from '@/components/layout/Sidebar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import InsightCard from '@/components/report/InsightCard'
import UpgradePrompt from '@/components/ui/UpgradePrompt'
import Modal from '@/components/ui/Modal'
import api from '@/lib/axios'
import { useAuthStore } from '@/store/authStore'
import { useReportStore } from '@/store/reportStore'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { useCountUp } from '@/hooks/useCountUp'
import type { Report } from '@/types/report'

export default function ReportView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const isPro = user?.tier === 'pro' || user?.tier === 'agency'
  const deleteReport = useReportStore((s) => s.deleteReport)

  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [pptxLoading, setPptxLoading] = useState(false)
  const reducedMotion = useReducedMotion()
  const displayGenTime = useCountUp(
    report?.generation_time_seconds != null ? Math.round(report.generation_time_seconds) : null,
    700,
    reducedMotion,
  )
  const displayRowCount = useCountUp(
    typeof report?.row_count === 'number' ? report.row_count : null,
    700,
    reducedMotion,
  )

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api
      .get(`/reports/${id}`)
      .then((res) => setReport(res.data))
      .catch(() => setError('Failed to load report'))
      .finally(() => setLoading(false))
  }, [id])

  const handleDelete = async () => {
    if (!id) return
    setDeleting(true)
    try {
      await deleteReport(id)
      navigate('/dashboard')
    } catch {
      toast.error('Failed to delete report')
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  const handleRetry = async () => {
    if (!id) return
    setRetrying(true)
    try {
      await api.post(`/reports/${id}/retry`)
      navigate('/dashboard')
    } catch {
      toast.error('Failed to retry report generation')
    } finally {
      setRetrying(false)
    }
  }

  const handleShare = async () => {
    if (!id) return
    try {
      const { data } = await api.post(`/reports/${id}/share`, { expires_days: 30, password: null })
      await navigator.clipboard.writeText(data.share_url)
      setReport((prev) => prev ? { ...prev, share_token: data.share_token } : null)
      toast.success('Share link copied!')
    } catch {
      toast.error('Failed to create share link')
    }
  }

  const handlePptxExport = async () => {
    if (!id) return
    setPptxLoading(true)
    try {
      const response = await api.get(`/reports/${id}/export/pptx`, {
        responseType: 'blob',
      })
      const blob = response.data
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `naxely_report_${id.slice(0, 8)}.pptx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('PowerPoint exported successfully')
    } catch {
      toast.error('Export failed. Please try again.')
    } finally {
      setPptxLoading(false)
    }
  }

  const handleRevokeShare = async () => {
    if (!id) return
    try {
      await api.delete(`/reports/${id}/share`)
      setReport((prev) => prev ? { ...prev, share_token: null } : null)
      toast.success('Share link revoked')
    } catch {
      toast.error('Failed to revoke share link')
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-paper dark:bg-darkBg">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-paper dark:bg-darkBg">
        <p className="text-gray-500 dark:text-gray-400">{error ?? 'Report not found'}</p>
        <Button variant="ghost" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </div>
    )
  }

  const statusVariant = (status: Report['status']) => {
    switch (status) {
      case 'completed':
        return 'success' as const
      case 'processing':
        return 'warning' as const
      case 'failed':
        return 'error' as const
    }
  }

  return (
    <div className="flex h-screen bg-slate dark:bg-darkBg">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-gray-200 bg-paper px-6 py-4 dark:border-gray-700 dark:bg-darkBg">
          <div className="flex items-center gap-4">
            <h1 className="font-display text-xl font-bold text-ink dark:text-gray-100">{report.title}</h1>
            <Badge variant={statusVariant(report.status)} text={report.status} />
          </div>
          <div className="flex items-center gap-2">
            {report.pdf_url && (
              <a href={report.pdf_url} download>
                <Button variant="primary" size="sm">
                  <Download className="mr-1.5 h-4 w-4" /> Download PDF
                </Button>
              </a>
            )}
            {user?.tier === 'agency' ? (
              <Button variant="outline" size="sm" onClick={handlePptxExport} loading={pptxLoading}>
                <Presentation className="mr-1.5 h-4 w-4" /> Export as PowerPoint
              </Button>
            ) : (
              <Button variant="outline" size="sm" disabled title="Agency plan required">
                <Presentation className="mr-1.5 h-4 w-4" /> Export as PowerPoint
              </Button>
            )}
            {isPro && report.share_token ? (
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={handleShare}>
                  <Share2 className="mr-1.5 h-4 w-4" /> Share
                </Button>
                <Button variant="danger" size="sm" onClick={handleRevokeShare}>
                  <X className="mr-1.5 h-4 w-4" /> Revoke
                </Button>
              </div>
            ) : isPro && (
              <Button variant="ghost" size="sm" onClick={handleShare}>
                <Share2 className="mr-1.5 h-4 w-4" /> Share
              </Button>
            )}
            <Button variant="danger" size="sm" onClick={() => setConfirmDelete(true)}>
              <Trash2 className="mr-1.5 h-4 w-4" /> Delete
            </Button>
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto bg-slate p-4 dark:bg-darkBg">
            {report.status === 'failed' ? (
              <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
                <AlertTriangle className="h-12 w-12 text-red-400" />
                <div className="text-center">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Report generation failed</h2>
                  {report.error_message && (
                    <p className="mt-2 max-w-md text-sm text-gray-500 dark:text-gray-400">
                      {report.error_message}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                    Your column mapping and settings are preserved.
                  </p>
                </div>
                <Button size="sm" loading={retrying} onClick={handleRetry}>
                  Try Again
                </Button>
              </div>
            ) : report.pdf_url ? (
              <iframe
                src={report.pdf_url}
                title="Report PDF"
                className="h-full w-full rounded-lg border border-gray-200 bg-paper dark:border-gray-700 dark:bg-darkBg"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <p className="text-gray-500 dark:text-gray-400">PDF preview not available</p>
              </div>
            )}
          </div>

          <div className="w-96 overflow-y-auto border-l border-gray-200 bg-paper p-6 dark:border-gray-700 dark:bg-darkBg">
            <div className="space-y-6">
              {report.ai_skipped && (
                <div className="rounded-lg border border-orange-200 bg-orange-50 p-3 dark:border-orange-800 dark:bg-orange-900/30">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-orange-600 dark:text-orange-400" />
                    <div className="flex-1 text-sm text-orange-800 dark:text-orange-200">
                      <p className="font-medium">AI insights were rate-limited.</p>
                      <p className="mt-1 text-xs text-orange-600 dark:text-orange-400">
                        Upload the same CSV and generate a new report to retry.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {report.status !== 'failed' && report.error_message && (
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-800 dark:bg-yellow-900/30">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">{report.error_message}</p>
                  </div>
                </div>
              )}

              {report.generation_time_seconds != null && (
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <Clock className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  Generated in <span className="font-mono tabular-nums">{displayGenTime}</span> seconds
                </div>
              )}

              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <FileText className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                <span className="font-mono tabular-nums">{displayRowCount}</span> rows
              </div>

              {isPro && report.ai_summary && (() => {
                const text = report.ai_summary.trim();
                const firstDot = text.indexOf('.');
                const lead = firstDot > 30 ? text.slice(0, firstDot + 1) : text;
                const body = firstDot > 30 ? text.slice(firstDot + 1).trim() : '';
                return (
                  <div className="rounded-xl border border-black/5 dark:border-white/5 bg-white dark:bg-[#1e1c18] p-5">
                    <h3 className="mb-3 text-xs font-medium tracking-widest uppercase text-amber-600 dark:text-amber-400">
                      AI Summary
                    </h3>
                    <p className="font-display text-[15px] font-semibold text-ink dark:text-paper leading-snug mb-3">
                      {lead}
                    </p>
                    {body && (
                      <p className="text-sm text-ink/60 dark:text-paper/50 leading-relaxed">
                        {body}
                      </p>
                    )}
                  </div>
                );
              })()}

              {isPro && report.ai_insights && report.ai_insights.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">Insights</h3>
                  <div className="space-y-3">
                    {report.ai_insights.map((insight, idx) => (
                      <InsightCard key={idx} insight={insight} />
                    ))}
                  </div>
                </div>
              )}

              {!isPro && (
                <UpgradePrompt feature="AI Summary & Insights" />
              )}

              {isPro && report.ai_anomalies && report.ai_anomalies.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">Anomaly Alerts</h3>
                  <div className="space-y-2">
                    {report.ai_anomalies.map((anomaly, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-800 dark:bg-yellow-900/30"
                      >
                        <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
                        <div>
                          <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                            {anomaly.column}: <span className="font-mono tabular-nums">{anomaly.value}</span>
                          </p>
                          <p className="text-xs text-yellow-600 dark:text-yellow-400">
                            Expected: <span className="font-mono tabular-nums">{anomaly.expected}</span> — Deviation: <span className="font-mono tabular-nums">{anomaly.deviation}</span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-xs text-gray-400 dark:text-gray-500">
                Created {format(new Date(report.created_at), 'MMM d, yyyy h:mm a')}
              </p>
            </div>
          </div>
        </div>
      </main>

      <Modal isOpen={confirmDelete} onClose={() => setConfirmDelete(false)} title="Delete Report">
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          Are you sure you want to delete "{report.title}"? This cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" loading={deleting} onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  )
}
