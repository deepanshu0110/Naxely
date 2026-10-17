import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { readFileSync } from 'fs'
import { join } from 'path'

vi.mock('vite-react-ssg', () => ({
  Head: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="ssg-head">{children}</div>
  ),
}))
vi.mock('@/components/layout/Navbar', () => ({ default: () => <div>Navbar</div> }))

import BlogPostByok from '../BlogPostByok'
import BlogPostCsvToPdf from '../BlogPostCsvToPdf'
import BlogPostWhiteLabel from '../BlogPostWhiteLabel'
import BlogPostHub from '../BlogPostHub'
import BlogPostClientReporting from '../BlogPostClientReporting'
import BlogPostBestFreelanceReporting from '../BlogPostBestFreelanceReporting'
import BlogPostPythonCsvToPdf from '../BlogPostPythonCsvToPdf'
import BlogPostTwoWeeks from '../BlogPostTwoWeeks'
import BlogPostClientReportChecklist from '../BlogPostClientReportChecklist'
import BlogPostAnomalyDetection from '../BlogPostAnomalyDetection'
import BlogPostGoogleSheets from '../BlogPostGoogleSheets'
import BlogPostExcelToPdf from '../BlogPostExcelToPdf'

function renderWithRouter(Component: React.ComponentType) {
  return render(
    <MemoryRouter>
      <Component />
    </MemoryRouter>,
  )
}

function blogPostingScript(component: React.ComponentType): string | null {
  const { container } = renderWithRouter(component)
  const head = container.querySelector('[data-testid="ssg-head"]')
  const scripts = head?.querySelectorAll('script[type="application/ld+json"]') ?? []
  for (const script of scripts) {
    try {
      const parsed = JSON.parse(script.textContent ?? '{}') as Record<string, unknown>
      if (parsed['@type'] === 'BlogPosting') {
        return script.textContent ?? ''
      }
    } catch {
      // not JSON, keep looking
    }
  }
  return null
}

const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/

const POSTS: Array<{
  Component: React.ComponentType
  path: string
  dateModified: string
}> = [
  { Component: BlogPostByok, path: '/blog/byok-ai-reporting-tool', dateModified: '2026-10-17' },
  { Component: BlogPostCsvToPdf, path: '/blog/csv-to-pdf-report-generator', dateModified: '2026-10-17' },
  { Component: BlogPostWhiteLabel, path: '/blog/white-label-client-reporting-agencies', dateModified: '2026-10-17' },
  { Component: BlogPostHub, path: '/blog/automating-client-reports', dateModified: '2026-09-25' },
  { Component: BlogPostClientReporting, path: '/blog/client-reporting-software-guide', dateModified: '2026-10-17' },
  { Component: BlogPostBestFreelanceReporting, path: '/blog/best-client-reporting-software-freelancers', dateModified: '2026-10-17' },
  { Component: BlogPostPythonCsvToPdf, path: '/blog/python-csv-to-pdf-reports', dateModified: '2026-10-17' },
  { Component: BlogPostTwoWeeks, path: '/blog/two-weeks-building-naxely', dateModified: '2026-10-17' },
  { Component: BlogPostClientReportChecklist, path: '/blog/what-should-client-report-include-checklist', dateModified: '2026-08-02' },
  { Component: BlogPostAnomalyDetection, path: '/blog/anomaly-detection-in-client-reports', dateModified: '2026-10-17' },
  { Component: BlogPostGoogleSheets, path: '/blog/google-sheets-client-reports', dateModified: '2026-10-17' },
  { Component: BlogPostExcelToPdf, path: '/blog/excel-to-pdf-report-generator', dateModified: '2026-10-17' },
]

describe.each(POSTS)('freshness: $path', ({ Component, path, dateModified }) => {
  it('declares dateModified in BlogPosting JSON-LD', () => {
    const text = blogPostingScript(Component)
    expect(text).not.toBeNull()
    expect(text).toContain(`"dateModified":"${dateModified}T00:00:00Z"`)
  })

  it('keeps datePublished unchanged', () => {
    const text = blogPostingScript(Component)
    expect(text).not.toBeNull()
    expect(text).toMatch(/"datePublished":"\d{4}-\d{2}-\d{2}T00:00:00Z"/)
  })

  it('dateModified is valid ISO 8601 UTC', () => {
    const text = blogPostingScript(Component)
    const match = text?.match(/"dateModified":"([^"]+)"/)
    expect(match?.[1]).toMatch(ISO)
  })

  it('canonical URL is the slash-free path', () => {
    const { container } = renderWithRouter(Component)
    const head = container.querySelector('[data-testid="ssg-head"]')
    expect(head?.querySelector('link[rel="canonical"]')).toHaveAttribute('href', `https://www.naxely.com${path}`)
  })
})

describe('sitemap lastmod matches each post dateModified', () => {
  const sitemap = readFileSync(join(import.meta.dirname, '../../../public/sitemap.xml'), 'utf8')
  const entries = new Map<string, string>()
  for (const m of sitemap.matchAll(/<loc>(https:\/\/www\.naxely\.com[^<]+)<\/loc>\s*<lastmod>([^<]+)<\/lastmod>/g)) {
    entries.set(m[1], m[2])
  }

  it('contains every post URL', () => {
    for (const { path } of POSTS) {
      expect(entries.has(`https://www.naxely.com${path}`)).toBe(true)
    }
  })

  it.each(POSTS)('$path lastmod equals dateModified', ({ path, dateModified }) => {
    expect(entries.get(`https://www.naxely.com${path}`)).toBe(dateModified)
  })
})
