import { format, isValid } from 'date-fns'

/**
 * Safely format a date string using date-fns format().
 * Returns the formatted string if the input is valid, or empty string otherwise.
 * Prevents RangeError crashes from unparseable date values.
 */
export function formatBillingDate(dateStr: string | null | undefined): string {
  if (!dateStr) return ''
  const parsed = new Date(dateStr)
  if (!isValid(parsed)) return ''
  return format(parsed, 'MMMM d, yyyy')
}
