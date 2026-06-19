import { useState, useEffect } from 'react'
import type { ColumnConfig, ColumnInfo } from '@/types/report'

interface ColumnMapperProps {
  columns: ColumnInfo[]
  onChange: (config: ColumnConfig[]) => void
}

const typeOptions: ColumnConfig['type'][] = ['date', 'metric', 'dimension']

export default function ColumnMapper({ columns, onChange }: ColumnMapperProps) {
  const [config, setConfig] = useState<ColumnConfig[]>([])

  useEffect(() => {
    const initial = columns.map((col) => ({
      original_name: col.original_name,
      display_name: col.suggested_name,
      type: col.suggested_type,
      include: true,
    }))
    setConfig(initial)
    onChange(initial)
  }, [columns, onChange])

  const updateField = (idx: number, field: keyof ColumnConfig, value: string | boolean) => {
    const updated = config.map((c, i) => (i === idx ? { ...c, [field]: value } : c))
    setConfig(updated)
    onChange(updated)
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase text-gray-500 dark:border-gray-700">
            <th className="pb-3 pr-4">Original Name</th>
            <th className="pb-3 pr-4">Display Name</th>
            <th className="pb-3 pr-4">Type</th>
            <th className="pb-3 pr-4">Include</th>
            <th className="pb-3">Sample Values</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {columns.map((col, idx) => (
            <tr key={col.original_name}>
              <td className="py-3 pr-4 font-medium text-gray-900 dark:text-gray-100">{col.original_name}</td>
              <td className="py-3 pr-4">
                <input
                  type="text"
                  value={config[idx]?.display_name ?? ''}
                  onChange={(e) => updateField(idx, 'display_name', e.target.value)}
                  className="w-40 rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
              </td>
              <td className="py-3 pr-4">
                <select
                  value={config[idx]?.type ?? 'dimension'}
                  onChange={(e) => updateField(idx, 'type', e.target.value)}
                  className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                >
                  {typeOptions.map((t) => (
                    <option key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </option>
                  ))}
                </select>
              </td>
              <td className="py-3 pr-4">
                <button
                  onClick={() => updateField(idx, 'include', !config[idx]?.include)}
                  className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer items-center rounded-full transition-colors ${
                    config[idx]?.include ? 'bg-amber-500' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      config[idx]?.include ? 'translate-x-4' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </td>
              <td className="py-3">
                <div className="flex flex-wrap gap-1">
                  {col.sample_values.slice(0, 3).map((v, i) => (
                    <span key={i} className="inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500 dark:bg-gray-700 dark:text-gray-400">
                      {String(v ?? '—')}
                    </span>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
