import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FileUpload from '../FileUpload'

const mockUploadFile = vi.hoisted(() => vi.fn())
const toastError = vi.hoisted(() => vi.fn())

const captured = vi.hoisted(() => ({
  onDrop: vi.fn(),
  onDropRejected: vi.fn(),
}))

vi.mock('react-hot-toast', () => ({ default: { error: toastError } }))

vi.mock('@/store/reportStore', () => ({
  useReportStore: (selector: any) => {
    const state = { uploadFile: mockUploadFile }
    return selector ? selector(state) : state
  },
}))

vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn(({ onDrop, onDropRejected }) => {
    captured.onDrop = onDrop
    captured.onDropRejected = onDropRejected
    return {
      getRootProps: () => ({ tabIndex: 0 }),
      getInputProps: () => ({ 'data-testid': 'dropzone-input' }),
      isDragActive: false,
    }
  }),
}))

vi.mock('@/components/ui/Spinner', () => ({
  default: ({ size }: any) => <div data-testid="spinner" data-size={size} />,
}))

const mockResult = {
  upload_id: 'up-123',
  filename: 'test.csv',
  file_url: 'https://example.com/test.csv',
  row_count: 100,
  column_count: 5,
  columns: [],
  preview_rows: [],
}

function renderFileUpload(onUploadComplete = vi.fn()) {
  return { onUploadComplete, ...render(<FileUpload onUploadComplete={onUploadComplete} />) }
}

describe('FileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dropzone with upload prompt', () => {
    renderFileUpload()
    expect(screen.getByText("Drag & drop your CSV or XLSX file")).toBeInTheDocument()
    expect(screen.getByText('or click to browse')).toBeInTheDocument()
  })

  it('shows spinner and uploading text while uploading', async () => {
    mockUploadFile.mockImplementation(() => new Promise(() => {}))
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    captured.onDrop([file])

    expect(await screen.findByTestId('spinner')).toBeInTheDocument()
    expect(screen.getByText('Uploading...')).toBeInTheDocument()
  })

  it('shows file info after successful upload', async () => {
    mockUploadFile.mockResolvedValue(mockResult)
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    expect(await screen.findByText('test.csv')).toBeInTheDocument()
    expect(screen.getByText('100 rows × 5 columns')).toBeInTheDocument()
  })

  it('calls onUploadComplete after successful upload', async () => {
    mockUploadFile.mockResolvedValue(mockResult)
    const onUploadComplete = vi.fn()
    renderFileUpload(onUploadComplete)

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith(mockResult)
    })
  })

  it('reset button clears upload state', async () => {
    mockUploadFile.mockResolvedValue(mockResult)
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])
    expect(await screen.findByText('test.csv')).toBeInTheDocument()

    const resetBtn = screen.getByRole('button')
    await userEvent.click(resetBtn)

    expect(screen.getByText("Drag & drop your CSV or XLSX file")).toBeInTheDocument()
  })

  it('displays error message on failed upload', async () => {
    mockUploadFile.mockRejectedValue(new Error('Server error'))
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    expect(await screen.findByText('Server error')).toBeInTheDocument()
  })

  it('does not set error for 401 status', async () => {
    const err = { response: { status: 401 } }
    mockUploadFile.mockRejectedValue(err)
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    await waitFor(() => {
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
    })
  })

  it('does not set error for 402 status', async () => {
    const err = { response: { status: 402 } }
    mockUploadFile.mockRejectedValue(err)
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    await waitFor(() => {
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
    })
  })

  it('shows fallback message when error is not an Error instance', async () => {
    mockUploadFile.mockRejectedValue('string error')
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    expect(await screen.findByText('Upload failed. Please try again.')).toBeInTheDocument()
  })

  it('uses API response message on upload error', async () => {
    mockUploadFile.mockRejectedValue({
      response: { data: { message: 'API custom error' } },
    })
    renderFileUpload()

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    await captured.onDrop([file])

    expect(await screen.findByText('API custom error')).toBeInTheDocument()
  })

  it('shows toast for too-large files', () => {
    renderFileUpload()

    captured.onDropRejected([{
      file: { name: 'big.csv' },
      errors: [{ code: 'file-too-large' }],
    }])

    expect(toastError).toHaveBeenCalledWith('File too large. Maximum size is 10MB.')
  })

  it('shows toast for invalid file type', () => {
    renderFileUpload()

    captured.onDropRejected([{
      file: { name: 'bad.exe' },
      errors: [{ code: 'file-invalid-type' }],
    }])

    expect(toastError).toHaveBeenCalledWith('Invalid file type. Please upload a CSV or Excel (.xlsx) file.')
  })

  it('shows generic toast for other rejection errors', () => {
    renderFileUpload()

    captured.onDropRejected([{
      file: { name: 'unknown.xzy' },
      errors: [{ code: 'unknown-error', message: 'Something went wrong' }],
    }])

    expect(toastError).toHaveBeenCalledWith('Something went wrong')
  })
})
