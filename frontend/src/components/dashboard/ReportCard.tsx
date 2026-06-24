import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { FileText, MoreHorizontal, Download, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { useCountUp } from '@/hooks/useCountUp'
import type { Report } from '@/types/report'

const statusVariant = (status: Report['status']) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'processing':
      return 'warning'
    case 'failed':
      return 'error'
  }
}

const statusLabel = (status: Report['status']) => {
  switch (status) {
    case 'completed':
      return 'Done'
    case 'processing':
      return 'Generating'
    case 'failed':
      return 'Failed'
  }
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

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(report.id)
      toast.success('Report deleted')
    } catch {
      toast.error('Failed to delete report')
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  return (
    <>
      <div
        className={`relative flex cursor-pointer items-center gap-4 rounded-xl border bg-paper p-4 shadow-sm transition-all duration-150 ease-in-out hover:shadow-md dark:bg-darkBg ${
          isSelected
            ? 'border-amber-500 ring-2 ring-amber-500/30 dark:border-amber-400'
            : 'border-amber-200/40 dark:border-amber-900/40'
        }`}
        onClick={() => navigate(`/report/${report.id}`)}
      >
        {onToggleSelect && (
          <div className="absolute left-3 top-3 z-10">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect(report.id)}
              onClick={(e) => e.stopPropagation()}
              className="h-4 w-4 cursor-pointer accent-amber-500"
            />
          </div>
        )}
        {/* Icon thumbnail */}
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-500/10">
          <FileText className="h-5 w-5 text-amber-500" />
        </div>

        {/* Title + date */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-ink dark:text-gray-100" title={report.title}>
            {report.title}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {format(new Date(report.created_at), 'MMM d, yyyy')}
          </p>
        </div>

        {/* Row count — hidden on mobile */}
        <div className="hidden flex-shrink-0 text-right sm:block">
          <p className="font-mono tabular-nums text-sm text-ink dark:text-gray-100">{displayRowCount}</p>
          <p className="text-[10px] text-gray-400 dark:text-gray-500">rows</p>
        </div>

        {/* Status badge */}
        <Badge variant={statusVariant(report.status)} text={statusLabel(report.status)} />

        {/* Download — always visible */}
        {report.pdf_url && (
          <a
            href={report.pdf_url}
            download
            onClick={(e) => e.stopPropagation()}
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md text-gray-400 transition-colors duration-150 ease-in-out hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            title="Download PDF"
          >
            <Download className="h-4 w-4" />
          </a>
        )}

        {/* 3-dot menu — View + Delete only */}
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
