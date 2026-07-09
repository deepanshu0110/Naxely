import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useReportStore } from '@/store/reportStore'

const { mockGet, mockPost, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
}))

vi.mock('@/lib/axios', () => ({
  default: {
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
  },
}))

function mockReportsList() {
  return {
    reports: [
      { id: 'r1', title: 'Report One', status: 'completed', row_count: 100, pdf_url: '/r1.pdf', share_token: null, share_view_count: 0, created_at: '2026-01-01T00:00:00Z', template_type: 'marketing', ai_summary: null, ai_insights: null, ai_anomalies: null },
      { id: 'r2', title: 'Report Two', status: 'completed', row_count: 200, pdf_url: '/r2.pdf', share_token: null, share_view_count: 0, created_at: '2026-01-02T00:00:00Z', template_type: 'marketing', ai_summary: null, ai_insights: null, ai_anomalies: null },
    ],
    total: 2,
    limit: 20,
    offset: 0,
  }
}

function resetStore() {
  useReportStore.setState({
    reports: [],
    total: 0,
    uploadedFile: null,
    generationStatus: null,
    isGenerating: false,
    isLoading: false,
    error: null,
  })
}

describe('reportStore — initial state', () => {
  beforeEach(() => resetStore())

  it('starts with empty reports, no upload, not generating', () => {
    const s = useReportStore.getState()
    expect(s.reports).toEqual([])
    expect(s.total).toBe(0)
    expect(s.uploadedFile).toBeNull()
    expect(s.generationStatus).toBeNull()
    expect(s.isGenerating).toBe(false)
    expect(s.isLoading).toBe(false)
    expect(s.error).toBeNull()
  })
})

describe('reportStore — fetchReports', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls GET /reports and sets reports + total', async () => {
    mockGet.mockResolvedValue({ data: mockReportsList() })

    await useReportStore.getState().fetchReports()

    expect(mockGet).toHaveBeenCalledWith('/reports', { params: { offset: 0, limit: 20 } })
    const s = useReportStore.getState()
    expect(s.reports).toHaveLength(2)
    expect(s.total).toBe(2)
    expect(s.isLoading).toBe(false)
    expect(s.error).toBeNull()
  })

  it('sets error on failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'))

    await useReportStore.getState().fetchReports()

    const s = useReportStore.getState()
    expect(s.error).toBe('Network error')
    expect(s.isLoading).toBe(false)
    expect(s.reports).toEqual([])
  })
})

describe('reportStore — uploadFile', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls POST /reports/upload with FormData and sets uploadedFile', async () => {
    const uploadResult = {
      upload_id: 'up-1',
      filename: 'test.csv',
      file_url: '/files/test.csv',
      row_count: 50,
      column_count: 5,
      columns: [],
      preview_rows: [],
    }
    mockPost.mockResolvedValue({ data: uploadResult })

    const file = new File(['a,b,c\n1,2,3'], 'test.csv', { type: 'text/csv' })
    const result = await useReportStore.getState().uploadFile(file)

    expect(mockPost).toHaveBeenCalled()
    const callArgs = mockPost.mock.calls[0]
    expect(callArgs[0]).toBe('/reports/upload')
    expect(callArgs[1]).toBeInstanceOf(FormData)
    expect(callArgs[2]?.headers?.['Content-Type']).toBe('multipart/form-data')

    expect(result).toEqual(uploadResult)
    expect(useReportStore.getState().uploadedFile).toEqual(uploadResult)
  })
})

