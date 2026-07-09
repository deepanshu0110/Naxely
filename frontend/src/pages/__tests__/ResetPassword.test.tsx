import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockUpdatePassword = vi.hoisted(() => vi.fn())
const mockNavigate = vi.hoisted(() => vi.fn())
const mockGetSession = vi.hoisted(() => vi.fn())

const authStateHelpers = vi.hoisted(() => {
  let callback: ((event: string) => void) | null = null
  return {
    getCallback: () => callback,
    onAuthStateChange: vi.fn((cb: (event: string) => void) => {
      callback = cb
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    }),
  }
})

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({ updatePassword: mockUpdatePassword }),
}))

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: authStateHelpers.onAuthStateChange,
    },
  },
}))

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

vi.mock('vite-react-ssg', () => ({
  Head: () => null,
}))

import toast from 'react-hot-toast'
import ResetPassword from '../ResetPassword'

function renderPage() {
  return render(
    <MemoryRouter>
      <ResetPassword />
    </MemoryRouter>,
  )
}

describe('ResetPassword page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows checking spinner initially (before session check timer)', () => {
    mockGetSession.mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText('Verifying reset link...')).toBeInTheDocument()
  })

  it('shows "invalid or expired" when no session and no PASSWORD_RECOVERY event after 3s', async () => {
    vi.useFakeTimers()
    mockGetSession.mockResolvedValue({ data: { session: null } })
    renderPage()

    await vi.advanceTimersByTimeAsync(3000)

    expect(screen.getByText(/invalid or has expired/i)).toBeInTheDocument()
  })

  it('shows form when PASSWORD_RECOVERY event fires', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } })
    renderPage()

    const callback = authStateHelpers.getCallback()
    expect(callback).not.toBeNull()
    callback!('PASSWORD_RECOVERY')

    await waitFor(() => {
      expect(screen.getByText('Set a new password')).toBeInTheDocument()
    })
  })

  it('password mismatch shows validation error', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } })
    renderPage()

    const callback = authStateHelpers.getCallback()
    callback!('PASSWORD_RECOVERY')

    await screen.findByText('Set a new password')

    await userEvent.type(screen.getByLabelText('New password'), 'password123')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'password456')
    await userEvent.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument()
  })

  it('short password (<8 chars) shows validation error', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } })
    renderPage()

    const callback = authStateHelpers.getCallback()
    callback!('PASSWORD_RECOVERY')

    await screen.findByText('Set a new password')

    await userEvent.type(screen.getByLabelText('New password'), 'short')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'longenough123')
    const form = screen.getByRole('button', { name: /update password/i }).closest('form')!
    fireEvent.submit(form)

    expect(await screen.findByText('Password must be at least 8 characters')).toBeInTheDocument()
  })

  it('valid form submission calls updatePassword, toast.success, navigates to /login', async () => {
    mockUpdatePassword.mockResolvedValue(undefined)
    mockGetSession.mockResolvedValue({ data: { session: null } })
    renderPage()

    const callback = authStateHelpers.getCallback()
    callback!('PASSWORD_RECOVERY')

    await screen.findByText('Set a new password')

    await userEvent.type(screen.getByLabelText('New password'), 'newSecurePass1')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newSecurePass1')
    await userEvent.click(screen.getByRole('button', { name: /update password/i }))

    await waitFor(() => {
      expect(mockUpdatePassword).toHaveBeenCalledWith('newSecurePass1')
    })
    expect(toast.success).toHaveBeenCalledWith('Password updated successfully')
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })
})