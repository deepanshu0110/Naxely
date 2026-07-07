import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Head } from 'vite-react-ssg'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'
import Button from '@/components/ui/Button'

const forgotSchema = z.object({
  email: z.string().email('Please enter a valid email'),
})

type ForgotForm = z.infer<typeof forgotSchema>

export default function ForgotPassword() {
  const { sendPasswordResetEmail } = useAuthStore()
  const [sent, setSent] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
  })

  const onSubmit = async (data: ForgotForm) => {
    setIsSubmitting(true)
    try {
      await sendPasswordResetEmail(data.email)
      setSent(true)
    } catch {
      toast.error('Something went wrong. Please try again later.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate px-4">
      <Head>
        <title>Forgot Password — Naxely</title>
        <meta name="robots" content="noindex, nofollow" />
        <meta name="description" content="Reset your Naxely account password." />
        <link rel="canonical" href="https://www.naxely.com/forgot-password" />
      </Head>
      <div className="w-full max-w-md rounded-xl bg-paper p-8 shadow-md">
        <div className="mb-8 text-center">
          <h1 className="font-display text-2xl font-bold text-ink">Naxely</h1>
          <p className="mt-2 text-sm font-body text-gray-500">Reset your password</p>
        </div>

        {sent ? (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
              <svg className="h-6 w-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm text-gray-600">
              If an account exists for that email, a reset link is on its way. Please check your inbox (and spam folder).
            </p>
            <Link
              to="/login"
              className="mt-6 inline-block text-sm font-medium text-amber-500 transition-colors duration-150 ease-in-out hover:text-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 rounded-sm"
            >
              Back to log in
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-body font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                {...register('email')}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-ink placeholder-gray-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full justify-center" loading={isSubmitting}>
              Send reset link
            </Button>

            <p className="text-center text-sm text-gray-500">
              <Link to="/login" className="font-medium text-amber-500 transition-colors duration-150 ease-in-out hover:text-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 rounded-sm">
                Back to log in
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  )
}
