import type { ReactNode } from 'react'

interface EmptyStateProps {
  illustration: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export default function EmptyState({ illustration, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-6">{illustration}</div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-gray-500 dark:text-gray-400">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
