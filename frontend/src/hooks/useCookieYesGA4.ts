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

let ga4Loaded = false

function loadGA4() {
  if (ga4Loaded || typeof window === 'undefined') return
  ga4Loaded = true

  window.dataLayer = window.dataLayer || []
  window.gtag = function gtag(...args: unknown[]) { window.dataLayer.push(args) }

  window.gtag('consent', 'default', {
    ad_storage: 'denied',
    analytics_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500,
  })

  window.gtag('js', new Date())
  window.gtag('config', 'G-0Z7ZKHB7PB')

  const script = document.createElement('script')
  script.async = true
  script.src = 'https://www.googletagmanager.com/gtag/js?id=G-0Z7ZKHB7PB'
  document.head.appendChild(script)
}

function analyticsGranted(): boolean {
  const consent = window.getCkyConsent?.()
  return consent?.categories?.analytics === true
}

function updateConsent() {
  if (typeof window.gtag !== 'function') return

  window.gtag('consent', 'update', {
    analytics_storage: 'granted',
  })
}

export default function useCookieYesGA4() {
  useEffect(() => {
    const check = () => {
      if (analyticsGranted()) {
        loadGA4()
        updateConsent()
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
