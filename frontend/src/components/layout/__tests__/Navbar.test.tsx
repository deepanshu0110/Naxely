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
})
