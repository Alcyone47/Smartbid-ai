import { useState } from "react"
import { FileSpreadsheet, FileText, FileDown, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { useComplianceSummary } from "@/hooks/use-matching"
import { reportsApi } from "@/api/reports"
import { ApiError } from "@/lib/api-client"
import type { VendorComplianceSummary } from "@/types/api"

function complianceColor(pct: number) {
  return pct >= 85 ? "#059669" : pct >= 60 ? "#D97706" : "#DC2626"
}

export function ReportsPanel({ projectId }: { projectId: string }) {
  const { data: summaries, isLoading } = useComplianceSummary(projectId)
  const [downloading, setDownloading] = useState<string | null>(null)

  const rows = summaries ?? []
  const noData = rows.length === 0

  const handleDownload = async (key: string, fn: () => Promise<void>) => {
    setDownloading(key)
    try {
      await fn()
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Download failed")
    } finally {
      setDownloading(null)
    }
  }
  const avgCompliance =
    rows.length > 0 ? Math.round(rows.reduce((sum, r) => sum + r.overall_compliance_pct, 0) / rows.length) : 0
  const totalMatched = rows.reduce((sum, r) => sum + r.matched, 0)
  const totalMismatches = rows.reduce((sum, r) => sum + r.unmatched, 0)
  const leader = rows[0]

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ReportCard
          icon={FileSpreadsheet}
          iconBg="bg-emerald-50"
          iconColor="#059669"
          title="Excel Export"
          subtitle="Full compliance matrix, sortable"
          cta=".xlsx"
          disabled={noData}
          loading={downloading === "xlsx"}
          onClick={() => handleDownload("xlsx", () => reportsApi.matrixXlsx(projectId))}
        />
        <ReportCard
          icon={FileText}
          iconBg="bg-red-50"
          iconColor="#DC2626"
          title="PDF Report"
          subtitle="Executive summary, shareable"
          cta=".pdf"
          primary
          disabled={noData}
          loading={downloading === "pdf"}
          onClick={() => handleDownload("pdf", () => reportsApi.summaryPdf(projectId))}
        />
        <ReportCard
          icon={FileDown}
          iconBg="bg-secondary"
          iconColor="#2563EB"
          title="CSV Export"
          subtitle="Raw data for BI tools"
          cta=".csv"
          disabled={noData}
          loading={downloading === "csv"}
          onClick={() => handleDownload("csv", () => reportsApi.matrixCsv(projectId))}
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <div className="border-b border-slate-100 px-5 py-4 text-sm font-semibold text-foreground">
          Compliance Summary
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="py-8 text-center text-sm text-muted-foreground">Loading compliance summary…</div>
          ) : rows.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No compliance results yet. Run matching on this project's vendor datasheets first.
            </div>
          ) : (
            <>
              <div className="mb-5 flex flex-wrap gap-6">
                <SummaryStat value={`${avgCompliance}%`} label="Avg. compliance" color={complianceColor(avgCompliance)} />
                <SummaryStat value={String(totalMatched)} label="Requirements matched" />
                <SummaryStat value={String(totalMismatches)} label="Mismatches" color={totalMismatches > 0 ? "#DC2626" : undefined} />
                <SummaryStat value={String(rows.length)} label="Vendors compared" />
              </div>
              {leader ? (
                <div className="mb-4 text-[12.5px] leading-relaxed text-muted-foreground">
                  <span className="font-semibold text-foreground">{leader.vendor_name}</span> leads with{" "}
                  {leader.overall_compliance_pct}% overall compliance.
                </div>
              ) : null}
              <div className="flex flex-col gap-2">
                {rows.map((row) => (
                  <VendorRow key={row.vendor_name} row={row} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function VendorRow({ row }: { row: VendorComplianceSummary }) {
  const color = complianceColor(row.overall_compliance_pct)
  return (
    <div className="flex items-center gap-4 rounded-lg border border-slate-100 px-4 py-3">
      <div className="w-40 truncate text-[13.5px] font-semibold text-foreground">{row.vendor_name}</div>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full" style={{ width: `${row.overall_compliance_pct}%`, background: color }} />
      </div>
      <div className="w-12 text-right text-[13px] font-bold" style={{ color }}>
        {row.overall_compliance_pct}%
      </div>
      <div className="w-56 text-right text-[11.5px] text-muted-foreground">
        {row.matched} matched · {row.partial} partial · {row.unmatched} unmet
        <span className="ml-1 text-slate-400">
          (mandatory {row.mandatory_met}/{row.mandatory_total})
        </span>
      </div>
    </div>
  )
}

function SummaryStat({ value, label, color }: { value: string; label: string; color?: string }) {
  return (
    <div>
      <div className="text-xl font-bold" style={color ? { color } : undefined}>
        {value}
      </div>
      <div className="text-[11px] text-muted-foreground">{label}</div>
    </div>
  )
}

function ReportCard({
  icon: Icon,
  iconBg,
  iconColor,
  title,
  subtitle,
  cta,
  primary,
  disabled,
  loading,
  onClick,
}: {
  icon: typeof FileText
  iconBg: string
  iconColor: string
  title: string
  subtitle: string
  cta: string
  primary?: boolean
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
}) {
  const isDisabled = disabled || loading
  const base = "flex items-center justify-center gap-1.5 rounded-lg py-2 text-[13px] font-semibold transition-colors"
  const enabledStyle = primary
    ? "bg-primary text-white hover:bg-primary/90"
    : "border border-border text-foreground hover:bg-background"
  const disabledStyle = primary
    ? "cursor-not-allowed bg-primary/50 text-white"
    : "cursor-not-allowed border border-border text-muted-foreground"
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5">
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconBg}`}>
        <Icon size={17} style={{ color: iconColor }} />
      </div>
      <div>
        <div className="text-sm font-bold text-foreground">{title}</div>
        <div className="mt-0.5 text-xs text-muted-foreground">{subtitle}</div>
      </div>
      <button
        onClick={onClick}
        disabled={isDisabled}
        title={disabled && !loading ? "Run matching to enable exports" : undefined}
        className={`${base} ${isDisabled ? disabledStyle : enabledStyle}`}
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : null}
        {loading ? "Preparing…" : `Download ${cta}`}
      </button>
    </div>
  )
}
