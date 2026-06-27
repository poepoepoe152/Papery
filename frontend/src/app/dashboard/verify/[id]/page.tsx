"use client";

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, downloadReport } from "@/lib/api";
import type { Finding, Severity, VerificationDetail } from "@/lib/types";

const SEVERITY_STYLES: Record<Severity, string> = {
  CRITICAL: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
  MAJOR: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  MINOR: "bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
};

const RESULT_STYLES: Record<string, string> = {
  PASS: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
  WARN: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  FAIL: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
};

const STAGES = ["QUEUED", "EXTRACTING", "COMPARING", "DONE"];

export default function ResultPage() {
  const params = useParams();
  const id = params.id as string;
  const [detail, setDetail] = useState<VerificationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const d = await apiFetch<VerificationDetail>(`/verifications/${id}`);
      setDetail(d);
      return d.status;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
      return "FAILED";
    }
  }, [id]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let active = true;
    const tick = async () => {
      const status = await load();
      if (active && (status === "QUEUED" || status === "PROCESSING")) {
        timer = setTimeout(tick, 2000);
      }
    };
    tick();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [load]);

  // Merge reference + target field values keyed by field_key.
  const rows = useMemo(() => {
    if (!detail) return [];
    const ref: Record<string, string> = {};
    const tgt: Record<string, string> = {};
    const labels: Record<string, string> = {};
    for (const d of detail.documents) {
      for (const [k, v] of Object.entries(d.fields || {})) {
        const target = d.role === "REFERENCE" ? ref : tgt;
        if (!(k in target)) target[k] = v.raw;
      }
    }
    const findingByField: Record<string, Finding> = {};
    for (const f of detail.findings) {
      labels[f.field_key] = f.field_label || f.field_key;
      if (!(f.field_key in findingByField)) findingByField[f.field_key] = f;
    }
    const keys = Array.from(new Set([...Object.keys(ref), ...Object.keys(tgt)]));
    return keys.sort().map((k) => ({
      key: k,
      label: labels[k] || k,
      ref: ref[k] ?? null,
      tgt: tgt[k] ?? null,
      finding: findingByField[k] || null,
    }));
  }, [detail]);

  async function updateFinding(findingId: string, status: string) {
    try {
      await apiFetch(`/findings/${findingId}`, {
        method: "PATCH",
        body: { status },
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function onDownload(fmt: "PDF" | "XLSX" | "JSON") {
    setDownloading(fmt);
    try {
      await downloadReport(id, fmt);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  }

  if (error) {
    return (
      <div className="rounded-lg bg-rose-50 px-4 py-3 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
        {error}
      </div>
    );
  }
  if (!detail) {
    return (
      <div className="flex items-center gap-2 text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading…
      </div>
    );
  }

  const processing = detail.status === "QUEUED" || detail.status === "PROCESSING";

  return (
    <div className="space-y-6">
      <Link href="/dashboard/history" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-600">
        <ArrowLeft className="h-4 w-4" /> Back to history
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{detail.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {detail.doc_types.join(", ") || "—"}
          </p>
        </div>
        {detail.status === "COMPLETED" && (
          <div className="flex flex-wrap items-center gap-3">
            <span
              className={`rounded-full px-3 py-1 text-sm font-semibold ${
                RESULT_STYLES[detail.overall_result || ""] || ""
              }`}
            >
              {detail.overall_result}
            </span>
            <span className="text-sm text-slate-500">
              ● {detail.critical_count} Critical &nbsp;● {detail.major_count} Major
              &nbsp;● {detail.minor_count} Minor
            </span>
            <div className="flex gap-2">
              {(["PDF", "XLSX", "JSON"] as const).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => onDownload(fmt)}
                  className="btn-secondary px-3 py-2"
                  disabled={downloading === fmt}
                >
                  {downloading === fmt ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  {fmt}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {processing && (
        <div className="card">
          <div className="flex items-center gap-2 font-medium">
            <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
            Processing… {detail.stage}
          </div>
          <div className="mt-4 flex gap-2">
            {STAGES.map((stage) => {
              const reached =
                STAGES.indexOf(stage) <= STAGES.indexOf(detail.stage || "QUEUED");
              return (
                <div
                  key={stage}
                  className={`flex-1 rounded-full py-1 text-center text-xs ${
                    reached
                      ? "bg-brand-600 text-white"
                      : "bg-slate-200 text-slate-500 dark:bg-slate-800"
                  }`}
                >
                  {stage}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {detail.status === "FAILED" && (
        <div className="rounded-lg bg-rose-50 px-4 py-3 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
          Processing failed: {detail.error_message}
        </div>
      )}

      {detail.status === "COMPLETED" && (
        <>
          {/* Split-screen field comparison */}
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-xs uppercase text-slate-500 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Field</th>
                  <th className="px-4 py-3">Reference</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {rows.map((r) => {
                  const sev = r.finding?.severity;
                  const isProblem =
                    r.finding &&
                    !["NORMALIZED"].includes(r.finding.match_type);
                  return (
                    <tr key={r.key}>
                      <td className="px-4 py-3 font-medium">{r.label}</td>
                      <td className="px-4 py-3 font-mono text-xs">{r.ref ?? "—"}</td>
                      <td
                        className={`px-4 py-3 font-mono text-xs ${
                          isProblem && sev === "CRITICAL"
                            ? "text-rose-600"
                            : isProblem && sev === "MAJOR"
                            ? "text-amber-600"
                            : ""
                        }`}
                      >
                        {r.tgt ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {!r.finding ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                            <CheckCircle2 className="h-3.5 w-3.5" /> match
                          </span>
                        ) : (
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                              SEVERITY_STYLES[r.finding.severity]
                            }`}
                          >
                            {r.finding.match_type}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Findings detail */}
          <div>
            <h2 className="mb-3 text-lg font-semibold">
              Findings ({detail.findings.filter((f) => f.match_type !== "NORMALIZED").length})
            </h2>
            {detail.findings.length === 0 ? (
              <div className="card text-sm text-slate-500">
                No differences detected. All fields match.
              </div>
            ) : (
              <div className="space-y-3">
                {detail.findings.map((f) => (
                  <div key={f.id} className="card">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                              SEVERITY_STYLES[f.severity]
                            }`}
                          >
                            {f.severity}
                          </span>
                          <span className="font-semibold">{f.field_label}</span>
                          {f.status !== "OPEN" && (
                            <span className="text-xs text-slate-400">({f.status})</span>
                          )}
                        </div>
                        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                          {f.explanation}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-4 text-xs">
                          <span>
                            Reference:{" "}
                            <span className="font-mono">{f.reference_value ?? "—"}</span>
                          </span>
                          <span>
                            Detected:{" "}
                            <span className="font-mono">{f.detected_value ?? "—"}</span>
                          </span>
                          {f.suggested_fix && (
                            <span className="text-brand-600">
                              Suggested: <span className="font-mono">{f.suggested_fix}</span>
                            </span>
                          )}
                        </div>
                      </div>
                      {f.status === "OPEN" && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => updateFinding(f.id, "ACCEPTED")}
                            className="btn-secondary px-3 py-1.5 text-xs"
                          >
                            Accept
                          </button>
                          <button
                            onClick={() => updateFinding(f.id, "DISMISSED")}
                            className="btn-secondary px-3 py-1.5 text-xs"
                          >
                            Dismiss
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="mt-4 flex items-center gap-1 text-xs text-slate-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              Dismissals and corrections are stored as learning feedback for admin review.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
