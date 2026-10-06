import * as Sentry from '@sentry/react'
import { ViteReactSSG } from 'vite-react-ssg'
import { reloadOnce } from './lib/chunkReload'
import { routes } from './App'
import './index.css'
import './assets/google-fonts.css'

if (import.meta.env.PROD && !import.meta.env.SSR) {
  Sentry.init({
    dsn: 'https://bf67d0529321de1ce6d6ec3503bbf087@o4511461891637248.ingest.de.sentry.io/4511981668139088',
  })
}

// Recover from stale-chunk preload failures with a single guarded reload.
// Browser only: this module also executes in Node during SSG prerender.
if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
  window.addEventListener('vite:preloadError', (event) => {
    if (reloadOnce()) {
      event.preventDefault()
    }
  })
}

export const createRoot = ViteReactSSG({ routes })
