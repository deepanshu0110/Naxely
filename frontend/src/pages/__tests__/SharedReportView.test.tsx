import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SharedReportView from '../SharedReportView'

vi.mock('@/lib/axios', () => ({
  default: {
    get: vi.fn(),
  },
}))

import api from '@/lib/axios'

function renderPage(token = 'test-token') {
  return render(
    <MemoryRouter initialEntries={[`/share/${token}`]}>
      <Routes>
        <Route path="/share/:token" element={<SharedReportView />} />
      </Routes>
    </MemoryRouter>,
  )
}

const mockReportData = {
  id: 'rep-001',
  title: 'Q2 Performance Report',
  status: 'completed',
  template_type: 'marketing',
  ai_summary: null,
  ai_insights: [],
  ai_anomalies: [],
  pdf_url: 'https://supabase.co/reports/report.pdf',
  created_at: '2026-06-15T12:00:00Z',
}

describe('SharedReportView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading skeleton while fetching', () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockReturnValue(new Promise<never>(() => {}))

    renderPage()

    expect(screen.getByTestId('shared-report-skeleton')).toBeInTheDocument()
  })

  it('renders report metadata and iframe on success', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockResolvedValue({ data: mockReportData })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Q2 Performance Report')).toBeInTheDocument()
    })

    const iframe = screen.getByTitle('Report PDF')
    expect(iframe).toBeInTheDocument()
    expect(iframe).toHaveAttribute('src', 'https://supabase.co/reports/report.pdf')

    expect(screen.getByText('Jun 15, 2026')).toBeInTheDocument()
  })

  it('shows expiry message on 410 and hides iframe', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockRejectedValue({ response: { status: 410 }, message: 'Gone' })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('This link has expired or has been revoked.')).toBeInTheDocument()
    })

    expect(screen.queryByTitle('Report PDF')).not.toBeInTheDocument()
  })

  it('shows not-found/expired message on 404', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockRejectedValue({ response: { status: 404 }, message: 'Not Found' })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('This link has expired or is invalid.')).toBeInTheDocument()
    })
  })

  it('shows retry button on generic/network error', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockRejectedValue({ message: 'Network Error', response: { status: 500 } })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Something went wrong. Please try again.')).toBeInTheDocument()
    })

    expect(screen.getByText('Try again')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('hides footer when is_white_label is true', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockResolvedValue({ data: { ...mockReportData, is_white_label: true } })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Q2 Performance Report')).toBeInTheDocument()
    })

    expect(screen.queryByTestId('powered-by-footer')).not.toBeInTheDocument()
  })

  it('shows footer when is_white_label is undefined (API gap)', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockResolvedValue({ data: { ...mockReportData } })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Q2 Performance Report')).toBeInTheDocument()
    })

    expect(screen.getByTestId('powered-by-footer')).toBeInTheDocument()
    expect(screen.getByText('Powered by Naxely')).toBeInTheDocument()
  })

  it('shows footer when is_white_label is false', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockResolvedValue({ data: { ...mockReportData, is_white_label: false } })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Q2 Performance Report')).toBeInTheDocument()
    })

    expect(screen.getByTestId('powered-by-footer')).toBeInTheDocument()
    expect(screen.getByText('Powered by Naxely')).toBeInTheDocument()
  })

  it('has dark mode classes on key elements', async () => {
    const mockGet = vi.mocked(api.get)
    mockGet.mockResolvedValue({ data: { ...mockReportData, is_white_label: false } })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Q2 Performance Report')).toBeInTheDocument()
    })

    const container = screen.getByTestId('shared-report-container')
    expect(container.className).toContain('dark:bg-darkBg')

    const header = screen.getByTestId('shared-report-header')
    expect(header.className).toContain('dark:border-gray-700')

    const title = screen.getByTestId('report-title')
    expect(title.className).toContain('dark:text-gray-100')

    const footer = screen.getByTestId('powered-by-footer')
    expect(footer.className).toContain('dark:border-gray-700')
    expect(footer.className).toContain('dark:text-gray-500')
  })
})
