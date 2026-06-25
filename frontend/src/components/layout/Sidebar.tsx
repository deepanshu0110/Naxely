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
  PanelLeftClose,
  PanelLeftOpen,
  Clock,
  Globe,
  type LucideIcon,
} from 'lucide-react'
import { useReducedMotion } from '@/hooks/useReducedMotion'

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
  { label: 'Scheduled Reports', icon: Clock, href: '/scheduled-reports', tiers: ['agency'], hideForOthers: true },
  { label: 'Templates', icon: LayoutTemplate, href: '#', tiers: ['pro', 'agency'], disabled: true, lockedFor: ['free'] },
  { label: 'Settings', icon: Settings, href: '/settings', tiers: ['free', 'pro', 'agency'] },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const [menuOpen, setMenuOpen] = useState(false)
  const [isDark, setIsDark] = useState(() => document.documentElement.classList.contains('dark'))
  const [hidden, setHidden] = useState(() => {
    try {
      const stored = localStorage.getItem('naxely_sidebar_hidden')
      if (stored !== null) return stored === 'true'
    } catch {}
    return window.innerWidth < 1024
  })
  const reducedMotion = useReducedMotion()
  const menuRef = useRef<HTMLDivElement>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const tier = user?.tier ?? 'free'
  const sidebarId = 'app-sidebar'

  useEffect(() => {
    try {
      localStorage.setItem('naxely_sidebar_hidden', String(hidden))
    } catch {}
  }, [hidden])

  useEffect(() => {
    const dark = document.documentElement.classList.contains('dark')
    setIsDark(dark)
    if (user?.theme_preference === 'dark') {
      document.documentElement.classList.add('dark')
    } else if (user?.theme_preference === 'light') {
      document.documentElement.classList.remove('dark')
    }
  }, [user?.theme_preference])

  const wrapperTransition = reducedMotion ? '' : 'transition-all duration-200'
  const slideTransition = reducedMotion ? '' : 'transition-transform duration-200'

  return (
    <>
      {hidden && (
        <button
          onClick={() => setHidden(false)}
          className="fixed left-3 top-4 z-30 flex h-8 w-8 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:text-gray-500 dark:hover:bg-gray-700/50 dark:hover:text-gray-300"
          aria-label="Toggle sidebar"
          aria-expanded={false}
          aria-controls={sidebarId}
        >
          <PanelLeftOpen className="h-5 w-5" />
        </button>
      )}
      <div className={`shrink-0 overflow-hidden ${wrapperTransition} ${hidden ? 'w-0' : 'w-60'}`}>
      <aside
        id={sidebarId}
        className={`flex h-screen flex-col border-r w-60 shrink-0 bg-paper dark:bg-darkBg border-amber-200/40 dark:border-amber-900/40 ${slideTransition} ${hidden ? '-translate-x-full' : 'translate-x-0'}`}
      >
      <div className="flex h-16 items-center justify-between px-4">
        <Link to="/dashboard" className="font-display text-xl font-bold text-ink dark:text-gray-100">Naxely</Link>
        <button
          onClick={() => setHidden(true)}
          className="flex h-8 w-8 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:text-gray-500 dark:hover:bg-gray-700/50 dark:hover:text-gray-300"
          aria-label="Toggle sidebar"
          aria-expanded={true}
          aria-controls={sidebarId}
        >
          <PanelLeftClose className="h-5 w-5" />
        </button>
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
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
                isActive
              ? 'bg-amber-50 text-amber-600 dark:border-l-amber-400 dark:bg-amber-900/40 dark:text-amber-300'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700/50 dark:hover:text-gray-100'
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
          <div className="rounded-lg bg-slate px-3 py-3 dark:bg-gray-700/50">
            <p className="mb-1.5 text-xs text-gray-600 dark:text-gray-400">
              {user?.reports_this_month ?? 0} of {user?.monthly_limit ?? 3} reports used
            </p>
            <div className="h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-600">
              <div
                className={`h-1.5 rounded-full transition-all duration-150 ease-in-out ${
                  (user?.reports_this_month ?? 0) >= (user?.monthly_limit ?? 3)
                    ? 'bg-red-500'
                    : 'bg-amber-500'
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
            className="flex items-center justify-between rounded-lg bg-amber-500 px-3 py-2.5 text-sm font-medium text-white transition-colors duration-150 ease-in-out hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            Upgrade to Pro
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      <div className="flex items-center justify-between border-t border-amber-200/40 px-4 py-2.5 dark:border-amber-900/40">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </span>
        <button
          role="switch"
          aria-checked={isDark}
          onClick={async () => {
            const next = !isDark
            setIsDark(next)
            document.documentElement.classList.toggle('dark', next)
            try {
              await api.post('/settings/theme', { theme: next ? 'dark' : 'light' })
            } catch {
              setIsDark(!next)
              document.documentElement.classList.toggle('dark', !next)
            }
            useAuthStore.getState().fetchProfile()
          }}
          className={`relative inline-flex h-[22px] w-[40px] flex-shrink-0 cursor-pointer items-center rounded-full transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
            isDark ? 'bg-amber-500' : 'bg-slate dark:bg-gray-500'
          }`}
        >
          <span
            className={`inline-block h-[18px] w-[18px] transform rounded-full bg-white shadow transition-transform duration-150 ease-in-out ${
              isDark ? 'translate-x-[20px]' : 'translate-x-0.5'
            }`}
          />
        </button>
      </div>

      <a
        href="https://naxely.com"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
      >
        <Globe className="h-5 w-5" />
        <span>Visit Homepage</span>
      </a>
      <div className="relative border-t border-amber-200/40 px-4 py-3 dark:border-amber-900/40" ref={menuRef}>
        <button
          className="flex w-full items-center gap-3 rounded-lg px-1 py-1 text-left transition-colors duration-150 ease-in-out hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:hover:bg-gray-700/50"
          onClick={() => setMenuOpen((o) => !o)}
        >
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.full_name}
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-xs font-medium text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
              {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink dark:text-paper">
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
            <div className="absolute bottom-full left-2 right-2 z-20 mb-2 overflow-hidden rounded-lg border border-amber-200/40 bg-paper shadow-lg dark:border-amber-900/40 dark:bg-darkBg">
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 transition-colors duration-150 ease-in-out hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-gray-300 dark:hover:bg-gray-700/50"
                onClick={() => {
                  setMenuOpen(false)
                  navigate('/settings')
                }}
              >
                <Settings className="h-4 w-4" />
                Settings
              </button>
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 transition-colors duration-150 ease-in-out hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-red-400 dark:hover:bg-red-900/30"
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
    </div>
    </>
  )
}
