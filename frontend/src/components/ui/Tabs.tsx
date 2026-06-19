import { clsx } from 'clsx'
import type { ReactNode } from 'react'

interface TabItem {
  id: string
  label: string
  disabled?: boolean
}

interface TabsProps {
  items: TabItem[]
  activeId: string
  onChange: (id: string) => void
  children: ReactNode
}

export default function Tabs({ items, activeId, onChange, children }: TabsProps) {
  return (
    <div>
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex gap-6" aria-label="Tabs">
          {items.map((tab) => (
            <button
              key={tab.id}
              disabled={tab.disabled}
              onClick={() => onChange(tab.id)}
              className={clsx(
                'whitespace-nowrap border-b-2 px-1 py-3 text-sm font-body font-medium transition-colors',
                tab.id === activeId
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300',
                tab.disabled && 'cursor-not-allowed opacity-50',
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="mt-6">{children}</div>
    </div>
  )
}
