import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const mockNavigate = vi.hoisted(() => vi.fn())
const mockFetchProfile = vi.hoisted(() => vi.fn())

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('@/lib/axios', () => ({
  default: { post: vi.fn() },
}))

import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import WelcomeModal from '../WelcomeModal'

function renderModal(onClose = vi.fn()) {
  return { onClose, ...render(<WelcomeModal onClose={onClose} />) }
}

describe('WelcomeModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuthStore).mockImplementation((selector?: any) => {
      const state = { fetchProfile: mockFetchProfile }
      return selector ? selector(state) : state
    })
  })

  it('renders heading "Welcome to Naxely"', () => {
    renderModal()
    expect(screen.getByText('Welcome to Naxely')).toBeInTheDocument()
  })

  it('renders "Try with sample data" button', () => {
    renderModal()
    expect(screen.getByText('Try with sample data →')).toBeInTheDocument()
  })

  it('renders "Upload my own CSV" button', () => {
    renderModal()
    expect(screen.getByText('Upload my own CSV')).toBeInTheDocument()
  })

  it('renders "Skip for now" link', () => {
    renderModal()
    expect(screen.getByText('Skip for now')).toBeInTheDocument()
  })

  it('calls api.post, fetchProfile, and onClose when "Skip for now" is clicked', async () => {
    const { onClose } = renderModal()
    const user = userEvent.setup()

    await user.click(screen.getByText('Skip for now'))

    expect(api.post).toHaveBeenCalledWith('/auth/skip-onboarding')
    expect(mockFetchProfile).toHaveBeenCalledOnce()
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('calls api.post for sample upload then navigation when "Try with sample data" is clicked', async () => {
    const mockUploadResult = {
      upload_id: 'up-123',
      filename: 'test.csv',
      file_url: 'https://example.com/test.csv',
      row_count: 100,
      column_count: 5,
      columns: [],
      preview_rows: [],
    }

    vi.mocked(api.post).mockResolvedValueOnce({ data: mockUploadResult })
    vi.mocked(api.post).mockResolvedValueOnce({})

    renderModal()
    const user = userEvent.setup()

    await user.click(screen.getByText('Try with sample data →'))

    expect(api.post).toHaveBeenCalledWith('/reports/sample-upload')
    expect(api.post).toHaveBeenCalledWith('/auth/complete-onboarding')
    expect(mockNavigate).toHaveBeenCalledWith('/report/new', {
      state: { uploadResult: mockUploadResult },
    })
  })
})
