import { describe, it, expect } from 'vitest'
import { parseFormattedNumber, reapplyFormat } from '../useCountUp'

function roundTrip(input: string): string {
  const parsed = parseFormattedNumber(input)
  if (!parsed) return `PARSE_FAILED: ${input}`
  const result = reapplyFormat(parsed, parsed.numericValue)
  if (result !== input) {
    return `MISMATCH: parsed=${JSON.stringify(parsed)} input=${input} result=${result}`
  }
  return result
}

describe('parseFormattedNumber / reapplyFormat', () => {
  it('$4,392', () => {
    const p = parseFormattedNumber('$4,392')
    expect(p).not.toBeNull()
    expect(p!.prefix).toBe('$')
    expect(p!.numericValue).toBe(4392)
    expect(p!.decimalPlaces).toBe(0)
    expect(reapplyFormat(p!, 0)).toBe('$0')
    expect(reapplyFormat(p!, 2196)).toBe('$2,196')
    expect(reapplyFormat(p!, 4392)).toBe('$4,392')
    expect(roundTrip('$4,392')).toBe('$4,392')
  })

  it('85.3%', () => {
    const p = parseFormattedNumber('85.3%')
    expect(p).not.toBeNull()
    expect(p!.prefix).toBe('')
    expect(p!.numericValue).toBe(85.3)
    expect(p!.decimalPlaces).toBe(1)
    expect(p!.percentSuffix).toBe('%')
    expect(reapplyFormat(p!, 0)).toBe('0.0%')
    expect(reapplyFormat(p!, 42.6)).toBe('42.6%')
    expect(reapplyFormat(p!, 85.3)).toBe('85.3%')
    expect(roundTrip('85.3%')).toBe('85.3%')
  })

  it('1,250', () => {
    const p = parseFormattedNumber('1,250')
    expect(p).not.toBeNull()
    expect(p!.numericValue).toBe(1250)
    expect(p!.originalHasCommas).toBe(true)
    expect(reapplyFormat(p!, 1250)).toBe('1,250')
    expect(roundTrip('1,250')).toBe('1,250')
  })

  it('-3.2% (sign prefix)', () => {
    const p = parseFormattedNumber('-3.2%')
    expect(p).not.toBeNull()
    expect(p!.prefix).toBe('-')
    expect(p!.numericValue).toBe(3.2)
    expect(p!.decimalPlaces).toBe(1)
    expect(p!.percentSuffix).toBe('%')
    expect(reapplyFormat(p!, 3.2)).toBe('-3.2%')
    expect(roundTrip('-3.2%')).toBe('-3.2%')
  })

  it('+12.5% (positive sign prefix)', () => {
    const p = parseFormattedNumber('+12.5%')
    expect(p).not.toBeNull()
    expect(p!.prefix).toBe('+')
    expect(p!.numericValue).toBe(12.5)
    expect(reapplyFormat(p!, 12.5)).toBe('+12.5%')
    expect(roundTrip('+12.5%')).toBe('+12.5%')
  })

  it('-3.2% halves correctly', () => {
    const p = parseFormattedNumber('-3.2%')
    expect(p).not.toBeNull()
    expect(reapplyFormat(p!, 1.6)).toBe('-1.6%')
    expect(reapplyFormat(p!, 0)).toBe('0.0%')
  })

  it('Revenue reached $45,200 in March (sentence with embedded number)', () => {
    const p = parseFormattedNumber('Revenue reached $45,200 in March')
    expect(p).not.toBeNull()
    expect(p!.leadingText).toBe('Revenue reached ')
    expect(p!.prefix).toBe('$')
    expect(p!.numericValue).toBe(45200)
    expect(p!.trailingText).toBe(' in March')
    expect(reapplyFormat(p!, 45200)).toBe('Revenue reached $45,200 in March')
    expect(roundTrip('Revenue reached $45,200 in March')).toBe('Revenue reached $45,200 in March')
  })

  it('plain integer string', () => {
    expect(roundTrip('4392')).toBe('4392')
  })

  it('-€5,000.50 (complex case)', () => {
    const p = parseFormattedNumber('-€5,000.50')
    expect(p).not.toBeNull()
    expect(p!.prefix).toBe('-€')
    expect(p!.numericValue).toBe(5000.5)
    expect(p!.decimalPlaces).toBe(2)
    expect(reapplyFormat(p!, 5000.5)).toBe('-€5,000.50')
    expect(roundTrip('-€5,000.50')).toBe('-€5,000.50')
  })

  it('null/undefined returns null from parseFormattedNumber', () => {
    expect(parseFormattedNumber('')).toBeNull()
    expect(parseFormattedNumber('abc')).toBeNull()
  })
})
