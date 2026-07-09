import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockNavigate = vi.fn()
const mockUnsubscribe = vi.fn()
let authStateCallback: ((event: string) => void) | null = null

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      onAuthStateChange: vi.fn((callback: (event: string) => void) => {
        authStateCallback = callback
        return { data: { subscription: { unsubscribe: mockUnsubscribe } } }
      }),
    },
  },
}))

import AuthCallback from '../AuthCallback'

describe('AuthCallback page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authStateCallback = null
  })

  it('renders loading spinner and text', () => {
    render(
      <MemoryRouter>
        <AuthCallback />
      </MemoryRouter>,
    )

    expect(screen.getByText('Signing you in...')).toBeInTheDocument()
  })

  it('navigates to /dashboard on SIGNED_IN event', () => {
    render(
      <MemoryRouter>
        <AuthCallback />
      </MemoryRouter>,
    )

    expect(authStateCallback).not.toBeNull()
    authStateCallback!('SIGNED_IN')

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('does NOT navigate on other auth events', () => {
    render(
      <MemoryRouter>
        <AuthCallback />
      </MemoryRouter>,
    )

    authStateCallback!('SIGNED_OUT')
    authStateCallback!('TOKEN_REFRESHED')
    authStateCallback!('USER_UPDATED')

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('calls unsubscribe on unmount', () => {
    const { unmount } = render(
      <MemoryRouter>
        <AuthCallback />
      </MemoryRouter>,
    )

    unmount()

    expect(mockUnsubscribe).toHaveBeenCalledTimes(1)
  })
})
