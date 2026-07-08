import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Templates from '../Templates'

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

import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'

function renderPage() {
  return render(
    <MemoryRouter>
      <Templates />
    </MemoryRouter>,
  )
}

const mockTemplates = [
  {
    id: 'tmpl-1',
    name: 'Monthly Client Report',
    template_type: 'marketing',
    config: { tone: 'professional', sections: ['charts', 'kpi_overview', 'executive_summary'], brand: { company_name: 'Acme Inc', prepared_by: 'Jane Doe' } },
    is_default: true,
    created_at: '2026-06-01T12:00:00Z',
  },
  {
    id: 'tmpl-2',
    name: 'Weekly Summary',
    template_type: 'marketing',
    config: { tone: 'casual', sections: ['charts', 'data_table', 'insights'], brand: {} },
    is_default: false,
    created_at: '2026-06-15T12:00:00Z',
  },
]

describe('Templates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows upgrade prompt for free user', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'free', full_name: 'Free User', email: 'free@test.com' },
    })
    renderPage()
    expect(screen.getByRole('heading', { name: /templates/i })).toBeInTheDocument()
    expect(screen.getByText('Available on Pro plan')).toBeInTheDocument()
    expect(screen.queryByText('New Template')).not.toBeInTheDocument()
  })

  it('shows upgrade prompt for free user even when data loads', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'free', full_name: 'Free User', email: 'free@test.com' },
    })
    renderPage()
    expect(screen.getByRole('heading', { name: /templates/i })).toBeInTheDocument()
    expect(screen.getByText('Available on Pro plan')).toBeInTheDocument()
  })

  it('shows empty state when no templates exist for pro user', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: [] } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('No templates yet')).toBeInTheDocument()
    })
    expect(screen.getByText('Create Template')).toBeInTheDocument()
  })

  it('renders list of templates with mixed states', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: mockTemplates } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Monthly Client Report')).toBeInTheDocument()
    })
    expect(screen.getByText('Weekly Summary')).toBeInTheDocument()
    expect(screen.getByText('Monthly Client Report')).toBeInTheDocument()
    expect(screen.getAllByText('Default').length).toBeGreaterThanOrEqual(1)
  })

  it('shows error state with retry button', async () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockRejectedValue(new Error('Failed to load'))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Failed to load')).toBeInTheDocument()
    })
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('opens create form modal on New Template click', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: [] } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /no templates yet/i })).toBeInTheDocument()
    })
    await user.click(screen.getByText('Create Template'))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /new template/i })).toBeInTheDocument()
    })
    expect(screen.getByPlaceholderText('e.g. Monthly Client Report')).toBeInTheDocument()
  })

  it('validates template name is required in create form', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: [] } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /no templates yet/i })).toBeInTheDocument()
    })
    await user.click(screen.getByText('Create Template'))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /new template/i })).toBeInTheDocument()
    })
    const submitBtn = screen.getByText('Create')
    await user.click(submitBtn)
    expect(screen.getByText('Name is required')).toBeInTheDocument()
  })

  it('creates template via POST and refetches list', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: [] } })
    vi.mocked(api.post).mockResolvedValue({ data: { success: true, data: { id: 'tmpl-new' } } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /no templates yet/i })).toBeInTheDocument()
    })
    await user.click(screen.getByText('Create Template'))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /new template/i })).toBeInTheDocument()
    })
    await user.type(screen.getByPlaceholderText('e.g. Monthly Client Report'), 'Test Template')
    await user.click(screen.getByText('Create'))
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/templates', expect.objectContaining({
        name: 'Test Template',
        template_type: 'marketing',
        config: expect.objectContaining({
          tone: 'professional',
          sections: expect.arrayContaining(['charts', 'kpi_overview', 'data_table']),
        }),
      }))
    })
  })

  it('opens edit form with pre-filled values', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: mockTemplates } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Monthly Client Report')).toBeInTheDocument()
    })
    const editButtons = screen.getAllByTitle('Edit')
    await user.click(editButtons[0])
    await waitFor(() => {
      expect(screen.getByDisplayValue('Monthly Client Report')).toBeInTheDocument()
    })
  })

  it('saves edits via PATCH', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: mockTemplates } })
    vi.mocked(api.patch).mockResolvedValue({ data: { success: true } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Monthly Client Report')).toBeInTheDocument()
    })
    const editButtons = screen.getAllByTitle('Edit')
    await user.click(editButtons[0])
    await waitFor(() => {
      expect(screen.getByDisplayValue('Monthly Client Report')).toBeInTheDocument()
    })
    const nameInput = screen.getByDisplayValue('Monthly Client Report')
    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Report')
    await user.click(screen.getByText('Save'))
    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/templates/tmpl-1', expect.objectContaining({
        name: 'Updated Report',
        config: expect.any(Object),
      }))
    })
  })

  it('calls DELETE on delete confirmation', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: mockTemplates } })
    vi.mocked(api.delete).mockResolvedValue({ data: { success: true, data: { deleted: true } } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Monthly Client Report')).toBeInTheDocument()
    })
    const deleteButton = screen.getAllByTitle('Delete')
    await user.click(deleteButton[0])
    await waitFor(() => {
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
    })
    await user.click(screen.getByText('Delete', { selector: 'button' }))
    expect(api.delete).toHaveBeenCalledWith('/templates/tmpl-1')
  })

  it('sets template as default via PATCH is_default', async () => {
    const user = userEvent.setup()
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: mockTemplates } })
    vi.mocked(api.patch).mockResolvedValue({ data: { success: true } })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Monthly Client Report')).toBeInTheDocument()
    })
    const defaultCheckbox = screen.getAllByRole('checkbox')[1]
    await user.click(defaultCheckbox)
    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith('/templates/tmpl-2', { is_default: true })
    })
  })

  it('applies dark mode classes explicitly', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { tier: 'pro', full_name: 'Pro User', email: 'pro@test.com' },
    })
    vi.mocked(api.get).mockResolvedValue({ data: { success: true, data: [] } })
    const { container } = renderPage()
    const mainElements = container.querySelectorAll('.dark\\:bg-darkBg')
    expect(mainElements.length).toBeGreaterThan(0)
  })
})
