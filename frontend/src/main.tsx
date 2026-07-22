import { ViteReactSSG } from 'vite-react-ssg'
import { routes } from './App'
import './index.css'
import './assets/google-fonts.css'

export const createRoot = ViteReactSSG({ routes })
