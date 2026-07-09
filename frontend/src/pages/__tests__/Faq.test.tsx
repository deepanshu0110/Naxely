import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('@/components/layout/Navbar', () => ({
  default: () => <div>Navbar</div>,
}))

vi.mock('vite-react-ssg', () => ({
  Head: () => null,
}))

import Faq from '../Faq'

function renderPage() {
  return render(
    <MemoryRouter>
      <Faq />
    </MemoryRouter>,
  )
}

describe('FAQ page', () => {
  it('renders the heading', () => {
    renderPage()
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument()
  })

  it('renders all 8 FAQ items', () => {
    renderPage()
    expect(screen.getByText('Can ChatGPT create a report?')).toBeInTheDocument()
    expect(screen.getByText('How do I generate a report with AI?')).toBeInTheDocument()
    expect(screen.getByText('Which AI tool is free to generate reports?')).toBeInTheDocument()
    expect(screen.getByText('Is there a free AI tool to generate reports without a credit card?')).toBeInTheDocument()
    expect(screen.getByText('How can I tell if a report is AI-generated?')).toBeInTheDocument()
    expect(screen.getByText("What's the best AI for creating client reports?")).toBeInTheDocument()
    expect(screen.getByText('Do I need to pay for the AI, or does Naxely charge for it?')).toBeInTheDocument()
    expect(screen.getByText('Can I use AI to write a report from a Google Sheet?')).toBeInTheDocument()
  })

  it('renders a Footer with Naxely copyright', () => {
    renderPage()
    expect(screen.getByText(/Naxely © 2026/)).toBeInTheDocument()
  })
})
