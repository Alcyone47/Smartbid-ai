import { Fragment, useState } from "react"
import { ChevronDown, ChevronRight as ChevronRightSmall } from "lucide-react"
import { useVendorStackOptimization } from "@/hooks/use-matching"
import { StatusBadge } from "@/components/status-badge"
import type { OptimizedEquipmentSelection } from "@/types/api"

function complianceColor(pct: number) {
  return pct >= 85 ? "#059669" : pct >= 60 ? "#D97706" : "#DC2626"
}

function rowKey(selection: OptimizedEquipmentSelection) {
  return selection.equipment_key
}

export function VendorStackOptimizationTab({ projectId }: { projectId: string }) {
  const { data, isLoading } = useVendorStackOptimization(projectId)
  const [expandedKey, setExpandedKey] = useState<string | null>(null)

  const equipment = data?.equipment ?? []
  const vendorUsage = data?.vendor_usage ?? []
  const overallPct = data?.overall_optimized_compliance_pct ?? 0

  if (!isLoading && equipment.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card py-12 text-center">
        <p className="text-sm text-muted-foreground">
          Run matching for at least one vendor on the Compliance Matrix tab to see the recommended vendor stack.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-4 rounded-xl border border-border bg-card p-4.5">
        <div>
          <div className="mb-0.75 text-[11.5px] text-slate-400">Optimized Stack Compliance</div>
          <div className="text-[22px] font-bold" style={{ color: complianceColor(overallPct) }}>
            {overallPct}%
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          {vendorUsage.map((usage) => (
            <span
              key={usage.vendor_id}
              className="rounded-md bg-background px-2.5 py-1.25 text-[12px] font-semibold text-slate-600"
            >
              {usage.vendor_name} × {usage.equipment_count}
            </span>
          ))}
        </div>
      </div>

      <div className="relative overflow-hidden rounded-xl border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] border-collapse">
            <thead>
              <tr className="bg-background">
                <th className="px-5 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                  Equipment
                </th>
                <th className="px-3 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">
                  Recommended Vendor
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
              {equipment.map((selection) => {
                const key = rowKey(selection)
                const isUnmatched = selection.match_status === "unmatched"
                const isExpanded = expandedKey === key
                return (
                  <Fragment key={key}>
                    <tr
                      onClick={() => setExpandedKey(isExpanded ? null : key)}
                      className="cursor-pointer border-t border-slate-100 hover:bg-background"
                    >
                      <td className="px-5 py-3 text-[13px] font-medium text-foreground">
                        <div className="flex items-center gap-1.5">
                          {isExpanded ? (
                            <ChevronDown size={15} className="text-muted-foreground" />
                          ) : (
                            <ChevronRightSmall size={15} className="text-muted-foreground" />
                          )}
                          {selection.equipment_label}
                        </div>
                      </td>
                      {isUnmatched ? (
                        <td colSpan={3} className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-500">
                          <StatusBadge status="no_equipment_match" />
                          <span className="ml-2">No vendor matched this equipment</span>
                        </td>
                      ) : (
                        <>
                          <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">
                            {selection.best_vendor_name}
                          </td>
                          <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">
                            <span className="font-semibold text-emerald-600">{selection.matched}</span>
                            {selection.partial > 0 ? (
                              <span className="text-amber-600"> · {selection.partial} partial</span>
                            ) : null}
                            <span className="text-muted-foreground"> / {selection.total_specs} specs</span>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex min-w-25 items-center gap-2">
                              <div className="h-1.5 max-w-17.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                                <div
                                  className="h-full rounded-full"
                                  style={{
                                    width: `${selection.compliance_pct}%`,
                                    background: complianceColor(selection.compliance_pct),
                                  }}
                                />
                              </div>
                              <span className="text-xs font-semibold text-slate-700">
                                {selection.compliance_pct}%
                              </span>
                            </div>
                          </td>
                        </>
                      )}
                    </tr>
                    {isExpanded ? (
                      <tr className="border-t border-slate-100 bg-background">
                        <td colSpan={4} className="px-5 py-3">
                          <div className="overflow-x-auto rounded-lg border border-slate-100 bg-card">
                            <table className="w-full min-w-[600px] border-collapse">
                              <thead>
                                <tr className="bg-background">
                                  <th className="px-4 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                    Vendor
                                  </th>
                                  <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                    Compliance
                                  </th>
                                  <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                    Match Status
                                  </th>
                                  <th className="px-3 py-2 text-left text-[10.5px] font-semibold text-muted-foreground uppercase">
                                    Confidence
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                {selection.candidates.map((candidate) => (
                                  <tr key={candidate.vendor_id} className="border-t border-slate-100">
                                    <td className="px-4 py-2.5 text-[12.5px] font-medium text-foreground">
                                      {candidate.vendor_name}
                                      {candidate.vendor_id === selection.best_vendor_id ? (
                                        <span className="ml-1.5 text-[10px] font-semibold text-emerald-600">
                                          RECOMMENDED
                                        </span>
                                      ) : null}
                                    </td>
                                    <td className="px-3 py-2.5 text-[12.5px] whitespace-nowrap text-slate-700">
                                      {candidate.compliance_pct}%
                                    </td>
                                    <td className="px-3 py-2.5">
                                      <StatusBadge
                                        status={candidate.match_status === "matched" ? "match" : "no_equipment_match"}
                                      />
                                    </td>
                                    <td className="px-3 py-2.5 text-[12.5px] whitespace-nowrap text-slate-700">
                                      {candidate.equipment_match_confidence != null
                                        ? `${Math.round(candidate.equipment_match_confidence)}%`
                                        : "—"}
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
      </div>
    </div>
  )
}
