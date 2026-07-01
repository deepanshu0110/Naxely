import { useEffect, useState, useCallback } from 'react'
import { Pause, Play, Trash2, Edit3, Plus, AlertCircle, Upload, X } from 'lucide-react'
import Sidebar from '@/components/layout/Sidebar'
import EmptyState from '@/components/ui/EmptyState'
import { NaxelyMark } from '@/components/ui/NaxelyMark'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import UpgradePrompt from '@/components/ui/UpgradePrompt'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import type { ScheduledReport, ScheduledReportCreatePayload, ScheduledReportUpdatePayload } from '@/types/api'
import toast from 'react-hot-toast'

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function frequencyLabel(f: string): string {
  return f.charAt(0).toUpperCase() + f.slice(1)
}

type FormMode = 'create' | 'edit'

export default function ScheduledReports() {
  const { user } = useAuthStore()
  const isAgency = user?.tier === 'agency'

  const [reports, setReports] = useState<ScheduledReport[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [formMode, setFormMode] = useState<FormMode>('create')
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formName, setFormName] = useState('')
  const [formFrequency, setFormFrequency] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [formEmails, setFormEmails] = useState<string[]>([])
  const [formEmailInput, setFormEmailInput] = useState('')
  const [formEmailError, setFormEmailError] = useState<string | null>(null)
  const [formUploadId, setFormUploadId] = useState<string | null>(null)
  const [formUploadFile, setFormUploadFile] = useState<File | null>(null)
  const [formUploading, setFormUploading] = useState(false)
  const [formSubmitting, setFormSubmitting] = useState(false)
  const [formNameError, setFormNameError] = useState<string | null>(null)

  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [deleteName, setDeleteName] = useState('')
  const [deleting, setDeleting] = useState(false)

  const fetchReports = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const { data } = await api.get<ScheduledReport[]>('/scheduled-reports')
      setReports(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load scheduled reports'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAgency) fetchReports()
    else setIsLoading(false)
  }, [isAgency, fetchReports])

  function openCreateForm() {
    setFormMode('create')
    setEditingId(null)
    setFormName('')
    setFormFrequency('daily')
    setFormEmails([])
    setFormEmailInput('')
    setFormEmailError(null)
    setFormUploadId(null)
    setFormUploadFile(null)
    setFormNameError(null)
    setFormOpen(true)
  }

  function openEditForm(r: ScheduledReport) {
    setFormMode('edit')
    setEditingId(r.id)
    setFormName(r.name)
    setFormFrequency(r.frequency)
    setFormEmails([...r.recipient_emails])
    setFormEmailInput('')
    setFormEmailError(null)
    setFormUploadId(null)
    setFormUploadFile(null)
    setFormNameError(null)
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
  }

  function handleEmailKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addEmail()
    }
  }

  function addEmail() {
    const val = formEmailInput.trim().replace(/,+$/, '')
    if (!val) return
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(val)) {
      setFormEmailError('Invalid email format')
      return
    }
    setFormEmailError(null)
    if (!formEmails.includes(val)) {
      setFormEmails([...formEmails, val])
    }
    setFormEmailInput('')
  }

  function removeEmail(email: string) {
    setFormEmails(formEmails.filter((e) => e !== email))
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setFormUploadFile(file)
    setFormUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post<{ upload_id: string; filename: string }>('/reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setFormUploadId(data.upload_id)
      toast.success('File uploaded')
    } catch {
      toast.error('Failed to upload file')
      setFormUploadFile(null)
    } finally {
      setFormUploading(false)
    }
  }

  function validateForm(): boolean {
    let valid = true
    if (!formName.trim()) {
      setFormNameError('Name is required')
      valid = false
    } else {
      setFormNameError(null)
    }
    if (formEmails.length === 0) {
      setFormEmailError('At least one recipient is required')
      valid = false
    } else {
      setFormEmailError(null)
    }
    if (formMode === 'create' && !formUploadId) {
      toast.error('Please upload a source file')
      valid = false
    }
    return valid
  }

  async function handleFormSubmit() {
    if (!validateForm()) return
    setFormSubmitting(true)
    try {
      if (formMode === 'create') {
        const payload: ScheduledReportCreatePayload = {
          upload_id: formUploadId!,
          name: formName.trim(),
          frequency: formFrequency,
          recipient_emails: formEmails,
        }
        await api.post('/scheduled-reports', payload)
        toast.success('Scheduled report created')
      } else {
        const payload: ScheduledReportUpdatePayload = {
          name: formName.trim(),
          frequency: formFrequency,
          recipient_emails: formEmails,
        }
        await api.patch(`/scheduled-reports/${editingId}`, payload)
        toast.success('Scheduled report updated')
      }
      closeForm()
      await fetchReports()
    } catch {
    } finally {
      setFormSubmitting(false)
    }
  }

  async function handleToggleActive(r: ScheduledReport) {
    try {
      await api.patch(`/scheduled-reports/${r.id}`, { is_active: !r.is_active })
      setReports((prev) =>
        prev.map((rep) => (rep.id === r.id ? { ...rep, is_active: !rep.is_active } : rep)),
      )
      toast.success(r.is_active ? 'Report paused' : 'Report resumed')
    } catch {
    }
  }

  function openDeleteModal(r: ScheduledReport) {
    setDeleteId(r.id)
    setDeleteName(r.name)
  }

  function closeDeleteModal() {
    setDeleteId(null)
    setDeleteName('')
  }

  async function handleDelete() {
    if (!deleteId) return
    setDeleting(true)
    try {
      await api.delete(`/scheduled-reports/${deleteId}`)
      setReports((prev) => prev.filter((r) => r.id !== deleteId))
      toast.success('Scheduled report deleted')
      closeDeleteModal()
    } catch {
    } finally {
      setDeleting(false)
    }
  }

  if (!isAgency) {
    return (
      <div className="flex h-screen bg-slate dark:bg-darkBg">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-6 py-8">
            <h1 className="mb-8 font-display text-2xl font-bold text-ink dark:text-gray-100">Scheduled Reports</h1>
            <UpgradePrompt feature="Scheduled Reports" tier="Agency" />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-slate dark:bg-darkBg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="mb-8 flex items-center justify-between">
            <h1 className="font-display text-2xl font-bold text-ink dark:text-gray-100">Scheduled Reports</h1>
            <Button onClick={openCreateForm}>
              <Plus className="mr-1.5 h-4 w-4" />
              New Schedule
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/30">
              <AlertCircle className="mx-auto mb-2 h-6 w-6 text-red-500 dark:text-red-400" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              <Button variant="ghost" size="sm" className="mt-3" onClick={fetchReports}>
                Retry
              </Button>
            </div>
          ) : reports.length === 0 ? (
            <EmptyState
              illustration={<NaxelyMark size={48} />}
              title="No scheduled reports"
              description="Set up recurring reports to automatically generate and email PDFs to your clients on a daily, weekly, or monthly cadence."
              action={
                <Button onClick={openCreateForm}>
                  <Plus className="mr-1.5 h-4 w-4" />
                  Create Schedule
                </Button>
              }
            />
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate bg-paper shadow-md dark:border-gray-700 dark:bg-darkBg">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-gray-400">
                    <th className="px-4 py-3 font-body">Name</th>
                    <th className="px-4 py-3 font-body">Frequency</th>
                    <th className="px-4 py-3 font-body">Next Run</th>
                    <th className="px-4 py-3 font-body">Last Run</th>
                    <th className="px-4 py-3 font-body">Recipients</th>
                    <th className="px-4 py-3 font-body">Status</th>
                    <th className="px-4 py-3 font-body" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate dark:divide-gray-700">
                  {reports.map((r) => (
                    <tr key={r.id} className="group transition-colors hover:bg-amber-50/40 dark:hover:bg-amber-900/10">
                      <td className="max-w-[200px] truncate px-4 py-3 font-medium text-ink dark:text-gray-200">
                        {r.name}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {frequencyLabel(r.frequency)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-400">
                        {formatDate(r.next_run_at)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-400">
                        {formatDate(r.last_run_at)}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-sm font-medium text-ink dark:text-gray-200">
                          {r.recipient_emails.length}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={r.is_active ? 'success' : 'neutral'}
                          text={r.is_active ? 'Active' : 'Paused'}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleToggleActive(r)}
                            className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-slate hover:text-ink dark:hover:bg-gray-700 dark:hover:text-gray-200"
                            title={r.is_active ? 'Pause' : 'Resume'}
                          >
                            {r.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                          </button>
                          <button
                            onClick={() => openEditForm(r)}
                            className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-slate hover:text-ink dark:hover:bg-gray-700 dark:hover:text-gray-200"
                            title="Edit"
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => openDeleteModal(r)}
                            className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20 dark:hover:text-red-400"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Create / Edit Modal */}
      <Modal
        isOpen={formOpen}
        onClose={closeForm}
        title={formMode === 'create' ? 'Create Scheduled Report' : 'Edit Scheduled Report'}
      >
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Name</label>
            <input
              type="text"
              value={formName}
              onChange={(e) => { setFormName(e.target.value); setFormNameError(null) }}
              placeholder="Weekly Client Summary"
              className="w-full rounded-lg border border-slate bg-paper px-3 py-2 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-paper dark:placeholder-gray-500"
            />
            {formNameError && <p className="mt-1 text-xs text-red-500">{formNameError}</p>}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Frequency</label>
            <select
              value={formFrequency}
              onChange={(e) => setFormFrequency(e.target.value as 'daily' | 'weekly' | 'monthly')}
              className="w-full rounded-lg border border-slate bg-paper px-3 py-2 text-sm text-ink focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-paper"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Recipient Emails</label>
            <div className="flex flex-wrap gap-1.5 rounded-lg border border-slate bg-paper p-1.5 focus-within:border-amber-500 focus-within:ring-1 focus-within:ring-amber-500 dark:border-gray-600 dark:bg-darkBg">
              {formEmails.map((email) => (
                <span
                  key={email}
                  className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                >
                  {email}
                  <button onClick={() => removeEmail(email)} className="hover:text-amber-900 dark:hover:text-amber-100">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              <input
                type="text"
                value={formEmailInput}
                onChange={(e) => { setFormEmailInput(e.target.value); setFormEmailError(null) }}
                onKeyDown={handleEmailKeyDown}
                onBlur={() => { if (formEmailInput) addEmail() }}
                placeholder={formEmails.length === 0 ? 'Enter email, press Enter' : 'Add another...'}
                className="min-w-[140px] flex-1 border-0 bg-transparent px-1 py-1 text-sm text-ink placeholder-gray-400 focus:outline-none dark:text-paper dark:placeholder-gray-500"
              />
            </div>
            {formEmailError && <p className="mt-1 text-xs text-red-500">{formEmailError}</p>}
          </div>

          {formMode === 'create' && (
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Source File</label>
              {formUploadId ? (
                <div className="flex items-center gap-2 rounded-lg border border-mint/30 bg-mint/5 px-3 py-2 text-sm text-mint dark:border-mint/20 dark:bg-mint/10">
                  <Upload className="h-4 w-4" />
                  <span className="flex-1 truncate">{formUploadFile?.name}</span>
                  <button
                    onClick={() => { setFormUploadId(null); setFormUploadFile(null) }}
                    className="text-mint/60 hover:text-mint"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate px-4 py-3 text-sm text-gray-500 transition-colors hover:border-amber-400 hover:text-amber-600 dark:border-gray-600 dark:hover:border-amber-500 dark:hover:text-amber-400">
                  <Upload className="h-4 w-4" />
                  <span>{formUploading ? 'Uploading...' : 'Upload CSV or XLSX'}</span>
                  <input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={handleFileUpload}
                    disabled={formUploading}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" size="sm" onClick={closeForm} disabled={formSubmitting}>
              Cancel
            </Button>
            <Button size="sm" loading={formSubmitting} onClick={handleFormSubmit}>
              {formMode === 'create' ? 'Create' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={!!deleteId} onClose={closeDeleteModal} title="Delete Scheduled Report">
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          Are you sure you want to delete <span className="font-medium text-ink dark:text-gray-200">&ldquo;{deleteName}&rdquo;</span>? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" size="sm" onClick={closeDeleteModal} disabled={deleting}>
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
