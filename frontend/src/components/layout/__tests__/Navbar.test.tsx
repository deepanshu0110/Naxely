import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Link: ({ to, children, ...props }: any) => <a href={to} {...props}>{children}</a>,
  }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

import { useAuthStore } from '@/store/authStore'
import Navbar from '../Navbar'

function renderNavbar() {
  return render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>,
  )
}

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Log in, Start Free, and nav links when not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: false, user: null })
    renderNavbar()

    expect(screen.getByText('Log in')).toBeInTheDocument()
    expect(screen.getByText('Start Free')).toBeInTheDocument()
    expect(screen.getByText('Features')).toBeInTheDocument()
    expect(screen.getByText('Pricing')).toBeInTheDocument()
    expect(screen.getByText('How it works')).toBeInTheDocument()
    expect(screen.getByText('Guides')).toBeInTheDocument()
    expect(screen.getByText('Compare')).toBeInTheDocument()
  })

  it('logo links to / when not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: false, user: null })
    renderNavbar()

    const logo = screen.getByText('Naxely')
    expect(logo.closest('a')).toHaveAttribute('href', '/')
  })

  it('logo links to /dashboard when authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', email: 'test@test.com', full_name: 'Test' },
    })
    renderNavbar()

    const logo = screen.getByText('Naxely')
    expect(logo.closest('a')).toHaveAttribute('href', '/dashboard')
  })

  it('Guides dropdown contains 6 guide links', () => {
    vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: false, user: null })
    renderNavbar()

    expect(screen.getByText('How to Choose Client Reporting Software')).toBeInTheDocument()
    expect(screen.getByText('Best for Freelancers (2026)')).toBeInTheDocument()
    expect(screen.getByText('Automated Client Reporting: Complete Guide')).toBeInTheDocument()
    expect(screen.getByText('What Should a Client Report Include?')).toBeInTheDocument()
    expect(screen.getByText('Excel to PDF Report Generator')).toBeInTheDocument()
    expect(screen.getByText('Two Weeks Building Naxely')).toBeInTheDocument()
  })

  it('Compare dropdown contains 8 compare links and See all', () => {
    vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: false, user: null })
    renderNavbar()

    expect(screen.getByText('AgencyAnalytics')).toBeInTheDocument()
    expect(screen.getByText('Databox')).toBeInTheDocument()
    expect(screen.getByText('Powerdrill')).toBeInTheDocument()
    expect(screen.getByText('DashThis')).toBeInTheDocument()
    expect(screen.getByText('Whatagraph')).toBeInTheDocument()
    expect(screen.getByText('Klipfolio')).toBeInTheDocument()
    expect(screen.getByText('Bonsai')).toBeInTheDocument()
    expect(screen.getByText('Plutio')).toBeInTheDocument()
    expect(screen.getByText('See all comparisons →')).toBeInTheDocument()
  })
})
