import { useLocation, useNavigate } from 'react-router-dom'

import { ServiceUnavailableScreen } from '@/public-bundle/ServiceUnavailableScreen'

/** Wires up "Tentar novamente" to restart the bridge with the same token, without a real Hub round-trip. */
export function ServiceUnavailableRoute() {
  const navigate = useNavigate()
  const location = useLocation()
  const token = (location.state as { token?: string } | null)?.token

  return (
    <ServiceUnavailableScreen
      onRetry={() => {
        if (token) navigate(`/?token=${encodeURIComponent(token)}`, { replace: true })
        else navigate('/', { replace: true })
      }}
    />
  )
}
