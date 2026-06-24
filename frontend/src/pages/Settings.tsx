import { useEffect, useState, useCallback, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { formatBillingDate } from '@/lib/dates'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/axios'
import Sidebar from '@/components/layout/Sidebar'
import Tabs from '@/components/ui/Tabs'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import UpgradePrompt from '@/components/ui/UpgradePrompt'
import ApiKeyForm from '@/components/settings/ApiKeyForm'
import { Upload, Palette, AlertTriangle, Key, Copy, Check, Clock, XCircle } from 'lucide-react'
import type { ProfileResponse, BrandingResponse, CheckoutResponse, SubscriptionResponse } from '@/types/api'

const profileSchema = z.object({
  full_name: z
    .string()
    .min(1, 'Name is required')
    .max(255, 'Name too long')
    .transform((v) => v.trim()),
})

type ProfileForm = z.infer<typeof profileSchema>

interface ApiKey {
  id: string
  name: string
  key_display: string
  created_at: string
  last_used_at: string | null
  revoked: boolean
}

const brandingSchema = z.object({
  brand_color: z.string().regex(/^#[0-9a-fA-F]{6}$/, 'Must be a valid hex colour'),
  company_name: z.string().max(255, 'Company name too long').optional(),
})

type BrandingForm = z.infer<typeof brandingSchema>

export default function Settings() {
  const { user, fetchProfile } = useAuthStore()
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<ProfileResponse | null>(null)

  const fetchSettings = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get('/settings/profile')
      const data = response.data as ProfileResponse
      setProfile(data)
    } catch {
      setError('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  const tier = profile?.tier ?? user?.tier ?? 'free'
  const isProOrAbove = tier === 'pro' || tier === 'agency'
  const isAgency = tier === 'agency'

  const TABS = [
    { id: 'profile', label: 'Profile' },
    { id: 'api-key', label: 'API Key' },
    ...(isAgency ? [{ id: 'api-keys', label: 'API Keys' }] : []),
    { id: 'branding', label: 'Branding' },
    { id: 'billing', label: 'Billing' },
  ]

  if (loading) return <SettingsSkeleton />
  if (error) {
    return (
      <div className="flex h-screen bg-slate dark:bg-darkBg">
        <Sidebar />
        <main className="flex flex-1 items-center justify-center">
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/30">
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            <Button variant="ghost" size="sm" className="mt-3" onClick={fetchSettings}>Retry</Button>
          </div>
        </main>
      </div>
    )
  }
  if (!profile) return null

  return (
    <div className="flex h-screen bg-slate dark:bg-darkBg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <h1 className="mb-6 font-display text-2xl font-bold text-ink dark:text-gray-100">Settings</h1>
          <Tabs items={TABS} activeId={activeTab} onChange={setActiveTab}>
            {activeTab === 'profile' && <ProfileTab profile={profile} onSaved={fetchProfile} />}
            {activeTab === 'api-key' && (
              <ApiKeyForm
                hasKey={profile.has_api_key}
                provider={profile.ai_provider}
                keyPreview={profile.api_key_preview ?? null}
                tier={tier}
                onSaved={() => fetchSettings()}
                onDeleted={() => fetchSettings()}
              />
            )}
            {activeTab === 'api-keys' && <ApiKeysTab />}
            {activeTab === 'branding' && (
              isProOrAbove ? (
                <BrandingTab
                  logoUrl={profile.logo_url}
                  brandColor={profile.brand_color ?? '#D97A34'}
                  companyName={profile.company_name ?? ''}
                />
              ) : (
                <UpgradePrompt feature="Custom Branding" tier="Pro" />
              )
            )}
            {activeTab === 'billing' && <BillingTab profile={profile} tier={tier} tierExpiresAt={user?.tier_expires_at ?? null} />}
          </Tabs>
        </div>
      </main>
    </div>
  )
}

function SettingsSkeleton() {
  return (
    <div className="flex h-screen bg-slate dark:bg-darkBg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <div className="mb-6 h-8 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="mb-6 flex gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-9 w-20 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            ))}
          </div>
          <div className="space-y-4">
            <div className="h-10 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-10 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-10 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          </div>
        </div>
      </main>
    </div>
  )
}

function ProfileTab({ profile, onSaved }: { profile: ProfileResponse; onSaved: () => void }) {
  const [isSaving, setIsSaving] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: profile.full_name },
  })

  const onSubmit = async (data: ProfileForm) => {
    setIsSaving(true)
    try {
      await api.patch('/settings/profile', data)
      onSaved()
      toast.success('Profile updated')
    } catch {
      toast.error('Failed to update profile')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="full_name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Full name</label>
        <input
          id="full_name"
          {...register('full_name')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
        {errors.full_name && <p className="mt-1 text-xs text-red-500">{errors.full_name.message}</p>}
      </div>
      <div>
        <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
        <input
          id="email"
          type="email"
          readOnly
          value={profile.email}
          className="w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-400"
        />
        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">Email is managed through your account provider.</p>
      </div>
      <Button type="submit" loading={isSaving}>Save</Button>
    </form>
  )
}

function BrandingTab({ logoUrl, brandColor, companyName }: { logoUrl: string | null; brandColor: string; companyName: string }) {
  const [isSaving, setIsSaving] = useState(false)
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string | null>(logoUrl)
  const [dragOver, setDragOver] = useState(false)
  const [suggestedColors, setSuggestedColors] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<BrandingForm>({
    resolver: zodResolver(brandingSchema),
    defaultValues: { brand_color: brandColor, company_name: companyName },
  })

  const watchedColor = watch('brand_color')
  const watchedName = watch('company_name')

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && isValidImage(file)) {
      setLogoFile(file)
      setLogoPreview(URL.createObjectURL(file))
    } else {
      toast.error('Only PNG, JPG, or SVG files under 2MB are allowed')
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && isValidImage(file)) {
      setLogoFile(file)
      setLogoPreview(URL.createObjectURL(file))
    }
  }

  const onSubmit = async (data: BrandingForm) => {
    setIsSaving(true)
    try {
      const formData = new FormData()
      if (logoFile) formData.append('logo', logoFile)
      formData.append('brand_color', data.brand_color)
      formData.append('company_name', data.company_name ?? '')
      const brandResp = await api.post('/settings/branding', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const resp = brandResp.data as BrandingResponse
      setLogoPreview(resp.logo_url)
      setLogoFile(null)
      setValue('brand_color', resp.brand_color, { shouldValidate: true })
      setValue('company_name', resp.company_name, { shouldValidate: true })
      if (resp.suggested_colors) setSuggestedColors(resp.suggested_colors)
      toast.success('Branding saved')
    } catch {
      toast.error('Failed to save branding')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Logo</label>
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors duration-150 ease-in-out ${dragOver ? 'border-amber-500 bg-amber-50' : 'border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-700'}`}
        >
          {logoPreview ? (
            <div className="flex flex-col items-center gap-2">
              <img src={logoPreview} alt="Brand logo" className="h-16 max-w-[200px] object-contain" />
              <p className="text-xs text-gray-500 dark:text-gray-400">Drag & drop to replace, or click below</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-gray-400 dark:text-gray-500">
              <Upload className="h-8 w-8" />
              <p className="text-sm">Drag & drop your logo here</p>
              <p className="text-xs">PNG, JPG, or SVG — max 2MB</p>
            </div>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.svg"
          onChange={handleFileSelect}
          className="mt-2 text-sm text-gray-500 file:mr-2 file:rounded-md file:border-0 file:bg-amber-50 file:px-3 file:py-1 file:text-xs file:font-medium file:text-amber-600 file:transition-colors file:duration-150 file:ease-in-out hover:file:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:text-gray-400 dark:file:bg-amber-900/30 dark:file:text-amber-400"
        />
        {suggestedColors.length > 0 && (
          <div className="mt-3">
            <p className="mb-1.5 text-xs font-medium text-gray-500 dark:text-gray-400">Suggested brand colors</p>
            <div className="flex gap-2">
              {suggestedColors.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setValue('brand_color', c, { shouldValidate: true })}
                  className="h-7 w-7 rounded-full border border-gray-300 shadow-sm transition-transform duration-150 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1"
                  style={{ backgroundColor: c }}
                  title={c}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <div>
        <label htmlFor="brand_color" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Brand Colour</label>
        <div className="flex items-center gap-3">
          <input
            id="brand_color"
            type="text"
            {...register('brand_color')}
            className="w-32 rounded-md border border-gray-300 px-3 py-2 font-mono text-sm text-gray-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          />
          <input
            type="color"
            value={watchedColor ?? '#D97A34'}
            onChange={(e) => setValue('brand_color', e.target.value, { shouldValidate: true })}
            className="h-9 w-9 cursor-pointer rounded border border-gray-300 dark:border-gray-600"
          />
        </div>
        {errors.brand_color && <p className="mt-1 text-xs text-red-500">{errors.brand_color.message}</p>}
      </div>

      <div>
        <label htmlFor="company_name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Company Name</label>
        <input
          id="company_name"
          {...register('company_name')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
        />
      </div>

      <div>
        <h4 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">Preview</h4>
        <BrandingPreview
          companyName={watchedName ?? ''}
          brandColor={watchedColor ?? '#D97A34'}
          logoUrl={logoPreview}
        />
      </div>

      <Button type="submit" loading={isSaving}>Save Branding</Button>
    </form>
  )
}

function BrandingPreview({ companyName, brandColor, logoUrl }: { companyName: string; brandColor: string; logoUrl: string | null }) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700" style={{ width: 280, height: 200 }}>
      <div className="flex h-full flex-col items-center justify-center gap-3 p-4" style={{ backgroundColor: brandColor + '10' }}>
        <div
          className="flex h-1 w-16 rounded-full"
          style={{ backgroundColor: brandColor }}
        />
        {logoUrl && <img src={logoUrl} alt="Logo" className="h-10 max-w-[100px] object-contain" />}
        {!logoUrl && <Palette className="h-10 w-10 text-gray-300" />}
        <p className="text-sm font-semibold" style={{ color: brandColor }}>
          {companyName || 'Your Company'}
        </p>
        <div
          className="flex h-1 w-16 rounded-full"
          style={{ backgroundColor: brandColor }}
        />
        <p className="text-xs text-gray-400">Powered by Naxely</p>
      </div>
    </div>
  )
}

function BillingTab({ profile, tier, tierExpiresAt }: { profile: ProfileResponse; tier: string; tierExpiresAt: string | null }) {
  const [isCreatingCheckout, setIsCreatingCheckout] = useState<'pro' | 'agency' | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteEmail, setDeleteEmail] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  const [showDowngradeModal, setShowDowngradeModal] = useState<'pro' | 'free' | null>(null)
  const [isDowngrading, setIsDowngrading] = useState(false)
  const [downgradeMessage, setDowngradeMessage] = useState<string | null>(null)

  const [scheduledChange, setScheduledChange] = useState<{ type: 'pro' | 'free'; effectiveDate: string } | null>(null)
  const [isCancellingChange, setIsCancellingChange] = useState(false)
  const [subLoading, setSubLoading] = useState(true)

  const fetchSubscription = async () => {
    setSubLoading(true)
    try {
      const resp = await api.get('/payments/subscription')
      const data = resp.data as SubscriptionResponse
      if (!data.data.has_subscription) {
        setScheduledChange(null)
        return
      }
      if (data.data.scheduled_change) {
        const sc = data.data.scheduled_change
        if (sc.planned_tier === 'pro') {
          setScheduledChange({ type: 'pro', effectiveDate: sc.effective_at })
        }
      } else if (data.data.cancel_at_next_billing_date) {
        setScheduledChange({ type: 'free', effectiveDate: data.data.next_billing_date ?? '' })
      } else {
        setScheduledChange(null)
      }
    } catch {
      setScheduledChange(null)
    } finally {
      setSubLoading(false)
    }
  }

  useEffect(() => {
    if (tier !== 'free') {
      fetchSubscription()
    } else {
      setSubLoading(false)
    }
  }, [tier])

  const planLabels: Record<string, string> = {
    free: 'Free',
    pro: 'Pro — $29/month',
    agency: 'Agency — $79/month',
  }

  const handleUpgrade = async (plan: 'pro' | 'agency') => {
    setIsCreatingCheckout(plan)
    try {
      const resp = await api.post('/payments/checkout', { plan })
      const data = resp.data as CheckoutResponse
      window.location.href = data.checkout_url
    } catch {
      toast.error('Failed to start checkout. Please try again.')
      setIsCreatingCheckout(null)
    }
  }

  const handleDowngrade = async () => {
    const target = showDowngradeModal
    if (!target) return
    setIsDowngrading(true)
    try {
      await api.post('/payments/downgrade', { plan: target })
      setShowDowngradeModal(null)
      await fetchSubscription()
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail
      const message = typeof detail === 'string' ? detail : detail?.message
      toast.error(message || 'Failed to schedule downgrade. Please try again.')
    } finally {
      setIsDowngrading(false)
    }
  }

  const handleCancelScheduledChange = async () => {
    setIsCancellingChange(true)
    try {
      await api.post('/payments/cancel-scheduled-change')
      setScheduledChange(null)
      setDowngradeMessage(null)
      toast.success('Scheduled change cancelled')
    } catch {
      toast.error('Failed to cancel scheduled change')
    } finally {
      setIsCancellingChange(false)
    }
  }

  const effectiveDate = tierExpiresAt ? formatBillingDate(tierExpiresAt) : null
  const scheduledEffectiveDate = scheduledChange?.effectiveDate ? formatBillingDate(scheduledChange.effectiveDate) : null

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-body font-medium text-gray-700 dark:text-gray-300">Current Plan</h3>
        <div className="mt-2 flex items-center gap-2">
          <Badge variant={tier === 'free' ? 'neutral' : 'success'} text={planLabels[tier] ?? tier} />
        </div>
      </div>

      {tierExpiresAt && !scheduledChange && !downgradeMessage && (
        <div>
          <h3 className="text-sm font-body font-medium text-gray-700 dark:text-gray-300">Next Billing Date</h3>
          <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{effectiveDate}</p>
        </div>
      )}

      {downgradeMessage && (
        <div className="flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-800 dark:bg-yellow-900/30">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
          <p className="text-sm text-yellow-700 dark:text-yellow-400">{downgradeMessage}</p>
        </div>
      )}

      {(tier === 'free' || tier === 'pro') && !scheduledChange && (
        <div className="space-y-4">
          <h3 className="text-sm font-body font-medium text-gray-700 dark:text-gray-300">Upgrade</h3>
          {tier === 'free' && (
            <CompactPlanCard
              plan="pro"
              loading={isCreatingCheckout === 'pro'}
              price="$29/month"
              features={['Unlimited reports', 'AI insights', 'Custom branding', 'No watermark']}
              cta="Upgrade to Pro"
              onUpgrade={handleUpgrade}
            />
          )}
          <CompactPlanCard
            plan="agency"
            loading={isCreatingCheckout === 'agency'}
            price="$79/month"
            features={['Everything in Pro', 'Full white-label reports — every trace of Naxely branding removed', 'Priority support — direct, fast responses from the founder']}
            cta="Upgrade to Agency"
            onUpgrade={handleUpgrade}
          />
        </div>
      )}

      {tier !== 'free' && !scheduledChange && !subLoading && (
        <div className="space-y-3">
          <h3 className="text-sm font-body font-medium text-gray-700 dark:text-gray-300">Change Plan</h3>

          {tier === 'agency' && (
            <Card padding="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Downgrade to Pro</h4>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">$29/month — Unlimited reports, AI insights, custom branding</p>
                  {effectiveDate && <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">Takes effect next billing period ({effectiveDate})</p>}
                </div>
                <Button size="sm" variant="outline" onClick={() => setShowDowngradeModal('pro')}>Downgrade to Pro</Button>
              </div>
            </Card>
          )}

          <Card padding="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Downgrade to Free</h4>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">3 reports/month, CSV upload, basic charts, watermark</p>
                {effectiveDate && <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">Takes effect next billing period ({effectiveDate})</p>}
              </div>
              <Button size="sm" variant="outline" onClick={() => setShowDowngradeModal('free')}>Downgrade to Free</Button>
            </div>
          </Card>
        </div>
      )}

      {scheduledChange && (
        <Card padding="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Scheduled: moving to {scheduledChange.type === 'pro' ? 'Pro' : 'Free'}
              </h4>
              {scheduledEffectiveDate && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Takes effect {scheduledEffectiveDate}
                </p>
              )}
            </div>
            <Button size="sm" variant="outline" loading={isCancellingChange} onClick={handleCancelScheduledChange}>
              Cancel
            </Button>
          </div>
        </Card>
      )}

      <Modal
        isOpen={showDowngradeModal !== null}
        onClose={() => setShowDowngradeModal(null)}
        title={showDowngradeModal === 'pro' ? 'Downgrade to Pro' : 'Downgrade to Free'}
      >
        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-800 dark:bg-yellow-900/30">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-yellow-600 dark:text-yellow-400" />
            <p className="text-sm text-yellow-700 dark:text-yellow-400">
              {showDowngradeModal === 'pro'
                ? `You'll move to the Pro plan at the start of your next billing period${effectiveDate ? ` (${effectiveDate})` : ''}. Your Agency features will remain active until then.`
                : `Your ${tier.charAt(0).toUpperCase() + tier.slice(1)} access continues until the end of your current billing period${effectiveDate ? ` (${effectiveDate})` : ''}. After that, you'll be moved to the Free plan.`}
            </p>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">Are you sure you want to downgrade?</p>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setShowDowngradeModal(null)}>Keep Current Plan</Button>
            <Button variant="danger" loading={isDowngrading} onClick={handleDowngrade}>
              {showDowngradeModal === 'pro' ? 'Downgrade to Pro' : 'Downgrade to Free'}
            </Button>
          </div>
        </div>
      </Modal>

      <hr className="border-gray-200 dark:border-gray-700" />

      <div>
        <h3 className="text-sm font-medium text-red-700">Danger Zone</h3>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Once you delete your account, there is no going back. Please be certain.</p>
        <div className="mt-3">
          <Button variant="danger" onClick={() => setShowDeleteModal(true)}>Delete Account</Button>
          <Modal
            isOpen={showDeleteModal}
            onClose={() => { setShowDeleteModal(false); setDeleteEmail('') }}
            title="Delete Account"
          >
            <div className="space-y-4">
              <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/30">
                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600 dark:text-red-400" />
                <p className="text-sm text-red-700 dark:text-red-400">
                  This will permanently delete your account and all associated data. This action cannot be undone.
                </p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Type <strong>{profile?.email}</strong> to confirm:
              </p>
              <input
                type="email"
                value={deleteEmail}
                onChange={(e) => setDeleteEmail(e.target.value)}
                placeholder={profile?.email}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
              <div className="flex justify-end gap-3">
                <Button variant="ghost" onClick={() => { setShowDeleteModal(false); setDeleteEmail('') }}>Cancel</Button>
                <Button
                  variant="danger"
                  loading={isDeleting}
                  disabled={deleteEmail !== profile?.email}
                  onClick={async () => {
                    setIsDeleting(true)
                    try {
                      await api.delete('/settings/account', { data: { email: deleteEmail } })
                      toast.success('Account deleted')
                      setTimeout(() => window.location.href = '/', 1500)
                    } catch {
                      toast.error('Failed to delete account')
                    } finally {
                      setIsDeleting(false)
                      setShowDeleteModal(false)
                      setDeleteEmail('')
                    }
                  }}
                >
                  Permanently Delete
                </Button>
              </div>
            </div>
          </Modal>
        </div>
      </div>
    </div>
  )
}

function ApiKeysTab() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [showKeyModal, setShowKeyModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKey, setNewKey] = useState('')
  const [keyLoading, setKeyLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    api.get('/settings/api-keys').then(r => setApiKeys(r.data)).catch(() => {})
  }, [])

  const handleGenerate = async () => {
    if (!newKeyName.trim()) return
    setKeyLoading(true)
    try {
      const resp = await api.post('/settings/api-keys', { name: newKeyName.trim() })
      setNewKey(resp.data.key)
      setApiKeys(prev => [{
        id: resp.data.id,
        name: resp.data.name,
        key_display: `${resp.data.key_prefix}...${resp.data.key_suffix}`,
        created_at: resp.data.created_at,
        last_used_at: null,
        revoked: false,
      }, ...prev])
    } catch {
      toast.error('Failed to generate API key')
    } finally {
      setKeyLoading(false)
    }
  }

  const handleRevoke = async (keyId: string) => {
    try {
      await api.delete(`/settings/api-keys/${keyId}`)
      setApiKeys(prev => prev.filter(k => k.id !== keyId))
      toast.success('API key revoked')
    } catch {
      toast.error('Failed to revoke API key')
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(newKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-body font-medium text-gray-700 dark:text-gray-300">Programmatic Access</h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            API keys allow you to generate reports programmatically via the Naxely API.
          </p>
        </div>
        <Button size="sm" onClick={() => { setNewKey(''); setNewKeyName(''); setShowKeyModal(true) }}>
          <Key className="mr-1.5 h-4 w-4" />
          Generate New Key
        </Button>
      </div>

      {apiKeys.length === 0 ? (
        <div className="flex flex-col items-center py-12 text-center">
          <Key className="mb-3 h-10 w-10 text-gray-300 dark:text-gray-600" />
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">No API keys yet</h4>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Generate one to get started with the Naxely API.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {apiKeys.map((k) => (
            <Card key={k.id} padding="p-4">
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">{k.name}</h4>
                    {k.revoked && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                        <XCircle className="h-3 w-3" />
                        Revoked
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 font-mono text-xs text-gray-500 dark:text-gray-400">{k.key_display}</p>
                  <div className="mt-1.5 flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Created {k.created_at
                        ? new Date(k.created_at).toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'short', year: 'numeric',
                          })
                        : '—'}
                    </span>
                    <span>
                      Last used {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : 'Never'}
                    </span>
                  </div>
                </div>
                {!k.revoked && (
                  <Button variant="danger" size="sm" onClick={() => handleRevoke(k.id)}>
                    Revoke
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={showKeyModal} onClose={() => setShowKeyModal(false)} title="Generate API Key">
        {newKey ? (
          <div className="space-y-4">
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-900/30">
              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
                ⚠ Save this key — it will not be shown again.
              </p>
            </div>
            <div className="rounded-md border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800">
              <code className="break-all font-mono text-sm text-gray-900 dark:text-gray-100">{newKey}</code>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={handleCopy}>
                {copied ? <><Check className="mr-1.5 h-4 w-4" /> Copied</> : <><Copy className="mr-1.5 h-4 w-4" /> Copy</>}
              </Button>
              <Button onClick={() => setShowKeyModal(false)}>Done</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label htmlFor="key_name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Key Name
              </label>
              <input
                id="key_name"
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g. CI integration"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                onKeyDown={(e) => { if (e.key === 'Enter') handleGenerate() }}
              />
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setShowKeyModal(false)}>Cancel</Button>
              <Button loading={keyLoading} disabled={!newKeyName.trim()} onClick={handleGenerate}>
                Generate
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

function CompactPlanCard({ plan, loading, price, features, cta, onUpgrade }: { plan: 'pro' | 'agency'; loading: boolean; price: string; features: string[]; cta: string; onUpgrade: (plan: 'pro' | 'agency') => void }) {
  return (
    <Card padding="p-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{plan === 'pro' ? 'Pro' : 'Agency'}</h4>
          <p className="text-lg font-mono tabular-nums font-bold text-gray-900 dark:text-gray-100">{price}</p>
          <ul className="mt-2 space-y-1">
            {features.map((f) => (
              <li key={f} className="text-xs text-gray-500 dark:text-gray-400">
                <span className="text-amber-500">✓</span> {f}
              </li>
            ))}
          </ul>
        </div>
        <Button size="sm" loading={loading} onClick={() => onUpgrade(plan)}>{cta}</Button>
      </div>
    </Card>
  )
}

function isValidImage(file: File): boolean {
  const validTypes = ['image/png', 'image/jpeg', 'image/svg+xml']
  const maxSize = 2 * 1024 * 1024
  return validTypes.includes(file.type) && file.size <= maxSize
}
