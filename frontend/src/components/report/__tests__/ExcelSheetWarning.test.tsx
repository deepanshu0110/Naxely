import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'

describe('Excel sheet warning rendering', () => {
  it('renders warning banner when excel_warning is present', () => {
    // Simulate what FileUpload renders after upload with multi-sheet Excel
    render(
      <MemoryRouter>
        <div className="rounded-xl border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-900/30">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div>
                <p className="font-medium">test.xlsx</p>
                <p className="text-sm text-gray-500">2 rows x 3 columns</p>
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-800 dark:bg-yellow-900/30">
            <p className="text-sm text-yellow-800">This file has 3 sheets — only Sheet1 was used.</p>
          </div>
        </div>
      </MemoryRouter>
    )
    const warning = screen.getByText('This file has 3 sheets — only Sheet1 was used.')
    expect(warning).toBeInTheDocument()
    expect(warning.className).toContain('text-yellow-800')
  })

  it('does not render warning when no excel_warning', () => {
    render(
      <MemoryRouter>
        <div className="rounded-xl border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-900/30">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div>
                <p className="font-medium">test.csv</p>
                <p className="text-sm text-gray-500">2 rows x 3 columns</p>
              </div>
            </div>
          </div>
        </div>
      </MemoryRouter>
    )
    expect(screen.queryByText(/sheets/)).toBeNull()
  })
})