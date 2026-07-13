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

export default function useCookieYesGA4() {
  useEffect(() => {
    const check = () => {
      if (analyticsGranted()) {
        loadGA4()
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
