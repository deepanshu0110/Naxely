import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, render, waitFor } from '@testing-library/react'
import { useInView } from '../useInView'

type ObserverCallback = (entries: IntersectionObserverEntry[]) => void

let observerCallback: ObserverCallback | null = null
let disconnect: ReturnType<typeof vi.fn>

class MockIntersectionObserver {
  observe = vi.fn()
  disconnect: ReturnType<typeof vi.fn>
  unobserve = vi.fn()

  constructor(callback: ObserverCallback) {
    observerCallback = callback
    this.disconnect = vi.fn()
    disconnect = this.disconnect
  }
}

const OriginalIO = globalThis.IntersectionObserver

beforeEach(() => {
  observerCallback = null
  disconnect = vi.fn()
  globalThis.IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver
})

afterEach(() => {
  globalThis.IntersectionObserver = OriginalIO
})

function triggerIntersection() {
  observerCallback?.([{ isIntersecting: true } as IntersectionObserverEntry])
}

function TestComponent() {
  const { ref, inView } = useInView()
  return <div ref={ref} data-testid="target" data-inview={String(inView)} />
}

describe('useInView', () => {
  it('sets inView to true when observer triggers intersection', async () => {
    const { getByTestId } = render(<TestComponent />)

    expect(getByTestId('target').getAttribute('data-inview')).toBe('false')

    act(() => {
      triggerIntersection()
    })

    await waitFor(() => {
      expect(getByTestId('target').getAttribute('data-inview')).toBe('true')
    })
  })

  it('disconnects observer after first intersection', async () => {
    render(<TestComponent />)

    act(() => {
      triggerIntersection()
    })

    await waitFor(() => {
      expect(disconnect).toHaveBeenCalledOnce()
    })
  })
})