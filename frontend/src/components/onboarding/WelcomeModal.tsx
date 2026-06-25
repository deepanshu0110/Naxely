import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import Button from '@/components/ui/Button'
import type { UploadResult } from '@/types/report'

interface WelcomeModalProps {
  onClose: () => void
}

export default function WelcomeModal({ onClose }: WelcomeModalProps) {
  const navigate = useNavigate()
  const fetchProfile = useAuthStore((s) => s.fetchProfile)
  const [loading, setLoading] = useState<'sample' | 'upload' | null>(null)

  const handleSampleData = async () => {
    setLoading('sample')
    try {
      const { data } = await api.post<UploadResult>('/reports/sample-upload')
      await api.post('/auth/complete-onboarding')
      navigate('/report/new', { state: { uploadResult: data } })
    } catch {
      setLoading(null)
    }
  }

  const handleUploadOwn = async () => {
    setLoading('upload')
    try {
      await api.post('/auth/complete-onboarding')
      navigate('/report/new')
    } catch {
      setLoading(null)
    }
  }

  const handleSkip = async () => {
    try {
      await api.post('/auth/skip-onboarding')
      await fetchProfile()
      onClose()
    } catch {
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl border border-gray-200 bg-paper p-8 text-center shadow-2xl dark:border-gray-700 dark:bg-darkBg">
        <h1 className="font-display text-3xl font-bold text-ink dark:text-gray-100">
          Welcome to Naxely
        </h1>

        <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
          Turn your CSV data into a branded client report in 30 seconds.
        </p>

        <div className="mt-8 flex flex-col gap-3">
          <Button
            variant="primary"
            className="w-full"
            loading={loading === 'sample'}
            onClick={handleSampleData}
          >
            Try with sample data →
          </Button>

          <Button
            variant="outline"
            className="w-full"
            loading={loading === 'upload'}
            onClick={handleUploadOwn}
          >
            Upload my own CSV
          </Button>
        </div>

        <button
          onClick={handleSkip}
          className="mx-auto mt-6 block text-sm text-gray-400 underline-offset-2 hover:text-gray-600 hover:underline dark:text-gray-500 dark:hover:text-gray-300"
        >
          Skip for now
        </button>
      </div>
    </div>
  )
}
