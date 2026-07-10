import { useMemo, useState } from "react"
import { Search, ChevronLeft, ChevronRight, X } from "lucide-react"
import { StatusBadge } from "@/components/status-badge"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface MatrixRow {
  requirement: string
  vendor: string
  vendorValue: string
  expectedValue: string
  status: "Match" | "Partial" | "No Match"
  compliance: number
  sourcePage: number
  sourceDoc: string
  explanation: string
}

const ROWS: MatrixRow[] = [
  { requirement: "SD-WAN throughput ≥ 1 Gbps per branch appliance", vendor: "Nexbridge Networks", vendorValue: "1.2 Gbps sustained", expectedValue: "≥ 1 Gbps", status: "Match", compliance: 100, sourcePage: 12, sourceDoc: "Nexbridge_Networks_SDX-9000_Datasheet.pdf", explanation: "Vendor-reported sustained throughput of 1.2 Gbps exceeds the 1 Gbps minimum stated in RFP section 4.2." },
  { requirement: "SD-WAN throughput ≥ 1 Gbps per branch appliance", vendor: "Solara Systems", vendorValue: "950 Mbps sustained", expectedValue: "≥ 1 Gbps", status: "Partial", compliance: 78, sourcePage: 8, sourceDoc: "Solara_Systems_EdgeConnect_Spec.pdf", explanation: "Datasheet reports 950 Mbps under standard conditions, just under the 1 Gbps threshold." },
  { requirement: "SD-WAN throughput ≥ 1 Gbps per branch appliance", vendor: "Vantage Point Technologies", vendorValue: "800 Mbps sustained", expectedValue: "≥ 1 Gbps", status: "No Match", compliance: 45, sourcePage: 5, sourceDoc: "Vantage_Point_VP-Edge_Proposal.docx", explanation: "Proposal specifies 800 Mbps max throughput, well below the 1 Gbps requirement." },
  { requirement: "Zero-touch provisioning within 15 minutes", vendor: "Nexbridge Networks", vendorValue: "8 minutes average", expectedValue: "≤ 15 minutes", status: "Match", compliance: 100, sourcePage: 22, sourceDoc: "Nexbridge_Networks_SDX-9000_Datasheet.pdf", explanation: "Cloud-orchestrated ZTP completes in an average of 8 minutes across 50-site pilot." },
  { requirement: "Zero-touch provisioning within 15 minutes", vendor: "Solara Systems", vendorValue: "18 minutes average", expectedValue: "≤ 15 minutes", status: "No Match", compliance: 38, sourcePage: 11, sourceDoc: "Solara_Systems_EdgeConnect_Spec.pdf", explanation: "Manual credential approval extends average deployment time to 18 minutes." },
  { requirement: "Native integration with Cisco ISE for NAC", vendor: "Nexbridge Networks", vendorValue: "Certified Cisco ISE integration", expectedValue: "Native ISE support", status: "Match", compliance: 100, sourcePage: 31, sourceDoc: "Nexbridge_Networks_SDX-9000_Datasheet.pdf", explanation: "Cisco-certified interoperability partner with native pxGrid integration." },
  { requirement: "Native integration with Cisco ISE for NAC", vendor: "Vantage Point Technologies", vendorValue: "Third-party plugin required", expectedValue: "Native ISE support", status: "No Match", compliance: 30, sourcePage: 9, sourceDoc: "Vantage_Point_VP-Edge_Proposal.docx", explanation: "Requires a paid third-party connector to interoperate with ISE." },
  { requirement: "AES-256 encryption for all site-to-site tunnels", vendor: "Nexbridge Networks", vendorValue: "AES-256-GCM", expectedValue: "AES-256", status: "Match", compliance: 100, sourcePage: 15, sourceDoc: "Nexbridge_Networks_SDX-9000_Datasheet.pdf", explanation: "Uses AES-256-GCM for all IPsec tunnels by default." },
  { requirement: "99.99% uptime SLA, failover under 2 seconds", vendor: "Solara Systems", vendorValue: "99.9% SLA, 3.5s failover", expectedValue: "99.99% / ≤2s", status: "No Match", compliance: 42, sourcePage: 21, sourceDoc: "Solara_Systems_EdgeConnect_Spec.pdf", explanation: "Both SLA percentage and failover latency fall short of the requirement." },
]

