/** Centralizes reading Vite env vars -- nothing else in the app should call `import.meta.env` directly. */
export const env = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:9101',
  syncronHubUrl: (import.meta.env.VITE_SYNCRON_HUB_URL as string | undefined) ?? 'http://localhost:5100',
}
