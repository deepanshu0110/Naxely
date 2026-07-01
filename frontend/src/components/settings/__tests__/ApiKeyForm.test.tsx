import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('react-hot-toast')
vi.mock('@/lib/axios', () => ({ default: { post: vi.fn(), delete: vi.fn() } }))

import ApiKeyForm from '../ApiKeyForm'

function renderForm(overrides: Partial<React.ComponentProps<typeof ApiKeyForm>> = {}) {
  const props = {
    hasKey: false,
    provider: null as string | null,
    keyPreview: null as string | null,
    tier: 'free',
    onSaved: vi.fn(),
    onDeleted: vi.fn(),
    ...overrides,
  }
  return render(<ApiKeyForm {...props} />)
}

describe('ApiKeyForm Groq recommendation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows Groq recommendation link in info box', () => {
    renderForm()
    const groqLink = screen.getByText('Get a free Groq key')
    expect(groqLink).toBeInTheDocument()
    expect(groqLink).toHaveAttribute('href', 'https://console.groq.com/keys')
    expect(groqLink).toHaveAttribute('target', '_blank')
    expect(groqLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('shows recommendation regardless of key state', () => {
    renderForm({ hasKey: true, provider: 'groq', keyPreview: '...xyz' })
    expect(screen.getByText('Get a free Groq key')).toBeInTheDocument()
  })
})
