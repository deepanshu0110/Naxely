import { useState, useCallback, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'
import Sidebar from '@/components/layout/Sidebar'
import Button from '@/components/ui/Button'
import FileUpload from '@/components/report/FileUpload'
import ColumnMapper from '@/components/report/ColumnMapper'
import ReportConfigForm from '@/components/report/ReportConfig'
import GeneratingLoader from '@/components/report/GeneratingLoader'
import ChartCustomizer from '@/components/report/ChartCustomizer'
import api from '@/lib/axios'
import { useReportStatus } from '@/hooks/useReportStatus'
import { useReportStore } from '@/store/reportStore'
import { useAuthStore } from '@/store/authStore'
import type { UploadResult, ColumnConfig, ChartSpec, ReportConfig as ReportConfigType } from '@/types/report'
import type { Template } from '@/types/api'

const STEP_LABELS = ['Upload', 'Map', 'Configure', 'Charts', 'Generate']

export default function NewReport() {
  const [currentStep, setCurrentStep] = useState(1)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [columnConfig, setColumnConfig] = useState<ColumnConfig[]>([])
  const [reportTitle, setReportTitle] = useState('')
  const [reportTone, setReportTone] = useState('professional')
  const [reportSections, setReportSections] = useState<string[]>(['charts', 'kpi_overview', 'data_table'])
  const [reportDateRange, setReportDateRange] = useState<{ from: string; to: string } | undefined>(undefined)
  const [reportBrand, setReportBrand] = useState<{ company_name?: string; prepared_by?: string } | null>(null)
  const [chartSpecs, setChartSpecs] = useState<ChartSpec[]>([])
  const [generating, setGenerating] = useState(false)
  const [sourceType, setSourceType] = useState<'csv' | 'sheets'>('csv')
  const [sheetsUrl, setSheetsUrl] = useState('')
  const [sheetsConnecting, setSheetsConnecting] = useState(false)
  const [serviceAccountEmail, setServiceAccountEmail] = useState<string | null>(null)
  const [sheetsConfigLoading, setSheetsConfigLoading] = useState(false)
  const sheetsConfigFetched = useRef(false)
  const [templates, setTemplates] = useState<Template[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const templatesFetched = useRef(false)

  const generateReport = useReportStore((s) => s.generateReport)
  const user = useAuthStore((s) => s.user)
  const isPro = user?.tier === 'pro' || user?.tier === 'agency'
  const { progress, currentStep: statusStep, isPolling, timeoutMessage, startPolling } = useReportStatus()
  const location = useLocation()

  useEffect(() => {
    if (location.state?.uploadResult) {
      setUploadResult(location.state.uploadResult as UploadResult)
      setCurrentStep(2)
      window.history.replaceState({}, document.title)
    }
  }, [location.state])

  useEffect(() => {
    if (sourceType !== 'sheets' || sheetsConfigFetched.current) return
    sheetsConfigFetched.current = true
    setSheetsConfigLoading(true)
    api.get<{ service_account_email: string }>('/reports/sheets-config')
      .then(({ data }) => setServiceAccountEmail(data.service_account_email))
      .catch(() => setServiceAccountEmail(null))
      .finally(() => setSheetsConfigLoading(false))
  }, [sourceType])

  useEffect(() => {
    if (!isPro || templatesFetched.current) return
    templatesFetched.current = true
    api.get<Template[]>('/templates')
      .then(({ data }) => {
        setTemplates(data)
        const defaultTmpl = data.data.find((t) => t.is_default)
        if (defaultTmpl) {
          applyTemplate(defaultTmpl)
        }
      })
      .catch(() => {})
  }, [isPro])

  const applyTemplate = useCallback((tmpl: Template) => {
    setSelectedTemplateId(tmpl.id)
    if (tmpl.config?.tone) setReportTone(tmpl.config.tone)
    if (tmpl.config?.sections && tmpl.config.sections.length > 0) setReportSections(tmpl.config.sections)
    if (tmpl.config?.brand) {
      const brand: { company_name?: string; prepared_by?: string } = {}
      if (tmpl.config.brand.company_name) brand.company_name = tmpl.config.brand.company_name
      if (tmpl.config.brand.prepared_by) brand.prepared_by = tmpl.config.brand.prepared_by
      setReportBrand(Object.keys(brand).length > 0 ? brand : null)
    }
  }, [])

  const handleTemplateSelect = useCallback((templateId: string) => {
    if (!templateId) {
      setSelectedTemplateId('')
      return
    }
    const tmpl = templates.find((t) => t.id === templateId)
    if (tmpl) applyTemplate(tmpl)
  }, [templates, applyTemplate])

  const handleSheetsConnect = useCallback(async () => {
    if (!sheetsUrl.trim()) return
    setSheetsConnecting(true)
    try {
      const { data } = await api.post<UploadResult>('/reports/upload-sheets', { sheets_url: sheetsUrl.trim() })
      setUploadResult(data)
      setCurrentStep(2)
      toast.success('Sheet imported successfully')
    } catch {
    } finally {
      setSheetsConnecting(false)
    }
  }, [sheetsUrl])

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
      case 4:
        return true
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
      chart_specs: chartSpecs.length > 0 ? chartSpecs : undefined,
    }

    if (user?.tier !== 'free') {
      payload.brand = {
        company_name: reportBrand?.company_name || user?.company_name || '',
        prepared_by: reportBrand?.prepared_by || user?.full_name || '',
      }
    }

    try {
      const id = await generateReport(payload)
      setCurrentStep(5)
      startPolling(id)
    } catch {
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
    <div className="flex h-screen bg-slate dark:bg-darkBg">
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
                          ? 'bg-amber-500 text-white'
                          : isCompleted
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                      }`}
                    >
                      {isCompleted ? '✓' : stepNum}
                    </div>
                    <span
                      className={`mt-1 text-xs ${
                        isActive ? 'font-medium text-amber-600' : 'text-gray-400 dark:text-gray-500'
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

          <div className="rounded-xl border border-gray-200 bg-paper p-6 shadow-sm dark:border-gray-700 dark:bg-darkBg">
            {currentStep === 1 && (
              <div>
                <h2 className="mb-4 text-lg font-semibold text-ink dark:text-gray-100">Upload Data</h2>

                <div className="mb-6 flex gap-2">
                  <button
                    type="button"
                    onClick={() => { setSourceType('csv'); setUploadResult(null) }}
                    className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                      sourceType === 'csv'
                        ? 'bg-amber-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
                    }`}
                  >
                    CSV / Excel
                  </button>
                  <button
                    type="button"
                    onClick={() => { setSourceType('sheets'); setUploadResult(null) }}
                    className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                      sourceType === 'sheets'
                        ? 'bg-amber-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
                    }`}
                  >
                    Google Sheets
                  </button>
                </div>

                {sourceType === 'csv' ? (
                  <FileUpload onUploadComplete={handleUploadComplete} />
                ) : (
                  <div className="space-y-4">
                    {sheetsConfigLoading ? (
                      <p className="text-sm text-gray-400">Loading configuration...</p>
                    ) : serviceAccountEmail ? (
                      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200">
                        Share your Google Sheet with{' '}
                        <code className="break-all font-medium">{serviceAccountEmail}</code>
                      </div>
                    ) : (
                      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
                        Sheets connector not configured. Contact support.
                      </div>
                    )}

                    <div>
                      <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Google Sheets URL
                      </label>
                      <input
                        type="text"
                        value={sheetsUrl}
                        onChange={(e) => setSheetsUrl(e.target.value)}
                        placeholder="https://docs.google.com/spreadsheets/d/..."
                        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-amber-400 focus:ring-2 focus:ring-amber-200 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                      />
                    </div>

                    <Button
                      onClick={handleSheetsConnect}
                      disabled={!sheetsUrl.trim() || !serviceAccountEmail}
                      loading={sheetsConnecting}
                    >
                      Connect & Upload
                    </Button>
                  </div>
                )}
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

                {isPro && templates.length > 0 && (
                  <div className="mb-6">
                    <label className="mb-1.5 block text-xs font-medium text-gray-500 dark:text-gray-400">
                      Load from template
                    </label>
                    <select
                      value={selectedTemplateId}
                      onChange={(e) => handleTemplateSelect(e.target.value)}
                      className="w-full rounded-lg border border-slate bg-paper px-3 py-2 text-sm text-ink focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-paper"
                    >
                      <option value="">None</option>
                      {templates.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name}{t.is_default ? ' (Default)' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <ReportConfigForm onConfigChange={handleConfigChange} />
              </div>
            )}

            {currentStep === 4 && uploadResult && (
              <div>
                <h2 className="mb-4 text-lg font-semibold text-ink dark:text-gray-100">Customize Charts</h2>
                <ChartCustomizer
                  uploadId={uploadResult.upload_id}
                  columnConfig={columnConfig}
                  onSpecsChange={setChartSpecs}
                />
              </div>
            )}

            <div className="mt-8 flex items-center justify-between border-t border-gray-200 pt-4 dark:border-gray-700">
              <Button
                variant="outline"
                onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}
                disabled={currentStep === 1}
              >
                Back
              </Button>
              {currentStep < 4 ? (
                <Button onClick={() => setCurrentStep((s) => s + 1)} disabled={!canProceed()}>
                  Next
                </Button>
              ) : currentStep === 4 ? (
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
