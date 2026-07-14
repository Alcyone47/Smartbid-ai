import { apiRequest } from "@/lib/api-client"
import type { EquipmentComplianceGroup, VendorComplianceSummary } from "@/types/api"

export const matchingApi = {
  trigger: (projectId: string, vendorId: string) =>
    apiRequest<EquipmentComplianceGroup[]>(`/api/v1/projects/${projectId}/vendors/${vendorId}/match`, {
      method: "POST",
    }),
  list: (projectId: string) =>
    apiRequest<EquipmentComplianceGroup[]>(`/api/v1/projects/${projectId}/compliance-matrix`),
  summary: (projectId: string) =>
    apiRequest<VendorComplianceSummary[]>(`/api/v1/projects/${projectId}/compliance-summary`),
}
