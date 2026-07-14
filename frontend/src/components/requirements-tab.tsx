import { useRequirements } from "@/hooks/use-extraction"
import type { Document } from "@/types/api"

const PRIORITY_COLOR: Record<string, string> = {
  true: "#DC2626",
  false: "#2563EB",
}

export function RequirementsTab({ projectId, rfpDocument }: { projectId: string; rfpDocument: Document | undefined }) {
  const { data: requirements, isLoading } = useRequirements(projectId, rfpDocument?.id)

  if (!rfpDocument) {
    return <EmptyState message="Upload an RFP document to extract requirements." />
  }
  if (rfpDocument.status !== "completed") {
    return <EmptyState message={`RFP is ${rfpDocument.status}. Requirements will appear once extraction completes.`} />
  }
  if (isLoading) {
    return <EmptyState message="Loading requirements…" />
  }
  if (!requirements || requirements.length === 0) {
    return <EmptyState message="No requirements were extracted from this RFP." />
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-background">
            <th className="px-5 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">#</th>
            <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
              Requirement
            </th>
            <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
              Category
            </th>
            <th className="px-5 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
              Mandatory
            </th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((r, i) => (
            <tr key={r.id} className="border-t border-slate-100">
              <td className="px-5 py-3 text-[12.5px] text-slate-400">{String(i + 1).padStart(2, "0")}</td>
              <td className="max-w-105 px-3 py-3 text-[13px] font-medium text-foreground">
                {r.requirement_text}
                {r.expected_value ? (
                  <span className="ml-1.5 text-xs text-muted-foreground">
                    ({r.operator ?? ""} {r.expected_value} {r.unit ?? ""})
                  </span>
                ) : null}
              </td>
              <td className="px-3 py-3 text-[12.5px] text-slate-500">{r.category ?? "—"}</td>
              <td className="px-5 py-3">
                <span
                  className="text-[11.5px] font-semibold"
                  style={{ color: PRIORITY_COLOR[String(r.is_mandatory)] }}
                >
                  {r.is_mandatory ? "Mandatory" : "Optional"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center text-sm text-muted-foreground">
      {message}
    </div>
  )
}
