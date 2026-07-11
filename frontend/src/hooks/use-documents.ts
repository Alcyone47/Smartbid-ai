import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { documentsApi } from "@/api/documents"
import type { DocType } from "@/types/api"

export const documentsKey = (projectId: string) => ["projects", projectId, "documents"] as const

export function useDocuments(projectId: string) {
  return useQuery({
    queryKey: documentsKey(projectId),
    queryFn: () => documentsApi.list(projectId),
    enabled: !!projectId,
    // Poll while any document is extracting so the progress bar advances live;
    // stops automatically once everything is extracted/failed.
    refetchInterval: (query) =>
      (query.state.data ?? []).some((doc) => doc.status === "processing") ? 2000 : false,
  })
}

export function useUploadDocument(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, docType, vendorName }: { file: File; docType: DocType; vendorName?: string }) =>
      documentsApi.upload(projectId, file, docType, vendorName),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsKey(projectId) }),
  })
}

export function useDeleteDocument(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: string) => documentsApi.remove(projectId, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsKey(projectId) }),
  })
}
