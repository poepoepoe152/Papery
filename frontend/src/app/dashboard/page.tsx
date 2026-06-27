"use client";

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Users,
} from "lucide-react";
import Link from "next/link";

import { useAuth } from "@/lib/auth";

export default function DashboardPage() {
  const { user } = useAuth();
  const license = user?.license;

  const stats = [
    {
      label: "Documents this month",
      value: "0",
      sub: license?.monthly_document_limit
        ? `of ${license.monthly_document_limit} limit`
        : "",
      icon: FileText,
    },
    { label: "Critical errors found", value: "0", sub: "all time", icon: AlertTriangle },
    { label: "Verifications passed", value: "0", sub: "all time", icon: CheckCircle2 },
    {
      label: "Team members",
      value: "—",
      sub: license?.max_users ? `up to ${license.max_users}` : "",
      icon: Users,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {user?.full_name?.split(" ")[0]}</h1>
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
          Document processing (OCR & AI comparison) arrives in upcoming phases.
        </p>
        <Link href="/dashboard/verify" className="btn-primary mt-4">
          New Verification
        </Link>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold">Recent activity</h2>
        <p className="mt-3 text-sm text-slate-500">
          No verifications yet. Your history will appear here.
        </p>
      </div>
    </div>
  );
}
