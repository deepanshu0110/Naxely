import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

const mockUser = {
  id: 'user-1',
  email: 'pro@test.com',
  full_name: 'Pro User',
  tier: 'pro',
  avatar_url: null,
  tier_expires_at: null,
  has_api_key: false,
  ai_provider: null,
  logo_url: null,
  brand_color: null,
  company_name: null,
  reports_this_month: 2,
  monthly_limit: null,
  theme_preference: 'light',
  has_completed_onboarding: true,
}

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (s: any) => any) => {
    const state = {
      user: mockUser,
      session: { access_token: 'fake-token' },
      isLoading: false,
      isAuthenticated: true,
      initialize: vi.fn(),
      logout: vi.fn(),
      fetchProfile: vi.fn(),
    }
    return selector ? selector(state) : state
  },
}))

const mockDeleteReport = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))

vi.mock('@/store/reportStore', () => ({
  useReportStore: (selector: (s: any) => any) => {
    const state = { deleteReport: mockDeleteReport }
    return selector ? selector(state) : state
  },
}))

const mockGetFn = vi.hoisted(() => vi.fn())
const mockPostFn = vi.hoisted(() => vi.fn())
const mockDeleteFn = vi.hoisted(() => vi.fn())
vi.mock('@/lib/axios', () => ({
  default: { get: mockGetFn, post: mockPostFn, delete: mockDeleteFn },
}))

const mockToast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))
vi.mock('react-hot-toast', () => ({ default: mockToast }))

const mockWriteText = vi.hoisted(() => vi.fn().mockResolvedValue(undefined))

import ReportView from '../ReportView'

const mockReport = {
  id: 'rep-abc123',
  title: 'Q2 Performance Report',
  status: 'completed' as const,
  template_type: 'marketing',
  row_count: 1500,
  pdf_url: 'https://supabase.co/reports/rep-abc123.pdf',
  ai_summary: null,
  ai_insights: [],
  ai_anomalies: [],
  share_token: null,
  share_view_count: 0,
  created_at: '2026-06-15T12:00:00Z',
  generation_time_seconds: 45,
}

function renderView() {
  return render(
    <MemoryRouter initialEntries={['/report/rep-abc123']}>
      <Routes>
        <Route path="/report/:id" element={<ReportView />} />
      </Routes>
    </MemoryRouter>,
  )
}

function stubClipboard() {
  Object.defineProperty(window.navigator, 'clipboard', {
    configurable: true,
    value: { writeText: mockWriteText },
  })
}

function stubBlobDownload() {
  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    value: vi.fn(() => 'blob:test-url'),
  })
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    value: vi.fn(),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockUser.tier = 'pro'
})

describe('ReportView PDF download', () => {
  it('calls download endpoint on button click instead of navigating to signed URL', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    const downloadBtn = await screen.findByText('Download PDF')
    expect(downloadBtn).toBeInTheDocument()

    mockGetFn.mockResolvedValueOnce(new Blob(['fake-pdf'], { type: 'application/pdf' }))
    await userEvent.click(downloadBtn)

    await waitFor(() => {
      expect(mockGetFn).toHaveBeenCalledWith(
        '/reports/rep-abc123/download',
        expect.objectContaining({ responseType: 'blob' }),
      )
    })
  })
})

