import { apiRequest } from "@/lib/api-client"
import type { Document, ExtractedRequirement, ExtractedSpecification } from "@/types/api"

export const extractionApi = {
  trigger: (projectId: string, documentId: string) =>
    apiRequest<Document>(`/api/v1/projects/${projectId}/documents/${documentId}/extract`, { method: "POST" }),
  requirements: (projectId: string, documentId: string) =>
    apiRequest<ExtractedRequirement[]>(`/api/v1/projects/${projectId}/documents/${documentId}/requirements`),
  specifications: (projectId: string, documentId: string) =>
    apiRequest<ExtractedSpecification[]>(`/api/v1/projects/${projectId}/documents/${documentId}/specifications`),
}
