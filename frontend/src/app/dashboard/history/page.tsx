"use client";

import { History } from "lucide-react";

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">History</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          Search and re-download your previous verifications.
        </p>
      </div>

      <div className="card flex flex-col items-center justify-center py-16 text-center">
        <History className="h-10 w-10 text-slate-400" />
        <p className="mt-3 text-sm text-slate-500">No verifications yet.</p>
        <p className="mt-1 text-xs text-slate-400">
          History &amp; search arrive in Phase 12.
        </p>
      </div>
    </div>
  );
}
