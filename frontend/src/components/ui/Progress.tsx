import { clsx } from 'clsx'

interface ProgressProps {
  value: number
  label?: string
  color?: string
  className?: string
}

export default function Progress({ value, label, color, className }: ProgressProps) {
  return (
    <div className={className}>
      {label && <p className="mb-1.5 text-xs text-gray-600">{label}</p>}
      <div className="h-2 w-full rounded-full bg-gray-200">
        <div
          className={clsx('h-2 rounded-full transition-all', color ?? 'bg-indigo-500')}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}
