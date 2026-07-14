import { apiRequest } from "@/lib/api-client"
import type { Vendor } from "@/types/api"

export const vendorsApi = {
  list: (projectId: string) => apiRequest<Vendor[]>(`/api/projects/${projectId}/vendors`),
  create: (projectId: string, name: string) =>
    apiRequest<Vendor>(`/api/projects/${projectId}/vendors`, { method: "POST", body: { name } }),
  remove: (projectId: string, vendorId: string) =>
    apiRequest<void>(`/api/projects/${projectId}/vendors/${vendorId}`, { method: "DELETE" }),
}
