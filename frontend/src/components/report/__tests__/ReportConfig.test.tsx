import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockUser = vi.hoisted(() => ({
  id: 'user-1',
  email: 'free@test.com',
  full_name: 'Free User',
  tier: 'free',
  has_api_key: false,
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (s: any) => any) => {
    const state = { user: mockUser, isLoading: false, isAuthenticated: true, initialize: vi.fn(), logout: vi.fn(), fetchProfile: vi.fn() }
    return selector ? selector(state) : state
  },
}))

import ReportConfigForm from '../ReportConfig'

function renderForm() {
  return render(
    <MemoryRouter>
      <ReportConfigForm onConfigChange={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('ReportConfig Groq guidance', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows Groq guidance link when free tier with no stored key', () => {
    mockUser.tier = 'free'
    mockUser.has_api_key = false
    renderForm()
    const groqLinks = screen.getAllByText('Get a free Groq key')
    expect(groqLinks.length).toBeGreaterThan(0)
    expect(groqLinks[0]).toHaveAttribute('href', 'https://console.groq.com/keys')
    expect(groqLinks[0]).toHaveAttribute('target', '_blank')
    const settingsLinks = screen.getAllByText('Add API key')
    expect(settingsLinks.length).toBeGreaterThan(0)
    expect(settingsLinks[0]).toHaveAttribute('href', '/settings?tab=api-key')
  })

  it('hides Groq guidance when free tier with stored key', () => {
    mockUser.tier = 'free'
    mockUser.has_api_key = true
    renderForm()
    expect(screen.queryAllByText('Get a free Groq key').length).toBe(0)
    expect(screen.queryAllByText('Add API key').length).toBe(0)
    expect(screen.getAllByText('✅').length).toBeGreaterThan(0)
  })

  it('hides Groq guidance when pro tier without stored key', () => {
    mockUser.tier = 'pro'
    mockUser.has_api_key = false
    renderForm()
    expect(screen.queryAllByText('Get a free Groq key').length).toBe(0)
    expect(screen.queryAllByText('Add API key').length).toBe(0)
    expect(screen.getAllByText('✅').length).toBeGreaterThan(0)
  })

  it('hides Groq guidance when agency tier without stored key', () => {
    mockUser.tier = 'agency'
    mockUser.has_api_key = false
    renderForm()
    expect(screen.queryAllByText('Get a free Groq key').length).toBe(0)
    expect(screen.queryAllByText('Add API key').length).toBe(0)
    expect(screen.getAllByText('✅').length).toBeGreaterThan(0)
  })
})
