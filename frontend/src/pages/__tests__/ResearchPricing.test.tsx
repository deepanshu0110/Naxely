import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import fs from 'node:fs'
import path from 'node:path'

vi.mock('vite-react-ssg', () => ({
  Head: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="ssg-head">{children}</div>
  ),
}))

vi.mock('@/components/layout/Navbar', () => ({ default: () => <div>Navbar</div> }))
vi.mock('@/components/layout/Footer', () => ({ default: () => <div>Footer</div> }))

import ResearchPricing2026 from '../ResearchPricing2026'

const CSV_REL = 'public/research/client-reporting-tool-pricing-2026.csv'
const EXPECTED_HEADER =
  'vendor,product,plan,billing,price,currency,price_unit,included_units,extra_unit_price,free_plan,free_trial_days,white_label,pdf_export,source_url,captured_utc'

describe('ResearchPricing2026', () => {
  it('renders the H1', () => {
    render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    expect(
      screen.getByRole('heading', { level: 1 }),
    ).toHaveTextContent('What client reporting tools cost for 5, 12 and 25 clients')
  })

  it('renders both cost tables', () => {
    const { container } = render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    const tables = container.querySelectorAll('table')
    expect(tables.length).toBe(2)
    expect(tables[0].textContent).toContain('AgencyAnalytics')
    expect(tables[1].textContent).toContain('No monthly billing')
  })

  it('renders the disclosure line and the CSV download link', () => {
    render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    expect(screen.getByText(/I build Naxely, which competes with these tools/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /CSV of every plan and price/i })).toHaveAttribute(
      'href',
      '/research/client-reporting-tool-pricing-2026.csv',
    )
  })

  it('renders the author byline linking to /about', () => {
    render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'Deepanshu Garg' })).toHaveAttribute('href', '/about')
  })

  it('declares Article JSON-LD with October 2026 dates', () => {
    const { container } = render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    const head = container.querySelector('[data-testid="ssg-head"]')
    const scripts = head?.querySelectorAll('script[type="application/ld+json"]') ?? []
    const articles = [...scripts]
      .map((s) => JSON.parse(s.textContent ?? '{}') as Record<string, unknown>)
      .filter((p) => p['@type'] === 'Article')
    expect(articles.length).toBe(1)
    expect(articles[0]['datePublished']).toBe('2026-10-07')
    expect(articles[0]['dateModified']).toBe('2026-10-07')
  })
})

describe('research pricing CSV', () => {
  it('exists under public/ with the exact published header', () => {
    const abs = path.join(process.cwd(), CSV_REL)
    expect(fs.existsSync(abs)).toBe(true)
    const header = fs.readFileSync(abs, 'utf-8').split('\n')[0].trim()
    expect(header).toBe(EXPECTED_HEADER)
  })

  it('has data rows and no dropped columns', () => {
    const abs = path.join(process.cwd(), CSV_REL)
    const lines = fs.readFileSync(abs, 'utf-8').trim().split('\n')
    expect(lines.length).toBeGreaterThan(50)
    for (const line of lines.slice(1)) {
      expect(line).not.toContain('no separate pricing page')
    }
  })
})

describe('research page SEO', () => {
  it('declares the self-referencing canonical URL', () => {
    const { container } = render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    const head = container.querySelector('[data-testid="ssg-head"]')
    expect(head?.querySelector('link[rel="canonical"]')).toHaveAttribute(
      'href',
      'https://www.naxely.com/research/client-reporting-tool-pricing-2026',
    )
  })

  it('tables are real table elements with header cells', () => {
    const { container } = render(
      <MemoryRouter>
        <ResearchPricing2026 />
      </MemoryRouter>,
    )
    const tables = container.querySelectorAll('table')
    for (const table of tables) {
      expect(within(table as HTMLElement).getAllByRole('columnheader').length).toBeGreaterThan(0)
    }
  })
})
