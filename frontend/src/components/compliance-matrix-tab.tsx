import { useMemo, useState } from "react"
import { toast } from "sonner"
import { Search, ChevronLeft, ChevronRight, X, RefreshCw } from "lucide-react"
import { useComplianceMatrix, useTriggerMatching } from "@/hooks/use-matching"
import { StatusBadge } from "@/components/status-badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { ComplianceMatrixEntry, Document } from "@/types/api"

const PAGE_SIZE = 8

function complianceColor(pct: number) {
  return pct >= 85 ? "#059669" : pct >= 60 ? "#D97706" : "#DC2626"
}

function scorePercent(entry: ComplianceMatrixEntry) {
  return Math.round(Number(entry.match_score ?? 0) * 100)
}

export function ComplianceMatrixTab({
  projectId,
  vendorDocuments,
}: {
  projectId: string
  vendorDocuments: Document[]
}) {
  const { data: entries, isLoading } = useComplianceMatrix(projectId)
  const triggerMatching = useTriggerMatching(projectId)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [vendorFilter, setVendorFilter] = useState<string>("all")
  const [page, setPage] = useState(1)
  const [selectedEntry, setSelectedEntry] = useState<ComplianceMatrixEntry | null>(null)
  const [isRunningAll, setIsRunningAll] = useState(false)

  const matchableDocuments = vendorDocuments.filter((d) => d.status === "extracted")

  const vendorNames = useMemo(
    () => Array.from(new Set((entries ?? []).map((e) => e.vendor_name))).sort(),
    [entries],
  )

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return (entries ?? []).filter((e) => {
      const matchesQ = !q || e.requirement_text.toLowerCase().includes(q)
      const matchesS = statusFilter === "all" || e.status === statusFilter
      const matchesV = vendorFilter === "all" || e.vendor_name === vendorFilter
      return matchesQ && matchesS && matchesV
    })
  }, [entries, search, statusFilter, vendorFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const start = (currentPage - 1) * PAGE_SIZE
  const paged = filtered.slice(start, start + PAGE_SIZE)

  const handleRunMatching = async () => {
    if (matchableDocuments.length === 0) {
      toast.error("No vendor datasheets have finished extraction yet.")
      return
    }
    setIsRunningAll(true)
    try {
      for (const doc of matchableDocuments) {
        await triggerMatching.mutateAsync(doc.id)
      }
      toast.success("Matching complete")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Matching failed")
    } finally {
      setIsRunningAll(false)
    }
  }

  if (!isLoading && (entries ?? []).length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center">
        <p className="mb-4 text-sm text-muted-foreground">
          {matchableDocuments.length === 0
            ? "Upload and extract an RFP and at least one vendor datasheet, then run matching."
            : "No matching results yet."}
        </p>
        <Button onClick={handleRunMatching} disabled={isRunningAll || matchableDocuments.length === 0}>
          <RefreshCw size={14} className={isRunningAll ? "animate-spin" : ""} />
          {isRunningAll ? "Running…" : "Run matching"}
        </Button>
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex flex-wrap items-center gap-2.5 border-b border-slate-100 p-3.5">
        <div className="relative w-65">
          <Search size={14} className="absolute top-1/2 left-2.75 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            placeholder="Search requirements…"
            className="h-8.5 bg-background pl-8 text-[13px]"
          />
        </div>
        {["all", "match", "partial", "no_match"].map((s) => (
          <button
            key={s}
            onClick={() => {
              setStatusFilter(s)
              setPage(1)
            }}
            className={cn(
              "rounded-lg border px-3 py-1.75 text-[12.5px] font-semibold whitespace-nowrap",
              statusFilter === s ? "border-primary bg-secondary text-primary" : "border-border bg-card text-slate-700",
            )}
          >
            {s === "all" ? "All" : s === "no_match" ? "No Match" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
        <select
          value={vendorFilter}
          onChange={(e) => {
            setVendorFilter(e.target.value)
            setPage(1)
          }}
          className="rounded-lg border border-border bg-card px-2.5 py-1.75 text-[12.5px] text-slate-700"
        >
          <option value="all">All vendors</option>
          {vendorNames.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
        <Button
          variant="outline"
          className="ml-auto h-8.5 text-[12.5px]"
          onClick={handleRunMatching}
          disabled={isRunningAll || matchableDocuments.length === 0}
        >
          <RefreshCw size={13} className={isRunningAll ? "animate-spin" : ""} />
          {isRunningAll ? "Running…" : "Re-run matching"}
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[820px] border-collapse">
          <thead>
            <tr className="bg-background">
              <th className="px-5 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Requirement
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Vendor
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Vendor Value
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Match
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Compliance
              </th>
            </tr>
          </thead>
          <tbody>
            {paged.map((entry) => (
              <tr
                key={entry.id}
                onClick={() => setSelectedEntry(entry)}
                className="cursor-pointer border-t border-slate-100 hover:bg-background"
              >
                <td className="max-w-70 px-5 py-3 text-[13px] font-medium text-foreground">
                  {entry.requirement_text}
                </td>
                <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">{entry.vendor_name}</td>
                <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">
                  {entry.vendor_value ?? "—"}
                </td>
                <td className="px-3 py-3">
                  <StatusBadge status={entry.status} />
                </td>
                <td className="px-3 py-3">
                  <div className="flex min-w-25 items-center gap-2">
                    <div className="h-1.5 max-w-17.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${scorePercent(entry)}%`, background: complianceColor(scorePercent(entry)) }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-slate-700">{scorePercent(entry)}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
        <span className="text-[12.5px] text-muted-foreground">
          Showing {filtered.length === 0 ? 0 : start + 1}–{Math.min(start + PAGE_SIZE, filtered.length)} of{" "}
          {filtered.length} matches
        </span>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border hover:bg-background"
          >
            <ChevronLeft size={13} />
          </button>
          <span className="px-1.5 text-[12.5px] font-semibold text-slate-700">
            {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border hover:bg-background"
          >
            <ChevronRight size={13} />
          </button>
        </div>
      </div>

      {selectedEntry ? (
        <>
          <div onClick={() => setSelectedEntry(null)} className="fixed inset-0 z-40 bg-slate-900/35" />
          <div className="fixed top-0 right-0 z-50 flex h-screen w-110 flex-col bg-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 px-5.5 py-4.5">
              <span className="text-[15px] font-bold text-foreground">Requirement Detail</span>
              <X size={18} className="cursor-pointer text-muted-foreground" onClick={() => setSelectedEntry(null)} />
            </div>
            <div className="flex-1 overflow-y-auto p-5.5">
              <div className="mb-5 text-[14.5px] leading-relaxed font-semibold text-foreground">
                {selectedEntry.requirement_text}
              </div>
              <div className="mb-5 flex gap-5">
                <StatusBadge status={selectedEntry.status} />
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-foreground">{scorePercent(selectedEntry)}%</span>
                  <span className="text-xs text-muted-foreground">match score</span>
                </div>
              </div>
              <div className="mb-4 rounded-lg bg-background p-3.5">
                <div className="mb-2 text-[11px] font-semibold text-muted-foreground uppercase">
                  Vendor Specification — {selectedEntry.vendor_name}
                </div>
                <div className="mb-1 text-[13.5px] font-medium text-foreground">
                  {selectedEntry.vendor_value ?? "Not specified"}
                </div>
                <div className="text-xs text-muted-foreground">
                  Expected: {selectedEntry.operator ?? ""} {selectedEntry.expected_value ?? "—"}{" "}
                  {selectedEntry.unit ?? ""}
                </div>
              </div>
              <div className="mb-4">
                <div className="mb-2 text-[11px] font-semibold text-muted-foreground uppercase">
                  Matching Explanation
                </div>
                <p className="text-[13px] leading-relaxed text-slate-700">{selectedEntry.rationale}</p>
              </div>
              {selectedEntry.source_page ? (
                <div className="flex items-center gap-3 rounded-lg border border-slate-100 p-3">
                  <div className="min-w-0 flex-1">
                    <div className="text-[11.5px] text-muted-foreground">Page {selectedEntry.source_page}</div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
