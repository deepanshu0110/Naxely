import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-hot-toast')

const mockFetchReports = vi.fn().mockResolvedValue(undefined)
const mockDeleteReport = vi.fn().mockResolvedValue(undefined)
const mockBulkDeleteReports = vi.fn().mockResolvedValue(undefined)
const mockFetchProfile = vi.fn()

vi.mock('@/store/reportStore', () => ({
  useReportStore: vi.fn(),
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('@/components/layout/Sidebar', () => ({
  default: () => <div data-testid="sidebar" />,
}))

vi.mock('@/components/onboarding/WelcomeModal', () => ({
  default: ({ onClose }: any) => (
    <div data-testid="welcome-modal">
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))

vi.mock('@/components/ui/NaxelyMark', () => ({
  NaxelyMark: () => <div data-testid="naxely-mark" />,
}))

import { useReportStore } from '@/store/reportStore'
import { useAuthStore } from '@/store/authStore'
import Dashboard from '../Dashboard'
import type { Report } from '@/types/report'

const mockReports: Report[] = [
  {
    id: 'rep-1', title: 'Q1 Report', status: 'completed', template_type: 'marketing',
    row_count: 100, pdf_url: 'https://example.com/1.pdf', ai_summary: null,
    ai_insights: [], ai_anomalies: [], share_token: null, share_view_count: 0,
    created_at: '2026-06-01T12:00:00Z',
  },
  {
    id: 'rep-2', title: 'Q2 Report', status: 'processing', template_type: 'financial',
    row_count: 200, pdf_url: null, ai_summary: null,
    ai_insights: [], ai_anomalies: [], share_token: null, share_view_count: 0,
    created_at: '2026-06-02T12:00:00Z',
  },
]

function defaultUser(overrides: Record<string, any> = {}) {
  return {
    id: 'user-1', email: 'test@test.com', full_name: 'Test User', tier: 'free',
    has_completed_onboarding: true, tier_expires_at: null, has_api_key: false,
    ai_provider: null, logo_url: null, brand_color: null, company_name: null,
    reports_this_month: 0, monthly_limit: 3, theme_preference: 'light',
    avatar_url: null, ...overrides,
  }
}

function setupReportStore(overrides: Record<string, any> = {}) {
  vi.mocked(useReportStore).mockReturnValue({
    reports: [], isLoading: false, error: null,
    fetchReports: mockFetchReports, deleteReport: mockDeleteReport,
    bulkDeleteReports: mockBulkDeleteReports, ...overrides,
  })
}

function setupAuth(userOverrides: Record<string, any> = {}) {
  const user = defaultUser(userOverrides)
  vi.mocked(useAuthStore).mockImplementation((selector?: any) => {
    const state = { user, fetchProfile: mockFetchProfile }
    return selector ? selector(state) : state
  })
}

function renderPage() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupReportStore()
    setupAuth()
  })

  it('calls fetchReports on mount', () => {
    renderPage()
    expect(mockFetchReports).toHaveBeenCalledTimes(1)
  })

  it('shows loading spinner when isLoading and no reports', () => {
    setupReportStore({ isLoading: true })
    renderPage()
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
  })

  it('shows error with retry button', async () => {
    setupReportStore({ error: 'Failed to load' })
    renderPage()
    expect(screen.getByText('Failed to load')).toBeInTheDocument()
    await userEvent.click(screen.getByText('Retry'))
    expect(mockFetchReports).toHaveBeenCalledTimes(2)
  })

  it('shows empty state when no reports', () => {
    renderPage()
    expect(screen.getByText('No reports yet')).toBeInTheDocument()
    expect(screen.getByText('Create Report')).toBeInTheDocument()
  })

  it('renders report list', () => {
    setupReportStore({ reports: mockReports })
    renderPage()
    expect(screen.getByText('Q1 Report')).toBeInTheDocument()
    expect(screen.getByText('Q2 Report')).toBeInTheDocument()
  })

  it('shows welcome modal when onboarding incomplete', () => {
    setupAuth({ has_completed_onboarding: false })
    renderPage()
    expect(screen.getByTestId('welcome-modal')).toBeInTheDocument()
  })

  it('hides welcome modal when onboarding complete', () => {
    renderPage()
    expect(screen.queryByTestId('welcome-modal')).not.toBeInTheDocument()
  })

  it('shows bulk selection bar when reports selected', async () => {
    setupReportStore({ reports: mockReports })
    renderPage()

    const checkboxes = screen.getAllByRole('checkbox')
    await userEvent.click(checkboxes[0])

    expect(screen.getByText('1 selected')).toBeInTheDocument()
  })

  it('select all and clear buttons work', async () => {
    setupReportStore({ reports: mockReports })
    renderPage()

    const checkboxes = screen.getAllByRole('checkbox')
    await userEvent.click(checkboxes[0])

    const selectAll = screen.getByText(/select all/i)
    await userEvent.click(selectAll)
    expect(screen.getByText('2 selected')).toBeInTheDocument()

    await userEvent.click(screen.getByText('Clear'))
    expect(screen.queryByText(/selected/)).not.toBeInTheDocument()
  })

  it('opens bulk delete confirmation modal', async () => {
    setupReportStore({ reports: mockReports })
    renderPage()

    const checkboxes = screen.getAllByRole('checkbox')
    await userEvent.click(checkboxes[0])
    await userEvent.click(screen.getByText(/Delete 1/))

    expect(screen.getByText(/Delete 1 report\?/)).toBeInTheDocument()
  })

  it('calls bulkDeleteReports on confirm', async () => {
    setupReportStore({ reports: mockReports })
    renderPage()

    const checkboxes = screen.getAllByRole('checkbox')
    await userEvent.click(checkboxes[0])
    await userEvent.click(screen.getByText(/Delete 1/))

    const btns = screen.getAllByRole('button', { name: /delete/i })
    await userEvent.click(btns[btns.length - 1])

    expect(mockBulkDeleteReports).toHaveBeenCalledWith(['rep-1'])
  })

  it('closes welcome modal and refetches profile', async () => {
    setupAuth({ has_completed_onboarding: false })
    renderPage()
    expect(screen.getByTestId('welcome-modal')).toBeInTheDocument()

    await userEvent.click(screen.getByText('Close'))
    expect(screen.queryByTestId('welcome-modal')).not.toBeInTheDocument()
    expect(mockFetchProfile).toHaveBeenCalled()
  })
})
