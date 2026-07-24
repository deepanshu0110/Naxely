import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('vite-react-ssg', () => ({ Head: () => null }))

vi.mock('@/components/layout/Navbar', () => ({ default: () => <div>Navbar</div> }))

import NotFound from '../NotFound'
import Contact from '../Contact'
import Terms from '../Terms'
import Privacy from '../Privacy'
import Refund from '../Refund'
import Blog from '../Blog'
import BlogPostByok from '../BlogPostByok'
import BlogPostClientReporting from '../BlogPostClientReporting'
import BlogPostCsvToPdf from '../BlogPostCsvToPdf'
import BlogPostHub from '../BlogPostHub'
import BlogPostWhiteLabel from '../BlogPostWhiteLabel'

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

describe('Blog', () => {
  it('renders heading and at least one post link', () => {
    renderWithRouter(Blog)
    expect(screen.getByText('Blog')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /client reporting software/i })).toBeInTheDocument()
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
    expect(screen.getByText('Automating Client Reports: The Complete Guide for Freelancers and Agencies')).toBeInTheDocument()
  })
})

describe('BlogPostWhiteLabel', () => {
  it('renders blog post heading', () => {
    renderWithRouter(BlogPostWhiteLabel)
    expect(screen.getByText(/White Label Client Reporting for Agencies/)).toBeInTheDocument()
  })
})
