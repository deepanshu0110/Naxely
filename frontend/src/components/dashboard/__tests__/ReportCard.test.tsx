import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-hot-toast')

const mockGetFn = vi.hoisted(() => vi.fn())
vi.mock('@/lib/axios', () => ({
  default: { get: mockGetFn },
}))

import ReportCard from '../ReportCard'
import type { Report } from '@/types/report'

const mockReport: Report = {
  id: 'rep-abc123',
  title: 'Q2 Performance Report',
  status: 'completed',
  template_type: 'marketing',
  row_count: 1500,
  pdf_url: 'https://supabase.co/reports/rep-abc123.pdf',
  ai_summary: null,
  ai_insights: [],
  ai_anomalies: [],
  share_token: null,
  share_view_count: 0,
  created_at: '2026-06-15T12:00:00Z',
}

function renderCard(report = mockReport) {
  return render(
    <MemoryRouter>
      <ReportCard report={report} onDelete={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('ReportCard PDF download', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('downloads PDF via backend endpoint when download icon is clicked', async () => {
    renderCard()

    const downloadIcon = screen.getByTitle('Download PDF')
    expect(downloadIcon).toBeInTheDocument()

    mockGetFn.mockResolvedValueOnce(new Blob(['fake-pdf'], { type: 'application/pdf' }))
    await userEvent.click(downloadIcon)

    expect(mockGetFn).toHaveBeenCalledWith(
      '/reports/rep-abc123/download',
      expect.objectContaining({ responseType: 'blob' }),
    )
  })

  it('does not show download icon when pdf_url is null', () => {
    renderCard({ ...mockReport, pdf_url: null })

    expect(screen.queryByTitle('Download PDF')).not.toBeInTheDocument()
  })
})

describe('ReportCard warning indicators', () => {
  it('renders the stale-data icon when data_source_stale is true', () => {
    renderCard({ ...mockReport, data_source_stale: true })

    expect(screen.getByLabelText('Data may be stale — Google Sheet couldn\'t refresh at generation time')).toBeInTheDocument()
  })

  it('does NOT render the stale-data icon when data_source_stale is false', () => {
    renderCard({ ...mockReport, data_source_stale: false })

    expect(screen.queryByLabelText('Data may be stale — Google Sheet couldn\'t refresh at generation time')).not.toBeInTheDocument()
  })

  it('does NOT render the stale-data icon when data_source_stale is absent', () => {
    const { data_source_stale, ...withoutStale } = mockReport as Report & { data_source_stale?: boolean }
    renderCard(withoutStale as Report)

    expect(screen.queryByLabelText('Data may be stale — Google Sheet couldn\'t refresh at generation time')).not.toBeInTheDocument()
  })

  it('renders the Excel-warning icon when excel_warning is a non-empty string', () => {
    const warning = 'This file has 3 sheets — only Sheet1 was used.'
    renderCard({ ...mockReport, excel_warning: warning })

    expect(screen.getByLabelText(warning)).toBeInTheDocument()
  })

  it('does NOT render the Excel-warning icon when excel_warning is null', () => {
    renderCard({ ...mockReport, excel_warning: null })

    expect(screen.queryByTitle('This file has')).not.toBeInTheDocument()
  })

  it('does NOT render the Excel-warning icon when excel_warning is absent', () => {
    const { excel_warning, ...withoutWarning } = mockReport as Report & { excel_warning?: string | null }
    renderCard(withoutWarning as Report)

    expect(screen.queryByLabelText(/This file has/)).not.toBeInTheDocument()
  })
})
