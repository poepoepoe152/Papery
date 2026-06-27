"use client";

import { UploadCloud } from "lucide-react";

export default function VerifyPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">New Verification</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          Upload reference and target documents to verify.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {["Reference documents", "Target document(s)"].map((title) => (
          <div key={title} className="card">
            <h2 className="font-semibold">{title}</h2>
            <div className="mt-4 flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 py-12 text-center dark:border-slate-700">
              <UploadCloud className="h-10 w-10 text-slate-400" />
              <p className="mt-3 text-sm text-slate-500">
                Drag &amp; drop or browse
              </p>
              <p className="mt-1 text-xs text-slate-400">PDF · DOCX · PNG · JPG · TIFF</p>
            </div>
          </div>
        ))}
      </div>

      <div className="card border-amber-200 bg-amber-50 dark:border-amber-900/40 dark:bg-amber-900/20">
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Document upload, OCR, and AI comparison are implemented in upcoming
          phases (Phases 5–11). This page is the placeholder for the verification
          workflow.
        </p>
      </div>
    </div>
  );
}
