import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('@/lib/chunkReload', () => ({
  isChunkLoadError: vi.fn(),
  reloadOnce: vi.fn(),
}))

import SentryFallback from '@/components/ErrorFallback'
import { isChunkLoadError, reloadOnce } from '@/lib/chunkReload'

const mockIsChunk = vi.mocked(isChunkLoadError)
const mockReload = vi.mocked(reloadOnce)

describe('SentryFallback chunk recovery', () => {
  beforeEach(() => {
    mockIsChunk.mockReset()
    mockReload.mockReset()
  })

  it('calls reloadOnce for a chunk-load error', () => {
    mockIsChunk.mockReturnValue(true)
    mockReload.mockReturnValue(true)
    render(<SentryFallback error={new Error('Failed to fetch dynamically imported module')} />)
    expect(mockReload).toHaveBeenCalledTimes(1)
  })

  it('shows the Refresh page button when reloadOnce returns false', () => {
    mockIsChunk.mockReturnValue(true)
    mockReload.mockReturnValue(false)
    render(<SentryFallback error={new Error('Failed to fetch dynamically imported module')} />)
    expect(screen.getByRole('button', { name: /refresh page/i })).toBeInTheDocument()
  })

  it('does not call reloadOnce for a non-chunk error', () => {
    mockIsChunk.mockReturnValue(false)
    render(<SentryFallback error={new Error('boom')} />)
    expect(mockReload).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /refresh page/i })).toBeInTheDocument()
  })
})
