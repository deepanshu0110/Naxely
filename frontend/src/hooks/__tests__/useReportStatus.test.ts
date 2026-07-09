import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { useReportStatus } from '../useReportStatus'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock('react-hot-toast', () => ({ default: { error: vi.fn() } }))

const mockPollStatus = vi.fn()

vi.mock('@/store/reportStore', () => ({
  useReportStore: (selector: any) => selector({ pollStatus: mockPollStatus }),
}))

async function getToastError() {
  const toast = await import('react-hot-toast')
  return toast.default.error as ReturnType<typeof vi.fn>
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useReportStatus', () => {
  it('sets isPolling to true when startPolling is called', () => {
    vi.useFakeTimers()
    const { result } = renderHook(useReportStatus)

    act(() => {
      result.current.startPolling('report-1')
    })

    expect(result.current.isPolling).toBe(true)
  })

  it('stops polling and navigates to /report/{id} on completed status', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockPollStatus.mockResolvedValue({ status: 'completed', progress_percent: 100 })

    const { result } = renderHook(useReportStatus)

    act(() => {
      result.current.startPolling('report-1')
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false)
    })
    expect(mockNavigate).toHaveBeenCalledWith('/report/report-1')
  })

  it('stops polling, navigates to /dashboard, and calls toast.error on failed status', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockPollStatus.mockResolvedValue({
      status: 'failed',
      progress_percent: 50,
      error_message: 'Something went wrong',
    })

    const { result } = renderHook(useReportStatus)

    act(() => {
      result.current.startPolling('report-1')
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false)
    })
    expect((await getToastError())).toHaveBeenCalledWith('Something went wrong')
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('stops polling, navigates to /dashboard, and shows toast on API error', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockPollStatus.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(useReportStatus)

    act(() => {
      result.current.startPolling('report-1')
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false)
    })
    expect((await getToastError())).toHaveBeenCalledWith('Failed to check report status')
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('sets timeoutMessage after 30 polls without a terminal status', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockPollStatus.mockResolvedValue({ status: 'processing', progress_percent: 30 })

    const { result } = renderHook(useReportStatus)

    act(() => {
      result.current.startPolling('report-1')
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000 * 30 + 100)
    })

    await waitFor(() => {
      expect(result.current.timeoutMessage).toBe(
        'Report is taking longer than expected. Check back in a few minutes.',
      )
    })
    expect(result.current.isPolling).toBe(false)
  })

  it('stops polling if cancelledRef.current is true mid-poll', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    mockPollStatus.mockResolvedValue({ status: 'processing', progress_percent: 10 })

    const { result } = renderHook(useReportStatus)

    act(() => {
      result.current.startPolling('report-1')
    })

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    expect(mockPollStatus).toHaveBeenCalledTimes(1)
    await waitFor(() => {
      expect(result.current.isPolling).toBe(true)
    })
  })
})