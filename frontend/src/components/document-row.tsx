import { toast } from "sonner"
import { FileText, Trash2 } from "lucide-react"
import { useDeleteDocument } from "@/hooks/use-documents"
import { useTriggerExtraction } from "@/hooks/use-extraction"
import { StatusBadge } from "@/components/status-badge"
import type { Document } from "@/types/api"

export function DocumentRow({ projectId, document }: { projectId: string; document: Document }) {
  const triggerExtraction = useTriggerExtraction(projectId)
  const deleteDocument = useDeleteDocument(projectId)

  const handleExtract = async () => {
    try {
      await triggerExtraction.mutateAsync(document.id)
      toast.success("Extraction started")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to start extraction")
    }
  }

  const handleDelete = async () => {
    try {
      await deleteDocument.mutateAsync(document.id)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete document")
    }
  }

  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-100 px-3 py-2.75">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
        <FileText size={16} className="text-primary" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] font-semibold text-foreground">{document.original_filename}</div>
        <div className="text-[11.5px] text-slate-400">
          {document.vendor_name ? `${document.vendor_name} · ` : ""}
          {document.page_count ? `${document.page_count} pages` : document.mime_type}
          {document.error_message ? ` · ${document.error_message}` : ""}
        </div>
      </div>
      <StatusBadge status={document.status} />
      {document.status === "uploaded" || document.status === "failed" ? (
        <button
          onClick={handleExtract}
          disabled={triggerExtraction.isPending}
          className="text-xs font-semibold text-primary whitespace-nowrap"
        >
          {triggerExtraction.isPending ? "Starting…" : "Extract"}
        </button>
      ) : null}
      <Trash2
        size={15}
        className="shrink-0 cursor-pointer text-slate-300 hover:text-destructive"
        onClick={handleDelete}
      />
    </div>
  )
}
