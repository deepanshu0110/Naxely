import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('vite-react-ssg', () => ({
  Head: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="ssg-head">{children}</div>
  ),
}))

vi.mock('@/components/layout/Navbar', () => ({ default: () => <div>Navbar</div> }))

import NotFound from '../NotFound'
import Contact from '../Contact'
import Terms from '../Terms'
import Privacy from '../Privacy'
import Refund from '../Refund'
import CookiePolicy from '../CookiePolicy'
import Blog from '../Blog'
import BlogPostByok from '../BlogPostByok'
import BlogPostClientReporting from '../BlogPostClientReporting'
import BlogPostCsvToPdf from '../BlogPostCsvToPdf'
import BlogPostHub from '../BlogPostHub'
import BlogPostWhiteLabel from '../BlogPostWhiteLabel'
import BlogPostAnomalyDetection from '../BlogPostAnomalyDetection'
import BlogPostBestFreelanceReporting from '../BlogPostBestFreelanceReporting'
import BlogPostClientReportChecklist from '../BlogPostClientReportChecklist'
import BlogPostGoogleSheets from '../BlogPostGoogleSheets'
import BlogPostPythonCsvToPdf from '../BlogPostPythonCsvToPdf'
import BlogPostTwoWeeks from '../BlogPostTwoWeeks'
import ComparisonAgencyAnalytics from '../ComparisonAgencyAnalytics'
import ComparisonDatabox from '../ComparisonDatabox'
import ComparisonDashThis from '../ComparisonDashThis'
import ComparisonPowerdrill from '../ComparisonPowerdrill'
import ComparisonWhatagraph from '../ComparisonWhatagraph'

function renderWithRouter(Component: React.ComponentType) {
  return render(
    <MemoryRouter>
      <Component />
    </MemoryRouter>,
  )
}

describe('NotFound', () => {
  it('renders heading and back link', () => {
    renderWithRouter(NotFound)
    expect(screen.getByText('Page not found')).toBeInTheDocument()
    expect(screen.getByText('Go back to dashboard')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /go back/i })).toHaveAttribute('href', '/dashboard')
  })
})

describe('Contact', () => {
  it('renders heading and email link', () => {
    renderWithRouter(Contact)
    expect(screen.getByText('Contact Us')).toBeInTheDocument()
    expect(screen.getByText(/hello@naxely.com/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to home/i })).toHaveAttribute('href', '/')
  })
})

describe('Terms', () => {
  it('renders heading and usage section', () => {
    renderWithRouter(Terms)
    expect(screen.getByText('Terms of Service')).toBeInTheDocument()
    expect(screen.getByText(/By using Naxely, you agree/)).toBeInTheDocument()
    expect(screen.getByText('Usage')).toBeInTheDocument()
  })
})

describe('Privacy', () => {
  it('renders heading and data controller section', () => {
    renderWithRouter(Privacy)
    expect(screen.getByText('Privacy Policy')).toBeInTheDocument()
    expect(screen.getByText(/Naxely is committed to protecting your privacy/)).toBeInTheDocument()
    expect(screen.getByText('Data Controller')).toBeInTheDocument()
  })
})

describe('Refund', () => {
  it('renders heading and refund guarantee', () => {
    renderWithRouter(Refund)
    expect(screen.getByText('Refund Policy')).toBeInTheDocument()
    expect(screen.getByText(/14-day money-back guarantee/)).toBeInTheDocument()
    expect(screen.getByText("What's Covered")).toBeInTheDocument()
  })
})

describe('CookiePolicy', () => {
  it('renders heading and cookie categories', () => {
    renderWithRouter(CookiePolicy)
    expect(screen.getByText('Cookie Policy')).toBeInTheDocument()
    expect(screen.getByText('Necessary (Always Active)')).toBeInTheDocument()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText(/how to change your consent/i)).toBeInTheDocument()
  })
})

describe('Blog', () => {
  it('renders heading and at least one post link', () => {
    renderWithRouter(Blog)
    expect(screen.getByText('Blog')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /^How to Choose Client Reporting Software$/ })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /BYOK/i })).toBeInTheDocument()
  })
})

describe('BlogPostByok', () => {
  it('renders blog post heading', () => {
    renderWithRouter(BlogPostByok)
    expect(screen.getByText('Why Naxely Uses BYOK: Bring Your Own AI Key for Client Reports')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to blog/i })).toHaveAttribute('href', '/blog')
  })
})

describe('BlogPostClientReporting', () => {
  it('renders blog post heading', () => {
    renderWithRouter(BlogPostClientReporting)
    expect(screen.getByText('How to Choose Client Reporting Software')).toBeInTheDocument()
  })
})

