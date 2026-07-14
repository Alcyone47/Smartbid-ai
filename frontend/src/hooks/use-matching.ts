import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { matchingApi } from "@/api/matching"

export const complianceMatrixKey = (projectId: string) => ["projects", projectId, "compliance-matrix"] as const
export const complianceSummaryKey = (projectId: string) => ["projects", projectId, "compliance-summary"] as const

export function useComplianceMatrix(projectId: string) {
  return useQuery({
    queryKey: complianceMatrixKey(projectId),
    queryFn: () => matchingApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useComplianceSummary(projectId: string) {
  return useQuery({
    queryKey: complianceSummaryKey(projectId),
    queryFn: () => matchingApi.summary(projectId),
    enabled: !!projectId,
  })
}

export function useTriggerMatching(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vendorId: string) => matchingApi.trigger(projectId, vendorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complianceMatrixKey(projectId) })
      queryClient.invalidateQueries({ queryKey: complianceSummaryKey(projectId) })
    },
  })
}
