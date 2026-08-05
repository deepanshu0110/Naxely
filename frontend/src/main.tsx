// CI smoke-test marker: frontend-ci.yml triggers on pushes touching frontend/**
import { ViteReactSSG } from 'vite-react-ssg'
import { routes } from './App'
import './index.css'
import './assets/google-fonts.css'

export const createRoot = ViteReactSSG({ routes })
