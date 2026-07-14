import { useMemo, useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { Search, Calendar, MoreVertical, Pencil, Trash2 } from "lucide-react"
import { useProjects } from "@/hooks/use-projects"
import { StatusBadge } from "@/components/status-badge"
import { CreateProjectDialog } from "@/components/create-project-dialog"
import { EditProjectDialog } from "@/components/edit-project-dialog"
import { DeleteProjectDialog } from "@/components/delete-project-dialog"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import type { Project } from "@/types/api"

const STATUS_FILTERS = ["all", "draft", "in_progress", "in_review", "completed"]

export function ProjectsPage() {
  const { data: projects, isLoading } = useProjects()
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [editing, setEditing] = useState<Project | null>(null)
  const [deleting, setDeleting] = useState<Project | null>(null)

  const filtered = useMemo(() => {
    return (projects ?? []).filter((p) => {
      const q = search.toLowerCase()
      const matchesQ = !q || p.name.toLowerCase().includes(q) || (p.client_name ?? "").toLowerCase().includes(q)
      const matchesStatus = statusFilter === "all" || p.status === statusFilter
      return matchesQ && matchesStatus
    })
  }, [projects, search, statusFilter])

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Projects</h1>
          <p className="mt-1 text-[13.5px] text-muted-foreground">{projects?.length ?? 0} projects</p>
        </div>
        <CreateProjectDialog />
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-2.5">
        <div className="relative w-70">
          <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search projects…"
            className="pl-8.5"
          />
        </div>
        {STATUS_FILTERS.map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={cn(
              "rounded-lg border px-3.25 py-2 text-[13px] font-semibold whitespace-nowrap",
              statusFilter === status
                ? "border-primary bg-secondary text-primary"
                : "border-border bg-card text-slate-700",
            )}
          >
            {status === "all" ? "All" : status.replace("_", " ")}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="py-10 text-center text-sm text-muted-foreground">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="py-10 text-center text-sm text-muted-foreground">No projects match your filters.</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <div
              key={p.id}
              className="flex flex-col gap-3.5 rounded-xl border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-2.5">
                <div className="min-w-0">
                  <div className="text-[15px] leading-tight font-bold tracking-tight text-foreground">{p.name}</div>
                  <div className="mt-0.5 text-[12.5px] text-muted-foreground">{p.client_name ?? "No client set"}</div>
                </div>
                <div className="flex items-center gap-1.5">
                  <StatusBadge status={p.status} />
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        aria-label="Project actions"
                        className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-background"
                      >
                        <MoreVertical size={16} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onSelect={() => setEditing(p)}>
                        <Pencil size={14} />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem variant="destructive" onSelect={() => setDeleting(p)}>
                        <Trash2 size={14} />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-[12.5px] font-medium text-slate-700">
                <Calendar size={14} className="text-muted-foreground" />
                {new Date(p.created_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </div>
              <button
                onClick={() => navigate({ to: "/projects/$projectId", params: { projectId: p.id } })}
                className="mt-0.5 w-full rounded-lg border border-border py-2 text-[13px] font-semibold text-foreground hover:border-slate-300 hover:bg-background"
              >
                View Details
              </button>
            </div>
          ))}
        </div>
      )}

      {editing ? (
        <EditProjectDialog project={editing} open={!!editing} onOpenChange={() => setEditing(null)} />
      ) : null}
      {deleting ? (
        <DeleteProjectDialog project={deleting} open={!!deleting} onOpenChange={() => setDeleting(null)} />
      ) : null}
    </div>
  )
}
