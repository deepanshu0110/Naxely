import { clsx } from 'clsx'

interface BadgeProps {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral'
  text: string
  className?: string
}

const variantStyles: Record<string, string> = {
  success: 'bg-green-50 text-green-700 ring-green-600/20',
  warning: 'bg-yellow-50 text-yellow-700 ring-yellow-600/20',
  error: 'bg-red-50 text-red-700 ring-red-600/20',
  info: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  neutral: 'bg-gray-50 text-gray-700 ring-gray-600/20',
}

export default function Badge({ variant = 'neutral', text, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        variantStyles[variant],
        className,
      )}
    >
      {text}
    </span>
  )
}
