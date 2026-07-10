import { useSpecifications } from "@/hooks/use-extraction"
import { StatusBadge } from "@/components/status-badge"
import type { Document } from "@/types/api"

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
  if (vendorDocuments.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center text-sm text-muted-foreground">
        No vendor datasheets uploaded yet.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {vendorDocuments.map((doc, i) => (
        <VendorCard
          key={doc.id}
          projectId={projectId}
          document={doc}
          logoBg={LOGO_COLORS[i % LOGO_COLORS.length]}
        />
      ))}
    </div>
  )
}

function VendorCard({
  projectId,
  document,
  logoBg,
}: {
  projectId: string
  document: Document
  logoBg: string
}) {
  const { data: specifications } = useSpecifications(
    projectId,
    document.status === "extracted" ? document.id : undefined,
  )

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4.5">
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[13px] font-bold text-white"
          style={{ background: logoBg }}
        >
          {initials(document.vendor_name ?? "?")}
        </div>
        <div>
          <div className="text-[13.5px] font-bold text-foreground">{document.vendor_name ?? "Unknown vendor"}</div>
          <div className="text-[11.5px] text-muted-foreground">{document.original_filename}</div>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <StatusBadge status={document.status} />
        <span className="text-[12px] font-medium text-slate-500">
          {specifications ? `${specifications.length} specs extracted` : "—"}
        </span>
      </div>
    </div>
  )
}
