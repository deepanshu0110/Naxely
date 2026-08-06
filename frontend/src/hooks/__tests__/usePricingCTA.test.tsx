import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

const mockPost = vi.hoisted(() => vi.fn())
vi.mock('@/lib/axios', () => ({ default: { post: mockPost } }))

const mockToast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))
vi.mock('react-hot-toast', () => ({ default: mockToast }))

const mockInitialize = vi.hoisted(() => vi.fn())
vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
    initialize: mockInitialize,
  }),
}))

import { usePricingCTA } from '../usePricingCTA'

const originalLocation = window.location

beforeEach(() => {
  vi.clearAllMocks()
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: { href: '' },
  })
})

afterEach(() => {
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: originalLocation,
  })
})

describe('usePricingCTA', () => {
  it('exposes isAuthenticated from the store, starts with no loading plan, and initializes on mount', () => {
    const { result } = renderHook(() => usePricingCTA())

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.loading).toBeNull()
    expect(mockInitialize).toHaveBeenCalled()
  })

  it('posts the plan and redirects to the returned checkout_url', async () => {
    mockPost.mockResolvedValueOnce({ data: { checkout_url: 'https://checkout.example.com/pro' } })
    const { result } = renderHook(() => usePricingCTA())

    await act(async () => {
      await result.current.handleCheckout('pro')
    })

    expect(mockPost).toHaveBeenCalledWith('/payments/checkout', { plan: 'pro' })
    expect(window.location.href).toBe('https://checkout.example.com/pro')
    expect(mockToast.success).not.toHaveBeenCalled()
    expect(result.current.loading).toBe('pro')
  })

  it('shows a success toast when checkout returns no URL', async () => {
    mockPost.mockResolvedValueOnce({ data: {} })
    const { result } = renderHook(() => usePricingCTA())

    await act(async () => {
      await result.current.handleCheckout('agency')
    })

    expect(mockPost).toHaveBeenCalledWith('/payments/checkout', { plan: 'agency' })
    expect(mockToast.success).toHaveBeenCalledWith('Upgraded to Agency')
    expect(mockToast.error).not.toHaveBeenCalled()
    expect(result.current.loading).toBe('agency')
  })

  it('redirects to billing settings on a 401 response', async () => {
    mockPost.mockRejectedValueOnce({ response: { status: 401 } })
    const { result } = renderHook(() => usePricingCTA())

    await act(async () => {
      await result.current.handleCheckout('pro')
    })

    expect(window.location.href).toBe('/settings?tab=billing')
    expect(mockToast.error).not.toHaveBeenCalled()
  })

  it('shows an error toast and resets loading on any other failure', async () => {
    mockPost.mockRejectedValueOnce(new Error('network down'))
    const { result } = renderHook(() => usePricingCTA())

    await act(async () => {
      await result.current.handleCheckout('pro')
    })

    expect(mockToast.error).toHaveBeenCalledWith('Failed to start checkout. Please try again.')
    expect(result.current.loading).toBeNull()
    expect(window.location.href).toBe('')
  })
})
