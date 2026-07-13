import { useEffect } from 'react'

declare global {
  interface Window {
    dataLayer: unknown[]
    gtag: (...args: unknown[]) => void
    getCkyConsent?: () => {
      categories: Record<string, boolean>
    }
  }
}

function analyticsGranted(): boolean {
  const consent = window.getCkyConsent?.()
  return consent?.categories?.analytics === true
}

export default function useCookieYesGA4() {
  useEffect(() => {
    if (analyticsGranted()) {
      window.gtag('consent', 'update', {
        analytics_storage: 'granted',
      })
      return
    }

    const check = () => {
      if (analyticsGranted()) {
        window.gtag('consent', 'update', {
          analytics_storage: 'granted',
        })
        clearInterval(interval)
        return true
      }
      return false
    }

    const t = setTimeout(check, 500)
    const interval = setInterval(() => { if (check()) clearInterval(interval) }, 300)
    setTimeout(() => clearInterval(interval), 30000)

    return () => {
      clearTimeout(t)
      clearInterval(interval)
    }
  }, [])
}
