import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Shield, Trash2, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/axios'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Badge from '@/components/ui/Badge'
import type { ApiKeyResponse } from '@/types/api'

const apiKeySchema = z.object({
  provider: z.enum(['openai', 'claude'], { required_error: 'Select a provider' }),
  api_key: z
    .string()
    .min(1, 'API key is required')
    .refine(
      (val) => val.startsWith('sk-'),
      { message: 'OpenAI key must start with "sk-", Claude key must start with "sk-ant-"' },
    )
    .refine((val) => val.length <= 200, { message: 'API key too long (max 200 chars)' }),
})

type ApiKeyFormValues = z.infer<typeof apiKeySchema>

interface ApiKeyFormProps {
  hasKey: boolean
  provider: 'openai' | 'claude' | null
  keyPreview: string | null
  tier: string
  onSaved: (data: ApiKeyResponse) => void
  onDeleted: () => void
}

export default function ApiKeyForm({ hasKey, provider, keyPreview, tier, onSaved, onDeleted }: ApiKeyFormProps) {
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ApiKeyFormValues>({
    resolver: zodResolver(apiKeySchema),
    defaultValues: { provider: provider ?? 'openai', api_key: '' },
  })

  if (tier === 'free') {
    return (
      <UpgradePromptInline feature="AI API key management" tier="Pro" />
    )
  }

  const onSubmit = async (data: ApiKeyFormValues) => {
    setIsSaving(true)
    try {
      const keyResp = await api.post('/settings/api-key', data)
      const resp = keyResp.data as ApiKeyResponse
      onSaved(resp)
      reset({ provider: data.provider, api_key: '' })
      toast.success('API key saved')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save API key'
      toast.error(msg)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await api.delete('/settings/api-key')
      onDeleted()
      toast.success('API key removed')
      setShowDeleteModal(false)
    } catch {
      toast.error('Failed to delete API key')
    } finally {
      setIsDeleting(false)
    }
  }

  const statusLabel = hasKey
    ? `Connected (${provider === 'openai' ? 'OpenAI' : 'Claude'})`
    : 'Not configured'

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-medium text-gray-700">Current Status</h3>
        <div className="mt-2 flex items-center gap-2">
          <Badge variant={hasKey ? 'success' : 'neutral'} text={statusLabel} />
          {hasKey && keyPreview && (
            <span className="font-mono text-xs text-gray-500">{keyPreview}</span>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="provider" className="mb-1 block text-sm font-medium text-gray-700">
            Provider
          </label>
          <select
            id="provider"
            {...register('provider')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="openai">OpenAI</option>
            <option value="claude">Claude (Anthropic)</option>
          </select>
          {errors.provider && (
            <p className="mt-1 text-xs text-red-500">{errors.provider.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="api_key" className="mb-1 block text-sm font-medium text-gray-700">
            API Key
          </label>
          <input
            id="api_key"
            type="password"
            placeholder="sk-proj-..."
            autoComplete="off"
            {...register('api_key')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          {errors.api_key && (
            <p className="mt-1 text-xs text-red-500">{errors.api_key.message}</p>
          )}
        </div>

        <div className="flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 p-3">
          <Shield className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
          <p className="text-xs text-blue-700">
            Your key is encrypted with AES-256 and only used during report generation. It is never stored in plain text.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" loading={isSaving}>Save API Key</Button>
          {hasKey && (
            <Button
              type="button"
              variant="danger"
              onClick={() => setShowDeleteModal(true)}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              Delete
            </Button>
          )}
        </div>
      </form>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete API Key"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-600" />
            <p className="text-sm text-yellow-700">
              Removing your API key means AI-powered features (Executive Summary, Insight Cards, Anomaly Detection) will not work until you add a new key.
            </p>
          </div>
          <p className="text-sm text-gray-600">Are you sure you want to delete your API key?</p>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
            <Button variant="danger" loading={isDeleting} onClick={handleDelete}>Delete Key</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function UpgradePromptInline({ feature, tier }: { feature: string; tier: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <Shield className="h-5 w-5 flex-shrink-0 text-gray-400" />
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-700">{feature}</p>
        <p className="text-xs text-gray-500">Available on {tier} plan</p>
      </div>
      <a
        href="/pricing"
        className="rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-600"
      >
        Upgrade to {tier}
      </a>
    </div>
  )
}
