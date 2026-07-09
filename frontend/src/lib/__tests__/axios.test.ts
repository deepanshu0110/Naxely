import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import toast from 'react-hot-toast'

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn() },
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: { getState: vi.fn() },
}))

import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'

describe('axios request interceptor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('adds Authorization header when a session token exists', () => {
    vi.mocked(useAuthStore.getState).mockReturnValue({
      session: { access_token: 'my-jwt-token' },
    } as never)

    const handler = (api.interceptors.request as any).handlers[0].fulfilled
    const config = handler({ headers: {} })
    expect(config.headers.Authorization).toBe('Bearer my-jwt-token')
  })

  it('does NOT add Authorization header when session is null', () => {
    vi.mocked(useAuthStore.getState).mockReturnValue({
      session: null,
    } as never)

    const handler = (api.interceptors.request as any).handlers[0].fulfilled
    const config = handler({ headers: {} })
    expect(config.headers.Authorization).toBeUndefined()
  })
})

describe('axios response interceptor — unwrap', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('unwraps { success: true, data: [...] } to the inner array', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const response = { data: { success: true, data: [{ id: 1 }, { id: 2 }] } }
    const result = handler(response)
    expect(result.data).toEqual([{ id: 1 }, { id: 2 }])
  })

  it('unwraps { success: true, data: { single: "object" } } to the inner object', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const response = { data: { success: true, data: { single: 'object' } } }
    const result = handler(response)
    expect(result.data).toEqual({ single: 'object' })
  })

  it('does NOT unwrap a plain array (no success wrapper)', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const arr = [1, 2, 3]
    const response = { data: arr }
    const result = handler(response)
    expect(result.data).toBe(arr)
  })

  it('does NOT unwrap { success: false, data: [...] }', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const body = { success: false, data: [{ id: 1 }] }
    const response = { data: body }
    const result = handler(response)
    expect(result.data).toBe(body)
  })

  it('does NOT unwrap { success: true } without data field', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const body = { success: true }
    const response = { data: body }
    const result = handler(response)
    expect(result.data).toBe(body)
  })

  it('does NOT unwrap a non-object response (string)', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const response = { data: 'plain string' }
    const result = handler(response)
    expect(result.data).toBe('plain string')
  })

  it('does NOT unwrap a null response body', () => {
    const handler = (api.interceptors.response as any).handlers[0].fulfilled
    const response = { data: null }
    const result = handler(response)
    expect(result.data).toBeNull()
  })
})

describe('axios response interceptor — error handling', () => {
  let originalLocation: Location

  beforeEach(() => {
    vi.clearAllMocks()
    originalLocation = window.location
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    })
    vi.spyOn(window, 'dispatchEvent')
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    })
  })

  it('redirects to /login on 401', () => {
    const handler = (api.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 401, data: {} } }

    handler(error).catch(() => {})

    expect(window.location.href).toBe('/login')
  })

  it('dispatches upgrade-needed event and shows toast on 402', () => {
    const handler = (api.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 402, data: { message: 'Plan limit reached' } } }

    handler(error).catch(() => {})

    expect(window.dispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'upgrade-needed' }),
    )
    expect(toast.error).toHaveBeenCalledWith(
      'Plan limit reached — Upgrade your plan to continue.',
      expect.any(Object),
    )
  })

  it('shows toast with message field on generic error', () => {
    const handler = (api.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 500, data: { message: 'Server error' } } }

    handler(error).catch(() => {})

    expect(toast.error).toHaveBeenCalledWith('Server error', expect.any(Object))
  })

  it('shows toast with detail on generic error when no message field', () => {
    const handler = (api.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 500, data: { detail: 'Internal failure' } } }

    handler(error).catch(() => {})

    expect(toast.error).toHaveBeenCalledWith('Internal failure', expect.any(Object))
  })

  it('falls back to default message when response data has no recognizable field', () => {
    const handler = (api.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 500, data: {} } }

    handler(error).catch(() => {})

    expect(toast.error).toHaveBeenCalledWith(
      'Something went wrong. Please try again.',
      expect.any(Object),
    )
  })

  it('re-throws the error for the caller to handle', async () => {
    const handler = (api.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 500, data: { message: 'oops' } } }

    await expect(handler(error)).rejects.toBe(error)
  })
})