describe('ReportView error and not-found states', () => {
  it('shows the load error message with a working back button when the API fails', async () => {
    mockGetFn.mockRejectedValueOnce(new Error('boom'))
    renderView()

    expect(await screen.findByText('Failed to load report')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Back to Dashboard' }))
    expect(screen.queryByText('Failed to load report')).not.toBeInTheDocument()
  })

  it('shows "Report not found" when the API returns no report', async () => {
    mockGetFn.mockResolvedValueOnce({ data: null })
    renderView()

    expect(await screen.findByText('Report not found')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Back to Dashboard' })).toBeInTheDocument()
  })
})

describe('ReportView failed report and retry', () => {
  it('shows the failure screen with error message, preserved-settings note, and error badge', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, status: 'failed', error_message: 'PDF rendering timed out' },
    })
    renderView()

    expect(await screen.findByText('Report generation failed')).toBeInTheDocument()
    expect(screen.getByText('PDF rendering timed out')).toBeInTheDocument()
    expect(
      screen.getByText('Your column mapping and settings are preserved.'),
    ).toBeInTheDocument()

    const badge = screen.getByText('failed')
    expect(badge.className).toContain('bg-red-50')
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument()
    expect(screen.queryByText('PDF preview not available')).not.toBeInTheDocument()
  })

  it('renders the failure screen without an error message paragraph when none exists', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, status: 'failed', error_message: null },
    })
    renderView()

    expect(await screen.findByText('Report generation failed')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument()
  })

  it('retries via the retry endpoint and navigates back to the dashboard', async () => {
    mockPostFn.mockResolvedValueOnce({ data: {} })
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, status: 'failed', error_message: 'boom' },
    })
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: 'Try Again' }))

    await waitFor(() => {
      expect(mockPostFn).toHaveBeenCalledWith('/reports/rep-abc123/retry')
    })
    expect(screen.queryByText('Report generation failed')).not.toBeInTheDocument()
  })

  it('stays on the failure screen when the retry call fails', async () => {
    mockPostFn.mockRejectedValueOnce(new Error('nope'))
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, status: 'failed', error_message: 'boom' },
    })
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: 'Try Again' }))

    await waitFor(() => {
      expect(mockPostFn).toHaveBeenCalledTimes(1)
    })
    expect(screen.getByText('Report generation failed')).toBeInTheDocument()
  })
})

describe('ReportView status badge variants', () => {
  it('shows a warning badge for processing reports', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, status: 'processing', pdf_url: null },
    })
    renderView()

    await screen.findByText('processing')
    const badge = screen.getByText('processing')
    expect(badge.className).toContain('bg-yellow-50')
    expect(screen.getByText('PDF preview not available')).toBeInTheDocument()
  })
})

describe('ReportView PDF preview', () => {
  it('renders the PDF in an iframe when a pdf_url exists', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await screen.findByText('Q2 Performance Report')
    const iframe = document.querySelector('iframe[title="Report PDF"]')
    expect(iframe).not.toBeNull()
    expect(iframe?.getAttribute('src')).toBe('https://supabase.co/reports/rep-abc123.pdf')
    expect(screen.queryByText('PDF preview not available')).not.toBeInTheDocument()
  })

  it('shows the no-preview message when a completed report has no pdf_url', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, pdf_url: null } })
    renderView()

    expect(await screen.findByText('PDF preview not available')).toBeInTheDocument()
    expect(document.querySelector('iframe[title="Report PDF"]')).toBeNull()
  })
})

describe('ReportView AI summary', () => {
  it('splits a long summary into a lead sentence and a body paragraph', async () => {
    mockGetFn.mockResolvedValue({
      data: {
        ...mockReport,
        ai_summary:
          'Revenue grew strongly in the last quarter across all major channels. The bounce rate also improved slightly.',
      },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    const section = screen.getByText('AI Summary').closest('div.rounded-xl')
    expect(section).not.toBeNull()

    const paragraphs = section?.querySelectorAll('p') ?? []
    expect(paragraphs).toHaveLength(2)
    expect(paragraphs[0]?.textContent).toBe(
      'Revenue grew strongly in the last quarter across all major channels.',
    )
    expect(paragraphs[1]?.textContent).toBe('The bounce rate also improved slightly.')
  })

  it('keeps a short summary with an early dot as a single paragraph with no body', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, ai_summary: 'Short. Then more text.' },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    const section = screen.getByText('AI Summary').closest('div.rounded-xl')
    const paragraphs = section?.querySelectorAll('p') ?? []
    expect(paragraphs).toHaveLength(1)
    expect(paragraphs[0]?.textContent).toBe('Short. Then more text.')
  })

  it('renders a dotless summary as a single paragraph and trims whitespace', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, ai_summary: '  No anomalies detected  ' },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    const section = screen.getByText('AI Summary').closest('div.rounded-xl')
    const paragraphs = section?.querySelectorAll('p') ?? []
    expect(paragraphs).toHaveLength(1)
    expect(paragraphs[0]?.textContent).toBe('No anomalies detected')
  })

  it('renders no AI Summary section for non-pro users', async () => {
    mockUser.tier = 'free'
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, ai_summary: 'Revenue grew strongly.' },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('AI Summary')).not.toBeInTheDocument()
  })
})

