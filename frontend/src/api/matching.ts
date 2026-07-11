import { apiRequest } from "@/lib/api-client"
import type { ComplianceMatrixEntry } from "@/types/api"

export const matchingApi = {
  trigger: (projectId: string, documentId: string) =>
    apiRequest<ComplianceMatrixEntry[]>(`/api/v1/projects/${projectId}/documents/${documentId}/match`, {
      method: "POST",
    }),
  list: (projectId: string) =>
    apiRequest<ComplianceMatrixEntry[]>(`/api/v1/projects/${projectId}/compliance-matrix`),
}
