import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-hot-toast')

vi.mock('@/store/authStore', () => ({ useAuthStore: vi.fn() }))

vi.mock('@/lib/axios', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))

vi.mock('@/lib/dates', () => ({
  formatBillingDate: vi.fn(() => 'Jul 15, 2026'),
}))

vi.mock('@/components/layout/Sidebar', () => ({
  default: () => <div data-testid="sidebar" />,
}))

vi.mock('@/components/ui/Tabs', () => ({
  default: ({ items, activeId, onChange, children }: any) => (
    <div data-testid="tabs">
      <div data-testid="tab-buttons">
        {items.map((item: any) => (
          <button key={item.id} data-tab-id={item.id} onClick={() => onChange(item.id)}>
            {item.label}
          </button>
        ))}
      </div>
      <div data-testid="tab-content">{children}</div>
    </div>
  ),
}))

vi.mock('@/components/ui/UpgradePrompt', () => ({
  default: ({ feature, tier }: any) => (
    <div data-testid="upgrade-prompt">{feature} requires {tier} plan</div>
  ),
}))

vi.mock('@/components/settings/ApiKeyForm', () => ({
  default: () => <div data-testid="api-key-form" />,
}))



import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import Settings from '../Settings'

const mockProfile = {
  email: 'test@test.com',
  full_name: 'Test User',
  tier: 'free',
  ai_provider: null,
  has_api_key: false,
  api_key_preview: null,
  logo_url: null,
  brand_color: null,
  company_name: null,
  theme_preference: 'light',
  reports_this_month: 0,
  monthly_limit: null,
}

function defaultUser(overrides: Record<string, any> = {}) {
  return {
    id: 'user-1', email: 'test@test.com', full_name: 'Test User', tier: 'free',
    has_completed_onboarding: true, tier_expires_at: null, has_api_key: false,
    ai_provider: null, logo_url: null, brand_color: null, company_name: null,
    reports_this_month: 0, monthly_limit: null, theme_preference: 'light',
    avatar_url: null, ...overrides,
  }
}

function setupAuth(overrides: Record<string, any> = {}) {
  const user = defaultUser(overrides)
  vi.mocked(useAuthStore).mockReturnValue({ user, fetchProfile: vi.fn() })
}

function setupApi() {
  vi.mocked(api.get).mockResolvedValue({ data: mockProfile })
  vi.mocked(api.post).mockResolvedValue({ data: {} })
  vi.mocked(api.patch).mockResolvedValue({ data: {} })
  vi.mocked(api.delete).mockResolvedValue({ data: {} })
}

