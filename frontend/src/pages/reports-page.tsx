import { useState } from "react"
import { useProjects } from "@/hooks/use-projects"
import { ReportsPanel } from "@/components/reports-panel"

export function ReportsPage() {
  const { data: projects, isLoading } = useProjects()
  const [selectedId, setSelectedId] = useState<string>("")

  const projectId = selectedId || projects?.[0]?.id || ""

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Reports</h1>
          <p className="mt-1 text-[13.5px] text-muted-foreground">Compliance summary and exports per project</p>
        </div>
        {projects && projects.length > 0 ? (
          <select
            value={projectId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="rounded-lg border border-border bg-card px-3 py-2 text-[13px] font-medium text-slate-700"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        ) : null}
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-sm text-muted-foreground">Loading projects…</div>
      ) : !projectId ? (
        <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center text-sm text-muted-foreground">
          Create a project and run matching to see compliance reports.
        </div>
      ) : (
        <ReportsPanel projectId={projectId} />
      )}
    </div>
  )
}
