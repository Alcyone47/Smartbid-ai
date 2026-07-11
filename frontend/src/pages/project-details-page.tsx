import { useState } from "react"
import { Link, useParams } from "@tanstack/react-router"
import { FileText, CheckCircle2, Circle } from "lucide-react"
import { useProject } from "@/hooks/use-projects"
import { useDocuments } from "@/hooks/use-documents"
import { useComplianceMatrix } from "@/hooks/use-matching"
import { StatusBadge } from "@/components/status-badge"
import { DocumentUploadDialog } from "@/components/document-upload-dialog"
import { DocumentRow } from "@/components/document-row"
import { RequirementsTab } from "@/components/requirements-tab"
import { VendorsTab } from "@/components/vendors-tab"
import { ComplianceMatrixTab } from "@/components/compliance-matrix-tab"
import { ReportsPanel } from "@/components/reports-panel"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function ProjectDetailsPage() {
  const { projectId } = useParams({ from: "/_app/projects/$projectId" })
  const { data: project, isLoading: isProjectLoading } = useProject(projectId)
  const { data: documents } = useDocuments(projectId)
  const { data: complianceEntries } = useComplianceMatrix(projectId)
  const [tab, setTab] = useState("requirements")

  if (isProjectLoading || !project) {
    return <div className="py-10 text-center text-sm text-muted-foreground">Loading…</div>
  }

  const rfpDocuments = (documents ?? []).filter((d) => d.doc_type === "rfp")
  const vendorDocuments = (documents ?? []).filter((d) => d.doc_type === "vendor_proposal")
  const rfpDocument = rfpDocuments[0]

  const rfpExtracted = rfpDocument?.status === "extracted"
  const vendorsExtracted = vendorDocuments.length > 0 && vendorDocuments.every((d) => d.status === "extracted")

  return (
    <div>
      <div className="mb-2.5 flex items-center gap-2 text-[12.5px] text-slate-400">
        <Link to="/projects" className="font-medium text-slate-400">
          Projects
        </Link>
        <span>/</span>
        <span className="font-semibold text-slate-700">{project.name}</span>
      </div>

      <div className="mb-5.5 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-[21px] font-bold tracking-tight text-foreground">{project.name}</h1>
            <StatusBadge status={project.status} />
          </div>
          <p className="mt-1 text-[13.5px] text-muted-foreground">
            {project.client_name ?? "No client set"} · Created{" "}
            {new Date(project.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
          </p>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-1 items-start gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-border bg-card p-4.5">
            <div className="mb-3.5 text-[13.5px] font-semibold text-foreground">Project Information</div>
            <div className="grid grid-cols-2 gap-3.5">
              <Field label="Client" value={project.client_name ?? "—"} />
              <Field label="Vendors" value={`${vendorDocuments.length} in comparison`} />
              <Field label="Status" value={project.status} />
              <Field
                label="Created"
                value={new Date(project.created_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              />
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4.5">
            <div className="mb-3.5 flex items-center justify-between">
              <span className="text-[13.5px] font-semibold text-foreground">Uploaded RFP</span>
              {rfpDocuments.length === 0 ? (
                <DocumentUploadDialog projectId={projectId} docType="rfp" triggerLabel="Upload RFP" />
              ) : null}
            </div>
            <div className="flex flex-col gap-2">
              {rfpDocuments.length === 0 ? (
                <p className="text-xs text-muted-foreground">No RFP uploaded yet.</p>
              ) : (
                rfpDocuments.map((doc) => <DocumentRow key={doc.id} projectId={projectId} document={doc} />)
              )}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-4.5">
            <div className="mb-3.5 flex items-center justify-between">
              <span className="text-[13.5px] font-semibold text-foreground">Uploaded Vendor Datasheets</span>
              <DocumentUploadDialog projectId={projectId} docType="vendor_proposal" triggerLabel="Add vendor" />
            </div>
            <div className="flex flex-col gap-2">
              {vendorDocuments.length === 0 ? (
                <p className="text-xs text-muted-foreground">No vendor datasheets uploaded yet.</p>
              ) : (
                vendorDocuments.map((doc) => <DocumentRow key={doc.id} projectId={projectId} document={doc} />)
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-border bg-card p-4.5">
            <div className="mb-3.5 text-[13.5px] font-semibold text-foreground">Processing Status</div>
            <div className="flex flex-col gap-3">
              <ProcessingStep
                label="RFP requirements extracted"
                meta={rfpDocument ? rfpDocument.status : "not started"}
                done={rfpExtracted}
                available
              />
              <ProcessingStep
                label="Vendor datasheets parsed"
                meta={`${vendorDocuments.filter((d) => d.status === "extracted").length} of ${vendorDocuments.length}`}
                done={vendorsExtracted}
                available
              />
              <ProcessingStep
                label="Requirement matching"
                meta={complianceEntries && complianceEntries.length > 0 ? `${complianceEntries.length} entries` : "not run yet"}
                done={!!complianceEntries && complianceEntries.length > 0}
                available
              />
            </div>
          </div>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          <TabsTrigger value="vendors">Vendors</TabsTrigger>
          <TabsTrigger value="compliance">Compliance Matrix</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>
        <TabsContent value="requirements" className="mt-5">
          <RequirementsTab projectId={projectId} rfpDocument={rfpDocument} />
        </TabsContent>
        <TabsContent value="vendors" className="mt-5">
          <VendorsTab projectId={projectId} vendorDocuments={vendorDocuments} />
        </TabsContent>
        <TabsContent value="compliance" className="mt-5">
          <ComplianceMatrixTab projectId={projectId} vendorDocuments={vendorDocuments} />
        </TabsContent>
        <TabsContent value="reports" className="mt-5">
          <ReportsPanel projectId={projectId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mb-0.75 text-[11.5px] text-slate-400">{label}</div>
      <div className="text-[13px] font-semibold text-foreground">{value}</div>
    </div>
  )
}

function ProcessingStep({
  label,
  meta,
  done,
  available,
}: {
  label: string
  meta: string
  done: boolean
  available: boolean
}) {
  return (
    <div className={`flex items-center gap-2.5 ${available ? "" : "opacity-40"}`}>
      {done ? (
        <CheckCircle2 size={18} className="shrink-0 text-emerald-600" />
      ) : (
        <Circle size={18} className="shrink-0 text-slate-300" />
      )}
      <span className="flex-1 text-[13px] text-slate-700">{label}</span>
      <span className="text-[11.5px] font-medium text-slate-400">
        {available ? <FileText size={0} /> : null}
        {meta}
      </span>
    </div>
  )
}
