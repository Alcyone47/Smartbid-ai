import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { extractionApi } from "@/api/extraction"
import { documentsKey } from "@/hooks/use-documents"

export function useTriggerExtraction(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: string) => extractionApi.trigger(projectId, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsKey(projectId) }),
  })
}

export function useRequirements(projectId: string, documentId: string | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "documents", documentId, "requirements"],
    queryFn: () => extractionApi.requirements(projectId, documentId as string),
    enabled: !!projectId && !!documentId,
  })
}

export function useSpecifications(projectId: string, documentId: string | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "documents", documentId, "specifications"],
    queryFn: () => extractionApi.specifications(projectId, documentId as string),
    enabled: !!projectId && !!documentId,
  })
}
