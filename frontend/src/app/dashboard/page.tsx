"use client";

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Loader2,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { VerificationSummary } from "@/lib/types";

const RESULT_STYLES: Record<string, string> = {
  PASS: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  WARN: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  FAIL: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const license = user?.license;
  const [items, setItems] = useState<VerificationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<VerificationSummary[]>("/verifications?limit=100")
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const completed = items.filter((v) => v.status === "COMPLETED");
  const totalCritical = completed.reduce((n, v) => n + v.critical_count, 0);
  const passed = completed.filter((v) => v.overall_result === "PASS").length;

  const stats = [
    {
      label: "Verifications",
      value: items.length,
      sub: license?.monthly_document_limit
        ? `${license.monthly_document_limit} docs/mo limit`
        : "",
      icon: FileText,
    },
    { label: "Critical errors found", value: totalCritical, sub: "all time", icon: AlertTriangle },
    { label: "Verifications passed", value: passed, sub: "all time", icon: CheckCircle2 },
    {
      label: "Plan",
      value: license?.plan_name || "—",
      sub: license?.max_users ? `up to ${license.max_users} users` : "",
      icon: Users,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">
          Welcome back, {user?.full_name?.split(" ")[0]}
        </h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          Here&apos;s an overview of your verification workspace.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="card">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">{s.label}</p>
              <s.icon className="h-5 w-5 text-brand-600" />
            </div>
            <p className="mt-3 text-3xl font-bold">{s.value}</p>
            {s.sub && <p className="mt-1 text-xs text-slate-400">{s.sub}</p>}
          </div>
        ))}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold">Start a new verification</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Upload reference and target documents to detect mismatches.
        </p>
        <Link href="/dashboard/verify" className="btn-primary mt-4">
          New Verification
        </Link>
      </div>

      <div className="card">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent activity</h2>
          <Link href="/dashboard/history" className="text-sm text-brand-600 hover:underline">
            View all
          </Link>
        </div>
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">
            No verifications yet. Start your first one above.
          </p>
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {items.slice(0, 5).map((v) => (
              <li key={v.id} className="flex items-center justify-between py-3">
                <Link
                  href={`/dashboard/verify/${v.id}`}
                  className="font-medium hover:text-brand-600"
                >
                  {v.title}
                </Link>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400">
                    {new Date(v.created_at).toLocaleDateString()}
                  </span>
                  {v.overall_result ? (
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        RESULT_STYLES[v.overall_result] || ""
                      }`}
                    >
                      {v.overall_result}
                    </span>
                  ) : (
                    <span className="text-xs text-amber-600">{v.status}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
