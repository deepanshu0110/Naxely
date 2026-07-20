import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

export default function AuthAwareCta() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    import('@/store/authStore').then(({ useAuthStore }) => {
      setIsAuthenticated(useAuthStore.getState().isAuthenticated)
      const unsub = useAuthStore.subscribe(
        (state) => setIsAuthenticated(state.isAuthenticated),
      )
      return unsub
    })
  }, [])

  if (isAuthenticated) {
    return (
      <Link to="/dashboard"
        className="bg-amber-500 hover:bg-amber-600 text-white
          font-medium px-7 py-3 rounded-lg transition-colors text-base
          inline-block">
        Go to Dashboard →
      </Link>
    )
  }

  return (
    <>
      <Link to="/signup"
        className="
          relative overflow-hidden
          bg-amber-600 hover:bg-amber-700
          text-white font-medium px-7 py-3 rounded-lg
          transition-colors text-base inline-block
          group
        ">
        <span className="relative z-10">
          Generate your first report — free
        </span>
        <span className="
          absolute inset-0
          bg-gradient-to-r from-transparent via-white/20 to-transparent
          -translate-x-full group-hover:translate-x-full
          transition-transform duration-700 ease-in-out
        " />
      </Link>
      <Link to="/login"
        className="text-ink/60 dark:text-paper/50
          hover:text-ink dark:hover:text-paper
          font-medium text-base transition-colors">
        Sign in →
      </Link>
    </>
  )
}
