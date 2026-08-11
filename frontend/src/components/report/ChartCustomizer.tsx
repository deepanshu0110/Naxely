import { useState, useEffect } from 'react'
import { BarChart2, TrendingUp, PieChart, Activity, LayoutGrid } from 'lucide-react'
import api from '@/lib/axios'
import type { ChartSpec, ColumnConfig } from '@/types/report'

const CHART_TYPES = [
  { value: 'line', label: 'Line', icon: TrendingUp },
  { value: 'area', label: 'Area', icon: Activity },
  { value: 'bar', label: 'Bar', icon: BarChart2 },
  { value: 'lollipop', label: 'Lollipop', icon: BarChart2 },
  { value: 'pie', label: 'Pie', icon: PieChart },
  { value: 'donut', label: 'Donut', icon: PieChart },
  { value: 'scatter', label: 'Scatter', icon: BarChart2 },
  { value: 'histogram', label: 'Histogram', icon: BarChart2 },
  { value: 'box', label: 'Box Plot', icon: LayoutGrid },
  { value: 'heatmap', label: 'Heatmap', icon: LayoutGrid },
  { value: 'grouped_bar', label: 'Grouped Bar', icon: BarChart2 },
  { value: 'stacked_bar', label: 'Stacked Bar', icon: BarChart2 },
  { value: 'combo', label: 'Combo', icon: TrendingUp },
  { value: 'waterfall', label: 'Waterfall', icon: BarChart2 },
  { value: 'funnel', label: 'Funnel', icon: BarChart2 },
  { value: 'treemap', label: 'Treemap', icon: LayoutGrid },
]

interface ChartCustomizerProps {
  uploadId: string
  columnConfig: ColumnConfig[]
  onSpecsChange: (specs: ChartSpec[]) => void
  onAutoSpecsChange?: (specs: ChartSpec[], selector: 'ai' | 'rules') => void
  maxCharts?: number
}

export default function ChartCustomizer({
  uploadId,
  columnConfig,
  onSpecsChange,
  onAutoSpecsChange,
  maxCharts,
}: ChartCustomizerProps) {
  const [candidates, setCandidates] = useState<ChartSpec[]>([])
  const [included, setIncluded] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [capMessage, setCapMessage] = useState<string | null>(null)

  useEffect(() => {
    const fetchSuggestions = async () => {
      setLoading(true)
      setError(null)
      setCapMessage(null)
      try {
        const res = await api.post<{ chart_specs: ChartSpec[]; selector?: string }>(
          '/reports/preview-charts',
          {
            upload_id: uploadId,
            column_config: columnConfig,
          },
        )
        const fetched = res.data.chart_specs || []
        const selected = new Set<number>()
        fetched.forEach((s, i) => {
          if (s.recommended !== false) selected.add(i)
        })
        const recommended = fetched.filter((_, i) => selected.has(i))
        const selector: 'ai' | 'rules' = res.data.selector === 'ai' ? 'ai' : 'rules'
        setCandidates(fetched)
        setIncluded(selected)
        onSpecsChange(recommended)
        onAutoSpecsChange?.(recommended, selector)
        if (maxCharts && selected.size > maxCharts) {
          setCapMessage(`You can include up to ${maxCharts} charts on your plan.`)
        }
      } catch {
        setError('Could not load chart suggestions. Using defaults.')
      } finally {
        setLoading(false)
      }
    }
    fetchSuggestions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadId, maxCharts])

  const emit = (nextCandidates: ChartSpec[], nextIncluded: Set<number>) => {
    onSpecsChange(nextCandidates.filter((_, i) => nextIncluded.has(i)))
  }

  const toggleInclude = (index: number) => {
    const next = new Set(included)
    if (next.has(index)) {
      next.delete(index)
    } else {
      if (maxCharts && next.size >= maxCharts) {
        setCapMessage(`You can include up to ${maxCharts} charts on your plan.`)
        return
      }
      next.add(index)
    }
    setCapMessage(null)
    setIncluded(next)
    emit(candidates, next)
  }

  const updateSpec = (index: number, type: string) => {
    const updated = candidates.map((s, i) => (i === index ? { ...s, type } : s))
    setCandidates(updated)
    emit(updated, included)
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
        <p className="text-sm text-gray-500 dark:text-gray-400">Preparing chart recommendations...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h3 className="text-base font-semibold text-ink dark:text-gray-100">Charts & Visualizations</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          These charts are recommended based on your data. Include the ones you want and change any type below.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-600 dark:bg-amber-950 dark:text-amber-400">
          {error}
        </div>
      )}

      {capMessage && (
        <div
          role="alert"
          className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:bg-amber-950 dark:text-amber-400"
        >
          {capMessage}
        </div>
      )}

      <div className="flex flex-col gap-3">
        {candidates.map((spec, i) => {
          const checked = included.has(i)
          return (
            <div
              key={i}
              className={`flex items-center justify-between gap-4 rounded-xl border border-transparent bg-gray-50 p-4 transition hover:border-amber-500/30 dark:bg-gray-800 ${
                checked ? '' : 'opacity-60'
              }`}
            >
              <label className="flex min-w-0 cursor-pointer items-center gap-3">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleInclude(i)}
                  className="h-4 w-4 shrink-0 cursor-pointer rounded border-gray-300 accent-amber-500"
                  aria-label={`Include ${spec.title}`}
                />
                <span className="flex min-w-0 flex-col gap-0.5">
                  <span className="truncate text-sm font-medium text-ink dark:text-gray-100">
                    {spec.title}
                  </span>
                  <span className="font-mono text-xs text-gray-400 dark:text-gray-500">
                    {spec.x} → {spec.y}
                  </span>
                </span>
              </label>

              <select
                value={spec.type}
                onChange={(e) => updateSpec(i, e.target.value)}
                className="shrink-0 cursor-pointer rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-amber-500/40 dark:border-gray-600 dark:bg-darkBg dark:text-gray-100"
              >
                {CHART_TYPES.map((ct) => (
                  <option key={ct.value} value={ct.value}>
                    {ct.label}
                  </option>
                ))}
              </select>
            </div>
          )
        })}
      </div>

      {candidates.length === 0 && !loading && (
        <div className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
          No charts could be suggested for this data.
        </div>
      )}
    </div>
  )
}
