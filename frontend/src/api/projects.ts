import { apiRequest } from "@/lib/api-client"
import type { Project, ProjectCreateInput, ProjectUpdateInput } from "@/types/api"

export const projectsApi = {
  list: () => apiRequest<Project[]>("/api/projects"),
  get: (projectId: string) => apiRequest<Project>(`/api/projects/${projectId}`),
  create: (input: ProjectCreateInput) => apiRequest<Project>("/api/projects", { method: "POST", body: input }),
  update: (projectId: string, input: ProjectUpdateInput) =>
    apiRequest<Project>(`/api/projects/${projectId}`, { method: "PATCH", body: input }),
  remove: (projectId: string) => apiRequest<void>(`/api/projects/${projectId}`, { method: "DELETE" }),
}
