import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)

if (typeof window !== 'undefined') (window as any).__supabaseCacheBust = '2026-08-24-mobile-nav-fix'
