/** Mirrors backend/app/access/states.py::AccessErrorCode exactly. */
export const AccessErrorCode = {
  TOKEN_INVALID_OR_MISSING: 'token_invalid_or_missing',
  PLAN_EXPIRED: 'plan_expired',
  AUTH_SERVICE_UNAVAILABLE: 'auth_service_unavailable',
  WORK_SESSION_EXPIRED: 'work_session_expired',
  // Fase 13 -- sibling of WORK_SESSION_EXPIRED for a brand-new session that
  // simply hasn't uploaded anything yet (as opposed to one that had data
  // and lost it to the TTL). `dashboard/hooks.ts`'s `isWorkSessionExpired`
  // deliberately does NOT match this code -- see DashboardPage.tsx: this
  // one should fall through to the WelcomeHub screen, not the "sessão
  // expirada" notice.
  NO_DATA_YET: 'no_data_yet',
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
