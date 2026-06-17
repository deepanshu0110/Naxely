import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import {
  LayoutDashboard,
  FilePlus,
  LayoutTemplate,
  Settings,
  Lock,
  ArrowRight,
} from 'lucide-react'

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard', tiers: ['free', 'pro', 'agency'] },
  { label: 'New Report', icon: FilePlus, href: '/report/new', tiers: ['free', 'pro', 'agency'] },
  { label: 'Templates', icon: LayoutTemplate, href: '#', tiers: ['pro', 'agency'], lockedFor: ['free'] },
  { label: 'Settings', icon: Settings, href: '/settings', tiers: ['free', 'pro', 'agency'] },
]

export default function Sidebar() {
  const { user } = useAuthStore()
  const location = useLocation()
  const tier = user?.tier ?? 'free'

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center gap-2 px-6">
        <span className="text-xl font-bold text-gray-900">Databrief</span>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          if (item.hideForOthers && !item.tiers.includes(tier)) return null

          const isLocked = item.lockedFor?.includes(tier)
          const isActive = location.pathname === item.href

          return (
            <Link
              key={item.label}
              to={isLocked ? '/pricing' : item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-600'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
              {isLocked && <Lock className="ml-auto h-3.5 w-3.5 text-gray-400" />}
            </Link>
          )
        })}
      </nav>

      {tier === 'free' && (
        <div className="mx-3 mb-3 space-y-3">
          <div className="rounded-lg bg-gray-50 px-3 py-3">
            <p className="mb-1.5 text-xs text-gray-600">
              {user?.reports_this_month ?? 0} of {user?.monthly_limit ?? 3} reports used
            </p>
            <div className="h-1.5 w-full rounded-full bg-gray-200">
              <div
                className={`h-1.5 rounded-full transition-all ${
                  (user?.reports_this_month ?? 0) >= (user?.monthly_limit ?? 3)
                    ? 'bg-red-500'
                    : 'bg-indigo-500'
                }`}
                style={{
                  width: `${Math.min(
                    ((user?.reports_this_month ?? 0) / (user?.monthly_limit ?? 3)) * 100,
                    100,
                  )}%`,
                }}
              />
            </div>
          </div>

          <Link
            to="/pricing"
            className="flex items-center justify-between rounded-lg bg-indigo-500 px-3 py-2.5 text-sm font-medium text-white hover:bg-indigo-600"
          >
            Upgrade to Pro
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      <div className="border-t border-gray-200 px-4 py-3">
        <div className="flex items-center gap-3">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.full_name}
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-medium text-indigo-600">
              {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-gray-900">
              {user?.full_name ?? 'User'}
            </p>
            <p className="truncate text-xs text-gray-500">{user?.email ?? ''}</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
