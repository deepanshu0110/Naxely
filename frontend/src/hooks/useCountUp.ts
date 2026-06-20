import { useEffect, useRef, useState } from 'react'

export interface ParsedNumber {
  leadingText: string
  prefix: string
  numericValue: number
  percentSuffix: string
  trailingText: string
  decimalPlaces: number
  originalHasCommas: boolean
}

const NUMBER_REGEX = /^(.*?)([€£$¥+-]*)([\d,]+(?:\.\d+)?)(%?)(.*)$/

export function parseFormattedNumber(value: string): ParsedNumber | null {
  const match = value.match(NUMBER_REGEX)
  if (!match) return null

  const [, leadingText, prefix, numStr, percentSuffix, trailingText] = match
  const cleanNumStr = numStr.replace(/,/g, '')
  const numericValue = parseFloat(cleanNumStr)

  if (isNaN(numericValue)) return null

  const decimalMatch = numStr.match(/\.(\d+)$/)
  const decimalPlaces = decimalMatch ? decimalMatch[1].length : 0

  return {
    leadingText,
    prefix,
    numericValue: Math.abs(numericValue),
    percentSuffix,
    trailingText,
    decimalPlaces,
    originalHasCommas: value.includes(','),
  }
}

export function reapplyFormat(parsed: ParsedNumber, currentValue: number): string {
  let prefix = parsed.prefix
  if (currentValue === 0 && /[+-]/.test(prefix)) {
    prefix = prefix.replace(/[+-]/g, '')
  }

  let formatted: string
  if (parsed.originalHasCommas) {
    formatted = currentValue.toLocaleString('en-US', {
      minimumFractionDigits: parsed.decimalPlaces,
      maximumFractionDigits: parsed.decimalPlaces,
    })
  } else if (parsed.decimalPlaces > 0) {
    formatted = currentValue.toFixed(parsed.decimalPlaces)
  } else {
    formatted = String(currentValue)
  }
  return `${parsed.leadingText}${prefix}${formatted}${parsed.percentSuffix}${parsed.trailingText}`
}

export function useCountUp(
  targetValue: string | number | null | undefined,
  duration: number = 700,
  reducedMotion: boolean = false,
): string {
  const [display, setDisplay] = useState<string>('')

  const rafRef = useRef<number>(0)
  const lastValueRef = useRef<string | number | null | undefined>(undefined)

  useEffect(() => {
    if (targetValue == null) {
      setDisplay('—')
      lastValueRef.current = targetValue
      return
    }

    if (reducedMotion) {
      if (typeof targetValue === 'number') {
        setDisplay(targetValue.toLocaleString('en-US'))
      } else {
        setDisplay(targetValue)
      }
      lastValueRef.current = targetValue
      return
    }

    if (targetValue === lastValueRef.current) return

    lastValueRef.current = targetValue

    if (typeof targetValue === 'number') {
      const target = targetValue
      let startTime = 0

      setDisplay('0')

      const animate = (now: number) => {
        if (!startTime) startTime = now
        const elapsed = now - startTime
        const t = Math.min(elapsed / duration, 1)
        const eased = t * (2 - t)
        const current = eased * target
        setDisplay(current.toLocaleString('en-US'))
        if (t < 1) {
          rafRef.current = requestAnimationFrame(animate)
        }
      }
      rafRef.current = requestAnimationFrame(animate)
      return () => cancelAnimationFrame(rafRef.current)
    }

    const parsed = parseFormattedNumber(targetValue)
    if (!parsed) {
      setDisplay(targetValue)
      return
    }

    const target = parsed.numericValue
    let startTime = 0
    setDisplay(reapplyFormat(parsed, 0))

    const animate = (now: number) => {
      if (!startTime) startTime = now
      const elapsed = now - startTime
      const t = Math.min(elapsed / duration, 1)
      const eased = t * (2 - t)
      const current = eased * target
      setDisplay(reapplyFormat(parsed, current))
      if (t < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }
    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [targetValue, duration, reducedMotion])

  return display
}
