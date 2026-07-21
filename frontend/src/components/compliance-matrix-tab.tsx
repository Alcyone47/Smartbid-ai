import { Fragment, useMemo, useState } from "react"
import { toast } from "sonner"
import { Search, ChevronLeft, ChevronRight, ChevronDown, ChevronRight as ChevronRightSmall, RefreshCw, X } from "lucide-react"
import { useComplianceMatrix, useTriggerMatching } from "@/hooks/use-matching"
import { StatusBadge } from "@/components/status-badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import type { Document, EquipmentComplianceGroup, EquipmentSpecComparison } from "@/types/api"

const PAGE_SIZE = 8

const SELECT_CLASS =
  "rounded-lg border border-border bg-card px-2.5 py-1.75 text-[12.5px] text-slate-700"

type ComplianceFilter = "all" | "match" | "partial" | "unmet" | "no_equipment"

function complianceColor(pct: number) {
  return pct >= 85 ? "#059669" : pct >= 60 ? "#D97706" : "#DC2626"
}

// An equipment's overall outcome: no vendor equipment was even found (Stage 1
// unmatched), fully met (all specs matched), unmet (nothing matched or partially
// credited), or partial (anything in between).
function overallStatus(group: EquipmentComplianceGroup): Exclude<ComplianceFilter, "all"> {
  if (group.match_status === "unmatched") return "no_equipment"
  if (group.total_specs > 0 && group.matched === group.total_specs) return "match"
  if (group.matched === 0 && group.partial === 0) return "unmet"
  return "partial"
}

function specScorePercent(spec: EquipmentSpecComparison) {
  return Math.round(Number(spec.match_score ?? 0) * 100)
}

function groupKey(group: EquipmentComplianceGroup) {
  return `${group.vendor_id}:${group.equipment_key}`
}

function expectedText(spec: EquipmentSpecComparison) {
  const parts = [spec.operator, spec.expected_value, spec.unit].filter(Boolean)
  return parts.length > 0 ? parts.join(" ") : "—"
}

