import { useEffect, useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

export function usePricingCTA() {
  const { isAuthenticated, initialize } = useAuthStore()
  useEffect(() => { initialize() }, [initialize])
  const [loading, setLoading] = useState<'pro' | 'agency' | null>(null)

  const handleCheckout = async (plan: 'pro' | 'agency') => {
    setLoading(plan)
    try {
      const resp = await api.post('/payments/checkout', { plan })
      const data = resp.data as { checkout_url: string }
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      } else {
        toast.success(`Upgraded to ${plan === 'pro' ? 'Pro' : 'Agency'}`)
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } }
      if (axiosErr.response?.status === 401) {
        window.location.href = '/settings?tab=billing'
        return
      }
      toast.error('Failed to start checkout. Please try again.')
      setLoading(null)
    }
  }

  return { isAuthenticated, loading, handleCheckout }
}
