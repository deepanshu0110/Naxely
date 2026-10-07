import { describe, it, expect } from 'vitest'
import AgencyAnalytics from '../ComparisonAgencyAnalytics.tsx?raw'
import Bonsai from '../ComparisonBonsai.tsx?raw'
import DashThis from '../ComparisonDashThis.tsx?raw'
import Databox from '../ComparisonDatabox.tsx?raw'
import Klipfolio from '../ComparisonKlipfolio.tsx?raw'
import Plutio from '../ComparisonPlutio.tsx?raw'
import Powerdrill from '../ComparisonPowerdrill.tsx?raw'
import Whatagraph from '../ComparisonWhatagraph.tsx?raw'

const PAGES: string[] = [
  AgencyAnalytics,
  Bonsai,
  DashThis,
  Databox,
  Klipfolio,
  Plutio,
  Powerdrill,
  Whatagraph,
]

describe('compare pricing guards', () => {
  it('no Naxely-adjacent 30/mo cap (Pro is unlimited)', () => {
    const bad = PAGES.flatMap((src) =>
      src.split('\n').filter((line) => line.includes('Naxely') && line.includes('30/mo')),
    )
    expect(bad).toEqual([])
  })

  it('every compare page carries the price-checked date line', () => {
    const missing = PAGES.filter(
      (src) => !src.includes("Prices checked on the vendor's own pricing page on 7 October 2026."),
    ).length
    expect(missing).toBe(0)
  })
})
