import { describe, it, expect } from 'vitest'
import AgencyAnalytics from '../ComparisonAgencyAnalytics.tsx?raw'
import Bonsai from '../ComparisonBonsai.tsx?raw'
import DashThis from '../ComparisonDashThis.tsx?raw'
import Databox from '../ComparisonDatabox.tsx?raw'
import Klipfolio from '../ComparisonKlipfolio.tsx?raw'
import Plutio from '../ComparisonPlutio.tsx?raw'
import Powerdrill from '../ComparisonPowerdrill.tsx?raw'
import Whatagraph from '../ComparisonWhatagraph.tsx?raw'
import Research from '../ResearchPricing2026.tsx?raw'
import DataboxPage from '../ComparisonDatabox.tsx?raw'
import AnomalyPost from '../BlogPostAnomalyDetection.tsx?raw'
import HubPost from '../BlogPostHub.tsx?raw'
import ByokPost from '../BlogPostByok.tsx?raw'
import CsvPost from '../BlogPostCsvToPdf.tsx?raw'
import ExcelPost from '../BlogPostExcelToPdf.tsx?raw'
import SheetsPost from '../BlogPostGoogleSheets.tsx?raw'
import PythonPost from '../BlogPostPythonCsvToPdf.tsx?raw'
import TwoWeeksPost from '../BlogPostTwoWeeks.tsx?raw'
import WhiteLabelPost from '../BlogPostWhiteLabel.tsx?raw'

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

  it('no current $812/€699 figure next to Whatagraph (history sentence exempt)', () => {
    const HISTORICAL = 'Earlier captures showed from $812 (€699).'
    expect(Research.includes(HISTORICAL)).toBe(true)
    for (const src of [Whatagraph, Research]) {
      const stripped = src.split(HISTORICAL).join('')
      const bad = stripped
        .split('\n')
        .filter((line) => /812|€699|u20AC699/.test(line) && /whatagraph/i.test(line))
      expect(bad).toEqual([])
    }
  })
})

describe('breadcrumb schema', () => {
  function breadcrumbOf(src: string): Record<string, unknown> {
    const blocks = [...src.matchAll(/\{JSON\.stringify\((\{.*?\})\)\}<\/script>/gs)]
      .map((m) => m[1])
      .filter((s) => s.includes('BreadcrumbList'))
    expect(blocks.length).toBe(1)
    return JSON.parse(blocks[0]) as Record<string, unknown>
  }

  it('BreadcrumbList is present and valid on every compare page', () => {
    for (const src of PAGES) {
      const bc = breadcrumbOf(src)
      const items = bc['itemListElement'] as Array<Record<string, string>>
      expect(items[0]).toMatchObject({ name: 'Home', item: 'https://www.naxely.com/' })
      expect(items[items.length - 1]['item']).toMatch(/^https:\/\/www\.naxely\.com\//)
    }
  })

  it('BreadcrumbList is present and valid on the 9 posts', () => {
    const posts = [AnomalyPost, HubPost, ByokPost, CsvPost, ExcelPost, SheetsPost, PythonPost, TwoWeeksPost, WhiteLabelPost]
    for (const src of [DataboxPage, ...posts]) {
      const bc = breadcrumbOf(src)
      const items = bc['itemListElement'] as Array<Record<string, string>>
      expect(items[0]).toMatchObject({ name: 'Home', item: 'https://www.naxely.com/' })
    }
  })

  it('compare crumbs exclude the /compare index (it 404s)', () => {
    for (const src of PAGES) {
      const bc = breadcrumbOf(src)
      expect(JSON.stringify(bc)).not.toContain('naxely.com/compare"')
    }
  })
})
