import { ReportsPanelMock } from "@/components/reports-panel-mock"

export function ReportsPage() {
  return (
    <div>
      <div className="mb-5">
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">Reports</h1>
        <p className="mt-1 text-[13.5px] text-muted-foreground">Export compliance results across projects</p>
      </div>
      <ReportsPanelMock />
    </div>
  )
}