function renderPage() {
  return render(
    <MemoryRouter>
      <Settings />
    </MemoryRouter>,
  )
}

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupAuth()
    setupApi()
  })

  it('shows skeleton while loading', () => {
    vi.mocked(api.get).mockImplementation(() => new Promise(() => {}))
    const { container } = renderPage()
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
  })

  it('shows error state with retry button', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('Failed to load settings'))
    renderPage()

    expect(await screen.findByText('Failed to load settings')).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('renders profile tab by default', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    expect(api.get).toHaveBeenCalledWith('/settings/profile')
    expect(screen.getByText('Full name')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument()
  })

  it('profile tab shows email as read-only', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    const emailInput = screen.getByLabelText('Email')
    expect(emailInput).toHaveAttribute('readonly')
    expect(emailInput).toHaveValue('test@test.com')
  })

  it('profile tab saves name on submit', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    const nameInput = screen.getByLabelText('Full name')
    await userEvent.clear(nameInput)
    await userEvent.type(nameInput, 'Updated Name')

    await userEvent.click(screen.getByText('Save'))

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/settings/profile', { full_name: 'Updated Name' })
    })
  })

  it('switches to branding tab and shows upgrade prompt for free user', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Branding'))

    expect(screen.getByTestId('upgrade-prompt')).toBeInTheDocument()
    expect(screen.getByText('Custom Branding requires Pro plan')).toBeInTheDocument()
  })

  it('shows branding form for pro user', async () => {
    const proProfile = { ...mockProfile, tier: 'pro', brand_color: '#D97A34', company_name: 'Pro Co', logo_url: null }
    vi.mocked(api.get).mockResolvedValue({ data: proProfile })
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Branding'))
    await waitFor(() => {
      expect(screen.getByText('Brand Colour')).toBeInTheDocument()
    })

    expect(screen.getByDisplayValue('#D97A34')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Pro Co')).toBeInTheDocument()
  })

  it('branding validates hex colour on submit', async () => {
    const proProfile = { ...mockProfile, tier: 'pro', brand_color: '#D97A34', company_name: 'Pro Co', logo_url: null }
    vi.mocked(api.get).mockResolvedValue({ data: proProfile })
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Branding'))
    await waitFor(() => {
      expect(screen.getByText('Brand Colour')).toBeInTheDocument()
    })

    const colorInput = screen.getByDisplayValue('#D97A34')
    await userEvent.clear(colorInput)
    await userEvent.type(colorInput, 'red')

    await userEvent.click(screen.getByText('Save Branding'))

    expect(await screen.findByText('Must be a valid hex colour')).toBeInTheDocument()
  })

  it('switches to billing tab', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Billing'))

    expect(screen.getByText('Current Plan')).toBeInTheDocument()
  })

  it('billing tab shows account delete modal', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => {
      expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Delete Account'))
    expect(screen.getByText(/permanently delete your account/i)).toBeInTheDocument()
    expect(screen.getByText('Permanently Delete')).toBeInTheDocument()
  })

  it('renders API Key tab with ApiKeyForm', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('API Key'))
    expect(screen.getByTestId('api-key-form')).toBeInTheDocument()
  })

  it('calls api.delete with email on account delete confirm', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => {
      expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByText('Delete Account'))
    const emailInput = screen.getByPlaceholderText('test@test.com')
    await userEvent.type(emailInput, 'test@test.com')
    await userEvent.click(screen.getByText('Permanently Delete'))

    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith('/settings/account', {
        data: { email: 'test@test.com' },
      })
    })
  })

  it('branding tab saves branding on submit for pro user', async () => {
    const proProfile = { ...mockProfile, tier: 'pro', brand_color: '#D97A34', company_name: 'Pro Co', logo_url: null }
    vi.mocked(api.get).mockResolvedValue({ data: proProfile })
    const brandResp = { brand_color: '#D97A34', company_name: 'Pro Co', logo_url: 'https://example.com/logo.png', suggested_colors: ['#111', '#222'] }
    vi.mocked(api.post).mockResolvedValue({ data: brandResp })
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Branding'))
    await waitFor(() => expect(screen.getByText('Brand Colour')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Save Branding'))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/settings/branding',
        expect.any(FormData),
        expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } }),
      )
    })
    expect(screen.getByDisplayValue('#D97A34')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Pro Co')).toBeInTheDocument()
  })

  it('branding tab calls upgrade endpoint for free user on upgrade click', async () => {
    renderPage()

    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => expect(screen.getByText('Current Plan')).toBeInTheDocument())

    const upgradeBtn = screen.getByText('Upgrade to Pro')
    await userEvent.click(upgradeBtn)

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/payments/checkout', { plan: 'pro' })
    })
  })

  it('billing tab shows upgrade options for free user', async () => {
    renderPage()

    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => expect(screen.getByText('Current Plan')).toBeInTheDocument())

    expect(screen.getByText('Upgrade')).toBeInTheDocument()
    expect(screen.getByText('$29/month')).toBeInTheDocument()
    expect(screen.getByText('$79/month')).toBeInTheDocument()
    expect(screen.getAllByText('Upgrade to Pro').length).toBeGreaterThan(0)
    expect(screen.getByText('Upgrade to Agency')).toBeInTheDocument()
  })

  it('billing tab shows subscription data and downgrade options for pro user', async () => {
    const subResp = {
      data: {
        success: true,
        data: {
          has_subscription: true,
          scheduled_change: null,
          cancel_at_next_billing_date: false,
          next_billing_date: '2026-08-01',
          status: 'active',
        },
      },
    }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockResolvedValueOnce(subResp)
    setupAuth({ tier: 'pro', tier_expires_at: '2026-08-01' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => {
      expect(screen.getByText('Change Plan')).toBeInTheDocument()
    })

    expect(api.get).toHaveBeenCalledWith('/payments/subscription')
    expect(screen.getAllByText('Downgrade to Free').length).toBe(2)
    expect(screen.getByText('Jul 15, 2026')).toBeInTheDocument()
  })

  it('billing tab shows scheduled upgrade for pro user', async () => {
    const subResp = {
      data: {
        success: true,
        data: {
          has_subscription: true,
          scheduled_change: { planned_tier: 'pro', effective_at: '2026-09-01' },
          cancel_at_next_billing_date: false,
          next_billing_date: null,
          status: 'active',
        },
      },
    }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockResolvedValueOnce(subResp)
    setupAuth({ tier: 'pro', tier_expires_at: '2026-08-01' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => {
      expect(screen.getByText(/Scheduled/)).toBeInTheDocument()
    })

    expect(screen.getByText(/moving to Pro/)).toBeInTheDocument()
  })

  it('billing tab shows scheduled downgrade via cancel_at_next_billing_date', async () => {
    const subResp = {
      data: {
        success: true,
        data: {
          has_subscription: true,
          scheduled_change: null,
          cancel_at_next_billing_date: true,
          next_billing_date: '2026-09-01',
          status: 'active',
        },
      },
    }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockResolvedValueOnce(subResp)
    setupAuth({ tier: 'pro', tier_expires_at: '2026-08-01' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => {
      expect(screen.getByText(/Scheduled/)).toBeInTheDocument()
    })

    expect(screen.getByText(/moving to Free/)).toBeInTheDocument()
  })

  it('billing tab cancel scheduled change calls api', async () => {
    const subResp = {
      data: {
        success: true,
        data: {
          has_subscription: true,
          scheduled_change: { planned_tier: 'pro', effective_at: '2026-09-15' },
          cancel_at_next_billing_date: false,
          next_billing_date: null,
          status: 'active',
        },
      },
    }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockResolvedValueOnce(subResp)
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => expect(screen.getByText(/Scheduled/)).toBeInTheDocument())

    await userEvent.click(screen.getByText('Cancel'))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/payments/cancel-scheduled-change')
    })
  })

  it('billing tab handles subscription fetch error gracefully', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockRejectedValueOnce(new Error('network error'))
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => {
      expect(screen.getByText('Change Plan')).toBeInTheDocument()
    })
  })

  it('billing tab opens downgrade modal for pro user', async () => {
    const subResp = {
      data: {
        success: true,
        data: {
          has_subscription: true,
          scheduled_change: null,
          cancel_at_next_billing_date: false,
          next_billing_date: null,
          status: 'active',
        },
      },
    }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockResolvedValueOnce(subResp)
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => expect(screen.getByText('Change Plan')).toBeInTheDocument())

    const downgradeButton = screen.getAllByText('Downgrade to Free')[1]
    await userEvent.click(downgradeButton)
    await waitFor(() => {
      expect(screen.getByText(/Are you sure/)).toBeInTheDocument()
    })

    expect(screen.getByText('Keep Current Plan')).toBeInTheDocument()
  })

  it('billing tab downgrade modal confirms and calls api', async () => {
    const subResp = {
      data: {
        success: true,
        data: {
          has_subscription: true,
          scheduled_change: null,
          cancel_at_next_billing_date: false,
          next_billing_date: null,
          status: 'active',
        },
      },
    }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...mockProfile, tier: 'pro' } })
      .mockResolvedValueOnce(subResp)
    setupAuth({ tier: 'pro' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Billing'))
    await waitFor(() => expect(screen.getByText('Change Plan')).toBeInTheDocument())

    await userEvent.click(screen.getAllByText('Downgrade to Free')[1])
    await waitFor(() => {
      expect(screen.getByText(/Are you sure/)).toBeInTheDocument()
    })

    const confirmButtons = screen.getAllByRole('button', { name: /downgrade to free/i })
    await userEvent.click(confirmButtons[confirmButtons.length - 1])
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/payments/downgrade', { plan: 'free' })
    })
  })

  it('agency tier shows ApiKeys tab with key generation', async () => {
    const agencyProfile = { ...mockProfile, tier: 'agency', brand_color: '#D97A34' }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: agencyProfile })
      .mockResolvedValueOnce({ data: [] })
    setupAuth({ tier: 'agency' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    const apiKeysTab = screen.getByText('API Keys')
    expect(apiKeysTab).toBeInTheDocument()

    await userEvent.click(apiKeysTab)

    await waitFor(() => {
      expect(screen.getByText('Generate New Key')).toBeInTheDocument()
    })
  })

  it('api keys tab generates and shows new key', async () => {
    const agencyProfile = { ...mockProfile, tier: 'agency', brand_color: '#D97A34' }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: agencyProfile })
      .mockResolvedValueOnce({ data: [] })
    setupAuth({ tier: 'agency' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('API Keys'))
    await waitFor(() => expect(screen.getByText('Generate New Key')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Generate New Key'))

    const keyNameInput = screen.getByPlaceholderText('e.g. CI integration')
    await userEvent.type(keyNameInput, 'ci-key')

    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        id: 'key-1',
        name: 'ci-key',
        key: 'nxly_test_abc123',
        key_prefix: 'nxly_test',
        key_suffix: 'abc123',
        created_at: '2026-07-08T00:00:00Z',
      },
    })

    await userEvent.click(screen.getByText('Generate'))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/settings/api-keys', { name: 'ci-key' })
    })

    expect(screen.getByText(/nxly_test_abc123/)).toBeInTheDocument()
  })

  it('api keys tab revokes a key', async () => {
    const agencyProfile = { ...mockProfile, tier: 'agency' }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: agencyProfile })
      .mockResolvedValueOnce({
        data: [
          { id: 'key-1', name: 'test-key', key_display: 'nxly_test...abc123', created_at: '2026-07-08T00:00:00Z', last_used_at: null, revoked: false },
        ],
      })
    setupAuth({ tier: 'agency' })

    renderPage()
    await waitFor(() => expect(screen.getByText('Settings')).toBeInTheDocument())

    await userEvent.click(screen.getByText('API Keys'))
    await waitFor(() => expect(screen.getByText('test-key')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Revoke'))

    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith('/settings/api-keys/key-1')
    })
  })
})
