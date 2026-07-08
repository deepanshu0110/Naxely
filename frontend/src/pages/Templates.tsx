import { useEffect, useState, useCallback } from 'react'
import { Plus, Trash2, Edit3, AlertCircle, BookOpen, Briefcase, BarChart3, MessageCircle } from 'lucide-react'
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
import type { Template } from '@/types/api'
import toast from 'react-hot-toast'

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const toneCards = [
  { id: 'professional', label: 'Professional', icon: Briefcase },
  { id: 'casual', label: 'Casual', icon: MessageCircle },
  { id: 'data-heavy', label: 'Data-heavy', icon: BarChart3 },
  { id: 'story-driven', label: 'Story-driven', icon: BookOpen },
]

const freeSections = [
  { id: 'charts', label: 'Charts' },
  { id: 'kpi_overview', label: 'Key Metrics' },
  { id: 'data_table', label: 'Data Table' },
]

const proSections = [
  { id: 'executive_summary', label: 'Executive Summary' },
  { id: 'insights', label: 'AI Insights' },
  { id: 'anomalies', label: 'Anomaly Detection' },
  { id: 'trends', label: 'Trends' },
  { id: 'appendix', label: 'Appendix' },
]

const allSections = [...freeSections, ...proSections]

type FormMode = 'create' | 'edit'

