import { create } from 'zustand'
import type { Report, UploadResult, GenerationStatus, ReportConfig } from '@/types/report'
import api from '@/lib/axios'
import type { ReportsListResponse, GenerateResponse, StatusResponse } from '@/types/api'

interface ReportStore {
  reports: Report[]
  total: number
  uploadedFile: UploadResult | null
  generationStatus: GenerationStatus | null
  isGenerating: boolean
  isLoading: boolean
  error: string | null
  fetchReports: (offset?: number, limit?: number) => Promise<void>
  uploadFile: (file: File) => Promise<UploadResult>
  generateReport: (config: ReportConfig) => Promise<string>
  bulkDeleteReports: (ids: string[]) => Promise<void>
  pollStatus: (reportId: string) => Promise<GenerationStatus>
  deleteReport: (reportId: string) => Promise<void>
}

export const useReportStore = create<ReportStore>((set, get) => ({
  reports: [],
  total: 0,
  uploadedFile: null,
  generationStatus: null,
  isGenerating: false,
  isLoading: false,
  error: null,

  fetchReports: async (offset = 0, limit = 20) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.get<ReportsListResponse>('/reports', {
        params: { offset, limit },
      })
      set({ reports: data.reports, total: data.total, isLoading: false })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch reports'
      set({ error: message, isLoading: false })
    }
  },

  uploadFile: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<UploadResult>('/reports/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    set({ uploadedFile: data })
    return data
  },

  generateReport: async (config: ReportConfig) => {
    set({ isGenerating: true, generationStatus: null, error: null })
    try {
      const { data } = await api.post<GenerateResponse>('/reports/generate', config)
      set({ isGenerating: false })
      return data.report_id
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate report'
      set({ error: message, isGenerating: false })
      throw err
    }
  },

  pollStatus: async (reportId: string) => {
    const { data } = await api.get<StatusResponse>(`/reports/${reportId}/status`)
    const status: GenerationStatus = {
      report_id: data.report_id,
      status: data.status,
      progress_percent: data.progress_percent,
      current_step: data.current_step,
      steps_completed: data.steps_completed,
      steps_remaining: data.steps_remaining,
      pdf_url: data.pdf_url,
      generation_time_seconds: data.generation_time_seconds,
      error_message: data.error_message,
    }
    set({ generationStatus: status })

    if (status.status === 'completed' || status.status === 'failed') {
      set({ isGenerating: false })
      if (status.status === 'completed') {
        get().fetchReports()
      }
    }

    return status
  },

  deleteReport: async (reportId: string) => {
    await api.delete(`/reports/${reportId}`)
    set((state) => ({
      reports: state.reports.filter((r) => r.id !== reportId),
      total: state.total - 1,
    }))
  },

  bulkDeleteReports: async (ids: string[]) => {
    await api.post('/reports/bulk-delete', { report_ids: ids })
    set((state) => ({
      reports: state.reports.filter((r) => !ids.includes(r.id)),
      total: state.total - ids.length,
    }))
  },
}))