describe('ReportView insights', () => {
  it('renders insight cards with kpi, reason, action, and priority for pro users', async () => {
    mockGetFn.mockResolvedValue({
      data: {
        ...mockReport,
        ai_insights: [
          {
            kpi: 'Revenue',
            number: '42000',
            reason: 'Up 10% QoQ',
            action: 'Keep investing in paid ads',
            sentiment: 'positive',
            priority: 'high',
          },
        ],
      },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.getByText('Revenue')).toBeInTheDocument()
    expect(screen.getByText('Up 10% QoQ')).toBeInTheDocument()
    expect(screen.getByText('Keep investing in paid ads')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('renders no Insights section when the insights array is empty', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('Insights')).not.toBeInTheDocument()
  })

  it('renders no Insights section for non-pro users even with insights present', async () => {
    mockUser.tier = 'free'
    mockGetFn.mockResolvedValue({
      data: {
        ...mockReport,
        ai_insights: [
          {
            kpi: 'Revenue',
            number: '42000',
            reason: 'Up 10% QoQ',
            action: 'Keep investing',
            sentiment: 'positive',
            priority: 'high',
          },
        ],
      },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('Insights')).not.toBeInTheDocument()
  })
})

describe('ReportView share flow', () => {
  beforeEach(() => {
    stubClipboard()
  })

  it('creates a share link, copies it to the clipboard, and reveals the Revoke button', async () => {
    mockPostFn.mockResolvedValueOnce({
      data: { share_url: 'https://naxely.com/s/abc123', share_token: 'tok-xyz' },
    })
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: 'Share' }))

    await waitFor(() => {
      expect(mockPostFn).toHaveBeenCalledWith('/reports/rep-abc123/share', {
        expires_days: 30,
      })
    })
    expect(mockWriteText).toHaveBeenCalledWith('https://naxely.com/s/abc123')
    expect(mockToast.success).toHaveBeenCalledWith('Share link copied!')
    expect(await screen.findByRole('button', { name: 'Revoke' })).toBeInTheDocument()
  })

  it('revokes an existing share link and hides the Revoke button', async () => {
    mockDeleteFn.mockResolvedValueOnce({ data: {} })
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, share_token: 'tok-xyz' },
    })
    renderView()

    await screen.findByRole('button', { name: 'Revoke' })
    await userEvent.click(screen.getByRole('button', { name: 'Revoke' }))

    await waitFor(() => {
      expect(mockDeleteFn).toHaveBeenCalledWith('/reports/rep-abc123/share')
    })
    expect(mockToast.success).toHaveBeenCalledWith('Share link revoked')
    expect(screen.queryByRole('button', { name: 'Revoke' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Share' })).toBeInTheDocument()
  })

  it('shows no share button for free users', async () => {
    mockUser.tier = 'free'
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByRole('button', { name: 'Share' })).not.toBeInTheDocument()
  })

  it('fails silently when creating the share link errors: no clipboard write, no toast, no Revoke', async () => {
    mockPostFn.mockRejectedValueOnce(new Error('boom'))
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: 'Share' }))

    await waitFor(() => {
      expect(mockPostFn).toHaveBeenCalledTimes(1)
    })
    expect(mockWriteText).not.toHaveBeenCalled()
    expect(mockToast.success).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Revoke' })).not.toBeInTheDocument()
  })

  it('keeps the Revoke button when revoking fails', async () => {
    mockDeleteFn.mockRejectedValueOnce(new Error('boom'))
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, share_token: 'tok-xyz' },
    })
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: 'Revoke' }))

    await waitFor(() => {
      expect(mockDeleteFn).toHaveBeenCalledTimes(1)
    })
    expect(mockToast.success).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Revoke' })).toBeInTheDocument()
  })
})