export default function Templates() {
  const { user } = useAuthStore()
  const isPro = user?.tier === 'pro' || user?.tier === 'agency'

  const [templates, setTemplates] = useState<Template[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [formMode, setFormMode] = useState<FormMode>('create')
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formName, setFormName] = useState('')
  const [formNameError, setFormNameError] = useState<string | null>(null)
  const [formTone, setFormTone] = useState('professional')
  const [formSections, setFormSections] = useState<string[]>(freeSections.map((s) => s.id))
  const [formCompanyName, setFormCompanyName] = useState('')
  const [formPreparedBy, setFormPreparedBy] = useState('')
  const [formSubmitting, setFormSubmitting] = useState(false)

  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [deleteName, setDeleteName] = useState('')
  const [deleting, setDeleting] = useState(false)

  const fetchTemplates = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const resp = await api.get<Template[]>('/templates')
      setTemplates(resp.data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load templates'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isPro) fetchTemplates()
    else setIsLoading(false)
  }, [isPro, fetchTemplates])

  function openCreateForm() {
    setFormMode('create')
    setEditingId(null)
    setFormName('')
    setFormNameError(null)
    setFormTone('professional')
    setFormSections(freeSections.map((s) => s.id))
    setFormCompanyName('')
    setFormPreparedBy('')
    setFormOpen(true)
  }

  function openEditForm(t: Template) {
    setFormMode('edit')
    setEditingId(t.id)
    setFormName(t.name)
    setFormNameError(null)
    setFormTone(t.config?.tone || 'professional')
    setFormSections(t.config?.sections || freeSections.map((s) => s.id))
    setFormCompanyName(t.config?.brand?.company_name || '')
    setFormPreparedBy(t.config?.brand?.prepared_by || '')
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
  }

  function toggleSection(id: string) {
    setFormSections((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    )
  }

  async function handleFormSubmit() {
    if (!formName.trim()) {
      setFormNameError('Name is required')
      return
    }
    setFormNameError(null)
    setFormSubmitting(true)

    const config: Template['config'] = {
      tone: formTone,
      sections: formSections,
    }
    if (formCompanyName.trim() || formPreparedBy.trim()) {
      config.brand = {}
      if (formCompanyName.trim()) config.brand.company_name = formCompanyName.trim()
      if (formPreparedBy.trim()) config.brand.prepared_by = formPreparedBy.trim()
    }

    try {
      if (formMode === 'create') {
        await api.post('/templates', {
          name: formName.trim(),
          template_type: 'marketing',
          config,
        })
        toast.success('Template created')
      } else {
        await api.patch(`/templates/${editingId}`, {
          name: formName.trim(),
          config,
        })
        toast.success('Template updated')
      }
      closeForm()
      await fetchTemplates()
    } catch {
      toast.error(formMode === 'create' ? 'Failed to create template' : 'Failed to update template')
    } finally {
      setFormSubmitting(false)
    }
  }

  async function handleSetDefault(t: Template, value: boolean) {
    try {
      await api.patch(`/templates/${t.id}`, { is_default: value })
      setTemplates((prev) =>
        prev.map((tmpl) => ({
          ...tmpl,
          is_default: tmpl.id === t.id ? value : false,
        })),
      )
      toast.success(value ? 'Default template set' : 'Default template removed')
    } catch {
      toast.error('Failed to update default')
    }
  }

  function openDeleteModal(t: Template) {
    setDeleteId(t.id)
    setDeleteName(t.name)
  }

  function closeDeleteModal() {
    setDeleteId(null)
    setDeleteName('')
  }

  async function handleDelete() {
    if (!deleteId) return
    setDeleting(true)
    try {
      await api.delete(`/templates/${deleteId}`)
      setTemplates((prev) => prev.filter((t) => t.id !== deleteId))
      toast.success('Template deleted')
      closeDeleteModal()
    } catch {
      toast.error('Failed to delete template')
    } finally {
      setDeleting(false)
    }
  }

  if (!isPro) {
    return (
      <div className="flex h-screen bg-slate dark:bg-darkBg">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-6 py-8">
            <h1 className="mb-8 font-display text-2xl font-bold text-ink dark:text-gray-100">Templates</h1>
            <UpgradePrompt feature="Templates" tier="Pro" />
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
            <h1 className="font-display text-2xl font-bold text-ink dark:text-gray-100">Templates</h1>
            <Button onClick={openCreateForm}>
              <Plus className="mr-1.5 h-4 w-4" />
              New Template
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
              <Button variant="ghost" size="sm" className="mt-3" onClick={fetchTemplates}>
                Retry
              </Button>
            </div>
          ) : templates.length === 0 ? (
            <EmptyState
              illustration={<NaxelyMark size={48} />}
              title="No templates yet"
              description="Save your report configurations as reusable templates so you can apply them to future reports with one click."
              action={
                <Button onClick={openCreateForm}>
                  <Plus className="mr-1.5 h-4 w-4" />
                  Create Template
                </Button>
              }
            />
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate bg-paper shadow-md dark:border-gray-700 dark:bg-darkBg">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-gray-400">
                    <th className="px-4 py-3 font-body">Name</th>
                    <th className="px-4 py-3 font-body">Tone</th>
                    <th className="px-4 py-3 font-body">Sections</th>
                    <th className="px-4 py-3 font-body">Created</th>
                    <th className="px-4 py-3 font-body">Default</th>
                    <th className="px-4 py-3 font-body" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate dark:divide-gray-700">
                  {templates.map((t) => (
                    <tr key={t.id} className="group transition-colors hover:bg-amber-50/40 dark:hover:bg-amber-900/10">
                      <td className="max-w-[200px] truncate px-4 py-3 font-medium text-ink dark:text-gray-200">
                        {t.name}
                        {t.is_default && (
                          <span className="ml-2">
                            <Badge variant="success" text="Default" />
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {t.config?.tone ? (
                          <span className="capitalize">{t.config.tone.replace(/-/g, ' ')}</span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                        {t.config?.sections?.length ? (
                          <span>{t.config.sections.length}</span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-400">
                        {formatDate(t.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={t.is_default}
                          onChange={(e) => handleSetDefault(t, e.target.checked)}
                          className="h-4 w-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500 dark:border-gray-600"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openEditForm(t)}
                            className="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-slate hover:text-ink dark:hover:bg-gray-700 dark:hover:text-gray-200"
                            title="Edit"
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => openDeleteModal(t)}
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

      <Modal
        isOpen={formOpen}
        onClose={closeForm}
        title={formMode === 'create' ? 'New Template' : 'Edit Template'}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="ghost" size="sm" onClick={closeForm} disabled={formSubmitting}>
              Cancel
            </Button>
            <Button size="sm" loading={formSubmitting} onClick={handleFormSubmit}>
              {formMode === 'create' ? 'Create' : 'Save'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Name</label>
            <input
              type="text"
              value={formName}
              onChange={(e) => { setFormName(e.target.value); setFormNameError(null) }}
              placeholder="e.g. Monthly Client Report"
              className="w-full rounded-lg border border-slate bg-paper px-3 py-2 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-paper dark:placeholder-gray-500"
            />
            {formNameError && <p className="mt-1 text-xs text-red-500">{formNameError}</p>}
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-600 dark:text-gray-400">Tone</label>
            <div className="grid grid-cols-2 gap-2">
              {toneCards.map((t) => {
                const active = formTone === t.id
                const Icon = t.icon
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setFormTone(t.id)}
                    className={`flex items-center gap-2 rounded-lg border-2 px-3 py-2 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 ${
                      active
                        ? 'border-amber-500 bg-amber-50 text-amber-600 dark:border-amber-500 dark:bg-amber-900/30 dark:text-amber-400'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-gray-600'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {t.label}
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-xs font-medium text-gray-600 dark:text-gray-400">Sections</label>
            <div className="space-y-1.5">
              {allSections.map((s) => (
                <label
                  key={s.id}
                  className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 dark:border-gray-700 dark:bg-gray-800"
                >
                  <input
                    type="checkbox"
                    checked={formSections.includes(s.id)}
                    onChange={() => toggleSection(s.id)}
                    className="h-4 w-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500 dark:border-gray-600"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{s.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">Brand (optional)</label>
            <div className="space-y-2">
              <input
                type="text"
                value={formCompanyName}
                onChange={(e) => setFormCompanyName(e.target.value)}
                placeholder="Company name"
                className="w-full rounded-lg border border-slate bg-paper px-3 py-2 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-paper dark:placeholder-gray-500"
              />
              <input
                type="text"
                value={formPreparedBy}
                onChange={(e) => setFormPreparedBy(e.target.value)}
                placeholder="Prepared by"
                className="w-full rounded-lg border border-slate bg-paper px-3 py-2 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-paper dark:placeholder-gray-500"
              />
            </div>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!deleteId} onClose={closeDeleteModal} title="Delete Template">
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
