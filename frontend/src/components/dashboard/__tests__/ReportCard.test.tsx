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
