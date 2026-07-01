import { useState } from 'react'
import { Briefcase, MessageCircle, BarChart3, BookOpen } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

interface ReportConfigData {
  title: string
  dateFrom: string
  dateTo: string
  tone: string
  sections: string[]
}

interface ReportConfigProps {
  onConfigChange: (config: ReportConfigData) => void
}

const toneCards = [
  { id: 'professional', label: 'Professional', icon: Briefcase },
  { id: 'casual', label: 'Casual', icon: MessageCircle },
  { id: 'data-heavy', label: 'Data-heavy', icon: BarChart3 },
  { id: 'story-driven', label: 'Story-driven', icon: BookOpen },
]

const freeSections = [
  { id: 'charts', label: 'Charts', free: true },
  { id: 'kpi_overview', label: 'Key Metrics', free: true },
  { id: 'data_table', label: 'Data Table', free: true },
]

const proSections = [
  { id: 'executive_summary', label: 'Executive Summary', free: false },
  { id: 'insights', label: 'AI Insights', free: false },
  { id: 'anomalies', label: 'Anomaly Detection', free: false },
  { id: 'trends', label: 'Trends', free: false },
]

export default function ReportConfigForm({ onConfigChange }: ReportConfigProps) {
  const user = useAuthStore((s) => s.user)
  const isPro = user?.tier === 'pro' || user?.tier === 'agency'
  const isAiLocked = user?.tier === 'free' && !user?.has_api_key

  const [title, setTitle] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [tone, setTone] = useState('professional')
  const [sections, setSections] = useState<string[]>(
    [...freeSections.map((s) => s.id), ...(isPro ? proSections.map((s) => s.id) : [])],
  )

  const toggleSection = (id: string) => {
    const updated = sections.includes(id) ? sections.filter((s) => s !== id) : [...sections, id]
    setSections(updated)
  }

  const emit = () => {
    onConfigChange({ title, dateFrom, dateTo, tone, sections })
  }

  const handleTitleChange = (v: string) => {
    if (v.length <= 255) {
      setTitle(v)
      emit()
    }
  }

  return (
    <div className="space-y-8" onBlur={emit}>
      <div>
        <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Report Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          placeholder="e.g. Q1 2024 Marketing Performance"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">{title.length}/255</p>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">Date Range</label>
        <div className="flex gap-4">
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value)
              emit()
            }}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          />
          <span className="self-center text-gray-400 dark:text-gray-500">to</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value)
              emit()
            }}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
        </div>
      </div>

      <div>
        <label className="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-300">Tone</label>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {toneCards.map((t) => {
            const Icon = t.icon
            const active = tone === t.id
            return (
              <button
                key={t.id}
                onClick={() => {
                  setTone(t.id)
                  emit()
                }}
                className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
                  active
                    ? 'border-amber-500 bg-amber-50 text-amber-600 dark:border-amber-500 dark:bg-amber-900/30 dark:text-amber-400'
                    : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-gray-600'
                }`}
              >
                <Icon className="h-6 w-6" />
                <span className="text-xs font-medium">{t.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <label className="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-300">Sections</label>
        <div className="space-y-2">
          {freeSections.map((s) => (
              <label key={s.id} className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800">
                <input
                  type="checkbox"
                  checked={sections.includes(s.id)}
                  onChange={() => toggleSection(s.id)}
                    className="h-4 w-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500 dark:border-gray-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">{s.label}</span>
                <span className="ml-auto text-xs text-green-600">✅</span>
              </label>
          ))}
          {proSections.map((s) => (
            <label
              key={s.id}
              className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
                isAiLocked
                  ? 'cursor-not-allowed border-gray-200 bg-gray-50 opacity-50 dark:border-gray-700 dark:bg-gray-800'
                  : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
              }`}
            >
              <input
                type="checkbox"
                checked={sections.includes(s.id)}
                onChange={() => !isAiLocked && toggleSection(s.id)}
                disabled={isAiLocked}
                className="h-4 w-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500 dark:border-gray-600"
              />
              <span className={`text-sm ${isAiLocked ? 'text-gray-400' : 'text-gray-700'}`}>{s.label}</span>
              {isAiLocked ? (
                <span className="ml-auto flex items-center gap-1.5">
                  <a
                    href="/settings?tab=api-key"
                    className="text-xs text-amber-600 underline hover:no-underline"
                  >
                    Add API key
                  </a>
                  <span className="text-xs text-gray-400">·</span>
                  <a
                    href="https://console.groq.com/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-gray-400 underline hover:text-gray-600"
                  >
                    Get a free Groq key
                  </a>
                </span>
              ) : (
                <span className="ml-auto text-xs text-green-600">✅</span>
              )}
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}
