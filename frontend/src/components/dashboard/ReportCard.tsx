import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { FileText, MoreHorizontal, Download, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/axios'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { useCountUp } from '@/hooks/useCountUp'
import type { Report } from '@/types/report'

const statusVariant = (status: Report['status']) => {
  switch (status) {
    case 'completed': return 'success' as const
    case 'processing': return 'warning' as const
    case 'failed': return 'error' as const
  }
}

const statusLabel: Record<Report['status'], string> = {
  completed: 'Done',
  processing: 'Generating',
  failed: 'Failed',
}

interface ReportCardProps {
  report: Report
  onDelete: (id: string) => void
  isSelected?: boolean
  onToggleSelect?: (id: string) => void
}

export default function ReportCard({ report, onDelete, isSelected, onToggleSelect }: ReportCardProps) {
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const reducedMotion = useReducedMotion()
  const displayRowCount = useCountUp(report.row_count, 700, reducedMotion)

  const handleDownloadPdf = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!report.pdf_url) return
    try {
      const response = await api.get(`/reports/${report.id}/download`, {
        responseType: 'blob',
      })
      const blob = response.data
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `naxely_report_${report.id.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to download PDF')
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(report.id)
      toast.success('Report deleted')
    } catch {
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <>
      <div
        className={`group relative flex cursor-pointer items-center gap-4 rounded-xl border bg-paper p-4 shadow-sm transition-all duration-150 ease-in-out hover:shadow-md dark:bg-darkBg ${
          isSelected
            ? 'border-amber-500 ring-2 ring-amber-500/30 dark:border-amber-400'
            : 'border-amber-200/40 dark:border-amber-900/40'
        }`}
        onClick={() => navigate(`/report/${report.id}`)}
      >
        {onToggleSelect && (
          <div
            className={`absolute left-3 top-3 z-10 transition-opacity duration-150 ${
              isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
            }`}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect(report.id)}
              onClick={(e) => e.stopPropagation()}
              className="h-4 w-4 cursor-pointer accent-amber-500"
            />
          </div>
        )}

        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-500/10">
          <FileText className="h-5 w-5 text-amber-500" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate font-display text-sm font-semibold text-ink dark:text-gray-100" title={report.title}>
            {report.title}
          </p>
          <div className="mt-0.5 flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
            <span>{format(new Date(report.created_at), 'MMM d, yyyy')}</span>
            <span className="text-gray-300 dark:text-gray-600">·</span>
            <span className="font-mono tabular-nums">{displayRowCount}</span>
            <span>rows</span>
          </div>
        </div>

        <Badge variant={statusVariant(report.status)} text={statusLabel[report.status]} />

        {report.pdf_url && (
          <button
            onClick={handleDownloadPdf}
            className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded text-gray-300 opacity-0 transition-all duration-150 ease-in-out hover:bg-gray-100 hover:text-gray-600 group-hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            title="Download PDF"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
        )}

        <div className="relative flex-shrink-0">
          <button
            onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen) }}
            className="flex h-8 w-8 items-center justify-center rounded-md text-gray-400 transition-colors duration-150 ease-in-out hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-9 z-10 w-36 rounded-lg border border-slate bg-paper py-1 shadow-lg dark:border-gray-700 dark:bg-darkBg">
              <button
                onClick={() => {
                  setMenuOpen(false)
                  navigate(`/report/${report.id}`)
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 transition-colors duration-150 ease-in-out hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-gray-300 dark:hover:bg-gray-700/50"
              >
                View
              </button>
              <button
                onClick={() => {
                  setMenuOpen(false)
                  setConfirmDelete(true)
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 transition-colors duration-150 ease-in-out hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-red-400 dark:hover:bg-red-900/30"
              >
                <Trash2 className="h-4 w-4" /> Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={confirmDelete} onClose={() => setConfirmDelete(false)} title="Delete Report">
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          Are you sure you want to delete "{report.title}"? This action cannot be undone.
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
    </>
  )
}
