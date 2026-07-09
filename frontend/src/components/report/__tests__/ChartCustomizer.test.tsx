import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ChartSpec, ColumnConfig } from '@/types/report'

const mockPost = vi.hoisted(() => vi.fn())

vi.mock('@/lib/axios', () => ({
  default: { post: mockPost },
}))

import ChartCustomizer from '../ChartCustomizer'

const mockColumnConfig: ColumnConfig[] = [
  { original_name: 'sales', display_name: 'Sales', type: 'metric', include: true },
  { original_name: 'date', display_name: 'Date', type: 'date', include: true },
]

const mockChartSpecs: ChartSpec[] = [
  { x: 'date', y: 'sales', type: 'line', title: 'Sales over time' },
  { x: 'date', y: 'sales', type: 'bar', title: 'Sales by month' },
]

function renderChartCustomizer(onSpecsChange = vi.fn()) {
  return {
    onSpecsChange,
    ...render(
      <ChartCustomizer
        uploadId="up-123"
        columnConfig={mockColumnConfig}
        onSpecsChange={onSpecsChange}
      />,
    ),
  }
}

describe('ChartCustomizer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockPost.mockImplementation(() => new Promise(() => {}))
    renderChartCustomizer()
    expect(screen.getByText('AI is selecting the best charts...')).toBeInTheDocument()
  })

  it('renders error state when API fails', async () => {
    mockPost.mockRejectedValue(new Error('API error'))
    renderChartCustomizer()
    expect(
      await screen.findByText('Could not load chart suggestions. Using defaults.'),
    ).toBeInTheDocument()
  })

  it('renders chart specs when API succeeds', async () => {
    mockPost.mockResolvedValue({ data: { chart_specs: mockChartSpecs } })
    renderChartCustomizer()
    expect(await screen.findByText('Sales over time')).toBeInTheDocument()
    expect(screen.getByText('Sales by month')).toBeInTheDocument()
  })

  it('changing chart type calls updateSpec and onSpecsChange', async () => {
    const onSpecsChange = vi.fn()
    mockPost.mockResolvedValue({ data: { chart_specs: mockChartSpecs } })
    renderChartCustomizer(onSpecsChange)

    const selects = await screen.findAllByRole('combobox')
    expect(selects).toHaveLength(2)

    await userEvent.selectOptions(selects[0], 'area')

    await waitFor(() => {
      expect(onSpecsChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            x: 'date',
            y: 'sales',
            type: 'area',
            title: 'Sales over time',
          }),
        ]),
      )
    })
  })

  it('renders empty specs message when API returns no charts', async () => {
    mockPost.mockResolvedValue({ data: { chart_specs: [] } })
    renderChartCustomizer()
    expect(
      await screen.findByText('No charts could be suggested for this data.'),
    ).toBeInTheDocument()
  })
})
