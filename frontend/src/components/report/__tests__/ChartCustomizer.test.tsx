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
    expect(screen.getByText('Preparing chart recommendations...')).toBeInTheDocument()
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

describe('ChartCustomizer candidate selection', () => {
  const candidateSpecs: ChartSpec[] = [
    { x: 'date', y: 'sales', type: 'line', title: 'Sales over time', recommended: true },
    { x: 'date', y: 'sales', type: 'bar', title: 'Sales by month', recommended: true },
    { x: 'client', y: 'sales', type: 'bar', title: 'Sales by client', recommended: false },
  ]

  function renderCustomizer(opts: { maxCharts?: number; onSpecsChange?: ReturnType<typeof vi.fn> } = {}) {
    const onSpecsChange = opts.onSpecsChange ?? vi.fn()
    render(
      <ChartCustomizer
        uploadId="up-123"
        columnConfig={mockColumnConfig}
        onSpecsChange={onSpecsChange}
        maxCharts={opts.maxCharts}
      />,
    )
    return { onSpecsChange }
  }

  it('renders a selectable checkbox for every candidate returned, including non-recommended ones', async () => {
    mockPost.mockResolvedValue({ data: { chart_specs: candidateSpecs } })
    renderCustomizer()
    expect(await screen.findByText('Sales by client')).toBeInTheDocument()
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(3)
  })

  it('pre-checks only the recommended charts and emits exactly those to onSpecsChange', async () => {
    const onSpecsChange = vi.fn()
    mockPost.mockResolvedValue({ data: { chart_specs: candidateSpecs } })
    renderCustomizer({ onSpecsChange })

    await waitFor(() => {
      expect(onSpecsChange).toHaveBeenLastCalledWith([
        expect.objectContaining({ title: 'Sales over time' }),
        expect.objectContaining({ title: 'Sales by month' }),
      ])
    })
    expect(screen.getAllByRole('checkbox').filter((c) => (c as HTMLInputElement).checked)).toHaveLength(2)
  })

  it('unchecking a chart removes it from the emitted specs', async () => {
    const onSpecsChange = vi.fn()
    mockPost.mockResolvedValue({ data: { chart_specs: candidateSpecs } })
    renderCustomizer({ onSpecsChange })

    await screen.findByText('Sales by client')
    await userEvent.click(screen.getAllByRole('checkbox')[0])

    await waitFor(() => {
      expect(onSpecsChange).toHaveBeenLastCalledWith([
        expect.objectContaining({ title: 'Sales by month' }),
      ])
    })
  })

  it('checking a non-recommended chart adds it to the emitted specs', async () => {
    const onSpecsChange = vi.fn()
    mockPost.mockResolvedValue({ data: { chart_specs: candidateSpecs } })
    renderCustomizer({ onSpecsChange })

    await screen.findByText('Sales by client')
    await userEvent.click(screen.getAllByRole('checkbox')[2])

    await waitFor(() => {
      expect(onSpecsChange).toHaveBeenLastCalledWith(
        expect.arrayContaining([expect.objectContaining({ title: 'Sales by client' })]),
      )
    })
  })

  it('shows a cap message and refuses the check when selection would exceed the plan limit', async () => {
    mockPost.mockResolvedValue({ data: { chart_specs: candidateSpecs } })
    renderCustomizer({ maxCharts: 2 })

    await screen.findByText('Sales by client')
    await userEvent.click(screen.getAllByRole('checkbox')[2])

    expect(
      screen.getByText('You can include up to 2 charts on your plan.'),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox').filter((c) => (c as HTMLInputElement).checked)).toHaveLength(2)
  })

  it('offers histogram as a selectable chart type', async () => {
    mockPost.mockResolvedValue({ data: { chart_specs: candidateSpecs } })
    renderCustomizer()
    const selects = await screen.findAllByRole('combobox')
    await userEvent.selectOptions(selects[0], 'histogram')
    const options = Array.from(selects[0].querySelectorAll('option')).map((o) => o.value)
    expect(options).toContain('histogram')
  })
})

describe('ChartCustomizer auto specs capture', () => {
  const autoSpecs: ChartSpec[] = [
    { x: 'date', y: 'sales', type: 'line', title: 'Sales over time', recommended: true },
    { x: 'date', y: 'sales', type: 'bar', title: 'Sales by month', recommended: true },
    { x: 'client', y: 'sales', type: 'bar', title: 'Sales by client', recommended: false },
  ]

  it('emits untouched recommended specs and selector from the response', async () => {
    const onAutoSpecsChange = vi.fn()
    mockPost.mockResolvedValue({ data: { chart_specs: autoSpecs, selector: 'ai' } })
    render(
      <ChartCustomizer
        uploadId="up-123"
        columnConfig={mockColumnConfig}
        onSpecsChange={vi.fn()}
        onAutoSpecsChange={onAutoSpecsChange}
      />,
    )

    await waitFor(() => {
      expect(onAutoSpecsChange).toHaveBeenLastCalledWith(
        [
          expect.objectContaining({ title: 'Sales over time' }),
          expect.objectContaining({ title: 'Sales by month' }),
        ],
        'ai',
      )
    })
  })

  it('defaults to rules selector when response omits it', async () => {
    const onAutoSpecsChange = vi.fn()
    mockPost.mockResolvedValue({ data: { chart_specs: autoSpecs } })
    render(
      <ChartCustomizer
        uploadId="up-123"
        columnConfig={mockColumnConfig}
        onSpecsChange={vi.fn()}
        onAutoSpecsChange={onAutoSpecsChange}
      />,
    )

    await waitFor(() => {
      expect(onAutoSpecsChange).toHaveBeenCalledWith(expect.any(Array), 'rules')
    })
  })
})
