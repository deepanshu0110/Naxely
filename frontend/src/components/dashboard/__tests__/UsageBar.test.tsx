import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import UsageBar from '../UsageBar'

function renderUsageBar(reportsThisMonth: number, monthlyLimit: number | null) {
  return render(
    <MemoryRouter>
      <UsageBar reportsThisMonth={reportsThisMonth} monthlyLimit={monthlyLimit} />
    </MemoryRouter>,
  )
}

describe('UsageBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns nothing when monthlyLimit is null', () => {
    const { container } = renderUsageBar(0, null)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows correct usage text for free (2 of 3)', () => {
    renderUsageBar(2, 3)
    expect(screen.getByText('2 of 3 free reports used this month')).toBeInTheDocument()
  })

  it('at limit (3 of 3): shows "Upgrade for unlimited →" link to /pricing', () => {
    renderUsageBar(3, 3)
    expect(screen.getByText('3 of 3 free reports used this month')).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /upgrade for unlimited/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/pricing')
  })

  it('partial usage shows correct percentage', () => {
    renderUsageBar(1, 4)
    expect(screen.getByText('1 of 4 free reports used this month')).toBeInTheDocument()
  })

  it('0 reports used shows "0 of 3"', () => {
    renderUsageBar(0, 3)
    expect(screen.getByText('0 of 3 free reports used this month')).toBeInTheDocument()
  })
})