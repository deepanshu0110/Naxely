import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ColumnMapper from '../ColumnMapper'
import type { ColumnInfo, ColumnConfig } from '@/types/report'

const mockColumns: ColumnInfo[] = [
  {
    original_name: 'date',
    suggested_name: 'Date',
    suggested_type: 'date',
    sample_values: ['2024-01-01', '2024-01-02', '2024-01-03'],
    null_count: 0,
    unique_count: 30,
  },
  {
    original_name: 'revenue',
    suggested_name: 'Revenue',
    suggested_type: 'metric',
    sample_values: [100, 200, 300],
    null_count: 0,
    unique_count: 25,
  },
  {
    original_name: 'region',
    suggested_name: 'Region',
    suggested_type: 'dimension',
    sample_values: ['North', 'South', 'East'],
    null_count: 2,
    unique_count: 4,
  },
]

function renderMapper(columns = mockColumns, onChange = vi.fn()) {
  return { onChange, ...render(<ColumnMapper columns={columns} onChange={onChange} />) }
}

describe('ColumnMapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders column names and sample values', () => {
    renderMapper()

    expect(screen.getByText('date')).toBeInTheDocument()
    expect(screen.getByText('revenue')).toBeInTheDocument()
    expect(screen.getByText('region')).toBeInTheDocument()
    expect(screen.getByText('2024-01-01')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('North')).toBeInTheDocument()
  })

  it('calls onChange with initial config on mount', () => {
    const onChange = vi.fn()
    renderMapper(mockColumns, onChange)

    const expected: ColumnConfig[] = [
      { original_name: 'date', display_name: 'Date', type: 'date', include: true },
      { original_name: 'revenue', display_name: 'Revenue', type: 'metric', include: true },
      { original_name: 'region', display_name: 'Region', type: 'dimension', include: true },
    ]
    expect(onChange).toHaveBeenCalledWith(expected)
  })

  it('updates display name on input change', async () => {
    const onChange = vi.fn()
    renderMapper(mockColumns, onChange)

    const inputs = screen.getAllByRole('textbox')
    const displayInput = inputs[0]
    await userEvent.clear(displayInput)
    await userEvent.type(displayInput, 'Transaction Date')

    expect(onChange).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ original_name: 'date', display_name: 'Transaction Date' }),
      ]),
    )
  })

  it('changes type via dropdown', async () => {
    const onChange = vi.fn()
    renderMapper(mockColumns, onChange)

    const selects = screen.getAllByRole('combobox')
    await userEvent.selectOptions(selects[0], 'text')

    expect(onChange).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ original_name: 'date', type: 'text' }),
      ]),
    )
  })

  it('toggles include on button click', async () => {
    const onChange = vi.fn()
    renderMapper(mockColumns, onChange)

    const toggleBtns = screen.getAllByRole('button')
    const includeBtn = toggleBtns.find(b => b.classList.contains('relative'))
    if (includeBtn) {
      await userEvent.click(includeBtn)
    }

    expect(onChange).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ original_name: 'date', include: false }),
      ]),
    )
  })

  it('shows all 4 type options in dropdowns', () => {
    renderMapper()

    const selects = screen.getAllByRole('combobox')
    const options = Array.from(selects[0].querySelectorAll('option')).map(o => o.textContent)
    expect(options).toEqual(['Date', 'Metric', 'Dimension', 'Text'])
  })
})