describe('ReportView PowerPoint export', () => {
  beforeEach(() => {
    stubBlobDownload()
  })

  it('exports a PPTX via the export endpoint and shows a success toast for agency users', async () => {
    mockUser.tier = 'agency'
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    const exportBtn = await screen.findByRole('button', { name: 'Export as PowerPoint' })
    expect(exportBtn).toBeEnabled()

    mockGetFn.mockResolvedValueOnce(new Blob(['fake-pptx'], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' }))
    await userEvent.click(exportBtn)

    await waitFor(() => {
      expect(mockGetFn).toHaveBeenCalledWith(
        '/reports/rep-abc123/export/pptx',
        expect.objectContaining({ responseType: 'blob' }),
      )
    })
    expect(mockToast.success).toHaveBeenCalledWith('PowerPoint exported successfully')
  })

  it('disables the export button with an agency-only title for non-agency users', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    const exportBtn = await screen.findByRole('button', { name: 'Export as PowerPoint' })
    expect(exportBtn).toBeDisabled()
    expect(exportBtn).toHaveAttribute('title', 'Agency plan required')
  })
})

describe('ReportView modals', () => {
  it('opens the Send to Client modal from the header and closes it with Escape', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await userEvent.click(await screen.findByRole('button', { name: 'Send to Client' }))
    expect(screen.getByText('Send Report to Client')).toBeInTheDocument()
    expect(screen.getByText(/to your client via email/)).toBeInTheDocument()

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByText('Send Report to Client')).not.toBeInTheDocument()
  })

  it('cancels the delete confirmation without deleting', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await userEvent.click((await screen.findAllByRole('button', { name: 'Delete' }))[0])
    expect(screen.getByText('Delete Report')).toBeInTheDocument()
    expect(
      screen.getByText(/Are you sure you want to delete "Q2 Performance Report"\?/),
    ).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByText('Delete Report')).not.toBeInTheDocument()
    expect(mockDeleteReport).not.toHaveBeenCalled()
  })

  it('closes the delete confirmation with Escape without deleting', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await userEvent.click((await screen.findAllByRole('button', { name: 'Delete' }))[0])
    expect(screen.getByText('Delete Report')).toBeInTheDocument()

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByText('Delete Report')).not.toBeInTheDocument()
    expect(mockDeleteReport).not.toHaveBeenCalled()
  })
})

describe('ReportView info banners', () => {
  it('shows the rate-limit banner when ai_skipped is true', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, ai_skipped: true } })
    renderView()

    expect(await screen.findByText('AI insights were rate-limited.')).toBeInTheDocument()
    expect(
      screen.getByText('Upload the same CSV and generate a new report to retry.'),
    ).toBeInTheDocument()
  })

  it('shows no rate-limit banner when ai_skipped is false', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, ai_skipped: false } })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('AI insights were rate-limited.')).not.toBeInTheDocument()
  })

  it('shows the warning banner for a non-failed report that carries an error_message', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, error_message: 'Some columns were dropped' },
    })
    renderView()

    expect(await screen.findByText('Some columns were dropped')).toBeInTheDocument()
  })

  it('keeps the sidebar banner hidden for failed reports (message lives on the failure screen)', async () => {
    mockGetFn.mockResolvedValue({
      data: { ...mockReport, status: 'failed', error_message: 'rendering exploded' },
    })
    renderView()

    await screen.findByText('Report generation failed')
    expect(screen.getByText('rendering exploded')).toBeInTheDocument()
    expect(screen.getAllByText('rendering exploded')).toHaveLength(1)
  })
})

describe('ReportView stale data banner', () => {
  it('shows banner when data_source_stale is true', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, data_source_stale: true } })
    renderView()

    expect(await screen.findByText('This report was generated from cached data — the Google Sheet couldn\'t be refreshed at generation time. Data may be stale.')).toBeInTheDocument()
  })

  it('shows no banner when data_source_stale is false', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, data_source_stale: false } })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('This report was generated from cached data')).not.toBeInTheDocument()
  })

  it('shows no banner when data_source_stale is absent', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('This report was generated from cached data')).not.toBeInTheDocument()
  })
})