describe('reportStore — generateReport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls POST /reports/generate and returns report_id', async () => {
    mockPost.mockResolvedValue({ data: { report_id: 'rep-1', status: 'processing', estimated_seconds: 30, poll_url: '/reports/rep-1/status' } })

    const config = {
      upload_id: 'up-1',
      title: 'My Report',
      template_type: 'marketing',
      tone: 'professional',
      sections: ['kpi_overview', 'charts'],
      column_config: [],
    }
    const reportId = await useReportStore.getState().generateReport(config)

    expect(mockPost).toHaveBeenCalledWith('/reports/generate', config)
    expect(reportId).toBe('rep-1')
    expect(useReportStore.getState().isGenerating).toBe(false)
  })

  it('sets error and throws on failure', async () => {
    mockPost.mockRejectedValue(new Error('Generation failed'))

    const config = {
      upload_id: 'up-1',
      title: 'X',
      template_type: 'marketing',
      tone: 'professional',
      sections: [],
      column_config: [],
    }

    await expect(useReportStore.getState().generateReport(config)).rejects.toThrow('Generation failed')
    const s = useReportStore.getState()
    expect(s.error).toBe('Generation failed')
    expect(s.isGenerating).toBe(false)
  })
})

describe('reportStore — pollStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
    useReportStore.setState({ isGenerating: true, reports: [], total: 1 })
  })

  it('calls GET /reports/:id/status and sets generationStatus', async () => {
    mockGet.mockResolvedValue({ data: { report_id: 'rep-1', status: 'processing', progress_percent: 50, current_step: 'charts', steps_completed: ['data'], steps_remaining: ['pdf'] } })

    const status = await useReportStore.getState().pollStatus('rep-1')

    expect(mockGet).toHaveBeenCalledWith('/reports/rep-1/status')
    expect(status.status).toBe('processing')
    expect(status.progress_percent).toBe(50)
    expect(useReportStore.getState().generationStatus?.status).toBe('processing')
  })

  it('sets isGenerating=false and refetches reports on completed', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { report_id: 'rep-1', status: 'completed', progress_percent: 100 } })
      .mockResolvedValueOnce({ data: mockReportsList() })

    await useReportStore.getState().pollStatus('rep-1')

    expect(useReportStore.getState().isGenerating).toBe(false)
    expect(mockGet).toHaveBeenCalledTimes(2)
    expect(mockGet.mock.calls[1][0]).toBe('/reports')
  })

  it('sets isGenerating=false without refetch on failed', async () => {
    mockGet.mockResolvedValue({ data: { report_id: 'rep-1', status: 'failed', progress_percent: 60, error_message: 'PDF build error' } })

    await useReportStore.getState().pollStatus('rep-1')

    expect(useReportStore.getState().isGenerating).toBe(false)
    expect(useReportStore.getState().generationStatus?.error_message).toBe('PDF build error')
    expect(mockGet).toHaveBeenCalledTimes(1)
  })
})

describe('reportStore — deleteReport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useReportStore.setState({
      reports: [
        { id: 'r1', title: 'A' } as any,
        { id: 'r2', title: 'B' } as any,
      ],
      total: 2,
    })
  })

  it('calls DELETE /reports/:id and removes report from list', async () => {
    mockDelete.mockResolvedValue({})

    await useReportStore.getState().deleteReport('r1')

    expect(mockDelete).toHaveBeenCalledWith('/reports/r1')
    const s = useReportStore.getState()
    expect(s.reports).toHaveLength(1)
    expect(s.reports[0].id).toBe('r2')
    expect(s.total).toBe(1)
  })
})

describe('reportStore — bulkDeleteReports', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useReportStore.setState({
      reports: [
        { id: 'r1', title: 'A' } as any,
        { id: 'r2', title: 'B' } as any,
        { id: 'r3', title: 'C' } as any,
      ],
      total: 3,
    })
  })

  it('calls POST /reports/bulk-delete and removes selected reports', async () => {
    mockPost.mockResolvedValue({})

    await useReportStore.getState().bulkDeleteReports(['r1', 'r3'])

    expect(mockPost).toHaveBeenCalledWith('/reports/bulk-delete', { report_ids: ['r1', 'r3'] })
    const s = useReportStore.getState()
    expect(s.reports).toHaveLength(1)
    expect(s.reports[0].id).toBe('r2')
    expect(s.total).toBe(1)
  })
})
