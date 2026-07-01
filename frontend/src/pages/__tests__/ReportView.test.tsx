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

vi.mock('@/store/reportStore', () => ({
  useReportStore: (selector: (s: any) => any) => {
    const state = { deleteReport: vi.fn().mockResolvedValue(undefined) }
    return selector ? selector(state) : state
  },
}))

const mockGetFn = vi.hoisted(() => vi.fn())
vi.mock('@/lib/axios', () => ({
  default: { get: mockGetFn },
}))

vi.mock('react-hot-toast')

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

describe('ReportView PDF download', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

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