describe('ReportView anomaly alerts', () => {
  it('renders anomaly alerts with the real column/value/expected/deviation content', async () => {
    mockGetFn.mockResolvedValue({
      data: {
        ...mockReport,
        ai_anomalies: [
          { column: 'revenue', value: '25000', expected: '12000', deviation: '108%', severity: 'warning' },
          { column: 'churn_rate', value: '0.12', expected: '0.05', deviation: '140%', severity: 'critical' },
        ],
      },
    })
    renderView()

    expect(await screen.findByText('Anomaly Alerts')).toBeInTheDocument()

    const firstAlert = screen.getByText((_, el) => el?.tagName === 'P' && el.textContent === 'revenue: 25000')
    expect(firstAlert).toBeInTheDocument()
    expect(
      screen.getByText((_, el) => el?.tagName === 'P' && el.textContent === 'Expected: 12000 — Deviation: 108%'),
    ).toBeInTheDocument()

    const secondAlert = screen.getByText((_, el) => el?.tagName === 'P' && el.textContent === 'churn_rate: 0.12')
    expect(secondAlert).toBeInTheDocument()
    expect(
      screen.getByText((_, el) => el?.tagName === 'P' && el.textContent === 'Expected: 0.05 — Deviation: 140%'),
    ).toBeInTheDocument()

    expect(screen.queryByText('Upgrade to Pro')).not.toBeInTheDocument()
  })

  it('renders no anomaly alerts when ai_anomalies is an empty array', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, ai_anomalies: [] } })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('Anomaly Alerts')).not.toBeInTheDocument()
  })

  it('renders no anomaly alerts when ai_anomalies is absent', async () => {
    mockGetFn.mockResolvedValue({ data: { ...mockReport, ai_anomalies: null } })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('Anomaly Alerts')).not.toBeInTheDocument()
  })

  it('hides anomaly alerts from free users even when anomaly data is present', async () => {
    mockUser.tier = 'free'
    mockGetFn.mockResolvedValue({
      data: {
        ...mockReport,
        ai_anomalies: [
          { column: 'revenue', value: '25000', expected: '12000', deviation: '108%', severity: 'warning' },
        ],
      },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('Anomaly Alerts')).not.toBeInTheDocument()
  })
})

describe('ReportView upgrade prompt', () => {
  it('shows the upgrade prompt for free users with a working pricing link', async () => {
    mockUser.tier = 'free'
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    const upgradeLinks = await screen.findAllByRole('link', { name: /Upgrade to Pro/ })
    expect(upgradeLinks.length).toBeGreaterThan(0)
    for (const link of upgradeLinks) {
      expect(link).toHaveAttribute('href', '/pricing')
    }
    expect(screen.getByText('AI Summary & Insights')).toBeInTheDocument()
    expect(screen.getByText('Available on Pro plan')).toBeInTheDocument()
  })

  it('does not show the upgrade prompt for pro users', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('Upgrade to Pro')).not.toBeInTheDocument()
    expect(screen.queryByText('AI Summary & Insights')).not.toBeInTheDocument()
  })
})

describe('ReportView trend fields lock-in', () => {
  it('never renders trend_pct or trend_label even when present in the report payload', async () => {
    mockGetFn.mockResolvedValue({
      data: {
        ...mockReport,
        trend_pct: 87.3,
        trend_label: 'Strong growth',
      },
    })
    renderView()

    await screen.findByText('Q2 Performance Report')
    expect(screen.queryByText('87.3')).not.toBeInTheDocument()
    expect(screen.queryByText('Strong growth')).not.toBeInTheDocument()
    expect(screen.queryByText(/trend/i)).not.toBeInTheDocument()
  })
})

describe('ReportView delete flow', () => {
  it('confirms deletion then calls the store delete and navigates to dashboard', async () => {
    mockGetFn.mockResolvedValue({ data: mockReport })
    renderView()

    await screen.findByText('Q2 Performance Report')

    const headerDelete = screen.getAllByRole('button', { name: 'Delete' })[0]
    await userEvent.click(headerDelete)

    expect(screen.getByText('Delete Report')).toBeInTheDocument()

    const modalDelete = screen.getAllByRole('button', { name: 'Delete' })[1]
    await userEvent.click(modalDelete)

    await waitFor(() => {
      expect(mockDeleteReport).toHaveBeenCalledWith('rep-abc123')
    })
  })
})
