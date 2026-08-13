import { describe, expect, it } from 'vitest'

import { AccessApiError, AccessErrorCode } from './access-errors'

describe('AccessApiError', () => {
  it('carries the error code and message separately', () => {
    const error = new AccessApiError(AccessErrorCode.PLAN_EXPIRED, 'Plano expirado')
    expect(error.errorCode).toBe(AccessErrorCode.PLAN_EXPIRED)
    expect(error.message).toBe('Plano expirado')
    expect(error).toBeInstanceOf(Error)
  })

  it('has a distinct name for identification in stack traces/logs', () => {
    const error = new AccessApiError(AccessErrorCode.TOKEN_INVALID_OR_MISSING, 'x')
    expect(error.name).toBe('AccessApiError')
  })
})
