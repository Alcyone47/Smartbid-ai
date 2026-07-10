import type { LucideIcon } from "lucide-react"

interface KpiCardProps {
  label: string
  value: string
  delta?: string
  icon: LucideIcon
  accent?: string
}

export function KpiCard({ label, value, delta, icon: Icon, accent = "#2563EB" }: KpiCardProps) {
  return (
    <div className="flex flex-col gap-2.5 rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-[12.5px] font-semibold text-muted-foreground">{label}</span>
        <div
          className="flex h-6.5 w-6.5 items-center justify-center rounded-md"
          style={{ background: `${accent}1A` }}
        >
          <Icon size={13} strokeWidth={2.5} style={{ color: accent }} />
        </div>
      </div>
      <div className="text-[26px] font-bold tracking-tight text-foreground">{value}</div>
      {delta ? <div className="text-xs font-semibold text-emerald-600">{delta}</div> : null}
    </div>
  )
}
