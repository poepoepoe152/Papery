"use client";

import { History, Loader2, Search } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { VerificationSummary } from "@/lib/types";

const RESULT_STYLES: Record<string, string> = {
  PASS: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  WARN: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  FAIL: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
};

export default function HistoryPage() {
  const [items, setItems] = useState<VerificationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [result, setResult] = useState("");
  const [status, setStatus] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    const qs = new URLSearchParams();
    if (q) qs.set("q", q);
    if (result) qs.set("result", result);
    if (status) qs.set("status", status);
    try {
      const data = await apiFetch<VerificationSummary[]>(
        `/verifications?${qs.toString()}`
      );
      setItems(data);
    } finally {
      setLoading(false);
    }
  }, [q, result, status]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">History</h1>
          <p className="mt-1 text-slate-600 dark:text-slate-300">
            Search and re-open your previous verifications.
          </p>
        </div>
        <Link href="/dashboard/verify" className="btn-primary">
          New Verification
        </Link>
      </div>

      <div className="card flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            className="input pl-9"
            placeholder="Search by title…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <select className="input w-auto" value={result} onChange={(e) => setResult(e.target.value)}>
          <option value="">All results</option>
          <option value="PASS">Pass</option>
          <option value="WARN">Warn</option>
          <option value="FAIL">Fail</option>
        </select>
        <select className="input w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="COMPLETED">Completed</option>
          <option value="PROCESSING">Processing</option>
          <option value="QUEUED">Queued</option>
          <option value="FAILED">Failed</option>
        </select>
      </div>

      <div className="card overflow-x-auto p-0">
        {loading ? (
          <div className="flex items-center gap-2 p-6 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <History className="h-10 w-10 text-slate-400" />
            <p className="mt-3 text-sm text-slate-500">No verifications found.</p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800">
              <tr>
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Title</th>
                <th className="px-6 py-3">Type</th>
                <th className="px-6 py-3">User</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="px-6 py-3 text-slate-500">
                    {new Date(v.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-3 font-medium">
                    <Link href={`/dashboard/verify/${v.id}`} className="hover:text-brand-600">
                      {v.title}
                    </Link>
                  </td>
                  <td className="px-6 py-3 text-slate-500">{v.doc_types.join(", ") || "—"}</td>
                  <td className="px-6 py-3 text-slate-500">{v.created_by_name || "—"}</td>
                  <td className="px-6 py-3">
                    {v.status === "COMPLETED" ? (
                      <span className="text-xs text-slate-500">Completed</span>
                    ) : (
                      <span className="text-xs text-amber-600">{v.status}</span>
                    )}
                  </td>
                  <td className="px-6 py-3">
                    {v.overall_result ? (
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                          RESULT_STYLES[v.overall_result] || ""
                        }`}
                      >
                        {v.overall_result}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
