import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'

vi.mock('@/hooks/useReducedMotion', () => ({
  useReducedMotion: () => false,
}))

import GeneratingLoader from '../GeneratingLoader'

function renderLoader(overrides: Record<string, unknown> = {}) {
  return render(
    <GeneratingLoader
      currentStep="parsing"
      progress={50}
      isPolling={true}
      timeoutMessage={null}
      {...overrides}
    />,
  )
}

describe('GeneratingLoader', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders generating heading during polling', () => {
    renderLoader()
    expect(screen.getByText('Generating your report')).toBeInTheDocument()
  })

  it('renders all 4 step labels', () => {
    renderLoader()
    expect(screen.getByText('Parsing your data...')).toBeInTheDocument()
    expect(screen.getByText('Generating charts...')).toBeInTheDocument()
    expect(screen.getByText('Writing AI insights...')).toBeInTheDocument()
    expect(screen.getByText('Building your PDF...')).toBeInTheDocument()
  })

  it('renders 30-90 seconds text', () => {
    renderLoader()
    expect(screen.getByText('This usually takes 30\u201390 seconds')).toBeInTheDocument()
  })

  it('shows elapsed timer with seconds', () => {
    renderLoader()
    act(() => { vi.advanceTimersByTime(5000) })
    expect(screen.getByText('5s elapsed')).toBeInTheDocument()
  })

  it('shows timeout message when prop provided', () => {
    renderLoader({ timeoutMessage: 'Generation is taking longer than expected.' })
    expect(
      screen.getByText('Generation is taking longer than expected.'),
    ).toBeInTheDocument()
  })

  it('completed steps show green border indicator', () => {
    const { container } = renderLoader({ currentStep: 'pdf' })
    const completedCircles = container.querySelectorAll('.border-green-500')
    expect(completedCircles.length).toBe(3)
  })

  it('not polling renders gray bars at min height', () => {
    const { container } = renderLoader({ isPolling: false })
    const bars = container.querySelectorAll('.w-4.rounded-full')
    expect(bars.length).toBe(6)
    bars.forEach((bar) => {
      expect(bar.className).toContain('bg-gray-300')
    })
  })
})
