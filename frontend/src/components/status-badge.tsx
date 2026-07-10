import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<string, string> = {
  Completed: "bg-emerald-50 text-emerald-600",
  "In Review": "bg-blue-50 text-blue-600",
  "In Progress": "bg-amber-50 text-amber-600",
  Draft: "bg-slate-100 text-slate-500",
  Match: "bg-emerald-50 text-emerald-600",
  Partial: "bg-amber-50 text-amber-600",
  "No Match": "bg-red-50 text-red-600",
  Active: "bg-emerald-50 text-emerald-600",
  "Needs Review": "bg-red-50 text-red-600",
  uploaded: "bg-slate-100 text-slate-500",
  processing: "bg-amber-50 text-amber-600",
  extracted: "bg-emerald-50 text-emerald-600",
  failed: "bg-red-50 text-red-600",
}

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? "bg-slate-100 text-slate-500"
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11.5px] font-semibold whitespace-nowrap",
        style,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  )
}
