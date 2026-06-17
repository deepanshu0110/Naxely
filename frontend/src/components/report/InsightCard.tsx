import { clsx } from 'clsx'
import Badge from '@/components/ui/Badge'
import type { AIInsight } from '@/types/report'

const sentimentBorder: Record<string, string> = {
  positive: 'border-l-green-500',
  negative: 'border-l-red-500',
  neutral: 'border-l-gray-400',
}

const priorityVariant: Record<string, 'error' | 'warning' | 'neutral'> = {
  high: 'error',
  medium: 'warning',
  low: 'neutral',
}

export default function InsightCard({ insight }: { insight: AIInsight }) {
  return (
    <div
      className={clsx(
        'rounded-lg border border-gray-200 border-l-4 bg-white p-4 shadow-sm',
        sentimentBorder[insight.sentiment],
      )}
    >
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">📊 {insight.kpi}</h4>
        <Badge
          variant={priorityVariant[insight.priority]}
          text={insight.priority.toUpperCase()}
        />
      </div>

      <p className="mb-2 text-sm font-bold text-gray-800"># {insight.number}</p>
      <p className="mb-2 text-sm text-gray-600">▶ {insight.reason}</p>
      <p className="text-sm italic text-gray-500">✓ {insight.action}</p>
    </div>
  )
}
