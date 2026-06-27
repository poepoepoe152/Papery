"use client";

import { Building2, KeyRound, Loader2, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  AdminCompany,
  AdminLicense,
  AdminPlan,
  AdminStats,
} from "@/lib/types";

function money(cents: number) {
  return `$${(cents / 100).toLocaleString()}`;
}

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [companies, setCompanies] = useState<AdminCompany[]>([]);
  const [licenses, setLicenses] = useState<AdminLicense[]>([]);
  const [plans, setPlans] = useState<AdminPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newPlanId, setNewPlanId] = useState("");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, c, l, p] = await Promise.all([
        apiFetch<AdminStats>("/admin/stats"),
        apiFetch<AdminCompany[]>("/admin/companies"),
        apiFetch<AdminLicense[]>("/admin/licenses"),
        apiFetch<AdminPlan[]>("/admin/plans"),
      ]);
      setStats(s);
      setCompanies(c);
      setLicenses(l);
      setPlans(p);
      if (p.length && !newPlanId) setNewPlanId(p[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [newPlanId]);

  useEffect(() => {
    load();
  }, [load]);

  async function setCompanyStatus(id: string, status: string) {
    try {
      await apiFetch(`/admin/companies/${id}?status=${status}`, { method: "PATCH" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function generateLicense() {
    if (!newPlanId) return;
    setCreating(true);
    try {
      await apiFetch("/admin/licenses", {
        method: "POST",
        body: { plan_id: newPlanId },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate");
    } finally {
      setCreating(false);
    }
  }

  if (user?.role !== "SUPER_ADMIN") {
    return (
      <div className="rounded-lg bg-rose-50 px-4 py-3 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
        This area is restricted to platform administrators.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading…
      </div>
    );
  }

  const statCards = stats
    ? [
        { label: "Companies", value: stats.companies },
        { label: "Active companies", value: stats.active_companies },
        { label: "Users", value: stats.users },
        { label: "Verifications", value: stats.verifications },
        { label: "Documents processed", value: stats.documents_processed },
        { label: "MRR", value: money(stats.mrr_cents) },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Admin Panel</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          Platform-wide companies, licenses, plans, and usage.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-6">
        {statCards.map((s) => (
          <div key={s.label} className="card">
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className="mt-2 text-2xl font-bold">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Companies */}
      <div>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          <Building2 className="h-5 w-5" /> Companies
        </h2>
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800">
              <tr>
                <th className="px-6 py-3">Company</th>
                <th className="px-6 py-3">Plan</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Users</th>
                <th className="px-6 py-3">Docs</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {companies.map((c) => (
                <tr key={c.id}>
                  <td className="px-6 py-3 font-medium">{c.name}</td>
                  <td className="px-6 py-3 text-slate-500">{c.plan_name || "—"}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        c.status === "ACTIVE"
                          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                          : "bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-slate-500">{c.user_count}</td>
                  <td className="px-6 py-3 text-slate-500">{c.documents_used}</td>
                  <td className="px-6 py-3 text-right">
                    {c.status === "SUSPENDED" ? (
                      <button
                        onClick={() => setCompanyStatus(c.id, "ACTIVE")}
                        className="text-xs font-semibold text-emerald-600 hover:underline"
                      >
                        Activate
                      </button>
                    ) : (
                      <button
                        onClick={() => setCompanyStatus(c.id, "SUSPENDED")}
                        className="text-xs font-semibold text-rose-600 hover:underline"
                      >
                        Suspend
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Licenses */}
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <KeyRound className="h-5 w-5" /> Licenses
          </h2>
          <div className="flex items-center gap-2">
            <select
              className="input w-auto"
              value={newPlanId}
              onChange={(e) => setNewPlanId(e.target.value)}
            >
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <button onClick={generateLicense} className="btn-primary" disabled={creating}>
              <Plus className="h-4 w-4" /> Generate key
            </button>
          </div>
        </div>
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800">
              <tr>
                <th className="px-6 py-3">Key</th>
                <th className="px-6 py-3">Plan</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Company</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {licenses.map((l) => (
                <tr key={l.id}>
                  <td className="px-6 py-3 font-mono text-xs">{l.license_key}</td>
                  <td className="px-6 py-3 text-slate-500">{l.plan_name || "—"}</td>
                  <td className="px-6 py-3 text-slate-500">{l.status}</td>
                  <td className="px-6 py-3 text-slate-500">{l.company_name || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
