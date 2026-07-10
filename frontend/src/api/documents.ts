import { apiRequest } from "@/lib/api-client"
import type { DocType, Document } from "@/types/api"

export const documentsApi = {
  list: (projectId: string) => apiRequest<Document[]>(`/api/projects/${projectId}/documents`),
  get: (projectId: string, documentId: string) =>
    apiRequest<Document>(`/api/projects/${projectId}/documents/${documentId}`),
  upload: (projectId: string, file: File, docType: DocType, vendorName?: string) => {
    const formData = new FormData()
    formData.append("doc_type", docType)
    if (vendorName) formData.append("vendor_name", vendorName)
    formData.append("file", file)
    return apiRequest<Document>(`/api/projects/${projectId}/documents`, { method: "POST", formData })
  },
  remove: (projectId: string, documentId: string) =>
    apiRequest<void>(`/api/projects/${projectId}/documents/${documentId}`, { method: "DELETE" }),
}
