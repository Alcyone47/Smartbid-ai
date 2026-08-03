import { apiRequest } from "@/lib/api-client"
import type { OrgMe } from "@/types/api"

export const orgApi = {
  me: () => apiRequest<OrgMe>("/api/v1/org/me"),
}
