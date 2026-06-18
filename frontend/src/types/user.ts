export interface User {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  tier: 'free' | 'pro' | 'agency'
  tier_expires_at: string | null
  has_api_key: boolean
  ai_provider: 'openai' | 'claude' | 'gemini' | null
  logo_url: string | null
  brand_color: string | null
  company_name: string | null
  reports_this_month: number
  monthly_limit: number | null
}
