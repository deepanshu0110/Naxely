import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('vite-react-ssg', () => ({ Head: () => null }))

vi.mock('@/components/layout/Navbar', () => ({ default: () => <div>Navbar</div> }))

vi.mock('@/components/ui/NaxelyMark', () => ({
  NaxelyMark: ({ size, color }: { size?: number; color?: string }) => (
    <span data-testid="naxely-mark" data-size={size} data-color={color} />
  ),
}))

let mockIsAuthenticated = false
vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({ isAuthenticated: mockIsAuthenticated }),
}))

vi.mock('@/hooks/useInView', () => ({
  useInView: () => ({ ref: { current: null }, inView: true }),
}))

import Landing from '../Landing'

function renderPage() {
  return render(
    <MemoryRouter>
      <Landing />
    </MemoryRouter>,
  )
}

describe('Landing page', () => {
  beforeEach(() => {
    mockIsAuthenticated = false
    vi.clearAllMocks()
  })

  it('renders hero heading and CTA for unauthenticated', () => {
    renderPage()
    expect(screen.getByText(/Turn raw data into/)).toBeInTheDocument()
    expect(screen.getByText(/client-ready reports/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /generate your first report/i })).toHaveAttribute('href', '/signup')
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login')
  })

  it('shows Go to Dashboard when authenticated', () => {
    mockIsAuthenticated = true
    renderPage()
    expect(screen.getByRole('link', { name: /go to dashboard/i })).toHaveAttribute('href', '/dashboard')
    expect(screen.queryByRole('link', { name: /generate your first report/i })).not.toBeInTheDocument()
  })

  it('renders How It Works section', () => {
    renderPage()
    expect(screen.getByText('How it works')).toBeInTheDocument()
    expect(screen.getByText('Upload your CSV or connect Google Sheets')).toBeInTheDocument()
    expect(screen.getByText('Configure your report in seconds')).toBeInTheDocument()
    expect(screen.getByText('Download a professional PDF in under 2 minutes')).toBeInTheDocument()
  })

  it('renders Features section', () => {
    renderPage()
    expect(screen.getByText('Everything you need')).toBeInTheDocument()
    expect(screen.getByText(/From raw data to client-ready PDF/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /upload a csv/i })).toBeInTheDocument()
  })

  it('renders Pricing section with plan names', () => {
    renderPage()
    const pricingHeadings = screen.getAllByText('Pricing')
    expect(pricingHeadings.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByRole('heading', { name: 'Free' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Pro' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Agency' })).toBeInTheDocument()
  })

  it('renders Testimonials stats section', () => {
    renderPage()
    expect(screen.getByText('Built for serious reporting work')).toBeInTheDocument()
    expect(screen.getByText('6,000+')).toBeInTheDocument()
    expect(screen.getByText('< 1 min')).toBeInTheDocument()
    expect(screen.getByText('16')).toBeInTheDocument()
  })

  it('renders FAQ section', () => {
    renderPage()
    expect(screen.getByText('Frequently asked questions')).toBeInTheDocument()
    expect(screen.getByText('Is Naxely free to use?')).toBeInTheDocument()
    expect(screen.getByText('Do I need my own AI API key?')).toBeInTheDocument()
  })

  it('renders Final CTA section', () => {
    renderPage()
    expect(screen.getByText(/Ready to stop spending hours on reports/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /get started free/i })).toHaveAttribute('href', '/signup')
  })

  it('renders Footer with legal links', () => {
    renderPage()
    const naxelyTexts = screen.getAllByText('Naxely')
    expect(naxelyTexts.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/Turn data into insights/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /privacy policy/i })).toHaveAttribute('href', '/privacy')
    expect(screen.getByRole('link', { name: /terms of service/i })).toHaveAttribute('href', '/terms')
  })

  it('renders NaxelyMark in the hero tag', () => {
    renderPage()
    const marks = screen.getAllByTestId('naxely-mark')
    expect(marks.length).toBeGreaterThanOrEqual(1)
  })

  it('renders Sample Report section', () => {
    renderPage()
    expect(screen.getByText(/See a Real Sample/)).toBeInTheDocument()
    expect(screen.getByText(/Download Sample CSV/)).toBeInTheDocument()
    expect(screen.getByText(/View Sample PDF Report/)).toBeInTheDocument()
  })
})
