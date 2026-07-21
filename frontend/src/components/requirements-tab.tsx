import { useRequirements } from "@/hooks/use-extraction"
import type { Document, Requirement } from "@/types/api"

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
              Parameter
            </th>
            <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
              Minimum Required Specification
            </th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((requirement) => (
            <RequirementGroup key={requirement.id} requirement={requirement} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RequirementGroup({ requirement }: { requirement: Requirement }) {
  return (
    <>
      <tr className="border-t border-border bg-background/60">
        <td colSpan={3} className="px-5 py-2.5">
          <span className="text-[13px] font-semibold text-foreground">{requirement.equipment_label}</span>
          {requirement.category ? (
            <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
              {requirement.category}
            </span>
          ) : null}
          <span className="ml-2 text-[11.5px] text-slate-400">
            {requirement.parameters.length} parameter{requirement.parameters.length === 1 ? "" : "s"}
          </span>
        </td>
      </tr>
      {requirement.parameters.map((p, i) => (
        <tr key={p.id} className="border-t border-slate-100">
          <td className="px-5 py-3 text-[12.5px] text-slate-400">{String(i + 1).padStart(2, "0")}</td>
          <td className="max-w-105 px-3 py-3 text-[13px] font-medium text-foreground">
            {p.parameter_label}
            <span className="block text-[12px] font-normal text-muted-foreground">{p.parameter_text}</span>
          </td>
          <td className="px-3 py-3 text-[12.5px] text-slate-500">
            {p.expected_value ? (
              <span>
                {p.operator ?? ""} {p.expected_value} {p.unit ?? ""}
              </span>
            ) : (
              "—"
            )}
          </td>
        </tr>
      ))}
    </>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center text-sm text-muted-foreground">
      {message}
    </div>
  )
}
