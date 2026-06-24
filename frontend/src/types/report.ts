export interface Report {
  id: string
  title: string
  template_type: string
  status: 'processing' | 'completed' | 'failed'
  row_count: number
  pdf_url: string | null
  ai_summary: string | null
  ai_insights: AIInsight[] | null
  ai_anomalies: AIAnomaly[] | null
  share_token: string | null
  share_view_count: number
  created_at: string
  generation_time_seconds?: number
  error_message?: string | null
  ai_skipped?: boolean
}

export interface AIInsight {
  kpi: string
  number: string
  reason: string
  action: string
  sentiment: 'positive' | 'negative' | 'neutral'
  priority: 'high' | 'medium' | 'low'
}

export interface AIAnomaly {
  column: string
  value: string | number
  expected: string | number
  deviation: string
  severity: 'warning' | 'critical'
}

export interface UploadResult {
  upload_id: string
  filename: string
  file_url: string
  row_count: number
  column_count: number
  columns: ColumnInfo[]
  preview_rows: Record<string, unknown>[]
}

export interface ColumnInfo {
  original_name: string
  suggested_name: string
  suggested_type: 'date' | 'metric' | 'dimension' | 'text'
  sample_values: (string | number | null)[]
  null_count: number
  unique_count: number
}

export interface ColumnConfig {
  original_name: string
  display_name: string
  type: 'date' | 'metric' | 'dimension' | 'text'
  include: boolean
}

export interface ChartSpec {
  x: string
  y: string
  type: string
  title: string
}

export interface ReportConfig {
  upload_id: string
  title: string
  template_type: string
  tone: string
  sections: string[]
  date_range?: { from: string; to: string }
  column_config: ColumnConfig[]
  brand?: { company_name: string; prepared_by: string }
  workspace_id?: string | null
  chart_specs?: ChartSpec[]
}

export interface GenerationStatus {
  report_id: string
  status: 'processing' | 'completed' | 'failed'
  progress_percent: number
  current_step?: string
  steps_completed?: string[]
  steps_remaining?: string[]
  pdf_url?: string
  generation_time_seconds?: number
  error_message?: string
  estimated_seconds?: number
}

export interface Workspace {
  id: string
  name: string
  client_name: string
  logo_url: string | null
  brand_color: string | null
  report_count: number
  created_at: string
}
