import { ViteReactSSG } from 'vite-react-ssg'
import { routes } from './App'
import { useAuthStore } from './store/authStore'
import './index.css'

export const createRoot = ViteReactSSG(
  { routes },
  () => useAuthStore.getState().initialize(),
)
