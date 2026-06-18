import { describe, it, expect } from 'vitest'
import { formatBillingDate } from '../dates'

describe('formatBillingDate', () => {
  it('returns empty string for null', () => {
    expect(formatBillingDate(null)).toBe('')
  })

  it('returns empty string for undefined', () => {
    expect(formatBillingDate(undefined)).toBe('')
  })

  it('formats a valid ISO date', () => {
    expect(formatBillingDate('2026-07-18T08:58:32.441467Z')).toBe('July 18, 2026')
  })

  it('formats a valid date with timezone offset', () => {
    expect(formatBillingDate('2026-07-18T08:58:32.441467+00:00')).toBe('July 18, 2026')
  })

  it('formats a valid date with timezone offset and Z (malformed double-timezone)', () => {
    // The original bug: isoformat() + "Z" on an aware datetime produces "...+00:00Z"
    // which new Date() cannot parse. Should not crash.
    expect(formatBillingDate('2026-07-18T08:58:32.441467+00:00Z')).toBe('')
  })

  it('returns empty string for completely unparseable string', () => {
    expect(formatBillingDate('not-a-date')).toBe('')
  })

  it('returns empty string for empty string', () => {
    expect(formatBillingDate('')).toBe('')
  })
})
