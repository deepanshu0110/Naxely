import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockNavigate = vi.fn()
const mockLoginWithGoogle = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    loginWithGoogle: mockLoginWithGoogle,
  }),
}))

const mockSignUp = vi.hoisted(() => vi.fn())

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      signUp: mockSignUp,
    },
  },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn() },
}))

vi.mock('vite-react-ssg', () => ({
  Head: () => null,
}))

import toast from 'react-hot-toast'
import Signup from '../Signup'

function renderPage() {
  return render(
    <MemoryRouter>
      <Signup />
    </MemoryRouter>,
  )
}

describe('Signup page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form with name, email, and password fields', () => {
    renderPage()
    expect(screen.getByLabelText('Full name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('renders Google OAuth button', () => {
    renderPage()
    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
  })

  it('calls loginWithGoogle when Google button is clicked', async () => {
    renderPage()
    await userEvent.click(screen.getByText('Continue with Google'))
    expect(mockLoginWithGoogle).toHaveBeenCalledTimes(1)
  })

  it('shows validation error for empty name', async () => {
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText('Name is required')).toBeInTheDocument()
  })

  it('shows validation error for invalid email', async () => {
    renderPage()

    await userEvent.type(screen.getByLabelText('Full name'), 'Alice')
    await userEvent.type(screen.getByLabelText('Email'), 'not-email')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    const form = screen.getByRole('button', { name: /create account/i }).closest('form')!
    fireEvent.submit(form)

    expect(await screen.findByText('Please enter a valid email')).toBeInTheDocument()
  })

  it('shows validation error for short password', async () => {
    renderPage()

    await userEvent.type(screen.getByLabelText('Full name'), 'Alice')
    await userEvent.type(screen.getByLabelText('Email'), 'test@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'short')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText('Password must be at least 8 characters')).toBeInTheDocument()
  })

  it('calls supabase.auth.signUp and navigates on success', async () => {
    mockSignUp.mockResolvedValue({ data: { user: { id: 'u1' } }, error: null })

    renderPage()

    await userEvent.type(screen.getByLabelText('Full name'), 'Alice')
    await userEvent.type(screen.getByLabelText('Email'), 'alice@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'securePass123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith({
        email: 'alice@test.com',
        password: 'securePass123',
        options: { data: { full_name: 'Alice' } },
      })
    })
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('shows toast error on signup failure', async () => {
    mockSignUp.mockResolvedValue({
      data: { user: null },
      error: new Error('User already registered'),
    })

    renderPage()

    await userEvent.type(screen.getByLabelText('Full name'), 'Alice')
    await userEvent.type(screen.getByLabelText('Email'), 'alice@test.com')
    await userEvent.type(screen.getByLabelText('Password'), 'securePass123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('User already registered')
    })
  })

  it('shows default error message when error has empty message', async () => {
    mockSignUp.mockResolvedValue({
      data: { user: null },
      error: new Error(''),
    })

    renderPage()

    await userEvent.type(screen.getByLabelText('Full name'), 'Alice')
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.com')
    await userEvent.type(screen.getByLabelText('Password'), 'securePass123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Sign up failed. Please try again.')
    })
  })

  it('shows default error message when error has no message', async () => {
    mockSignUp.mockResolvedValue({
      data: { user: null },
      error: new Error(),
    })

    renderPage()

    await userEvent.type(screen.getByLabelText('Full name'), 'Alice')
    await userEvent.type(screen.getByLabelText('Email'), 'a@b.com')
    await userEvent.type(screen.getByLabelText('Password'), 'securePass123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Sign up failed. Please try again.')
    })
  })

  it('shows password strength meter', async () => {
    renderPage()

    const passwordInput = screen.getByLabelText('Password')
    await userEvent.type(passwordInput, 'weak')

    expect(screen.getByText('Weak')).toBeInTheDocument()
  })

  it('shows "Strong" for a complex password', async () => {
    renderPage()

    const passwordInput = screen.getByLabelText('Password')
    await userEvent.type(passwordInput, 'StrongP@ss1')

    expect(await screen.findByText('Strong')).toBeInTheDocument()
  })

  it('hides strength meter when password is empty', () => {
    renderPage()
    expect(screen.queryByText('Weak')).not.toBeInTheDocument()
    expect(screen.queryByText('Fair')).not.toBeInTheDocument()
    expect(screen.queryByText('Good')).not.toBeInTheDocument()
    expect(screen.queryByText('Strong')).not.toBeInTheDocument()
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
})
