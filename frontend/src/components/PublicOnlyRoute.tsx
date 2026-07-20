import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export default function PublicOnlyRoute() {
  const { isAuthenticated, isLoading, initialize } = useAuthStore()

  useEffect(() => { initialize() }, [initialize])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-5 w-32 animate-pulse rounded bg-gray-200" />
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
