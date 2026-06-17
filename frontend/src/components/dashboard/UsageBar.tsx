import { Link } from 'react-router-dom'
import Progress from '@/components/ui/Progress'

interface UsageBarProps {
  reportsThisMonth: number
  monthlyLimit: number | null
}

export default function UsageBar({ reportsThisMonth, monthlyLimit }: UsageBarProps) {
  if (monthlyLimit === null) return null

  const atLimit = reportsThisMonth >= monthlyLimit
  const pct = (reportsThisMonth / monthlyLimit) * 100

  return (
    <div>
      <Progress
        value={pct}
        label={`${reportsThisMonth} of ${monthlyLimit} free reports used this month`}
        color={atLimit ? 'bg-red-500' : 'bg-gray-400'}
      />
      {atLimit && (
        <Link to="/pricing" className="mt-2 inline-block text-xs font-medium text-red-500 hover:text-red-600">
          Upgrade for unlimited →
        </Link>
      )}
    </div>
  )
}
