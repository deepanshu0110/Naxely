import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockNavigate = vi.fn()
const mockLoginWithEmail = vi.fn()
const mockLoginWithGoogle = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    loginWithEmail: mockLoginWithEmail,
    loginWithGoogle: mockLoginWithGoogle,
  }),
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn() },
}))

vi.mock('vite-react-ssg', () => ({
  Head: () => null,
}))

import toast from 'react-hot-toast'
import Login from '../Login'

function renderPage() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  )
}

describe('Login page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form with email and password fields', () => {
    renderPage()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument()
  })

  it('renders Google OAuth button', () => {
    renderPage()
    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
  })

  it('renders links to sign up and forgot password', () => {
    renderPage()
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument()
    expect(screen.getByText('Sign up')).toBeInTheDocument()
    expect(screen.getByText('Forgot password?')).toBeInTheDocument()
  })

  it('calls loginWithGoogle when Google button is clicked', async () => {
    renderPage()
    await userEvent.click(screen.getByText('Continue with Google'))
    expect(mockLoginWithGoogle).toHaveBeenCalledTimes(1)
  })

  it('calls loginWithEmail and navigates to /dashboard on valid submit', async () => {
    mockLoginWithEmail.mockResolvedValue(undefined)
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(mockLoginWithEmail).toHaveBeenCalledWith('test@test.com', 'password123')
    })
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('shows toast error on failed login', async () => {
    mockLoginWithEmail.mockRejectedValue(new Error('Invalid login credentials'))
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Invalid login credentials')
    })
  })

  it('shows generic message when rejected with empty message', async () => {
    mockLoginWithEmail.mockRejectedValue(new Error(''))
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed. Please check your credentials and try again.')
    })
  })

  it('shows generic message when rejected with no message', async () => {
    mockLoginWithEmail.mockRejectedValue(new Error())
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed. Please check your credentials and try again.')
    })
  })

  it('shows client-side validation error for invalid email', async () => {
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'not-an-email')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    const form = screen.getByRole('button', { name: /log in/i }).closest('form')!
    fireEvent.submit(form)

    expect(await screen.findByText('Please enter a valid email')).toBeInTheDocument()
  })

  it('shows client-side validation error for short password', async () => {
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'short')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    expect(await screen.findByText('Password must be at least 8 characters')).toBeInTheDocument()
  })

  it('toggles password visibility', async () => {
    renderPage()

    const passwordInput = screen.getByLabelText('Password')
    expect(passwordInput).toHaveAttribute('type', 'password')

    const toggleBtn = screen.getByRole('button', { name: /show password/i })
    await userEvent.click(toggleBtn)
    expect(passwordInput).toHaveAttribute('type', 'text')
    expect(toggleBtn).toHaveAttribute('aria-label', 'Hide password')

    await userEvent.click(toggleBtn)
    expect(passwordInput).toHaveAttribute('type', 'password')
    expect(toggleBtn).toHaveAttribute('aria-label', 'Show password')
  })

  it('disables the submit button while submitting', async () => {
    mockLoginWithEmail.mockImplementation(() => new Promise<never>(() => {}))
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))

    expect(screen.getByRole('button', { name: /log in/i })).toBeDisabled()
  })
})