export function ComplianceMatrixTab({
  projectId,
  vendorDocuments,
}: {
  projectId: string
  vendorDocuments: Document[]
}) {
  const { data: groups, isLoading } = useComplianceMatrix(projectId)
  const triggerMatching = useTriggerMatching(projectId)
  const [search, setSearch] = useState("")
  const [vendorFilter, setVendorFilter] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<ComplianceFilter>("all")
  const [page, setPage] = useState(1)
  const [expandedKey, setExpandedKey] = useState<string | null>(null)
  const [isRunningAll, setIsRunningAll] = useState(false)

  // A vendor is matchable once at least one of its PDFs has finished extraction.
  const matchableVendorIds = useMemo(
    () =>
      Array.from(
        new Set(
          vendorDocuments
            .filter((d) => d.status === "completed" && d.vendor_id)
            .map((d) => d.vendor_id as string),
        ),
      ),
    [vendorDocuments],
  )

  const vendorNames = useMemo(
    () => Array.from(new Set((groups ?? []).map((g) => g.vendor_name))).sort(),
    [groups],
  )

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return (groups ?? []).filter((g) => {
      const matchesQ = !q || g.equipment_label.toLowerCase().includes(q)
      const matchesV = vendorFilter === "all" || g.vendor_name === vendorFilter
      const matchesStatus = statusFilter === "all" || overallStatus(g) === statusFilter
      return matchesQ && matchesV && matchesStatus
    })
  }, [groups, search, vendorFilter, statusFilter])

  const filtersActive = search !== "" || vendorFilter !== "all" || statusFilter !== "all"

  const clearFilters = () => {
    setSearch("")
    setVendorFilter("all")
    setStatusFilter("all")
    setPage(1)
  }

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const start = (currentPage - 1) * PAGE_SIZE
  const paged = filtered.slice(start, start + PAGE_SIZE)

  const handleRunMatching = async () => {
    if (matchableVendorIds.length === 0) {
      toast.error("No vendor datasheets have finished extraction yet.")
      return
    }
    setIsRunningAll(true)
    try {
      for (const vendorId of matchableVendorIds) {
        await triggerMatching.mutateAsync(vendorId)
      }
      toast.success("Matching complete")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Matching failed")
    } finally {
      setIsRunningAll(false)
    }
  }

  if (!isLoading && (groups ?? []).length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center">
        <p className="mb-4 text-sm text-muted-foreground">
          {matchableVendorIds.length === 0
            ? "Upload and extract an RFP and at least one vendor datasheet, then run matching."
            : "No matching results yet."}
        </p>
        <Button onClick={handleRunMatching} disabled={isRunningAll || matchableVendorIds.length === 0}>
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
            placeholder="Search equipment…"
            className="h-8.5 bg-background pl-8 text-[13px]"
          />
        </div>
        <select
          value={vendorFilter}
          onChange={(e) => {
            setVendorFilter(e.target.value)
            setPage(1)
          }}
          className={SELECT_CLASS}
        >
          <option value="all">All vendors</option>
          {vendorNames.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value as ComplianceFilter)
            setPage(1)
          }}
          className={SELECT_CLASS}
        >
          <option value="all">All compliance</option>
          <option value="match">Match</option>
          <option value="partial">Partial match</option>
          <option value="unmet">Unmet</option>
          <option value="no_equipment">Equipment not found</option>
        </select>
        {filtersActive ? (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded-lg px-2 py-1.75 text-[12.5px] font-semibold text-slate-500 hover:bg-background hover:text-slate-700"
          >
            <X size={13} />
            Clear
          </button>
        ) : null}
        <Button
          variant="outline"
          className="ml-auto h-8.5 text-[12.5px]"
          onClick={handleRunMatching}
          disabled={isRunningAll || matchableVendorIds.length === 0}
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
                Equipment
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Vendor
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Specs
              </th>
              <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                Compliance
              </th>
            </tr>
          </thead>
          <tbody>
            {paged.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-[13px] text-muted-foreground">
                  No equipment match the current filters.{" "}
                  <button onClick={clearFilters} className="font-semibold text-primary hover:underline">
                    Clear filters
                  </button>
                </td>
              </tr>
            ) : null}
            {paged.map((group) => {
              const key = groupKey(group)
              const isUnmatched = group.match_status === "unmatched"
              const isExpanded = !isUnmatched && expandedKey === key
              return (
                <Fragment key={key}>
                  <tr
                    onClick={() => !isUnmatched && setExpandedKey(isExpanded ? null : key)}
                    className={`border-t border-slate-100 ${isUnmatched ? "" : "cursor-pointer hover:bg-background"}`}
                  >
                    <td className="px-5 py-3 text-[13px] font-medium text-foreground">
                      <div className="flex items-center gap-1.5">
                        {isUnmatched ? (
                          <span className="inline-block w-[15px]" />
                        ) : isExpanded ? (
                          <ChevronDown size={15} className="text-muted-foreground" />
                        ) : (
                          <ChevronRightSmall size={15} className="text-muted-foreground" />
                        )}
                        {group.equipment_label}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">{group.vendor_name}</td>
                    {isUnmatched ? (
                      <td colSpan={2} className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-500">
                        <StatusBadge status="no_equipment_match" />
                        <span className="ml-2">Equipment Not Found</span>
                      </td>
                    ) : (
                      <>
                        <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">
                          <span className="font-semibold text-emerald-600">{group.matched}</span>
                          {group.partial > 0 ? (
                            <span className="text-amber-600"> · {group.partial} partial</span>
                          ) : null}
                          <span className="text-muted-foreground"> / {group.total_specs} specs</span>
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex min-w-25 items-center gap-2">
                            <div className="h-1.5 max-w-17.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${group.compliance_pct}%`,
                                  background: complianceColor(group.compliance_pct),
                                }}
                              />
                            </div>
                            <span className="text-xs font-semibold text-slate-700">{group.compliance_pct}%</span>
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                  {isExpanded ? (
                    <tr className="border-t border-slate-100 bg-background">
                      <td colSpan={4} className="px-5 py-3">
                        <div className="overflow-x-auto rounded-lg border border-slate-100 bg-card">
                          <table className="w-full min-w-[700px] border-collapse">
                            <thead>
                              <tr className="bg-background">
                                <th className="px-4 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                  Required Spec
                                </th>
                                <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                  Required Value
                                </th>
                                <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                  Vendor Value
                                </th>
                                <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                  Status
                                </th>
                                <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                  Score
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {group.specs.map((spec) => (
                                <tr key={spec.id} className="border-t border-slate-100">
                                  <td className="px-4 py-2.5 text-[12.5px] font-medium text-foreground">
                                    {spec.requirement_label}
                                    {spec.is_mandatory ? (
                                      <span className="ml-1.5 text-[10px] font-semibold text-red-500">MANDATORY</span>
                                    ) : null}
                                    <div className="mt-0.5 text-[11.5px] font-normal text-muted-foreground">
                                      {spec.rationale}
                                    </div>
                                  </td>
                                  <td className="px-3 py-2.5 text-[12.5px] whitespace-nowrap text-slate-700">
                                    {expectedText(spec)}
                                  </td>
                                  <td className="px-3 py-2.5 text-[12.5px] whitespace-nowrap text-slate-700">
                                    {spec.vendor_value ?? "—"}
                                  </td>
                                  <td className="px-3 py-2.5">
                                    <StatusBadge status={spec.status} />
                                  </td>
                                  <td className="px-3 py-2.5 text-[12.5px] font-semibold text-slate-700">
                                    {specScorePercent(spec)}%
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
        <span className="text-[12.5px] text-muted-foreground">
          Showing {filtered.length === 0 ? 0 : start + 1}–{Math.min(start + PAGE_SIZE, filtered.length)} of{" "}
          {filtered.length} equipment
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
    </div>
  )
}
