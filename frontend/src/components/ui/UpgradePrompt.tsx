import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

interface UpgradePromptProps {
  feature: string
  tier?: string
}

export default function UpgradePrompt({ feature, tier = 'Pro' }: UpgradePromptProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-700/50">
      <Lock className="h-5 w-5 flex-shrink-0 text-gray-400 dark:text-gray-500" />
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{feature}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">Available on {tier} plan</p>
      </div>
      <Link
        to="/pricing"
        className="rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-600"
      >
        Upgrade to {tier}
      </Link>
    </div>
  )
}
