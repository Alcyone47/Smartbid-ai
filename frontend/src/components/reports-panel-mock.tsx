import { FileSpreadsheet, FileText, FileDown } from "lucide-react"

export function ReportsPanelMock() {
  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-amber-100 bg-amber-50 px-4 py-2 text-xs font-medium text-amber-700">
        Demo data — report generation isn't implemented on the backend yet.
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <ReportCard icon={FileSpreadsheet} iconBg="bg-emerald-50" iconColor="#059669" title="Excel Export" subtitle="Full compliance matrix, sortable" cta=".xlsx" />
        <ReportCard icon={FileText} iconBg="bg-red-50" iconColor="#DC2626" title="PDF Report" subtitle="Executive summary, shareable" cta=".pdf" primary />
        <ReportCard icon={FileDown} iconBg="bg-secondary" iconColor="#2563EB" title="CSV Export" subtitle="Raw data for BI tools" cta=".csv" />
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <div className="border-b border-slate-100 px-5 py-4 text-sm font-semibold text-foreground">Report Preview</div>
        <div className="bg-background p-6">
          <div className="mx-auto max-w-140 rounded-lg border border-border bg-card p-7 shadow-sm">
            <div className="mb-1 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
              SmartBid AI · Compliance Summary
            </div>
            <div className="mb-3.5 text-[17px] font-bold text-foreground">Enterprise SD-WAN Modernization</div>
            <div className="mb-4 flex gap-5">
              <div>
                <div className="text-xl font-bold text-emerald-600">86%</div>
                <div className="text-[11px] text-muted-foreground">Avg. compliance</div>
              </div>
              <div>
                <div className="text-xl font-bold text-foreground">24</div>
                <div className="text-[11px] text-muted-foreground">Requirements matched</div>
              </div>
              <div>
                <div className="text-xl font-bold text-destructive">3</div>
                <div className="text-[11px] text-muted-foreground">Mismatches</div>
              </div>
            </div>
            <div className="mb-3.5 h-px bg-slate-100" />
            <div className="text-[12.5px] leading-relaxed text-muted-foreground">
              Nexbridge Networks leads with 94% overall compliance, followed by Orbital Compute at 87%.
            </div>
          </div>
        </div>
      </div>
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
}: {
  icon: typeof FileText
  iconBg: string
  iconColor: string
  title: string
  subtitle: string
  cta: string
  primary?: boolean
}) {
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
        disabled
        className={
          primary
            ? "cursor-not-allowed rounded-lg bg-primary/50 py-2 text-[13px] font-semibold text-white"
            : "cursor-not-allowed rounded-lg border border-border py-2 text-[13px] font-semibold text-foreground"
        }
      >
        Download {cta}
      </button>
    </div>
  )
}
