"use client";

import { UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Member, Role } from "@/lib/types";

const ROLE_OPTIONS: Role[] = ["ADMIN", "MANAGER", "STAFF"];

export default function TeamPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";

  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // add-member form
  const [showForm, setShowForm] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("STAFF");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<Member[]>("/team/members");
      setMembers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load members");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function addMember(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await apiFetch("/team/members", {
        method: "POST",
        body: { full_name: fullName, email, password, role },
      });
      setFullName("");
      setEmail("");
      setPassword("");
      setRole("STAFF");
      setShowForm(false);
      await load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to add member");
    } finally {
      setSubmitting(false);
    }
  }

  async function changeRole(id: string, newRole: Role) {
    try {
      await apiFetch(`/team/members/${id}`, {
        method: "PATCH",
        body: { role: newRole },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update role");
    }
  }

  async function toggleStatus(m: Member) {
    const newStatus = m.status === "DISABLED" ? "ACTIVE" : "DISABLED";
    try {
      await apiFetch(`/team/members/${m.id}`, {
        method: "PATCH",
        body: { status: newStatus },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team</h1>
          <p className="mt-1 text-slate-600 dark:text-slate-300">
            Manage your company members and their roles.
          </p>
        </div>
        {isAdmin && (
          <button onClick={() => setShowForm((s) => !s)} className="btn-primary">
            <UserPlus className="h-4 w-4" /> Add member
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
          {error}
        </div>
      )}

      {isAdmin && showForm && (
        <form onSubmit={addMember} className="card space-y-4">
          <h2 className="font-semibold">New team member</h2>
          {formError && (
            <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Full name</label>
              <input
                required
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                required
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Temporary password</label>
              <input
                type="text"
                required
                minLength={8}
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
              />
            </div>
            <div>
              <label className="label">Role</label>
              <select
                className="input"
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
              >
                <option value="STAFF">Staff</option>
                <option value="MANAGER">Manager</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Adding…" : "Add member"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="card overflow-x-auto p-0">
        {loading ? (
          <p className="p-6 text-sm text-slate-500">Loading members…</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800">
              <tr>
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Role</th>
                <th className="px-6 py-3">Status</th>
                {isAdmin && <th className="px-6 py-3 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {members.map((m) => {
                const isSelf = m.id === user?.id;
                return (
                  <tr key={m.id}>
                    <td className="px-6 py-3 font-medium">
                      {m.full_name}
                      {isSelf && (
                        <span className="ml-2 text-xs text-slate-400">(you)</span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-slate-600 dark:text-slate-300">
                      {m.email}
                    </td>
                    <td className="px-6 py-3">
                      {isAdmin && !isSelf ? (
                        <select
                          className="input py-1 text-xs"
                          value={m.role}
                          onChange={(e) => changeRole(m.id, e.target.value as Role)}
                        >
                          {ROLE_OPTIONS.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium dark:bg-slate-800">
                          {m.role}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${
                          m.status === "ACTIVE"
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                            : "bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                    {isAdmin && (
                      <td className="px-6 py-3 text-right">
                        {!isSelf && (
                          <button
                            onClick={() => toggleStatus(m)}
                            className="text-xs font-semibold text-brand-600 hover:underline"
                          >
                            {m.status === "DISABLED" ? "Enable" : "Disable"}
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
