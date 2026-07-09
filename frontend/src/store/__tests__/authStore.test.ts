import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore } from '@/store/authStore'

const {
  mockGetSession,
  mockOnAuthStateChange,
  mockSignInWithPassword,
  mockSignInWithOAuth,
  mockSignOut,
  mockResetPasswordForEmail,
  mockUpdateUser,
} = vi.hoisted(() => ({
  mockGetSession: vi.fn(),
  mockOnAuthStateChange: vi.fn(() => ({
    data: { subscription: { unsubscribe: vi.fn() } },
  })),
  mockSignInWithPassword: vi.fn(),
  mockSignInWithOAuth: vi.fn(),
  mockSignOut: vi.fn(),
  mockResetPasswordForEmail: vi.fn(),
  mockUpdateUser: vi.fn(),
}))

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: mockOnAuthStateChange,
      signInWithPassword: mockSignInWithPassword,
      signInWithOAuth: mockSignInWithOAuth,
      signOut: mockSignOut,
      resetPasswordForEmail: mockResetPasswordForEmail,
      updateUser: mockUpdateUser,
    },
  },
}))

const mockApiGet = vi.hoisted(() => vi.fn())

vi.mock('@/lib/axios', () => ({
  default: {
    get: mockApiGet,
  },
}))

function resetStore() {
  useAuthStore.setState({
    user: null,
    session: null,
    isLoading: false,
    isAuthenticated: false,
  })
}

function setBypassAuth(val: string) {
  import.meta.env.VITE_BYPASS_AUTH = val
}

describe('authStore — initial state', () => {
  beforeEach(() => {
    resetStore()
  })

  it('starts with null user, null session, not authenticated', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.session).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})

describe('authStore — loginWithGoogle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls supabase signInWithOAuth with Google provider', async () => {
    mockSignInWithOAuth.mockResolvedValue({ data: {}, error: null })

    await useAuthStore.getState().loginWithGoogle()

    expect(mockSignInWithOAuth).toHaveBeenCalledWith({
      provider: 'google',
      options: { redirectTo: expect.stringContaining('/auth/callback') },
    })
  })
})

describe('authStore — sendPasswordResetEmail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls supabase resetPasswordForEmail with email', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ data: {}, error: null })

    await useAuthStore.getState().sendPasswordResetEmail('test@test.com')

    expect(mockResetPasswordForEmail).toHaveBeenCalledWith('test@test.com', {
      redirectTo: expect.stringContaining('/auth/reset-password'),
    })
  })

  it('throws when resetPasswordForEmail returns an error', async () => {
    mockResetPasswordForEmail.mockResolvedValue({
      data: {},
      error: new Error('User not found'),
    })

    await expect(
      useAuthStore.getState().sendPasswordResetEmail('test@test.com'),
    ).rejects.toThrow('User not found')
  })
})

describe('authStore — updatePassword', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls supabase updateUser with new password', async () => {
    mockUpdateUser.mockResolvedValue({ data: {}, error: null })

    await useAuthStore.getState().updatePassword('newPass123')

    expect(mockUpdateUser).toHaveBeenCalledWith({ password: 'newPass123' })
  })

  it('throws when updateUser returns an error', async () => {
    mockUpdateUser.mockResolvedValue({
      data: {},
      error: new Error('Weak password'),
    })

    await expect(
      useAuthStore.getState().updatePassword('short'),
    ).rejects.toThrow('Weak password')
  })
})

describe('authStore — loginWithEmail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls supabase signInWithPassword with email and password', async () => {
    mockSignInWithPassword.mockResolvedValue({ data: {}, error: null })

    await useAuthStore.getState().loginWithEmail('test@test.com', 'password123')

    expect(mockSignInWithPassword).toHaveBeenCalledWith({
      email: 'test@test.com',
      password: 'password123',
    })
  })

  it('throws when signInWithPassword returns an error', async () => {
    mockSignInWithPassword.mockResolvedValue({
      data: {},
      error: new Error('Invalid login credentials'),
    })

    await expect(
      useAuthStore.getState().loginWithEmail('test@test.com', 'wrong'),
    ).rejects.toThrow('Invalid login credentials')
  })
})

describe('authStore — logout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({
      user: { id: 'u1', email: 'a@b.com' } as any,
      session: { access_token: 'tok' } as any,
      isAuthenticated: true,
    })
  })

  it('calls supabase signOut and clears state', async () => {
    mockSignOut.mockResolvedValue({ error: null })

    await useAuthStore.getState().logout()

    expect(mockSignOut).toHaveBeenCalled()
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.session).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})

describe('authStore — fetchProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
  })

  it('calls /auth/verify and sets user on success', async () => {
    const profile = { id: 'u1', email: 'a@b.com', full_name: 'Alice' }
    mockApiGet.mockResolvedValue({ data: profile })

    await useAuthStore.getState().fetchProfile()

    expect(mockApiGet).toHaveBeenCalledWith('/auth/verify')
    expect(useAuthStore.getState().user).toEqual(profile)
  })

  it('clears auth state on API failure', async () => {
    useAuthStore.setState({
      user: { id: 'u1' } as any,
      session: { access_token: 'tok' } as any,
      isAuthenticated: true,
    })

    mockApiGet.mockRejectedValue(new Error('Network error'))

    await useAuthStore.getState().fetchProfile()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.session).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})

describe('authStore — initialize', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetStore()
    setBypassAuth('false')
  })

  it('sets isAuthenticated=false when no session exists', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } })

    await useAuthStore.getState().initialize()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.isLoading).toBe(false)
    expect(state.session).toBeNull()
  })

  it('sets isAuthenticated=true and fetches profile when session exists', async () => {
    const fakeSession = { access_token: 'tok', user: { id: 'u1' } }
    mockGetSession.mockResolvedValue({ data: { session: fakeSession } })
    const profile = { id: 'u1', email: 'a@b.com', full_name: 'Bob' }
    mockApiGet.mockResolvedValue({ data: profile })

    await useAuthStore.getState().initialize()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.isLoading).toBe(false)
    expect(state.session).toBe(fakeSession)
    expect(mockApiGet).toHaveBeenCalledWith('/auth/verify')
  })

  it('subscribes to onAuthStateChange', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } })

    await useAuthStore.getState().initialize()

    expect(mockOnAuthStateChange).toHaveBeenCalled()
  })

  it('bypass-auth mode sets dev user and skips supabase calls', async () => {
    setBypassAuth('true')

    await useAuthStore.getState().initialize()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.isLoading).toBe(false)
    expect(state.user?.id).toBe('dev')
    expect(state.user?.email).toBe('dev@test.com')
    expect(mockGetSession).not.toHaveBeenCalled()
  })
})
