export type ProjectStatus = "draft" | "in_progress" | "in_review" | "completed" | string

export interface Project {
  id: string
  org_id: string
  name: string
  client_name: string | null
  status: ProjectStatus
  status_override: ProjectStatus | null
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
  // null clears the override (back to auto-derived); omit to leave unchanged.
  status_override?: ProjectStatus | null
}

export type DocType = "rfp" | "vendor_proposal"

export type DocumentStatus = "queued" | "extracting" | "retrying" | "completed" | "failed" | string

export interface Vendor {
  id: string
  project_id: string
  name: string
  document_count: number
  created_at: string
}

export interface Document {
  id: string
  org_id: string
  project_id: string
  doc_type: DocType
  vendor_name: string | null
  vendor_id: string | null
  storage_path: string
  original_filename: string
  mime_type: string
  page_count: number | null
  status: DocumentStatus
  extraction_progress: number
  error_message: string | null
  uploaded_by: string
  created_at: string
}

// A single parameter of a requirement with its Minimum Required Specification.
export interface RequirementParameter {
  id: string
  requirement_id: string
  parameter_key: string
  parameter_label: string
  parameter_text: string
  expected_value: string | null
  unit: string | null
  operator: string | null
  is_mandatory: boolean
  source_page: number | null
  created_at: string
}

// A requirement is one equipment/item and holds a list of parameters.
export interface Requirement {
  id: string
  document_id: string
  project_id: string
  equipment_key: string
  equipment_label: string
  category: string | null
  source_page: number | null
  created_at: string
  parameters: RequirementParameter[]
}

export interface ExtractedSpecification {
  id: string
  document_id: string
  project_id: string
  vendor_name: string
  equipment_key: string
  equipment_label: string
  spec_key: string
  spec_label: string
  spec_text: string
  value: string | null
  unit: string | null
  source_page: number | null
  created_at: string
}

export type ComplianceStatus = "match" | "partial" | "no_match"

export interface EquipmentSpecComparison {
  id: string
  requirement_id: string
  matched_specification_id: string | null
  requirement_label: string
  requirement_text: string
  expected_value: string | null
  unit: string | null
  operator: string | null
  is_mandatory: boolean
  vendor_value: string | null
  source_page: number | null
  status: ComplianceStatus
  match_score: number | string | null
  rationale: string
}

export interface EquipmentComplianceGroup {
  equipment_key: string
  equipment_label: string
  vendor_name: string
  vendor_id: string
  compliance_pct: number
  total_specs: number
  matched: number
  partial: number
  unmatched: number
  specs: EquipmentSpecComparison[]
}

export interface VendorComplianceSummary {
  vendor_name: string
  overall_compliance_pct: number
  total_requirements: number
  matched: number
  partial: number
  unmatched: number
  mandatory_total: number
  mandatory_met: number
  mandatory_partial: number
  mandatory_unmet: number
  optional_total: number
  optional_met: number
  optional_partial: number
  optional_unmet: number
}

export interface ApiErrorBody {
  success: false
  message: string
  error_code: string
}
