import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { WorkSessionExpiredNotice } from './WorkSessionExpiredNotice'

/** PARTE 5.6 state 5 -- deliberately NOT a public-bundle block screen (the
 * ANZ session/JWT is still valid here, only the workspace TTL lapsed), so
 * its test lives alongside the dashboard, not with the other 4 access
 * states in public-bundle/access-screens.test.tsx. */
describe('WorkSessionExpiredNotice', () => {
  it('explains that the session (auth) is still valid, only the data expired', () => {
    render(<WorkSessionExpiredNotice onReupload={() => {}} />)
    expect(screen.getByText('Sua sessão de trabalho expirou')).toBeInTheDocument()
    expect(screen.getByText(/continua conectado/i)).toBeInTheDocument()
  })

  it('calls onReupload (not a Hub redirect) when the action button is clicked', () => {
    const onReupload = vi.fn()
    render(<WorkSessionExpiredNotice onReupload={onReupload} />)
    screen.getByRole('button', { name: /Enviar extratos novamente/i }).click()
    expect(onReupload).toHaveBeenCalledOnce()
  })
})
