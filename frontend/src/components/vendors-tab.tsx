import { useMemo, useState } from "react"
import { toast } from "sonner"
import { FileText, Trash2 } from "lucide-react"
import { useSpecifications, useTriggerExtraction } from "@/hooks/use-extraction"
import { useVendors } from "@/hooks/use-vendors"
import { StatusBadge } from "@/components/status-badge"
import { DocumentUploadDialog } from "@/components/document-upload-dialog"
import { DeleteVendorDialog } from "@/components/delete-vendor-dialog"
import type { Document, Vendor } from "@/types/api"

const LOGO_COLORS = ["#2563EB", "#7C3AED", "#0EA5E9", "#DC2626", "#059669", "#D97706"]

function initials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

export function VendorsTab({ projectId, vendorDocuments }: { projectId: string; vendorDocuments: Document[] }) {
  const { data: vendors } = useVendors(projectId)
  const [removingVendor, setRemovingVendor] = useState<Vendor | null>(null)

  const documentsByVendor = useMemo(() => {
    const map = new Map<string, Document[]>()
    for (const doc of vendorDocuments) {
      if (!doc.vendor_id) continue
      const list = map.get(doc.vendor_id)
      if (list) list.push(doc)
      else map.set(doc.vendor_id, [doc])
    }
    return map
  }, [vendorDocuments])

  if (!vendors || vendors.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center text-sm text-muted-foreground">
        No vendors yet. Upload a vendor datasheet to get started.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {vendors.map((vendor, i) => (
        <VendorCard
          key={vendor.id}
          projectId={projectId}
          vendor={vendor}
          documents={documentsByVendor.get(vendor.id) ?? []}
          logoBg={LOGO_COLORS[i % LOGO_COLORS.length]}
          onRemove={() => setRemovingVendor(vendor)}
        />
      ))}
      {removingVendor ? (
        <DeleteVendorDialog
          projectId={projectId}
          vendorId={removingVendor.id}
          vendorName={removingVendor.name}
          open={!!removingVendor}
          onOpenChange={() => setRemovingVendor(null)}
        />
      ) : null}
    </div>
  )
}

function VendorCard({
  projectId,
  vendor,
  documents,
  logoBg,
  onRemove,
}: {
  projectId: string
  vendor: Vendor
  documents: Document[]
  logoBg: string
  onRemove: () => void
}) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4.5">
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[13px] font-bold text-white"
          style={{ background: logoBg }}
        >
          {initials(vendor.name)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-[13.5px] font-bold text-foreground">{vendor.name}</div>
          <div className="text-[11.5px] text-muted-foreground">
            {documents.length} {documents.length === 1 ? "file" : "files"}
          </div>
        </div>
        <button
          onClick={onRemove}
          title="Remove vendor"
          className="shrink-0 text-slate-300 hover:text-destructive"
        >
          <Trash2 size={15} />
        </button>
      </div>

      <div className="flex flex-col gap-1.5">
        {documents.length === 0 ? (
          <div className="text-[12px] text-muted-foreground">No files uploaded yet.</div>
        ) : (
          documents.map((doc) => <VendorDocumentRow key={doc.id} projectId={projectId} document={doc} />)
        )}
      </div>

      <div className="mt-0.5 border-t border-slate-100 pt-2.5">
        <DocumentUploadDialog
          projectId={projectId}
          docType="vendor_proposal"
          triggerLabel="Add file"
          presetVendorName={vendor.name}
        />
      </div>
    </div>
  )
}

function VendorDocumentRow({ projectId, document }: { projectId: string; document: Document }) {
  const { data: specifications } = useSpecifications(
    projectId,
    document.status === "completed" ? document.id : undefined,
  )
  const triggerExtraction = useTriggerExtraction(projectId)

  const handleExtract = async () => {
    try {
      await triggerExtraction.mutateAsync(document.id)
      toast.success("Extraction started")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to start extraction")
    }
  }

  return (
    <div className="flex flex-col gap-1 rounded-lg bg-background px-2.5 py-1.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5">
          <FileText size={13} className="shrink-0 text-muted-foreground" />
          <span className="truncate text-[12px] text-slate-700">{document.original_filename}</span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="text-[11px] font-medium text-slate-500">
            {specifications ? `${specifications.length} specs` : "—"}
          </span>
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
        </div>
      </div>
      {document.status === "extracting" || document.status === "retrying" ? (
        <div className="flex items-center gap-2">
          <div className="h-1 max-w-40 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-amber-500 transition-all duration-500"
              style={{ width: `${document.extraction_progress}%` }}
            />
          </div>
          <span className="text-[11px] font-semibold text-amber-600">
            {document.status === "retrying" ? "Retrying…" : `${document.extraction_progress}%`}
          </span>
        </div>
      ) : null}
    </div>
  )
}
