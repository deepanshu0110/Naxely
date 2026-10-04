import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

/**
 * Guard: every public, static, indexable route in App.tsx must be listed in
 * vite.config.ts `includedRoutes`, otherwise it silently falls back to
 * shell.html and crawlers see the homepage head (no title/meta/h1).
 * This exact failure mode dropped /login and /signup from prerendering
 * without any build warning (Bing flags, Oct 2026).
 *
 * Routes intentionally excluded (documented, not accidental):
 */
const INTENTIONALLY_EXCLUDED = new Set([
  // Transient OAuth/token flows — must never be prerendered or indexed.
  '/auth/callback',
  '/auth/reset-password',
  // Auth-gated app pages — user-specific, served behind login, noindexed.
  '/dashboard',
  '/report/new',
  '/scheduled-reports',
  '/templates',
  '/settings',
  '/settings/api-key',
  '/settings/billing',
  '/settings/branding',
])

function readRepoFile(rel: string): string {
  return fs.readFileSync(path.join(process.cwd(), rel), 'utf-8')
}

describe('SSG route coverage', () => {
  it('every static public route in App.tsx is in vite.config includedRoutes', () => {
    const appSrc = readRepoFile('src/App.tsx')
    const viteConfig = readRepoFile('vite.config.ts')

    const routePaths = [...appSrc.matchAll(/path:\s*'([^']+)'/g)].map((m) => m[1])
    expect(routePaths.length).toBeGreaterThan(0)

    const includedBlock = viteConfig.split('includedRoutes')[1]
    const included = new Set(
      [...includedBlock.matchAll(/'(\/[^']*)'/g)].map((m) => m[1]),
    )

    const missing = [...new Set(routePaths)].filter((p) => {
      if (p.includes(':') || p === '*') return false // dynamic/wildcard: can't prerender
      if (INTENTIONALLY_EXCLUDED.has(p)) return false
      return !included.has(p)
    })

    expect(missing).toEqual([])
  })
})
