export type Role = "SUPER_ADMIN" | "ADMIN" | "MANAGER" | "STAFF";

export interface CompanyInfo {
  id: string;
  name: string;
  status: string;
}

export interface LicenseInfo {
  status: string;
  plan_name: string | null;
  expires_at: string | null;
  monthly_document_limit: number | null;
  max_users: number | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  status: string;
  company: CompanyInfo | null;
  license: LicenseInfo | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Member {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  status: string;
  last_login_at: string | null;
}

export interface FileInfo {
  id: string;
  original_name: string;
  size_bytes: number | null;
  mime_type: string | null;
}

export interface DocumentInfo {
  id: string;
  role: "REFERENCE" | "TARGET";
  original_name: string | null;
  doc_type: string | null;
  doc_type_label: string | null;
  doc_type_confidence: number | null;
  page_count: number | null;
  fields: Record<string, { raw: string; normalized: string; confidence: number }> | null;
  text: string | null;
}

export type Severity = "CRITICAL" | "MAJOR" | "MINOR";

export interface Finding {
  id: string;
  field_key: string;
  field_label: string | null;
  reference_value: string | null;
  detected_value: string | null;
  match_type: string;
  severity: Severity;
  confidence: number | null;
  explanation: string | null;
  suggested_fix: string | null;
  status: string;
}

export interface VerificationSummary {
  id: string;
  title: string;
  status: string;
  stage: string | null;
  overall_result: string | null;
  critical_count: number;
  major_count: number;
  minor_count: number;
  created_at: string;
  completed_at: string | null;
  created_by_name: string | null;
  doc_types: string[];
}

export interface VerificationDetail extends VerificationSummary {
  documents: DocumentInfo[];
  findings: Finding[];
  error_message: string | null;
}

export interface AdminStats {
  companies: number;
  active_companies: number;
  users: number;
  verifications: number;
  documents_processed: number;
  mrr_cents: number;
}

export interface AdminCompany {
  id: string;
  name: string;
  status: string;
  plan_name: string | null;
  license_status: string | null;
  expires_at: string | null;
  user_count: number;
  documents_used: number;
}

export interface AdminLicense {
  id: string;
  license_key: string;
  plan_name: string | null;
  status: string;
  company_name: string | null;
  expires_at: string | null;
}

export interface AdminPlan {
  id: string;
  name: string;
  monthly_document_limit: number;
  max_users: number;
  price_cents: number;
  is_active: boolean;
}
