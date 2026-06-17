import axios from 'axios'
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
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    if (error.response?.status === 402) {
      window.dispatchEvent(new CustomEvent('upgrade-needed'))
    }
    return Promise.reject(error)
  },
)

export default api
