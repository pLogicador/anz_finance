import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { InstitutionalBlockScreen } from './InstitutionalBlockScreen'
import { PlanExpiredScreen } from './PlanExpiredScreen'
import { ServiceUnavailableScreen } from './ServiceUnavailableScreen'
import { ValidatingScreen } from './ValidatingScreen'

/**
 * PARTE 5.6's 6 access states, as far as they're each independently
 * testable render-wise: 4 of the 6 are pure "public-bundle" screens tested
 * here (validating / token-invalid / plan-expired / service-unavailable).
 * "Autorizado" is the real dashboard (covered by the dashboard's own
 * component tests, not a block screen) and "sessão de trabalho expirada"
 * is `dashboard/WorkSessionExpiredNotice.test.tsx` (a different file
 * since it deliberately lives in `dashboard/`, not `public-bundle/`).
 *
 * The point of testing these 4 individually is that PARTE 5.4 requires
 * them to be VISIBLY DISTINCT (different icon/title/copy/action) even
 * though token-invalid and plan-expired both fully block access for
 * different reasons -- a regression that silently merged their copy back
 * together wouldn't fail any type check.
 */
describe('access-state screens are visibly distinct from each other', () => {
  it('ValidatingScreen shows a transient loading state, no action button', () => {
    render(<ValidatingScreen />)
    expect(screen.getByText('Validando acesso...')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('InstitutionalBlockScreen (token invalid/missing) links back to the Hub, not to a plan page', () => {
    render(<InstitutionalBlockScreen />)
    expect(screen.getByText('Acesso pelo Syncron Hub')).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /Ir para o Syncron Hub/i })
    expect(link).toHaveAttribute('href', expect.not.stringContaining('/planos'))
  })

  it('PlanExpiredScreen has distinct copy from InstitutionalBlockScreen and links to plans', () => {
    render(<PlanExpiredScreen />)
    expect(screen.getByText('Seu plano Syncron expirou')).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /Ver planos na Syncron/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('/planos'))
  })

  it('ServiceUnavailableScreen offers a working retry action, not a Hub link', () => {
    const onRetry = vi.fn()
    render(<ServiceUnavailableScreen onRetry={onRetry} />)
    expect(screen.getByText('Não foi possível confirmar seu acesso')).toBeInTheDocument()
    const button = screen.getByRole('button', { name: /Tentar novamente/i })
    button.click()
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('InstitutionalBlockScreen and PlanExpiredScreen use different icons despite both fully blocking access', () => {
    // The regression this guards against: collapsing "token invalid" and
    // "plan expired" into the same generic block screen, which PARTE 5.4
    // explicitly forbids -- they're different problems with different
    // resolutions (go to the Hub vs. go renew a plan).
    const { container: invalid, unmount: unmountInvalid } = render(<InstitutionalBlockScreen />)
    const invalidIcon = invalid.querySelector('.rounded-full')?.textContent
    unmountInvalid()

    const { container: expired, unmount: unmountExpired } = render(<PlanExpiredScreen />)
    const expiredIcon = expired.querySelector('.rounded-full')?.textContent
    unmountExpired()

    expect(invalidIcon).not.toBe(expiredIcon)
  })
})
