import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { vendorsApi } from "@/api/vendors"
import { documentsKey } from "@/hooks/use-documents"
import { complianceMatrixKey, complianceSummaryKey } from "@/hooks/use-matching"

export const vendorsKey = (projectId: string) => ["projects", projectId, "vendors"] as const

export function useVendors(projectId: string) {
  return useQuery({
    queryKey: vendorsKey(projectId),
    queryFn: () => vendorsApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useCreateVendor(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => vendorsApi.create(projectId, name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: vendorsKey(projectId) }),
  })
}

export function useDeleteVendor(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vendorId: string) => vendorsApi.remove(projectId, vendorId),
    onSuccess: () => {
      // Removing a vendor cascades to its documents, specs, and compliance rows.
      queryClient.invalidateQueries({ queryKey: vendorsKey(projectId) })
      queryClient.invalidateQueries({ queryKey: documentsKey(projectId) })
      queryClient.invalidateQueries({ queryKey: complianceMatrixKey(projectId) })
      queryClient.invalidateQueries({ queryKey: complianceSummaryKey(projectId) })
    },
  })
}
