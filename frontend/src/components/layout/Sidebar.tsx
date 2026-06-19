import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useRef, useState, useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import {
  LayoutDashboard,
  FilePlus,
  LayoutTemplate,
  Settings,
  Lock,
  ArrowRight,
  LogOut,
  Sun,
  Moon,
  type LucideIcon,
} from 'lucide-react'

interface NavItem {
  label: string
  icon: LucideIcon
  href: string
  tiers: string[]
  disabled?: boolean
  lockedFor?: string[]
  hideForOthers?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard', tiers: ['free', 'pro', 'agency'] },
  { label: 'New Report', icon: FilePlus, href: '/report/new', tiers: ['free', 'pro', 'agency'] },
  { label: 'Templates', icon: LayoutTemplate, href: '#', tiers: ['pro', 'agency'], disabled: true, lockedFor: ['free'] },
  { label: 'Settings', icon: Settings, href: '/settings', tiers: ['free', 'pro', 'agency'] },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const tier = user?.tier ?? 'free'

  useEffect(() => {
    if (user?.theme_preference === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [user?.theme_preference])

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div className="flex h-16 items-center gap-2 px-6">
        <span className="text-xl font-bold text-gray-900 dark:text-gray-100">Naxely</span>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          if (item.hideForOthers && !item.tiers.includes(tier)) return null

          const isLocked = item.lockedFor?.includes(tier)

          if (item.disabled && !isLocked) {
            return (
              <div
                key={item.label}
                className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-400 dark:text-gray-500"
              >
                <item.icon className="h-5 w-5" />
                <span className="flex-1">{item.label}</span>
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-gray-500 dark:bg-gray-700 dark:text-gray-400">
                  Coming Soon
                </span>
              </div>
            )
          }

          const isActive = location.pathname === item.href

          return (
            <Link
              key={item.label}
              to={isLocked ? '/pricing' : item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
              ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-700/50 dark:hover:text-gray-200'
              }`}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
              {isLocked && <Lock className="ml-auto h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />}
            </Link>
          )
        })}
      </nav>

      {tier === 'free' && (
        <div className="mx-3 mb-3 space-y-3">
          <div className="rounded-lg bg-gray-50 px-3 py-3 dark:bg-gray-700/50">
            <p className="mb-1.5 text-xs text-gray-600 dark:text-gray-400">
              {user?.reports_this_month ?? 0} of {user?.monthly_limit ?? 3} reports used
            </p>
            <div className="h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-600">
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

      <button
        onClick={async () => {
          const next = user?.theme_preference === 'dark' ? 'light' : 'dark'
          await api.post('/settings/theme', { theme: next })
          document.documentElement.classList.toggle('dark', next === 'dark')
          useAuthStore.getState().fetchProfile()
        }}
        className="flex w-full items-center gap-3 border-t border-gray-200 px-6 py-2.5 text-sm text-gray-500 transition-colors hover:text-gray-700 dark:border-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        {user?.theme_preference === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        {user?.theme_preference === 'dark' ? 'Light Mode' : 'Dark Mode'}
      </button>

      <div className="relative border-t border-gray-200 px-4 py-3" ref={menuRef}>
        <button
          className="flex w-full items-center gap-3 rounded-lg px-1 py-1 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50"
          onClick={() => setMenuOpen((o) => !o)}
        >
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.full_name}
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-medium text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
              {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
              {user?.full_name ?? 'User'}
            </p>
            <p className="truncate text-xs text-gray-500 dark:text-gray-400">{user?.email ?? ''}</p>
          </div>
        </button>

        {menuOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setMenuOpen(false)}
            />
            <div className="absolute bottom-full left-2 right-2 z-20 mb-2 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700/50"
                onClick={() => {
                  setMenuOpen(false)
                  navigate('/settings')
                }}
              >
                <Settings className="h-4 w-4" />
                Settings
              </button>
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/30"
                onClick={async () => {
                  setMenuOpen(false)
                  await logout()
                  navigate('/login')
                }}
              >
                <LogOut className="h-4 w-4" />
                Log out
              </button>
            </div>
          </>
        )}
      </div>
    </aside>
  )
}
