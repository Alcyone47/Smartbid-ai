import { useQuery } from "@tanstack/react-query"
import { projectsApi } from "@/api/projects"
import { documentsApi } from "@/api/documents"

export interface VendorSummary {
  vendorName: string
  documentCount: number
  lastUpdated: string
  status: "Active" | "In Progress" | "Needs Review"
}

export function useVendorSummaries() {
  return useQuery({
    queryKey: ["vendor-summaries"],
    queryFn: async (): Promise<VendorSummary[]> => {
      const projects = await projectsApi.list()
      const documentsByProject = await Promise.all(projects.map((p) => documentsApi.list(p.id)))
      const vendorDocs = documentsByProject
        .flat()
        .filter((d) => d.doc_type === "vendor_proposal" && d.vendor_name)

      const byVendor = new Map<string, { documents: typeof vendorDocs }>()
      for (const doc of vendorDocs) {
        const name = doc.vendor_name as string
        const entry = byVendor.get(name)
        if (entry) entry.documents.push(doc)
        else byVendor.set(name, { documents: [doc] })
      }

      return Array.from(byVendor.entries())
        .map(([vendorName, { documents }]) => {
          const lastUpdated = documents.reduce(
            (latest, d) => (new Date(d.created_at) > new Date(latest) ? d.created_at : latest),
            documents[0].created_at,
          )
          const hasFailed = documents.some((d) => d.status === "failed")
          const allExtracted = documents.every((d) => d.status === "extracted")
          const status: VendorSummary["status"] = hasFailed ? "Needs Review" : allExtracted ? "Active" : "In Progress"
          return { vendorName, documentCount: documents.length, lastUpdated, status }
        })
        .sort((a, b) => a.vendorName.localeCompare(b.vendorName))
    },
  })
}
