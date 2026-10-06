import { useEffect } from 'react'
import { isChunkLoadError, reloadOnce } from '@/lib/chunkReload'

export default function SentryFallback({ error }: { error?: unknown }) {
  // Chunk-load failures (stale hashed chunk after a deploy) auto-recover
  // with one guarded reload. The guard returns false when a reload already
  // happened within 10 seconds (truly missing file) — then the manual
  // "Refresh page" button below is the way out. No loop either way.
  const chunkError = isChunkLoadError(error)
  useEffect(() => {
    if (chunkError) {
      reloadOnce()
    }
  }, [chunkError])
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-paper px-6 text-center dark:bg-darkBg">
      <h1 className="font-display text-2xl font-bold text-ink dark:text-gray-100">Something went wrong</h1>
      <p className="max-w-md text-sm text-gray-500 dark:text-gray-400">An unexpected error occurred. Please refresh the page to continue.</p>
      <button
        onClick={() => window.location.reload()}
        className="rounded-lg bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
      >
        Refresh page
      </button>
    </div>
  )
}
