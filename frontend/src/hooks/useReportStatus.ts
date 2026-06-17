import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useReportStore } from '@/store/reportStore'
import type { GenerationStatus } from '@/types/report'

interface UseReportStatusReturn {
  progress: number
  currentStep: string
  isPolling: boolean
  timeoutMessage: string | null
  startPolling: (reportId: string) => void
}

const MAX_POLLS = 30
const POLL_INTERVAL = 3000

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

export function useReportStatus(): UseReportStatusReturn {
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [isPolling, setIsPolling] = useState(false)
  const [timeoutMessage, setTimeoutMessage] = useState<string | null>(null)
  const cancelledRef = useRef(false)
  const navigate = useNavigate()
  const pollStatus = useReportStore((s) => s.pollStatus)

  const startPolling = useCallback(
    (reportId: string) => {
      cancelledRef.current = false
      setIsPolling(true)
      setTimeoutMessage(null)

      const poll = async () => {
        for (let i = 0; i < MAX_POLLS; i++) {
          if (cancelledRef.current) {
            setIsPolling(false)
            return
          }

          await sleep(POLL_INTERVAL)

          try {
            const data: GenerationStatus = await pollStatus(reportId)

            if (data.status === 'completed') {
              setIsPolling(false)
              if (data.error_message) {
                toast.error(data.error_message)
              }
              navigate(`/report/${reportId}`)
              return
            }

            if (data.status === 'failed') {
              setIsPolling(false)
              toast.error(data.error_message ?? 'Report generation failed')
              navigate('/dashboard')
              return
            }

            setProgress(data.progress_percent)
            if (data.current_step) setCurrentStep(data.current_step)
          } catch {
            setIsPolling(false)
            toast.error('Failed to check report status')
            navigate('/dashboard')
            return
          }
        }

        setIsPolling(false)
        setTimeoutMessage('Report is taking longer than expected. Check back in a few minutes.')
      }

      poll()
    },
    [pollStatus, navigate],
  )

  return { progress, currentStep, isPolling, timeoutMessage, startPolling }
}
