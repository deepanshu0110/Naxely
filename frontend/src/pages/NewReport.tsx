import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import Sidebar from '@/components/layout/Sidebar'
import Button from '@/components/ui/Button'
import FileUpload from '@/components/report/FileUpload'
import ColumnMapper from '@/components/report/ColumnMapper'
import ReportConfigForm from '@/components/report/ReportConfig'
import GeneratingLoader from '@/components/report/GeneratingLoader'
import { useReportStatus } from '@/hooks/useReportStatus'
import { useReportStore } from '@/store/reportStore'
import { useAuthStore } from '@/store/authStore'
import type { UploadResult, ColumnConfig, ReportConfig as ReportConfigType } from '@/types/report'

const STEP_LABELS = ['Upload', 'Map', 'Configure', 'Generate']

export default function NewReport() {
  const [currentStep, setCurrentStep] = useState(1)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [columnConfig, setColumnConfig] = useState<ColumnConfig[]>([])
  const [reportTitle, setReportTitle] = useState('')
  const [reportTone, setReportTone] = useState('professional')
  const [reportSections, setReportSections] = useState<string[]>(['charts', 'kpi_overview', 'data_table'])
  const [reportDateRange, setReportDateRange] = useState<{ from: string; to: string } | undefined>(undefined)
  const [generating, setGenerating] = useState(false)

  const generateReport = useReportStore((s) => s.generateReport)
  const user = useAuthStore((s) => s.user)
  const { progress, currentStep: statusStep, isPolling, timeoutMessage, startPolling } = useReportStatus()

  const handleUploadComplete = useCallback((result: UploadResult) => {
    setUploadResult(result)
    setCurrentStep(2)
  }, [])

  const handleColumnConfigChange = useCallback((config: ColumnConfig[]) => {
    setColumnConfig(config)
  }, [])

  const handleConfigChange = useCallback(
    (config: { title: string; dateFrom: string; dateTo: string; tone: string; sections: string[] }) => {
      setReportTitle(config.title)
      setReportTone(config.tone)
      setReportSections(config.sections)
      setReportDateRange(
        config.dateFrom && config.dateTo ? { from: config.dateFrom, to: config.dateTo } : undefined,
      )
    },
    [],
  )

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return !!uploadResult
      case 2:
        return columnConfig.some((c) => c.include)
      case 3:
        return reportTitle.trim().length > 0
      default:
        return false
    }
  }

  const handleGenerate = async () => {
    if (!uploadResult) return
    setGenerating(true)

    const payload: ReportConfigType = {
      upload_id: uploadResult.upload_id,
      title: reportTitle,
      template_type: 'marketing',
      tone: reportTone,
      sections: reportSections,
      date_range: reportDateRange,
      column_config: columnConfig,
      workspace_id: null,
    }

    if (user?.tier !== 'free') {
      payload.brand = {
        company_name: user?.company_name ?? '',
        prepared_by: user?.full_name ?? '',
      }
    }

    try {
      const id = await generateReport(payload)
      setCurrentStep(4)
      startPolling(id)
    } catch {
      toast.error('Failed to generate report')
      setGenerating(false)
    }
  }

  if (generating || isPolling) {
    return (
      <GeneratingLoader
        currentStep={statusStep}
        progress={progress}
        isPolling={isPolling}
        timeoutMessage={timeoutMessage}
      />
    )
  }

  return (
    <div className="flex h-screen bg-slate dark:bg-ink">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <div className="mb-8">
            <h1 className="font-display text-2xl font-bold text-ink dark:text-gray-100">New Report</h1>
          </div>

          <div className="mb-8 flex items-center justify-center">
            {STEP_LABELS.map((label, idx) => {
              const stepNum = idx + 1
              const isActive = stepNum === currentStep
              const isCompleted = stepNum < currentStep
              return (
                <div key={label} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                        isActive
                          ? 'bg-indigo-500 text-white'
                          : isCompleted
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                      }`}
                    >
                      {isCompleted ? '✓' : stepNum}
                    </div>
                    <span
                      className={`mt-1 text-xs ${
                        isActive ? 'font-medium text-indigo-600' : 'text-gray-400 dark:text-gray-500'
                      }`}
                    >
                      {label}
                    </span>
                  </div>
                  {idx < STEP_LABELS.length - 1 && <div className="mx-4 h-0.5 w-12 bg-gray-200 dark:bg-gray-700" />}
                </div>
              )
            })}
          </div>

          <div className="rounded-xl border border-gray-200 bg-paper p-6 shadow-sm dark:border-gray-700 dark:bg-ink">
            {currentStep === 1 && (
              <div>
                <h2 className="mb-4 text-lg font-semibold text-ink dark:text-gray-100">Upload Data</h2>
                <FileUpload onUploadComplete={handleUploadComplete} />
              </div>
            )}

            {currentStep === 2 && uploadResult && (
              <div>
                <h2 className="mb-4 text-lg font-semibold text-ink dark:text-gray-100">Map Columns</h2>
                <ColumnMapper columns={uploadResult.columns} onChange={handleColumnConfigChange} />
              </div>
            )}

            {currentStep === 3 && (
              <div>
                <h2 className="mb-4 text-lg font-semibold text-ink dark:text-gray-100">Configure Report</h2>
                <ReportConfigForm onConfigChange={handleConfigChange} />
              </div>
            )}

            <div className="mt-8 flex items-center justify-between border-t border-gray-200 pt-4 dark:border-gray-700">
              <Button
                variant="ghost"
                onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}
                disabled={currentStep === 1}
              >
                Back
              </Button>
              {currentStep < 3 ? (
                <Button onClick={() => setCurrentStep((s) => s + 1)} disabled={!canProceed()}>
                  Next
                </Button>
              ) : currentStep === 3 ? (
                <Button onClick={handleGenerate} disabled={!canProceed()} loading={generating}>
                  Generate Report
                </Button>
              ) : null}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
