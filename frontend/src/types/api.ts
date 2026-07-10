export type ProjectStatus = "draft" | "in_progress" | "in_review" | "completed" | string

export interface Project {
  id: string
  org_id: string
  name: string
  client_name: string | null
  status: ProjectStatus
  created_by: string
  created_at: string
  updated_at: string
}

export interface ProjectCreateInput {
  name: string
  client_name?: string | null
}

export interface ProjectUpdateInput {
  name?: string
  client_name?: string | null
  status?: string
}

export type DocType = "rfp" | "vendor_proposal"

export type DocumentStatus = "uploaded" | "processing" | "extracted" | "failed" | string

export interface Document {
  id: string
  org_id: string
  project_id: string
  doc_type: DocType
  vendor_name: string | null
  storage_path: string
  original_filename: string
  mime_type: string
  page_count: number | null
  status: DocumentStatus
  error_message: string | null
  uploaded_by: string
  created_at: string
}

export interface ExtractedRequirement {
  id: string
  document_id: string
  project_id: string
  requirement_key: string
  requirement_label: string
  category: string | null
  requirement_text: string
  expected_value: string | null
  unit: string | null
  operator: string | null
  is_mandatory: boolean
  source_page: number | null
  created_at: string
}

export interface ExtractedSpecification {
  id: string
  document_id: string
  project_id: string
  vendor_name: string
  spec_key: string
  spec_label: string
  spec_text: string
  value: string | null
  unit: string | null
  source_page: number | null
  created_at: string
}

export interface ApiErrorBody {
  success: false
  message: string
  error_code: string
}
