"use client";

import { useAuth } from "@/lib/auth";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-3 last:border-0 dark:border-slate-800">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-medium">{value ?? "—"}</span>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const license = user?.license;

  const expires = license?.expires_at
    ? new Date(license.expires_at).toLocaleDateString()
    : "—";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          Your profile, company, and license details.
        </p>
      </div>

      <div className="card">
        <h2 className="mb-2 text-lg font-semibold">Profile</h2>
        <Row label="Name" value={user?.full_name} />
        <Row label="Email" value={user?.email} />
        <Row label="Role" value={user?.role} />
      </div>

      <div className="card">
        <h2 className="mb-2 text-lg font-semibold">Company</h2>
        <Row label="Company" value={user?.company?.name} />
        <Row label="Status" value={user?.company?.status} />
      </div>

      <div className="card">
        <h2 className="mb-2 text-lg font-semibold">License</h2>
        <Row label="Plan" value={license?.plan_name} />
        <Row label="Status" value={license?.status} />
        <Row label="Monthly document limit" value={license?.monthly_document_limit} />
        <Row label="Maximum users" value={license?.max_users} />
        <Row label="Expires" value={expires} />
      </div>
    </div>
  );
}
