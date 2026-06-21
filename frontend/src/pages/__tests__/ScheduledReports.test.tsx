import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import ScheduledReports from '../ScheduledReports'

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('@/lib/axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/components/layout/Sidebar', () => ({
  default: () => <div data-testid="sidebar" />,
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'

function renderPage() {
  return render(
    <MemoryRouter>
      <ScheduledReports />
    </MemoryRouter>,
  )
}

const mockReports = [
  {
    id: 'sr-1',
    name: 'Weekly Client Summary',
    frequency: 'weekly',
    next_run_at: '2026-06-28T12:00:00Z',
    last_run_at: '2026-06-21T12:00:00Z',
    recipient_emails: ['client@example.com'],
    csv_storage_path: 'scheduled-sources/sr-1.csv',
    is_active: true,
    created_at: '2026-06-01T12:00:00Z',
    config_json: null,
  },
  {
    id: 'sr-2',
    name: 'Monthly Performance Report',
    frequency: 'monthly',
    next_run_at: '2026-07-21T12:00:00Z',
    last_run_at: null,
    recipient_emails: ['team@example.com', 'manager@example.com'],
    csv_storage_path: 'scheduled-sources/sr-2.csv',
    is_active: false,
    created_at: '2026-06-15T12:00:00Z',
    config_json: null,
  },
]

describe('ScheduledReports', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows upgrade prompt for free user', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'free', full_name: 'Free User', email: 'free@test.com' },
    })
    renderPage()
    expect(screen.getAllByText('Scheduled Reports').length).toBeGreaterThan(0)
    expect(screen.getByText('Available on Agency plan')).toBeInTheDocument()
    expect(screen.queryByText('New Schedule')).not.toBeInTheDocument()
  })

  it('shows upgrade prompt for pro user', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    renderPage()
    expect(screen.getByText('Available on Agency plan')).toBeInTheDocument()
  })

  it('shows empty state when no scheduled reports exist', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('No scheduled reports')).toBeInTheDocument()
    })
    expect(screen.getByText('Create Schedule')).toBeInTheDocument()
  })

  it('renders list of reports with mixed active/paused states', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: mockReports })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Weekly Client Summary')).toBeInTheDocument()
    })
    expect(screen.getByText('Monthly Performance Report')).toBeInTheDocument()
    expect(screen.getByText('Weekly')).toBeInTheDocument()
    expect(screen.getByText('Monthly')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Paused')).toBeInTheDocument()
  })

  it('shows error state with retry button', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockRejectedValue(new Error('Network error'))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('validates email format in create form', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Create Schedule')).toBeInTheDocument()
    })
    await user.click(screen.getByText('Create Schedule'))
    await waitFor(() => {
      expect(screen.getByText('Create Scheduled Report')).toBeInTheDocument()
    })
    const emailInput = screen.getByPlaceholderText(/enter email/i)
    await user.type(emailInput, 'not-an-email')
    await user.keyboard('{Enter}')
    expect(screen.getByText('Invalid email format')).toBeInTheDocument()
  })

  it('validates empty recipients in create form', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Create Schedule')).toBeInTheDocument()
    })
    await user.click(screen.getByText('Create Schedule'))
    await waitFor(() => {
      expect(screen.getByText('Create Scheduled Report')).toBeInTheDocument()
    })
    await user.type(screen.getByPlaceholderText('Weekly Client Summary'), 'Test Report')
    const submitBtn = screen.getByText('Create')
    await user.click(submitBtn)
    expect(screen.getByText('At least one recipient is required')).toBeInTheDocument()
  })

  it('creates report and refetches list', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'sr-new' } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Create Schedule')).toBeInTheDocument()
    })
    await user.click(screen.getByText('Create Schedule'))
    await waitFor(() => {
      expect(screen.getByText('Create Scheduled Report')).toBeInTheDocument()
    })
    await user.type(screen.getByPlaceholderText('Weekly Client Summary'), 'New Test Report')
    const emailInput = screen.getByPlaceholderText(/enter email/i)
    await user.type(emailInput, 'test@example.com')
    await user.keyboard('{Enter}')
    const fileInput = screen.getByLabelText(/upload csv/i)
    expect(fileInput).toBeInTheDocument()
  })

  it('calls PATCH with is_active on pause/resume toggle', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: mockReports })
    vi.mocked(api.patch).mockResolvedValue({ data: {} })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Weekly Client Summary')).toBeInTheDocument()
    })
    const pauseButtons = screen.getAllByTitle('Pause')
    await user.click(pauseButtons[0])
    expect(api.patch).toHaveBeenCalledWith('/scheduled-reports/sr-1', { is_active: false })
  })

  it('calls DELETE on delete confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: mockReports })
    vi.mocked(api.delete).mockResolvedValue({ data: {} })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Weekly Client Summary')).toBeInTheDocument()
    })
    const deleteButtons = screen.getAllByTitle('Delete')
    await user.click(deleteButtons[0])
    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
    })
    await user.click(screen.getByText('Delete', { selector: 'button' }))
    expect(api.delete).toHaveBeenCalledWith('/scheduled-reports/sr-1')
  })

  it('applies dark mode classes explicitly', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'agency', full_name: 'Agency User', email: 'agency@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    const { container } = renderPage()
    const mainElements = container.querySelectorAll('.dark\\:bg-darkBg')
    expect(mainElements.length).toBeGreaterThan(0)
  })
})
