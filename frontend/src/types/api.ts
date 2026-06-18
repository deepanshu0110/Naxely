import type { User } from './user'
import type { Report, GenerationStatus, UploadResult, Workspace } from './report'

export interface ApiResponse<T> {
  success: boolean
  data: T
  error?: ApiError | null
}

export interface ApiError {
  error: boolean
  code: string
  message: string
  detail?: string | null
}

export interface AuthVerifyResponse {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  tier: User['tier']
  tier_expires_at: string | null
  has_api_key: boolean
  ai_provider: User['ai_provider']
  logo_url: string | null
  brand_color: string | null
  company_name: string | null
  reports_this_month: number
  monthly_limit: number | null
}

export interface UploadResponse extends UploadResult {}

export interface GenerateResponse {
  report_id: string
  status: string
  estimated_seconds: number
  poll_url: string
}

export interface StatusResponse extends GenerationStatus {}

export interface ReportsListResponse {
  reports: Report[]
  total: number
  limit: number
  offset: number
}

export interface ShareResponse {
  share_url: string
  share_token: string
  expires_at: string
}

export interface ApiKeyResponse {
  provider: string
  key_preview: string
  saved_at: string
}

export interface BrandingResponse {
  logo_url: string
  brand_color: string
  company_name: string
}

export interface ProfileResponse {
  email: string
  full_name: string
  tier: User['tier']
  ai_provider: User['ai_provider']
  has_api_key: boolean
  api_key_preview: string | null
  logo_url: string | null
  brand_color: string | null
  company_name: string | null
  reports_this_month: number
  monthly_limit: number | null
}

export interface DeleteResponse {
  deleted: boolean
}

export interface CancelSubscriptionResponse {
  cancelled: boolean
  access_until: string
  message: string
}

export interface CheckoutResponse {
  checkout_url: string
}

export interface DowngradeResponse {
  success: boolean
  data: {
    planned_tier: string
    effective_date: string
    scheduled_change_id?: string | null
    message: string
  }
}

export interface ScheduledChange {
  id: string
  product_id: string
  planned_tier: string
  effective_at: string
}

export interface SubscriptionResponse {
  success: boolean
  data: {
    has_subscription: boolean
    subscription_id?: string
    status?: string
    next_billing_date?: string | null
    cancel_at_next_billing_date?: boolean
    scheduled_change?: ScheduledChange | null
  }
}

export interface Plan {
  id: string
  name: string
  price_monthly: number
  features: string[]
  dodo_product_id?: string
}

export interface PlansResponse {
  plans: Plan[]
}

export interface Template {
  id: string
  name: string
  template_type: string
  is_default: boolean
  created_at: string
}

export interface WorkspaceListResponse extends Array<Workspace> {}
