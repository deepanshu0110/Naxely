import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const mockPost = vi.hoisted(() => vi.fn())
vi.mock('@/lib/axios', () => ({ default: { post: mockPost } }))

const mockToast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))
vi.mock('react-hot-toast', () => ({ default: mockToast }))

import SendToClientModal from '../SendToClientModal'

const onClose = vi.fn()

function renderModal(isOpen = true) {
  return render(
    <SendToClientModal isOpen={isOpen} onClose={onClose} reportId="rep-1" reportTitle="Q1 Report" />,
  )
}

function emailInput() {
  return screen.getByPlaceholderText(/Enter email, press Enter or comma|Add more/)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SendToClientModal rendering', () => {
  it('renders nothing when closed', () => {
    const { container } = renderModal(false)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows title, report name and action buttons when open', () => {
    renderModal()
    expect(screen.getByText('Send Report to Client')).toBeInTheDocument()
    expect(screen.getByText(/Q1 Report/)).toBeInTheDocument()
    expect(screen.getByText('Recipients')).toBeInTheDocument()
    expect(screen.getByText('Message')).toBeInTheDocument()
    expect(screen.getByText('(optional)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })
})

describe('SendToClientModal recipient entry', () => {
  it('adds an email chip on Enter and clears the input', async () => {
    renderModal()
    await userEvent.type(emailInput(), 'a@test.com{enter}')

    expect(screen.getByText('a@test.com')).toBeInTheDocument()
    expect(emailInput()).toHaveValue('')
  })

  it('adds an email chip when a comma is typed', async () => {
    renderModal()
    await userEvent.type(emailInput(), 'b@test.com,')

    expect(screen.getByText('b@test.com')).toBeInTheDocument()
    expect(emailInput()).toHaveValue('')
  })

  it('rejects an invalid email with an inline error and adds no chip', async () => {
    renderModal()
    await userEvent.type(emailInput(), 'not-an-email{enter}')

    expect(screen.getByText('Invalid email format')).toBeInTheDocument()
    expect(screen.queryByText('not-an-email')).not.toBeInTheDocument()
  })

  it('does not duplicate an existing email', async () => {
    renderModal()
    await userEvent.type(emailInput(), 'a@test.com{enter}')
    await userEvent.type(emailInput(), 'a@test.com{enter}')

    expect(screen.getAllByText('a@test.com')).toHaveLength(1)
  })

  it('adds the email on blur', () => {
    renderModal()
    fireEvent.change(emailInput(), { target: { value: 'c@test.com' } })
    fireEvent.blur(emailInput())

    expect(screen.getByText('c@test.com')).toBeInTheDocument()
  })

  it('splits pasted comma/newline/semicolon lists into chips, skipping invalid entries', () => {
    renderModal()
    fireEvent.paste(emailInput(), {
      clipboardData: { getData: () => 'a@test.com, c@test.com\nbad-email; e@test.com' },
    })

    expect(screen.getByText('a@test.com')).toBeInTheDocument()
    expect(screen.getByText('c@test.com')).toBeInTheDocument()
    expect(screen.getByText('e@test.com')).toBeInTheDocument()
    expect(screen.queryByText('bad-email')).not.toBeInTheDocument()
  })

  it('removes a chip when its remove button is clicked', async () => {
    renderModal()
    await userEvent.type(emailInput(), 'a@test.com{enter}')

    const chip = screen.getByText('a@test.com').closest('span')
    expect(chip).not.toBeNull()
    await userEvent.click(within(chip as HTMLElement).getByRole('button'))

    expect(screen.queryByText('a@test.com')).not.toBeInTheDocument()
  })
})

describe('SendToClientModal send flow', () => {
  it('blocks sending with no recipients and shows a validation error', async () => {
    renderModal()
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(screen.getByText('At least one recipient is required')).toBeInTheDocument()
    expect(mockPost).not.toHaveBeenCalled()
    expect(onClose).not.toHaveBeenCalled()
  })

  it('sends recipients and message, shows success toast and closes', async () => {
    mockPost.mockResolvedValueOnce({ data: { sent: true } })
    renderModal()

    await userEvent.type(emailInput(), 'client@example.com{enter}')
    await userEvent.type(screen.getByPlaceholderText('Add a personal note...'), 'Please review!')
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/reports/rep-1/send', {
        recipients: ['client@example.com'],
        message: 'Please review!',
      })
    })
    expect(mockToast.success).toHaveBeenCalledWith('Report sent to client!')
    expect(onClose).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('client@example.com')).not.toBeInTheDocument()
  })

  it('omits the message key when the message is blank', async () => {
    mockPost.mockResolvedValueOnce({ data: { sent: true } })
    renderModal()

    await userEvent.type(emailInput(), 'client@example.com{enter}')
    await userEvent.type(screen.getByPlaceholderText('Add a personal note...'), '   ')
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/reports/rep-1/send', {
        recipients: ['client@example.com'],
        message: undefined,
      })
    })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('recovers after a failed send: no success toast, no close, and sending state resets', async () => {
    mockPost.mockRejectedValueOnce(new Error('boom'))
    mockPost.mockResolvedValueOnce({ data: { sent: true } })
    renderModal()

    await userEvent.type(emailInput(), 'client@example.com{enter}')
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledTimes(1)
    })
    expect(mockToast.success).not.toHaveBeenCalled()
    expect(onClose).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Send' }))
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledTimes(2)
    })
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})

describe('SendToClientModal cancel flow', () => {
  it('clears entered state and closes when Cancel is clicked', async () => {
    renderModal()
    await userEvent.type(emailInput(), 'a@test.com{enter}')
    await userEvent.type(screen.getByPlaceholderText('Add a personal note...'), 'hello')

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onClose).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('a@test.com')).not.toBeInTheDocument()
    expect(mockPost).not.toHaveBeenCalled()
  })
})
