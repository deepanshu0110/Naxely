import { create } from 'zustand'
import type { User } from '@/types/user'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import api from '@/lib/axios'
import type { AuthVerifyResponse } from '@/types/api'

interface AuthStore {
  user: User | null
  session: Session | null
  isLoading: boolean
  isAuthenticated: boolean
  initialize: () => Promise<void>
  loginWithGoogle: () => Promise<void>
  loginWithEmail: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchProfile: () => Promise<void>
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  session: null,
  isLoading: true,
  isAuthenticated: false,

  initialize: async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session) {
      set({ session, isAuthenticated: true, isLoading: false })
      get().fetchProfile()
    } else {
      set({ session: null, isAuthenticated: false, isLoading: false })
    }

    supabase.auth.onAuthStateChange((_event, newSession) => {
      set({ session: newSession, isAuthenticated: !!newSession })
      if (newSession) {
        get().fetchProfile()
      } else {
        set({ user: null })
      }
    })
  },

  loginWithGoogle: async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin + '/auth/callback',
      },
    })
  },

  loginWithEmail: async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  },

  logout: async () => {
    await supabase.auth.signOut()
    set({ user: null, session: null, isAuthenticated: false })
  },

  fetchProfile: async () => {
    try {
      const { data } = await api.get<AuthVerifyResponse>('/auth/verify')
      set({ user: data })
    } catch {
      set({ user: null, isAuthenticated: false, session: null })
    }
  },
}))
