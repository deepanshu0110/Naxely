import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'

export default function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        navigate('/dashboard')
      }
    })
    return () => data.subscription.unsubscribe()
  }, [navigate])

  return (
    <div className="flex h-screen items-center justify-center bg-paper dark:bg-darkBg">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-500" />
        <p className="text-base text-gray-600 dark:text-gray-400">Signing you in...</p>
      </div>
    </div>
  )
}