const VENDORS = ["Nexbridge Networks", "Solara Systems", "Vantage Point Technologies"]
const PAGE_SIZE = 6

function complianceColor(c: number) {
  return c >= 85 ? "#059669" : c >= 60 ? "#D97706" : "#DC2626"
}

export function ComplianceMatrixMock() {
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [vendorFilter, setVendorFilter] = useState<string>("all")
  const [page, setPage] = useState(1)
  const [selectedRow, setSelectedRow] = useState<MatrixRow | null>(null)

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return ROWS.filter((r) => {
      const matchesQ = !q || r.requirement.toLowerCase().includes(q)
      const matchesS = statusFilter === "all" || r.status === statusFilter
      const matchesV = vendorFilter === "all" || r.vendor === vendorFilter
      return matchesQ && matchesS && matchesV
    })
  }, [search, statusFilter, vendorFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const start = (currentPage - 1) * PAGE_SIZE
  const paged = filtered.slice(start, start + PAGE_SIZE)

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-card">
      <div className="border-b border-amber-100 bg-amber-50 px-5 py-2 text-xs font-medium text-amber-700">
        Demo data — the deterministic matching engine hasn't been built yet, so this tab isn't wired to real
        requirements/specifications.
      </div>

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
        {["all", "Match", "Partial", "No Match"].map((s) => (
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
            {s === "all" ? "All" : s}
          </button>
        ))}
        <select
          value={vendorFilter}
          onChange={(e) => {
            setVendorFilter(e.target.value)
            setPage(1)
          }}
          className="ml-auto rounded-lg border border-border bg-card px-2.5 py-1.75 text-[12.5px] text-slate-700"
        >
          <option value="all">All vendors</option>
          {VENDORS.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
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
            {paged.map((r, i) => (
              <tr
                key={i}
                onClick={() => setSelectedRow(r)}
                className="cursor-pointer border-t border-slate-100 hover:bg-background"
              >
                <td className="max-w-70 px-5 py-3 text-[13px] font-medium text-foreground">{r.requirement}</td>
                <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">{r.vendor}</td>
                <td className="px-3 py-3 text-[12.5px] whitespace-nowrap text-slate-700">{r.vendorValue}</td>
                <td className="px-3 py-3">
                  <StatusBadge status={r.status} />
                </td>
                <td className="px-3 py-3">
                  <div className="flex min-w-25 items-center gap-2">
                    <div className="h-1.5 max-w-17.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${r.compliance}%`, background: complianceColor(r.compliance) }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-slate-700">{r.compliance}%</span>
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

      {selectedRow ? (
        <>
          <div
            onClick={() => setSelectedRow(null)}
            className="fixed inset-0 z-40 bg-slate-900/35"
          />
          <div className="fixed top-0 right-0 z-50 flex h-screen w-110 flex-col bg-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 px-5.5 py-4.5">
              <span className="text-[15px] font-bold text-foreground">Requirement Detail</span>
              <X size={18} className="cursor-pointer text-muted-foreground" onClick={() => setSelectedRow(null)} />
            </div>
            <div className="flex-1 overflow-y-auto p-5.5">
              <div className="mb-5 text-[14.5px] leading-relaxed font-semibold text-foreground">
                {selectedRow.requirement}
              </div>
              <div className="mb-5 flex gap-5">
                <StatusBadge status={selectedRow.status} />
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-foreground">{selectedRow.compliance}%</span>
                  <span className="text-xs text-muted-foreground">compliant</span>
                </div>
              </div>
              <div className="mb-4 rounded-lg bg-background p-3.5">
                <div className="mb-2 text-[11px] font-semibold text-muted-foreground uppercase">
                  Vendor Specification — {selectedRow.vendor}
                </div>
                <div className="mb-1 text-[13.5px] font-medium text-foreground">{selectedRow.vendorValue}</div>
                <div className="text-xs text-muted-foreground">Expected: {selectedRow.expectedValue}</div>
              </div>
              <div className="mb-4">
                <div className="mb-2 text-[11px] font-semibold text-muted-foreground uppercase">
                  Matching Explanation
                </div>
                <p className="text-[13px] leading-relaxed text-slate-700">{selectedRow.explanation}</p>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-slate-100 p-3">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[12.5px] font-semibold text-foreground">{selectedRow.sourceDoc}</div>
                  <div className="text-[11.5px] text-muted-foreground">Page {selectedRow.sourcePage}</div>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
