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
