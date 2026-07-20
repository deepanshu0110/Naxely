import { useEffect } from 'react'

declare global {
  interface Window {
    clarity?: ((...args: unknown[]) => void) & { q?: unknown[][] }
  }
}

const CLARITY_ID = 'xlavj40yjz'

function analyticsGranted(): boolean {
  const consent = window.getCkyConsent?.()
  return consent?.categories?.analytics === true
}

function injectClarity(): void {
  if (window.clarity) return

  window.clarity = function (...args: unknown[]) {
    (window.clarity!.q = window.clarity!.q || []).push(args)
  } as unknown as (...args: unknown[]) => void

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.clarity.ms/tag/${CLARITY_ID}`
  const firstScript = document.getElementsByTagName('script')[0]
  firstScript?.parentNode?.insertBefore(script, firstScript)
}

export default function useCookieYesClarity() {
  useEffect(() => {
    if (analyticsGranted()) {
      injectClarity()
      return
    }

    const check = () => {
      if (analyticsGranted()) {
        injectClarity()
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
