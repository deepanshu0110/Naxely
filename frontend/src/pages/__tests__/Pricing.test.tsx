import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockPost = vi.hoisted(() => vi.fn())
let mockIsAuthenticated = false

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({ isAuthenticated: mockIsAuthenticated, initialize: vi.fn() }),
}))

vi.mock('@/components/layout/Navbar', () => ({
  default: () => <div>Navbar</div>,
}))

vi.mock('@/lib/axios', () => ({
  default: { post: mockPost },
}))

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

vi.mock('vite-react-ssg', () => ({
  Head: () => null,
}))

import Pricing from '../Pricing'

function renderPage() {
  return render(
    <MemoryRouter>
      <Pricing />
    </MemoryRouter>,
  )
}

describe('Pricing page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsAuthenticated = false
  })

  it('renders all 3 plan names (Free, Pro, Agency)', () => {
    renderPage()
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText('Pro')).toBeInTheDocument()
    expect(screen.getByText('Agency')).toBeInTheDocument()
  })

  it('Pro card shows "Most Popular" badge', () => {
    renderPage()
    expect(screen.getByText('Most Popular')).toBeInTheDocument()
  })

  it('Free plan shows "Start Free" Link to /signup', () => {
    renderPage()
    const link = screen.getByRole('link', { name: /start free/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/signup')
  })

  it('Pro shows correct price $29', () => {
    renderPage()
    expect(screen.getByText('$29')).toBeInTheDocument()
  })

  it('FAQ section renders', () => {
    renderPage()
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument()
    expect(screen.getByText('Can I cancel anytime?')).toBeInTheDocument()
    expect(screen.getByText('Do I need a credit card for the free plan?')).toBeInTheDocument()
    expect(screen.getByText('What AI providers are supported?')).toBeInTheDocument()
    expect(screen.getByText('Is my data secure?')).toBeInTheDocument()
    expect(screen.getByText('Can agencies white-label reports?')).toBeInTheDocument()
  })

  it('when not authenticated: Pro/Agency show Link to /signup', () => {
    renderPage()
    const upgradePro = screen.getByRole('link', { name: /upgrade to pro/i })
    expect(upgradePro).toBeInTheDocument()
    expect(upgradePro).toHaveAttribute('href', '/signup')

    const upgradeAgency = screen.getByRole('link', { name: /upgrade to agency/i })
    expect(upgradeAgency).toBeInTheDocument()
    expect(upgradeAgency).toHaveAttribute('href', '/signup')
  })

  it('when authenticated: Pro/Agency show Button (not Link)', () => {
    mockIsAuthenticated = true
    renderPage()

    expect(screen.queryByRole('link', { name: /upgrade to pro/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /upgrade to agency/i })).not.toBeInTheDocument()

    expect(screen.getByRole('button', { name: /upgrade to pro/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /upgrade to agency/i })).toBeInTheDocument()
  })
})