describe('BlogPostCsvToPdf', () => {
  it('renders blog post heading', () => {
    renderWithRouter(BlogPostCsvToPdf)
    expect(screen.getByText('CSV to PDF Report Generator: Turn Spreadsheet Data Into Client-Ready Reports')).toBeInTheDocument()
  })
})

describe('BlogPostHub', () => {
  it('renders blog post heading', () => {
    renderWithRouter(BlogPostHub)
    expect(screen.getByText('Automated Client Reporting: The Complete Guide for Freelancers and Agencies')).toBeInTheDocument()
  })
})

describe('BlogPostWhiteLabel', () => {
  it('renders blog post heading', () => {
    renderWithRouter(BlogPostWhiteLabel)
    expect(
      screen.getByRole('heading', { level: 1 }),
    ).toHaveTextContent(/White Label Client Reporting for Agencies/)
  })
})

const seoPages: Array<{
  name: string
  Component: React.ComponentType
  canonicalPath: string
  heading: RegExp
}> = [
  {
    name: 'BlogPostAnomalyDetection',
    Component: BlogPostAnomalyDetection,
    canonicalPath: '/blog/anomaly-detection-in-client-reports',
    heading: /Anomaly Detection Actually Catches/,
  },
  {
    name: 'BlogPostBestFreelanceReporting',
    Component: BlogPostBestFreelanceReporting,
    canonicalPath: '/blog/best-client-reporting-software-freelancers',
    heading: /Best Client Reporting Software for Freelancers/,
  },
  {
    name: 'BlogPostClientReportChecklist',
    Component: BlogPostClientReportChecklist,
    canonicalPath: '/blog/what-should-client-report-include-checklist',
    heading: /What Should a Client Report Actually Include/,
  },
  {
    name: 'BlogPostGoogleSheets',
    Component: BlogPostGoogleSheets,
    canonicalPath: '/blog/google-sheets-client-reports',
    heading: /Keeps Your Google Sheets Reports Current/,
  },
  {
    name: 'BlogPostPythonCsvToPdf',
    Component: BlogPostPythonCsvToPdf,
    canonicalPath: '/blog/python-csv-to-pdf-reports',
    heading: /Python CSV to PDF Reports/,
  },
  {
    name: 'BlogPostTwoWeeks',
    Component: BlogPostTwoWeeks,
    canonicalPath: '/blog/two-weeks-building-naxely',
    heading: /What Two Weeks of Building a Client-Reporting Tool/,
  },
  {
    name: 'ComparisonAgencyAnalytics',
    Component: ComparisonAgencyAnalytics,
    canonicalPath: '/compare/agencyanalytics',
    heading: /Agency Analytics Alternative/,
  },
  {
    name: 'ComparisonDatabox',
    Component: ComparisonDatabox,
    canonicalPath: '/compare/databox',
    heading: /Naxely vs Databox/,
  },
  {
    name: 'ComparisonDashThis',
    Component: ComparisonDashThis,
    canonicalPath: '/compare/dashthis',
    heading: /Naxely vs DashThis/,
  },
  {
    name: 'ComparisonPowerdrill',
    Component: ComparisonPowerdrill,
    canonicalPath: '/compare/powerdrill',
    heading: /Naxely vs Powerdrill/,
  },
  {
    name: 'ComparisonWhatagraph',
    Component: ComparisonWhatagraph,
    canonicalPath: '/compare/whatagraph',
    heading: /Naxely vs Whatagraph/,
  },
]

describe.each(seoPages)('$name smoke + SEO', ({ Component, canonicalPath, heading }) => {
  it('renders without throwing and declares canonical URL', () => {
    const { container } = renderWithRouter(Component)

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(heading)

    const head = container.querySelector('[data-testid="ssg-head"]')
    expect(head).not.toBeNull()
    expect(head?.querySelector('link[rel="canonical"]')).toHaveAttribute(
      'href',
      `https://www.naxely.com${canonicalPath}`,
    )
  })

  it('declares valid JSON-LD schema', () => {
    const { container } = renderWithRouter(Component)

    const head = container.querySelector('[data-testid="ssg-head"]')
    const scripts = head?.querySelectorAll('script[type="application/ld+json"]') ?? []
    expect(scripts.length).toBeGreaterThan(0)

    for (const script of scripts) {
      const parsed = JSON.parse(script.textContent ?? '{}') as Record<string, unknown>
      expect(parsed['@context']).toBe('https://schema.org')
      expect(parsed['@type']).toBeTruthy()
    }
  })
})
