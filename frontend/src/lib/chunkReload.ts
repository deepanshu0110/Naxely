/**
 * Auto-recovery for stale-chunk failures.
 *
 * When a deploy replaces hashed chunks, a tab holding old HTML can request
 * a chunk that no longer exists (e.g. `Failed to fetch dynamically
 * imported module`). The fix is a single reload, which fetches fresh HTML
 * (HTML is `max-age=0, must-revalidate`, never long-cached). The 10-second
 * guard prevents a reload loop when a file is truly missing.
 *
 * Every browser/DOM access is guarded: vite-react-ssg executes this module
 * in Node at build time.
 */

const RELOAD_KEY = 'chunk-reload-at'
const RELOAD_COOLDOWN_MS = 10_000

const CHUNK_ERROR_PATTERNS = [
  'failed to fetch dynamically imported module', // Chrome
  'error loading dynamically imported module', // Firefox
  'importing a module script failed', // Safari
]

export function isChunkLoadError(error: unknown): boolean {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
        ? error
        : ''
  if (!message) return false
  const lower = message.toLowerCase()
  return CHUNK_ERROR_PATTERNS.some((p) => lower.includes(p))
}

let lastReloadInMemory = 0

export function reloadOnce(): boolean {
  if (typeof window === 'undefined') return false
  const now = Date.now()
  // Same-load dedupe: preloadError and the ErrorBoundary can both fire for
  // one failure. Works even when sessionStorage is unavailable.
  if (now - lastReloadInMemory < RELOAD_COOLDOWN_MS) return false
  lastReloadInMemory = now
  try {
    const last = Number(window.sessionStorage.getItem(RELOAD_KEY))
    if (Number.isFinite(last) && now - last < RELOAD_COOLDOWN_MS) {
      return false
    }
  } catch {
    // sessionStorage unavailable (private mode, disabled cookies):
    // still reload once per page load rather than risk a loop.
    try {
      window.sessionStorage.setItem(RELOAD_KEY, String(now))
    } catch {
      // ignore
    }
    window.location.reload()
    return true
  }
  try {
    window.sessionStorage.setItem(RELOAD_KEY, String(now))
  } catch {
    // ignore storage write failures; the reload itself is what matters
  }
  window.location.reload()
  return true
}
