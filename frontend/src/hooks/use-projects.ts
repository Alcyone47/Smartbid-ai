import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { projectsApi } from "@/api/projects"
import type { ProjectCreateInput, ProjectUpdateInput } from "@/types/api"

export const projectsKey = ["projects"] as const
export const projectKey = (id: string) => ["projects", id] as const

export function useProjects() {
  return useQuery({ queryKey: projectsKey, queryFn: projectsApi.list })
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectKey(projectId),
    queryFn: () => projectsApi.get(projectId),
    enabled: !!projectId,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProjectCreateInput) => projectsApi.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: projectsKey }),
  })
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProjectUpdateInput) => projectsApi.update(projectId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKey })
      queryClient.invalidateQueries({ queryKey: projectKey(projectId) })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (projectId: string) => projectsApi.remove(projectId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: projectsKey }),
  })
}
