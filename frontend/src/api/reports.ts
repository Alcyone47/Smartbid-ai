import { downloadFile } from "@/lib/api-client"

const base = (projectId: string) => `/api/v1/projects/${projectId}/reports`

export const reportsApi = {
  matrixXlsx: (projectId: string) =>
    downloadFile(`${base(projectId)}/matrix.xlsx`, "compliance-matrix.xlsx"),
  matrixCsv: (projectId: string) =>
    downloadFile(`${base(projectId)}/matrix.csv`, "compliance-matrix.csv"),
  summaryPdf: (projectId: string) =>
    downloadFile(`${base(projectId)}/summary.pdf`, "compliance-summary.pdf"),
}
