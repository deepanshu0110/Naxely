import { useEffect, useState } from 'react'
import { Check, Loader2 } from 'lucide-react'

interface GeneratingLoaderProps {
  currentStep: string
  progress: number
  isPolling: boolean
  timeoutMessage: string | null
}

const steps = [
  { key: 'parsing', label: 'Parsing your data...' },
  { key: 'charts', label: 'Generating charts...' },
  { key: 'ai', label: 'Writing AI insights...' },
  { key: 'pdf', label: 'Building your PDF...' },
]

function stepIndexFromCurrent(currentStep: string): number {
  if (!currentStep) return 0
  const lower = currentStep.toLowerCase()
  if (lower.includes('pars') || lower.includes('data')) return 0
  if (lower.includes('chart')) return 1
  if (lower.includes('ai') || lower.includes('insight')) return 2
  if (lower.includes('pdf') || lower.includes('build')) return 3
  return 0
}

export default function GeneratingLoader({ currentStep, progress, isPolling, timeoutMessage }: GeneratingLoaderProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!isPolling) return
    const interval = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(interval)
  }, [isPolling])

  const activeIdx = stepIndexFromCurrent(currentStep)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-paper dark:bg-ink">
      <div className="w-full max-w-md px-6 text-center">
        <h2 className="mb-2 text-2xl font-bold text-gray-900 dark:text-gray-100">Generating your report</h2>
        <p className="mb-10 text-sm text-gray-500 dark:text-gray-400">This usually takes 30–90 seconds</p>

        <div className="mb-8 space-y-4">
          {steps.map((step, idx) => {
            const completed = idx < activeIdx
            const active = idx === activeIdx && isPolling

            return (
              <div key={step.key} className="flex items-center gap-4">
                <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 ${
                  completed
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/30'
                    : active
                      ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/30'
                      : 'border-gray-300 dark:border-gray-600'
                }`}>
                  {completed ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : active ? (
                    <Loader2 className="h-4 w-4 animate-spin text-amber-500" />
                  ) : (
                    <span className="text-xs text-gray-400 dark:text-gray-500">{idx + 1}</span>
                  )}
                </div>
                <span
                  className={`text-sm ${
                    completed
                      ? 'font-medium text-green-600 dark:text-green-400'
                      : active
                        ? 'font-medium text-amber-600 dark:text-amber-400'
                        : 'text-gray-400 dark:text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>

        {isPolling && (
          <div className="space-y-2">
            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-2 rounded-full bg-amber-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              {elapsed > 0 ? `${elapsed}s elapsed` : 'Starting...'}
            </p>
          </div>
        )}

        {timeoutMessage && (
          <div className="mt-6 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-900/30">
            <p className="text-sm text-yellow-700 dark:text-yellow-400">{timeoutMessage}</p>
          </div>
        )}
      </div>
    </div>
  )
}
