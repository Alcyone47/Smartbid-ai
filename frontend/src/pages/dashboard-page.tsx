import { Link, useNavigate } from "@tanstack/react-router"
import { Plus, FolderPlus, FileText, CheckCircle2 } from "lucide-react"
import { useProjects } from "@/hooks/use-projects"
import { StatusBadge } from "@/components/status-badge"
import { Button } from "@/components/ui/button"

export function DashboardPage() {
  const { data: projects, isLoading } = useProjects()
  const navigate = useNavigate()

  const recentProjects = [...(projects ?? [])]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Dashboard</h1>
          <p className="mt-1 text-[13.5px] text-muted-foreground">
            Here's what's happening across your bids.
          </p>
        </div>
        <Button onClick={() => navigate({ to: "/projects" })}>
          <Plus size={15} strokeWidth={2.5} />
          New Project
        </Button>
      </div>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div className="rounded-xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <span className="text-[14.5px] font-semibold text-foreground">Recent Projects</span>
            <Link to="/projects" className="text-[12.5px] font-semibold text-primary">
              View all
            </Link>
          </div>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-background">
                <th className="px-5 py-2.5 text-left text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                  Project
                </th>
                <th className="px-3 py-2.5 text-left text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={2} className="px-5 py-6 text-center text-sm text-muted-foreground">
                    Loading…
                  </td>
                </tr>
              ) : recentProjects.length === 0 ? (
                <tr>
                  <td colSpan={2} className="px-5 py-6 text-center text-sm text-muted-foreground">
                    No projects yet.
                  </td>
                </tr>
              ) : (
                recentProjects.map((p) => (
                  <tr
                    key={p.id}
                    className="cursor-pointer border-t border-slate-100 hover:bg-background"
                    onClick={() => navigate({ to: "/projects/$projectId", params: { projectId: p.id } })}
                  >
                    <td className="px-5 py-3">
                      <div className="text-[13.5px] font-semibold text-foreground">{p.name}</div>
                      <div className="text-xs text-slate-400">{p.client_name ?? "—"}</div>
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge status={p.status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <span className="text-[14.5px] font-semibold text-foreground">Quick Actions</span>
          </div>
          <div className="flex flex-col gap-1 p-3">
            <QuickAction
              icon={FolderPlus}
              iconBg="bg-secondary"
              iconColor="#2563EB"
              title="Start new project"
              subtitle="Upload an RFP to begin"
              onClick={() => navigate({ to: "/projects" })}
            />
            <QuickAction
              icon={FileText}
              iconBg="bg-violet-50"
              iconColor="#7C3AED"
              title="Browse vendors"
              subtitle="Compare submissions"
              onClick={() => navigate({ to: "/vendors" })}
            />
            <QuickAction
              icon={CheckCircle2}
              iconBg="bg-emerald-50"
              iconColor="#10B981"
              title="Open a project"
              subtitle="Compare vendors & export"
              onClick={() => navigate({ to: "/projects" })}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function QuickAction({
  icon: Icon,
  iconBg,
  iconColor,
  title,
  subtitle,
  onClick,
}: {
  icon: typeof FolderPlus
  iconBg: string
  iconColor: string
  title: string
  subtitle: string
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      className="flex cursor-pointer items-center gap-2.75 rounded-lg px-2.5 py-2.5 hover:bg-background"
    >
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
        <Icon size={15} strokeWidth={2} style={{ color: iconColor }} />
      </div>
      <div>
        <div className="text-[13px] font-semibold text-foreground">{title}</div>
        <div className="text-[11.5px] text-slate-400">{subtitle}</div>
      </div>
    </div>
  )
}
