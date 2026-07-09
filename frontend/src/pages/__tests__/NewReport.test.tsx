import { describe, it, expect, vi, beforeEach } from 'vitest'
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

vi.mock('@/lib/axios', () => ({
  default: { get: vi.fn(), post: vi.fn() },
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

vi.mock('@/components/report/ReportConfig', () => ({
  default: ({ onToneChange, onSectionsChange, onConfigChange }: any) => (
    <div data-testid="mock-report-config">
      <button data-testid="mock-config" onClick={() => {
        onToneChange('casual')
        onSectionsChange(['charts', 'kpi_overview', 'data_table', 'executive_summary'])
        onConfigChange({ title: 'Test Report', dateFrom: '2026-01-01', dateTo: '2026-06-30' })
      }}>
        Set Config
      </button>
    </div>
  ),
}))

vi.mock('@/components/report/ChartCustomizer', () => ({
  default: ({ onSpecsChange }: any) => (
    <div data-testid="mock-chart-customizer">
      <button data-testid="mock-charts" onClick={() => onSpecsChange([{ x: 'date', y: 'revenue', type: 'bar', title: 'Revenue' }])}>
        Set Charts
      </button>
    </div>
  ),
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
import api from '@/lib/axios'
import NewReport from '../NewReport'

function defaultUser(overrides: Record<string, any> = {}) {
  return {
    id: 'user-1', email: 'free@test.com', full_name: 'Free User', tier: 'free',
    has_completed_onboarding: true, tier_expires_at: null, has_api_key: false,
    ai_provider: null, logo_url: null, brand_color: null, company_name: null,
    reports_this_month: 0, monthly_limit: 3, theme_preference: 'light',
    avatar_url: null, ...overrides,
  }
}

function setupReportStore(overrides: Record<string, any> = {}) {
  vi.mocked(useReportStore).mockImplementation((selector?: any) => {
    const state = {
      generateReport: mockGenerateReport,
      uploadFile: vi.fn(),
      ...overrides,
    }
    return selector ? selector(state) : state
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

function renderPage(initialEntries: any[] = ['/report/new']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <NewReport />
    </MemoryRouter>,
  )
}

describe('NewReport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupReportStore()
    setupAuth()
    setupReportStatus()
    ;(api.get as any).mockResolvedValue({ data: [] })
  })

  it('renders sidebar and heading', () => {
    renderPage()
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByText('New Report')).toBeInTheDocument()
  })

  it('shows upload step by default', () => {
    renderPage()
    expect(screen.getByText('Upload Data')).toBeInTheDocument()
    expect(screen.getByText('CSV / Excel')).toBeInTheDocument()
  })

  it('toggles between CSV and Google Sheets sources', async () => {
    renderPage()
    expect(screen.getByText('CSV / Excel')).toBeInTheDocument()

    await userEvent.click(screen.getByText('Google Sheets'))
    expect(screen.getByPlaceholderText('https://docs.google.com/spreadsheets/d/...')).toBeInTheDocument()
  })

  it('back button is disabled at step 1', () => {
    renderPage()
    const backBtn = screen.getByText('Back').closest('button')
    expect(backBtn).toBeDisabled()
  })

  it('next button is disabled at step 1 without upload', () => {
    renderPage()
    const nextBtn = screen.getByText('Next').closest('button')
    expect(nextBtn).toBeDisabled()
  })

  it('advances to step 2 on file upload', async () => {
    renderPage()
    await userEvent.click(screen.getByTestId('mock-upload'))

    await waitFor(() => {
      expect(screen.getByText('Map Columns')).toBeInTheDocument()
    })
    expect(screen.getByTestId('mock-column-mapper')).toBeInTheDocument()
  })

  it('advances through steps 1 → 4', async () => {
    renderPage()

    await userEvent.click(screen.getByTestId('mock-upload'))
    await waitFor(() => expect(screen.getByText('Map Columns')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Configure Report')).toBeInTheDocument())

    await userEvent.click(screen.getByTestId('mock-config'))
    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Customize Charts')).toBeInTheDocument())
  })

  it('shows Generate Report button at step 4', async () => {
    renderPage()

    await userEvent.click(screen.getByTestId('mock-upload'))
    await waitFor(() => expect(screen.getByText('Map Columns')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Configure Report')).toBeInTheDocument())

    await userEvent.click(screen.getByTestId('mock-config'))
    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Customize Charts')).toBeInTheDocument())

    expect(screen.getByText('Generate Report')).toBeInTheDocument()
  })

  it('fetches templates for pro users on mount', async () => {
    setupAuth({ tier: 'pro', full_name: 'Pro User', company_name: 'Pro Co' })
    const templates = [
      { id: 't-1', name: 'Marketing', template_type: 'marketing', config: { tone: 'story-driven', sections: ['charts', 'kpi_overview', 'executive_summary'] }, is_default: true, created_at: '' },
    ]
    ;(api.get as any).mockResolvedValue({ data: templates })
    renderPage()

    await waitFor(() => {
      expect(api.get as any).toHaveBeenCalledWith('/templates')
    })
  })

  it('does not fetch templates for free users', () => {
    renderPage()
    expect(api.get as any).not.toHaveBeenCalledWith('/templates')
  })

  it('builds correct generate payload for pro user', async () => {
    mockGenerateReport.mockResolvedValue('report-123')
    setupAuth({ tier: 'pro', full_name: 'Pro User', company_name: 'Pro Co' })
    renderPage()

    await userEvent.click(screen.getByTestId('mock-upload'))
    await waitFor(() => expect(screen.getByText('Map Columns')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Configure Report')).toBeInTheDocument())

    await userEvent.click(screen.getByTestId('mock-config'))
    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Customize Charts')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Generate Report'))

    await waitFor(() => {
      expect(mockGenerateReport).toHaveBeenCalledWith(
        expect.objectContaining({
          upload_id: 'up-123',
          title: 'Test Report',
          sections: ['charts', 'kpi_overview', 'data_table', 'executive_summary'],
          tone: 'casual',
          date_range: { from: '2026-01-01', to: '2026-06-30' },
          brand: { company_name: 'Pro Co', prepared_by: 'Pro User' },
          workspace_id: null,
        }),
      )
    })
  })

  it('builds payload without brand for free user', async () => {
    mockGenerateReport.mockResolvedValue('report-123')
    renderPage()

    await userEvent.click(screen.getByTestId('mock-upload'))
    await waitFor(() => expect(screen.getByText('Map Columns')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Configure Report')).toBeInTheDocument())

    await userEvent.click(screen.getByTestId('mock-config'))
    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Customize Charts')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Generate Report'))

    await waitFor(() => {
      expect(mockGenerateReport).toHaveBeenCalledWith(
        expect.not.objectContaining({ brand: expect.anything() }),
      )
    })
  })

  it('shows GeneratingLoader when isPolling is true', () => {
    setupReportStatus({ isPolling: true, currentStep: 'charts', progress: 50 })
    renderPage()

    expect(screen.getByTestId('generating-loader')).toBeInTheDocument()
    expect(screen.getByTestId('gen-step')).toHaveTextContent('charts')
    expect(screen.getByTestId('gen-progress')).toHaveTextContent('50')
  })

  it('handles location state to skip to step 2', () => {
    renderPage([{ pathname: '/report/new', state: { uploadResult: mockUploadResult } }])

    expect(screen.getByText('Map Columns')).toBeInTheDocument()
    expect(screen.getByTestId('mock-column-mapper')).toBeInTheDocument()
  })

  it('shows GeneratingLoader when generating is true', async () => {
    mockGenerateReport.mockImplementation(() => new Promise(() => {}))
    setupAuth({ tier: 'pro', full_name: 'Pro User', company_name: 'Pro Co' })
    renderPage()

    await userEvent.click(screen.getByTestId('mock-upload'))
    await waitFor(() => expect(screen.getByText('Map Columns')).toBeInTheDocument())
    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Configure Report')).toBeInTheDocument())
    await userEvent.click(screen.getByTestId('mock-config'))
    await userEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Customize Charts')).toBeInTheDocument())

    await userEvent.click(screen.getByText('Generate Report'))

    expect(await screen.findByTestId('generating-loader')).toBeInTheDocument()
  })
})
