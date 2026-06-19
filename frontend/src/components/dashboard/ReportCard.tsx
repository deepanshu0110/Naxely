import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { MoreHorizontal, Download, Eye, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
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

export default function ReportCard({ report, onDelete }: { report: Report; onDelete: (id: string) => void }) {
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

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

  const truncatedTitle = report.title.length > 50 ? report.title.slice(0, 50) + '...' : report.title

  return (
    <>
      <div className="rounded-xl border border-slate bg-paper p-4 shadow-sm transition-all duration-150 ease-in-out hover:shadow-md dark:border-gray-700 dark:bg-darkBg">
        <div className="mb-3 flex items-start justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100" title={report.title}>
            {truncatedTitle}
          </h3>
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="rounded-md p-1 text-gray-400 transition-colors duration-150 ease-in-out hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:hover:bg-gray-700 dark:hover:text-gray-300"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-8 z-10 w-40 rounded-lg border border-slate bg-paper py-1 shadow-lg dark:border-gray-700 dark:bg-darkBg">
                {report.pdf_url && (
                  <a
                    href={report.pdf_url}
                    download
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 transition-colors duration-150 ease-in-out hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-gray-300 dark:hover:bg-gray-700/50"
                    onClick={() => setMenuOpen(false)}
                  >
                    <Download className="h-4 w-4" /> Download PDF
                  </a>
                )}
                <button
                  onClick={() => {
                    setMenuOpen(false)
                    navigate(`/report/${report.id}`)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 transition-colors duration-150 ease-in-out hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-gray-300 dark:hover:bg-gray-700/50"
                >
                  <Eye className="h-4 w-4" /> View
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

        <div className="mb-3 flex flex-wrap gap-2">
          <Badge variant="info" text={report.template_type} />
          <Badge variant={statusVariant(report.status)} text={report.status.charAt(0).toUpperCase() + report.status.slice(1)} />
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{report.row_count.toLocaleString()} rows</span>
          <span>{format(new Date(report.created_at), 'MMM d, yyyy')}</span>
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
