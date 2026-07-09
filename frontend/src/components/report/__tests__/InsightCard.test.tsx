import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { AIInsight } from '@/types/report'

vi.mock('@/hooks/useReducedMotion', () => ({
  useReducedMotion: () => false,
}))

vi.mock('@/hooks/useCountUp', () => ({
  useCountUp: (targetValue: string | number | null | undefined) =>
    targetValue != null ? String(targetValue) : '—',
}))

import InsightCard from '../InsightCard'

const baseInsight: AIInsight = {
  kpi: 'Revenue Growth',
  number: '42.5',
  reason: 'Q4 performance exceeded expectations',
  action: 'Continue current strategy',
  sentiment: 'positive',
  priority: 'high',
}

function renderCard(overrides: Partial<AIInsight> = {}) {
  return render(<InsightCard insight={{ ...baseInsight, ...overrides }} />)
}

describe('InsightCard', () => {
  it('renders KPI, number, reason, action', () => {
    renderCard()
    expect(screen.getByText(/Revenue Growth/)).toBeInTheDocument()
    expect(screen.getByText('# 42.5')).toBeInTheDocument()
    expect(
      screen.getByText('▶ Q4 performance exceeded expectations'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('✓ Continue current strategy'),
    ).toBeInTheDocument()
  })

  it('renders error badge variant for high priority', () => {
    renderCard({ priority: 'high' })
    const badge = screen.getByText('HIGH')
    expect(badge.className).toContain('bg-red-50')
  })

  it('renders warning badge variant for medium priority', () => {
    renderCard({ priority: 'medium' })
    const badge = screen.getByText('MEDIUM')
    expect(badge.className).toContain('bg-yellow-50')
  })

  it('renders neutral badge variant for low priority', () => {
    renderCard({ priority: 'low' })
    const badge = screen.getByText('LOW')
    expect(badge.className).toContain('bg-gray-50')
  })

  it('renders green border for positive sentiment', () => {
    const { container } = renderCard({ sentiment: 'positive' })
    expect(container.firstChild).toHaveClass('border-l-green-500')
  })

  it('renders red border for negative sentiment', () => {
    const { container } = renderCard({ sentiment: 'negative' })
    expect(container.firstChild).toHaveClass('border-l-red-500')
  })

  it('renders gray border for neutral sentiment', () => {
    const { container } = renderCard({ sentiment: 'neutral' })
    expect(container.firstChild).toHaveClass('border-l-gray-400')
  })
})
