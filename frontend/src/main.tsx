import * as Sentry from '@sentry/react'
import { ViteReactSSG } from 'vite-react-ssg'
import { routes } from './App'
import './index.css'
import './assets/google-fonts.css'

if (import.meta.env.PROD && !import.meta.env.SSR) {
  Sentry.init({
    dsn: 'https://bf67d0529321de1ce6d6ec3503bbf087@o4511461891637248.ingest.de.sentry.io/4511981668139088',
  })
}

export const createRoot = ViteReactSSG({ routes })
