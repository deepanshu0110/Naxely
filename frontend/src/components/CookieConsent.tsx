import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

declare global {
  interface Window { dataLayer: unknown[]; gtag: (...args: unknown[]) => void }
}

const STORAGE_KEY = 'naxely-ga-consent'

function loadGA4() {
  if (typeof window === 'undefined') return

  window.dataLayer = window.dataLayer || []
  window.gtag = function gtag(...args: unknown[]) { window.dataLayer.push(args) }

  window.gtag('js', new Date())
  window.gtag('config', 'G-0Z7ZKHB7PB')

  const script = document.createElement('script')
  script.async = true
  script.src = 'https://www.googletagmanager.com/gtag/js?id=G-0Z7ZKHB7PB'
  document.head.appendChild(script)
}

function getStoredConsent(): boolean | null {
  try {
    const val = localStorage.getItem(STORAGE_KEY)
    if (val === 'accepted') return true
    if (val === 'rejected') return false
  } catch {}
  return null
}

function setConsent(granted: boolean) {
  try {
    localStorage.setItem(STORAGE_KEY, granted ? 'accepted' : 'rejected')
  } catch {}
}

export default function CookieConsent() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const consent = getStoredConsent()
    if (consent === true) {
      loadGA4()
    } else if (consent === null) {
      setVisible(true)
    }
  }, [])

  function accept() {
    setConsent(true)
    loadGA4()
    setVisible(false)
  }

  function reject() {
    setConsent(false)
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white/95 backdrop-blur-sm dark:border-gray-700 dark:bg-darkBg/95">
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-4 px-6 py-4 sm:flex-row sm:justify-between">
        <p className="text-center text-xs leading-relaxed text-ink/60 dark:text-paper/50 sm:text-left">
          We use essential cookies for authentication and session management.
          We also use Google Analytics to understand how the site is used — only if you consent.
          <br />
          See our{' '}
          <Link to="/privacy" className="text-amber-600 underline hover:text-amber-700">
            Privacy Policy
          </Link>{' '}
          for details.
        </p>
        <div className="flex shrink-0 gap-3">
          <button
            onClick={reject}
            className="rounded-lg border border-gray-300 px-4 py-2 text-xs font-medium text-ink/70 hover:bg-gray-100 dark:border-gray-600 dark:text-paper/60 dark:hover:bg-gray-800"
          >
            Reject All
          </button>
          <button
            onClick={accept}
            className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-medium text-white hover:bg-amber-700"
          >
            Accept All
          </button>
        </div>
      </div>
    </div>
  )
}
