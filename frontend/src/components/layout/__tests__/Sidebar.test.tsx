import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockLogout = vi.hoisted(() => vi.fn())
const mockNavigate = vi.hoisted(() => vi.fn())
const mockUseAuthStore = vi.hoisted(() => {
  const fn = vi.fn(() => ({ user: null, logout: mockLogout }))
  return Object.assign(fn, { getState: vi.fn(() => ({ fetchProfile: vi.fn() })) })
})

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Link: ({ to, children, ...props }: any) => <a href={to} {...props}>{children}</a>,
    useLocation: () => ({ pathname: '/dashboard' }),
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: mockUseAuthStore,
}))

vi.mock('@/lib/axios', () => ({
  default: { post: vi.fn(), get: vi.fn() },
}))

vi.mock('@/hooks/useReducedMotion', () => ({
  useReducedMotion: () => false,
}))

import { useAuthStore } from '@/store/authStore'
import Sidebar from '../Sidebar'
import type { User } from '@/types/user'

const freeUser: User = {
  id: 'user-1',
  email: 'free@test.com',
  full_name: 'Free User',
  avatar_url: null,
  tier: 'free',
  tier_expires_at: null,
  has_api_key: false,
  ai_provider: null,
  logo_url: null,
  brand_color: null,
  company_name: null,
  reports_this_month: 1,
  monthly_limit: 3,
  theme_preference: 'light',
  has_completed_onboarding: true,
}

const proUser: User = {
  ...freeUser,
  tier: 'pro',
  reports_this_month: 5,
  monthly_limit: null,
  theme_preference: 'dark',
}

const agencyUser: User = {
  ...freeUser,
  tier: 'agency',
  reports_this_month: 20,
  monthly_limit: null,
  theme_preference: 'light',
}

function renderSidebar() {
  return render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>,
  )
}

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuthStore).mockReturnValue({ user: freeUser, logout: mockLogout })
  })

  it('renders all nav items visible to free tier', () => {
    renderSidebar()

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('New Report')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Templates')).toBeInTheDocument()
    expect(screen.queryByText('Scheduled Reports')).not.toBeInTheDocument()
  })

  it('shows Templates locked with lock icon and href /pricing for free tier', () => {
    renderSidebar()

    const templatesLink = screen.getByText('Templates').closest('a')
    expect(templatesLink).toHaveAttribute('href', '/pricing')
    expect(templatesLink?.querySelector('.lucide-lock')).toBeTruthy()
  })

  it('highlights the active route (Dashboard)', () => {
    renderSidebar()

    const dashboardLink = screen.getByText('Dashboard').closest('a')
    expect(dashboardLink).toHaveAttribute('href', '/dashboard')
    expect(dashboardLink).toBeInTheDocument()
  })

  it('renders free tier usage bar', () => {
    renderSidebar()

    expect(screen.getByText(/reports used/)).toBeInTheDocument()
    expect(screen.getByText('Upgrade to Pro')).toBeInTheDocument()
  })

  it('renders user menu with avatar fallback initial letter', () => {
    renderSidebar()

    expect(screen.getByText('F')).toBeInTheDocument()
    expect(screen.getByText('Free User')).toBeInTheDocument()
    expect(screen.getByText('free@test.com')).toBeInTheDocument()
  })

  it('renders theme toggle', () => {
    renderSidebar()

    expect(screen.getByRole('switch')).toBeInTheDocument()
  })

  it('collapses sidebar when collapse button is clicked', async () => {
    renderSidebar()

    const toggleButtonsBefore = screen.getAllByRole('button', { name: /toggle sidebar/i })
    expect(toggleButtonsBefore).toHaveLength(1)

    const user = userEvent.setup()
    await user.click(toggleButtonsBefore[0])

    const toggleButtonsAfter = screen.getAllByRole('button', { name: /toggle sidebar/i })
    expect(toggleButtonsAfter).toHaveLength(2)
  })

  it('hides usage bar and unlocks Templates for pro tier', () => {
    vi.mocked(useAuthStore).mockReturnValue({ user: proUser, logout: mockLogout })
    renderSidebar()

    expect(screen.queryByText(/reports used/)).not.toBeInTheDocument()
    expect(screen.queryByText('Upgrade to Pro')).not.toBeInTheDocument()

    const templatesLink = screen.getByText('Templates').closest('a')
    expect(templatesLink).toHaveAttribute('href', '/templates')
    expect(templatesLink?.querySelector('.lucide-lock')).toBeFalsy()

    expect(screen.queryByText('Scheduled Reports')).not.toBeInTheDocument()
  })

  it('shows Scheduled Reports and no Templates lock for agency tier', () => {
    vi.mocked(useAuthStore).mockReturnValue({ user: agencyUser, logout: mockLogout })
    renderSidebar()

    expect(screen.getByText('Scheduled Reports')).toBeInTheDocument()

    const templatesLink = screen.getByText('Templates').closest('a')
    expect(templatesLink).toHaveAttribute('href', '/templates')
    expect(templatesLink?.querySelector('.lucide-lock')).toBeFalsy()

    expect(screen.queryByText(/reports used/)).not.toBeInTheDocument()
  })
})
