import { describe, it, expect, vi, beforeEach } from 'vitest'
vi.setConfig({ testTimeout: 30_000 })
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-hot-toast')

const mockGenerateReport = vi.fn()
const mockStartPolling = vi.fn()

vi.mock('@/store/reportStore', () => ({
  useReportStore: vi.fn(),
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('@/hooks/useReportStatus', () => ({
  useReportStatus: vi.fn(),
}))

const mockApiGet = vi.hoisted(() => vi.fn())
const mockApiPost = vi.hoisted(() => vi.fn())
vi.mock('@/lib/axios', () => ({
  default: { get: mockApiGet, post: mockApiPost },
}))

vi.mock('@/components/layout/Sidebar', () => ({
  default: () => <div data-testid="sidebar" />,
}))

const mockUploadResult = {
  upload_id: 'up-123',
  filename: 'test.csv',
  file_url: 'https://example.com/test.csv',
  row_count: 100,
  column_count: 5,
  columns: [
    { original_name: 'date', suggested_name: 'Date', suggested_type: 'date', sample_values: ['2024-01-01', '2024-01-02'], null_count: 0, unique_count: 10 },
    { original_name: 'revenue', suggested_name: 'Revenue', suggested_type: 'metric', sample_values: [100, 200], null_count: 1, unique_count: 20 },
  ],
  preview_rows: [],
}

const mockColumnConfig = [
  { original_name: 'date', display_name: 'Date', type: 'date', include: true },
  { original_name: 'revenue', display_name: 'Revenue', type: 'metric', include: true },
]

vi.mock('@/components/report/FileUpload', () => ({
  default: ({ onUploadComplete }: any) => (
    <div data-testid="mock-file-upload">
      <button data-testid="mock-upload" onClick={() => onUploadComplete(mockUploadResult)}>
        Upload Complete
      </button>
    </div>
  ),
}))

vi.mock('@/components/report/ColumnMapper', () => ({
  default: ({ onChange }: any) => {
    onChange(mockColumnConfig)
    return <div data-testid="mock-column-mapper" />
  },
}))

vi.mock('@/components/report/ChartCustomizer', () => ({
  default: () => <div data-testid="mock-chart-customizer" />,
}))

vi.mock('@/components/report/GeneratingLoader', () => ({
  default: ({ currentStep, progress, timeoutMessage }: any) => (
    <div data-testid="generating-loader">
      <span data-testid="gen-step">{currentStep}</span>
      <span data-testid="gen-progress">{progress}</span>
      {timeoutMessage && <span data-testid="gen-timeout">{timeoutMessage}</span>}
    </div>
  ),
}))

import { useReportStore } from '@/store/reportStore'
import { useAuthStore } from '@/store/authStore'
import { useReportStatus } from '@/hooks/useReportStatus'
import NewReport from '../NewReport'

function defaultUser(overrides: Record<string, any> = {}) {
  return {
    id: 'user-1', email: 'pro@test.com', full_name: 'Pro User', tier: 'pro',
    has_completed_onboarding: true, tier_expires_at: null, has_api_key: false,
    ai_provider: null, logo_url: null, brand_color: null, company_name: 'Pro Co',
    reports_this_month: 0, monthly_limit: 10, theme_preference: 'light',
    avatar_url: null, ...overrides,
  }
}

function setupReportStore(overrides: Record<string, any> = {}) {
  vi.mocked(useReportStore).mockReturnValue({
    generateReport: mockGenerateReport,
    uploadFile: vi.fn(),
    ...overrides,
  })
}

function setupAuth(userOverrides: Record<string, any> = {}) {
  const user = defaultUser(userOverrides)
  vi.mocked(useAuthStore).mockImplementation((selector?: any) => {
    const state = { user, fetchProfile: vi.fn() }
    return selector ? selector(state) : state
  })
}

function setupReportStatus(overrides: Record<string, any> = {}) {
  vi.mocked(useReportStatus).mockReturnValue({
    progress: 0, currentStep: '', isPolling: false,
    timeoutMessage: null, startPolling: mockStartPolling,
    ...overrides,
  })
}

async function navigateToStep3() {
  await userEvent.click(screen.getByTestId('mock-upload'))
  await waitFor(() => expect(screen.getByText('Map Columns')).toBeInTheDocument())
  await userEvent.click(screen.getByText('Next'))
  await waitFor(() => expect(screen.getByText('Configure Report')).toBeInTheDocument())
}

describe('NewReport — regression: template selection survives unrelated field interaction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupReportStore()
    setupAuth()
    setupReportStatus()
    mockApiGet.mockResolvedValue({ data: [] })
  })

  it('selecting template then typing title keeps template tone and sections', async () => {
    const templates = [
      {
        id: 't-1', name: 'Story Template', template_type: 'marketing',
        config: { tone: 'story-driven', sections: ['charts', 'anomalies'], brand: { company_name: 'Template Co' } },
        is_default: true, created_at: '',
      },
    ]
    mockApiGet.mockResolvedValue({ data: templates })
    setupAuth({ tier: 'pro', company_name: 'Pro Co' })

    render(
      <MemoryRouter>
        <NewReport />
      </MemoryRouter>,
    )

    await navigateToStep3()

    await screen.findByText('Load from template')
    const templateSelect = screen.getByDisplayValue(/Story Template/) as HTMLSelectElement
    expect(templateSelect.value).toBe('t-1')

    const storyBtn = screen.getByText('Story-driven')
    expect(storyBtn.closest('button')).toHaveClass('border-amber-500')

    expect(screen.getByRole('checkbox', { name: /Anomaly Detection/ })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: /Charts/ })).toBeChecked()

    const titleInput = screen.getByPlaceholderText('e.g. Q1 2024 Marketing Performance')
    await userEvent.type(titleInput, 'My Custom Report Title')

    expect(storyBtn.closest('button')).toHaveClass('border-amber-500')
    expect(screen.getByRole('checkbox', { name: /Anomaly Detection/ })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: /Charts/ })).toBeChecked()
  })
})

describe('NewReport — regression: section checkboxes individually update state', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupReportStore()
    setupAuth({ tier: 'pro' })
    setupReportStatus()
    mockApiGet.mockResolvedValue({ data: [] })
  })

  it('toggles each of the 6 section checkboxes and updates state', async () => {
    render(
      <MemoryRouter>
        <NewReport />
      </MemoryRouter>,
    )

    await navigateToStep3()

    const sections = [
      { id: 'charts', label: 'Charts' },
      { id: 'kpi_overview', label: 'Key Metrics' },
      { id: 'data_table', label: 'Data Table' },
      { id: 'executive_summary', label: 'Executive Summary' },
      { id: 'insights', label: 'AI Insights' },
      { id: 'anomalies', label: 'Anomaly Detection' },
    ]

    for (const s of sections) {
      const checkbox = screen.getByRole('checkbox', { name: new RegExp(s.label) })
      const wasChecked = (checkbox as HTMLInputElement).checked

      await userEvent.click(checkbox)
      await waitFor(() => {
        expect((checkbox as HTMLInputElement).checked).toBe(!wasChecked)
      })

      await userEvent.click(checkbox)
      await waitFor(() => {
        expect((checkbox as HTMLInputElement).checked).toBe(wasChecked)
      })
    }
  })
})
