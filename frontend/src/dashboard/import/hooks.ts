import { useMutation } from '@tanstack/react-query'

import { commitCsv, previewCsv } from './api'

export function usePreviewCsv() {
  return useMutation({ mutationFn: previewCsv })
}

export function useCommitCsv() {
  return useMutation({ mutationFn: commitCsv })
}
