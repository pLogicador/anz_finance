/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_SYNCRON_HUB_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
