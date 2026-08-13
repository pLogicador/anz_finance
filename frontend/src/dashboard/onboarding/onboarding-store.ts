import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Just a "has this browser seen the tour" flag -- not user data, safe to
 * persist (unlike the AI settings store, which deliberately never
 * persists a user's own API key). Shared by the auto-shown onboarding
 * tour and the "Ver tour novamente" entry in the help center/command
 * palette.
 */
interface OnboardingState {
  seen: boolean
  markSeen: () => void
  reset: () => void
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      seen: false,
      markSeen: () => set({ seen: true }),
      reset: () => set({ seen: false }),
    }),
    { name: 'anz-finance-onboarding' },
  ),
)
