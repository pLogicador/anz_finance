/** Mirrors backend/app/access/states.py::AccessErrorCode exactly. */
export const AccessErrorCode = {
  TOKEN_INVALID_OR_MISSING: 'token_invalid_or_missing',
  PLAN_EXPIRED: 'plan_expired',
  AUTH_SERVICE_UNAVAILABLE: 'auth_service_unavailable',
  WORK_SESSION_EXPIRED: 'work_session_expired',
} as const

export type AccessErrorCode = (typeof AccessErrorCode)[keyof typeof AccessErrorCode]

export class AccessApiError extends Error {
  errorCode: AccessErrorCode

  constructor(errorCode: AccessErrorCode, message: string) {
    super(message)
    this.name = 'AccessApiError'
    this.errorCode = errorCode
  }
}
