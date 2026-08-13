import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'

import { ProtectedRoute } from '@/auth/ProtectedRoute'
import { RootRoute } from '@/auth/RootRoute'
import { ServiceUnavailableRoute } from '@/auth/ServiceUnavailableRoute'
import { InstitutionalBlockScreen } from '@/public-bundle/InstitutionalBlockScreen'
import { PlanExpiredScreen } from '@/public-bundle/PlanExpiredScreen'
import { ValidatingScreen } from '@/public-bundle/ValidatingScreen'

// Lazy: the authenticated app's JS must not be fetched until the access
// gate resolves to AUTHORIZED (PARTE 5.7 / 19.1 bundle-splitting
// requirement) -- this import() call is what actually defers the fetch,
// the vite.config.ts manualChunks split just keeps the output tidy.
const AppShell = lazy(() => import('@/app/AppShell'))

export const router = createBrowserRouter([
  { path: '/', element: <RootRoute /> },
  { path: '/blocked/token', element: <InstitutionalBlockScreen /> },
  { path: '/blocked/plan-expired', element: <PlanExpiredScreen /> },
  { path: '/blocked/service-unavailable', element: <ServiceUnavailableRoute /> },
  {
    path: '/app',
    element: (
      <ProtectedRoute>
        <Suspense fallback={<ValidatingScreen />}>
          <AppShell />
        </Suspense>
      </ProtectedRoute>
    ),
  },
])
