import { useEffect } from 'react'

const AHREFS_KEY = 'mLGKDP/FwJbJKvdq+NYeyg'

function analyticsGranted(): boolean {
  const consent = window.getCkyConsent?.()
  return consent?.categories?.analytics === true
}

function injectAhrefs(): void {
  if (document.querySelector('script[data-ahrefs-loaded]')) return

  const script = document.createElement('script')
  script.async = true
  script.dataset.ahrefsLoaded = 'true'
  script.dataset.key = AHREFS_KEY
  script.src = 'https://analytics.ahrefs.com/analytics.js'
  const firstScript = document.getElementsByTagName('script')[0]
  firstScript?.parentNode?.insertBefore(script, firstScript)
}

export default function useCookieYesAhrefs() {
  useEffect(() => {
    if (analyticsGranted()) {
      injectAhrefs()
      return
    }

    const check = () => {
      if (analyticsGranted()) {
        injectAhrefs()
        clearInterval(interval)
        return true
      }
      return false
    }

    const onConsentUpdate = () => { check() }

    document.addEventListener('cookieyes_consent_update', onConsentUpdate)

    const t = setTimeout(check, 1000)
    const interval = setInterval(() => { if (check()) clearInterval(interval) }, 500)
    setTimeout(() => clearInterval(interval), 300000)

    return () => {
      document.removeEventListener('cookieyes_consent_update', onConsentUpdate)
      clearTimeout(t)
      clearInterval(interval)
    }
  }, [])
}
