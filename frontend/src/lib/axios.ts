import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && body.success === true && body.data !== undefined) {
      response.data = body.data
    }
    return response
  },
  (error) => {
    const status = error.response?.status
    const data = error.response?.data

    if (status === 401) {
      window.location.href = '/login'
    } else if (status === 402) {
      window.dispatchEvent(new CustomEvent('upgrade-needed'))
      const upgradeMsg =
        data?.detail?.message ??
        data?.message ??
        "You've reached your plan limit."
      toast.error(
        `${upgradeMsg} — Upgrade your plan to continue.`,
        { duration: 5000 },
      )
    } else {
      const errorMessage =
        data?.message ??
        data?.detail?.message ??
        data?.detail ??
        'Something went wrong. Please try again.'
      if (typeof errorMessage === 'string') {
        toast.error(errorMessage, { duration: 4000 })
      }
    }

    return Promise.reject(error)
  },
)

export default api
