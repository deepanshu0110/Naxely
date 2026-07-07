import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import { supabase } from '@/lib/supabase'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'
import { Eye, EyeOff } from 'lucide-react'
import Button from '@/components/ui/Button'

const resetSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Password must be at least 8 characters'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type ResetForm = z.infer<typeof resetSchema>

export default function ResetPassword() {
  const navigate = useNavigate()
  const { updatePassword } = useAuthStore()
  const [hasToken, setHasToken] = useState(false)
  const [checking, setChecking] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetForm>({
    resolver: zodResolver(resetSchema),
  })

  useEffect(() => {
    let handled = false

    const checkExistingSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (session && !handled && !import.meta.env.SSR) {
        handled = true
        setHasToken(true)
        setChecking(false)
      }
    }

    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY' && !handled) {
        handled = true
        setHasToken(true)
        setChecking(false)
      }
    })

    checkExistingSession()

    const timeout = setTimeout(() => {
      if (!handled) {
        setHasToken(false)
        setChecking(false)
      }
    }, 3000)

    return () => {
      data.subscription.unsubscribe()
      clearTimeout(timeout)
    }
  }, [])

  const onSubmit = async (data: ResetForm) => {
    setIsSubmitting(true)
    try {
      await updatePassword(data.password)
      toast.success('Password updated successfully')
      navigate('/login')
    } catch (error) {
      console.error('Password update failed — full error:', error)
      toast.error('Failed to update password. The link may have expired.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate px-4">
        <Head>
          <title>Reset Password — Naxely</title>
          <meta name="robots" content="noindex, nofollow" />
        </Head>
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-500" />
          <p className="text-sm text-gray-500">Verifying reset link...</p>
        </div>
      </div>
    )
  }

  if (!hasToken) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate px-4">
        <Head>
          <title>Reset Password — Naxely</title>
          <meta name="robots" content="noindex, nofollow" />
        </Head>
        <div className="w-full max-w-md rounded-xl bg-paper p-8 text-center shadow-md">
          <p className="text-sm text-gray-600">
            This reset link is invalid or has expired. Request a new one.
          </p>
          <Link
            to="/forgot-password"
            className="mt-6 inline-block rounded-lg bg-amber-500 px-5 py-2.5 text-sm font-semibold text-white transition-colors duration-150 ease-in-out hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            Request new link
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate px-4">
      <Head>
        <title>Reset Password — Naxely</title>
        <meta name="robots" content="noindex, nofollow" />
        <link rel="canonical" href="https://www.naxely.com/auth/reset-password" />
      </Head>
      <div className="w-full max-w-md rounded-xl bg-paper p-8 shadow-md">
        <div className="mb-8 text-center">
          <h1 className="font-display text-2xl font-bold text-ink">Naxely</h1>
          <p className="mt-2 text-sm font-body text-gray-500">Set a new password</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-body font-medium text-gray-700">
              New password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                {...register('password')}
                className="w-full rounded-md border border-gray-300 px-3 py-2 pr-10 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="Min. 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 transition-colors duration-150 ease-in-out hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="confirmPassword" className="mb-1 block text-sm font-body font-medium text-gray-700">
              Confirm new password
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirm ? 'text' : 'password'}
                {...register('confirmPassword')}
                className="w-full rounded-md border border-gray-300 px-3 py-2 pr-10 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="Re-enter new password"
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 transition-colors duration-150 ease-in-out hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              >
                {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-red-500">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full justify-center" loading={isSubmitting}>
            Update password
          </Button>
        </form>
      </div>
    </div>
  )
}
