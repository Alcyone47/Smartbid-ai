import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { matchingApi } from "@/api/matching"

export const complianceMatrixKey = (projectId: string) => ["projects", projectId, "compliance-matrix"] as const

export function useComplianceMatrix(projectId: string) {
  return useQuery({
    queryKey: complianceMatrixKey(projectId),
    queryFn: () => matchingApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useTriggerMatching(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: string) => matchingApi.trigger(projectId, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: complianceMatrixKey(projectId) }),
  })
}
