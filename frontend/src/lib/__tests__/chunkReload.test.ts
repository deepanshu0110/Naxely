import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const reloadMock = vi.fn()

// Fresh module per test: reloadOnce keeps an in-memory cooldown stamp that
// must not leak between cases.
async function loadFresh() {
  vi.resetModules()
  return import('@/lib/chunkReload')
}

describe('isChunkLoadError', () => {
  it('matches the Chrome message', async () => {
    const { isChunkLoadError } = await loadFresh()
    expect(
      isChunkLoadError(
        new TypeError('Failed to fetch dynamically imported module: https://x/assets/Landing-abc.js'),
      ),
    ).toBe(true)
  })

  it('matches the Firefox message', async () => {
    const { isChunkLoadError } = await loadFresh()
    expect(isChunkLoadError(new Error('error loading dynamically imported module: foo'))).toBe(true)
  })

  it('matches the Safari message', async () => {
    const { isChunkLoadError } = await loadFresh()
    expect(isChunkLoadError(new Error('Importing a module script failed.'))).toBe(true)
  })

  it('rejects an unrelated error', async () => {
    const { isChunkLoadError } = await loadFresh()
    expect(isChunkLoadError(new Error('Network request failed'))).toBe(false)
    expect(isChunkLoadError(null)).toBe(false)
    expect(isChunkLoadError(undefined)).toBe(false)
  })
})

describe('reloadOnce', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true,
      configurable: true,
    })
    reloadMock.mockClear()
    vi.useFakeTimers()
    vi.setSystemTime(1_000_000)
    window.sessionStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('reloads on the first call', async () => {
    const { reloadOnce } = await loadFresh()
    expect(reloadOnce()).toBe(true)
    expect(reloadMock).toHaveBeenCalledTimes(1)
  })

  it('skips a second call within 10 seconds', async () => {
    const { reloadOnce } = await loadFresh()
    expect(reloadOnce()).toBe(true)
    vi.setSystemTime(1_000_000 + 5_000)
    expect(reloadOnce()).toBe(false)
    expect(reloadMock).toHaveBeenCalledTimes(1)
  })

  it('reloads again after the cooldown passes', async () => {
    const { reloadOnce } = await loadFresh()
    expect(reloadOnce()).toBe(true)
    vi.setSystemTime(1_000_000 + 11_000)
    expect(reloadOnce()).toBe(true)
    expect(reloadMock).toHaveBeenCalledTimes(2)
  })

  it('still reloads when sessionStorage throws', async () => {
    const { reloadOnce } = await loadFresh()
    vi.spyOn(window.sessionStorage.__proto__, 'getItem').mockImplementation(() => {
      throw new Error('denied')
    })
    expect(reloadOnce()).toBe(true)
    expect(reloadMock).toHaveBeenCalledTimes(1)
  })
})
