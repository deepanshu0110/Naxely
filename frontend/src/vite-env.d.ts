/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_DODO_CLIENT_TOKEN: string
  readonly VITE_ENVIRONMENT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
