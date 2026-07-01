import { useState, useMemo } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Shield, Trash2, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/axios'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Badge from '@/components/ui/Badge'
import type { ApiKeyResponse } from '@/types/api'

const PROVIDERS_NEEDING_KEY = ['openai', 'claude', 'groq', 'deepseek', 'mistral', 'together', 'gemini'] as const

const apiKeySchema = z.object({
  provider: z.enum(['gemini', 'openai', 'claude', 'groq', 'deepseek', 'mistral', 'together'], { required_error: 'Select a provider' }),
  api_key: z.string().optional(),
}).superRefine((data, ctx) => {
  if (!data.api_key || data.api_key.length === 0) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'API key is required for this provider', path: ['api_key'] })
  } else if (data.api_key.length > 200) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'API key too long (max 200 chars)', path: ['api_key'] })
  }
})

type ApiKeyFormValues = z.infer<typeof apiKeySchema>

type AiProvider = 'gemini' | 'openai' | 'claude' | 'groq' | 'deepseek' | 'mistral' | 'together'

interface ApiKeyFormProps {
  hasKey: boolean
  provider: AiProvider | null
  keyPreview: string | null
  tier: string
  onSaved: (data: ApiKeyResponse) => void
  onDeleted: () => void
}

export default function ApiKeyForm({ hasKey, provider, keyPreview, onSaved, onDeleted }: ApiKeyFormProps) {
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    control,
  } = useForm<ApiKeyFormValues>({
    resolver: zodResolver(apiKeySchema),
    defaultValues: { provider: provider ?? 'openai', api_key: '' },
  })

  const selectedProvider = useWatch({ control, name: 'provider' })
  const placeholder = useMemo(() => {
    switch (selectedProvider) {
      case 'openai': return 'sk-proj-...'
      case 'claude': return 'sk-ant-...'
      case 'groq': return 'gsk_...'
      case 'deepseek': return 'sk-...'
      case 'mistral': return '...'
      case 'together': return '...'
      case 'gemini': return 'AIza...'
      default: return ''
    }
  }, [selectedProvider])
  const needsKey = PROVIDERS_NEEDING_KEY.includes(selectedProvider as typeof PROVIDERS_NEEDING_KEY[number])

  const onSubmit = async (data: ApiKeyFormValues) => {
    setIsSaving(true)
    try {
      const payload = {
        provider: data.provider,
        api_key: data.api_key,
      }
      const keyResp = await api.post('/settings/api-key', payload)
      const resp = keyResp.data as ApiKeyResponse
      onSaved(resp)
      reset({ provider: data.provider, api_key: '' })
      toast.success(data.provider === 'gemini' ? 'Switched to Gemini' : 'API key saved')
    } catch {
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
    } finally {
      setIsDeleting(false)
    }
  }

  const providerLabels: Record<string, string> = {
    gemini: 'Gemini', openai: 'OpenAI', claude: 'Claude',
    groq: 'Groq', deepseek: 'DeepSeek', mistral: 'Mistral', together: 'Together AI',
  }
  const providerLabel = provider ? (providerLabels[provider] ?? provider) : 'None'
  const statusLabel = hasKey
    ? `Connected (${providerLabel})`
    : 'Not configured'

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Current Status</h3>
        <div className="mt-2 flex items-center gap-2">
          <Badge variant={hasKey ? 'success' : 'neutral'} text={statusLabel} />
          {hasKey && keyPreview && (
            <span className="font-mono text-xs text-gray-500 dark:text-gray-400">{keyPreview}</span>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="provider" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Provider
          </label>
          <select
            id="provider"
            {...register('provider')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          >
            <option value="gemini">Gemini</option>
            <option value="groq">Groq</option>
            <option value="deepseek">DeepSeek</option>
            <option value="openai">OpenAI</option>
            <option value="claude">Claude (Anthropic)</option>
            <option value="mistral">Mistral</option>
            <option value="together">Together AI</option>
          </select>
          {errors.provider && (
            <p className="mt-1 text-xs text-red-500">{errors.provider.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="api_key" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            API Key
          </label>
          <input
            id="api_key"
            type="password"
            placeholder={placeholder}
            autoComplete="off"
            disabled={!needsKey}
            {...register('api_key')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm text-gray-900 placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500 dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
          />
          {errors.api_key && (
            <p className="mt-1 text-xs text-red-500">{errors.api_key.message}</p>
          )}
        </div>

        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
          <Shield className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-600" />
          <div className="text-xs text-amber-700">
            <p>Add your own API key to enable AI insights. All plans support BYOK — bring keys from Gemini, Groq, DeepSeek, OpenAI and more.</p>
            <p className="mt-1">
              New to API keys?{' '}
              <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="font-medium underline hover:no-underline">Get a free Groq key</a>
              {' '}— no credit card needed, ready in minutes.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" loading={isSaving}>{needsKey ? 'Save API Key' : 'Save Provider'}</Button>
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
            <p className="text-sm text-gray-600 dark:text-gray-400">Are you sure you want to delete your API key?</p>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
            <Button variant="danger" loading={isDeleting} onClick={handleDelete}>Delete Key</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

