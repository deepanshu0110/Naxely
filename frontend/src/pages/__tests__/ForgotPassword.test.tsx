import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const mockSendPasswordResetEmail = vi.fn()

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({ sendPasswordResetEmail: mockSendPasswordResetEmail }),
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn() },
}))

vi.mock('vite-react-ssg', () => ({
  Head: () => null,
}))

import toast from 'react-hot-toast'
import ForgotPassword from '../ForgotPassword'

function renderPage() {
  return render(
    <MemoryRouter>
      <ForgotPassword />
    </MemoryRouter>,
  )
}

describe('ForgotPassword page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders reset password form with email input', () => {
    renderPage()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument()
  })

  it('invalid email shows validation error "Please enter a valid email"', async () => {
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'not-an-email')
    const form = screen.getByRole('button', { name: /send reset link/i }).closest('form')!
    fireEvent.submit(form)

    expect(await screen.findByText('Please enter a valid email')).toBeInTheDocument()
  })

  it('valid email submission calls sendPasswordResetEmail and shows success state', async () => {
    mockSendPasswordResetEmail.mockResolvedValue(undefined)
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'user@test.com')
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(mockSendPasswordResetEmail).toHaveBeenCalledWith('user@test.com')
    })

    expect(screen.getByText(/if an account exists/i)).toBeInTheDocument()
  })

  it('error during submission shows toast.error', async () => {
    mockSendPasswordResetEmail.mockRejectedValue(new Error('fail'))
    renderPage()

    await userEvent.type(screen.getByLabelText('Email'), 'user@test.com')
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Something went wrong. Please try again later.')
    })
  })

  it('"Back to log in" link exists', () => {
    renderPage()
    const links = screen.getAllByRole('link', { name: /back to log in/i })
    expect(links.length).toBeGreaterThanOrEqual(1)
    links.forEach((link) => {
      expect(link).toHaveAttribute('href', '/login')
    })
  })
})