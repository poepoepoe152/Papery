"use client";

import { FileText, Loader2, UploadCloud, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { apiFetch, uploadFile } from "@/lib/api";
import type { FileInfo, VerificationDetail } from "@/lib/types";

const ACCEPT = ".pdf,.docx,.png,.jpg,.jpeg,.tiff,.tif";

interface Slot {
  localId: string;
  name: string;
  status: "uploading" | "done" | "error";
  fileId?: string;
  error?: string;
}

function UploadZone({
  title,
  slots,
  onPick,
  onRemove,
}: {
  title: string;
  slots: Slot[];
  onPick: (files: FileList) => void;
  onRemove: (localId: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="card">
      <h2 className="font-semibold">{title}</h2>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="mt-4 flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 py-10 text-center transition hover:border-brand-500 hover:bg-brand-50/50 dark:border-slate-700 dark:hover:bg-slate-800/50"
      >
        <UploadCloud className="h-10 w-10 text-slate-400" />
        <p className="mt-3 text-sm text-slate-500">Click to browse</p>
        <p className="mt-1 text-xs text-slate-400">PDF · DOCX · PNG · JPG · TIFF</p>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.length) onPick(e.target.files);
          e.target.value = "";
        }}
      />
      {slots.length > 0 && (
        <ul className="mt-4 space-y-2">
          {slots.map((s) => (
            <li
              key={s.localId}
              className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-slate-700"
            >
              <span className="flex items-center gap-2 truncate">
                <FileText className="h-4 w-4 shrink-0 text-slate-400" />
                <span className="truncate">{s.name}</span>
              </span>
              <span className="flex items-center gap-2">
                {s.status === "uploading" && (
                  <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                )}
                {s.status === "done" && (
                  <span className="text-xs text-emerald-600">ready</span>
                )}
                {s.status === "error" && (
                  <span className="text-xs text-rose-600">{s.error || "failed"}</span>
                )}
                <button onClick={() => onRemove(s.localId)} aria-label="Remove">
                  <X className="h-4 w-4 text-slate-400 hover:text-rose-600" />
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function VerifyPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [refSlots, setRefSlots] = useState<Slot[]>([]);
  const [tgtSlots, setTgtSlots] = useState<Slot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handlePick(
    files: FileList,
    setSlots: React.Dispatch<React.SetStateAction<Slot[]>>
  ) {
    Array.from(files).forEach((file) => {
      const localId = `${file.name}-${Date.now()}-${Math.random()}`;
      setSlots((prev) => [
        ...prev,
        { localId, name: file.name, status: "uploading" },
      ]);
      uploadFile<FileInfo>(file)
        .then((info) =>
          setSlots((prev) =>
            prev.map((s) =>
              s.localId === localId ? { ...s, status: "done", fileId: info.id } : s
            )
          )
        )
        .catch((err) =>
          setSlots((prev) =>
            prev.map((s) =>
              s.localId === localId
                ? { ...s, status: "error", error: err.message }
                : s
            )
          )
        );
    });
  }

  const refIds = refSlots.filter((s) => s.fileId).map((s) => s.fileId!);
  const tgtIds = tgtSlots.filter((s) => s.fileId).map((s) => s.fileId!);
  const uploading = [...refSlots, ...tgtSlots].some((s) => s.status === "uploading");
  const canSubmit =
    refIds.length > 0 && tgtIds.length > 0 && !uploading && title.trim().length > 0;

  async function onSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      const v = await apiFetch<VerificationDetail>("/verifications", {
        method: "POST",
        body: {
          title: title.trim(),
          reference_file_ids: refIds,
          target_file_ids: tgtIds,
        },
      });
      router.push(`/dashboard/verify/${v.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start verification");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">New Verification</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          Upload reference and target documents. Papery extracts and compares
          every field.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-900/30 dark:text-rose-300">
          {error}
        </div>
      )}

      <div className="card">
        <label className="label" htmlFor="title">Verification title</label>
        <input
          id="title"
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Booking vs Draft B/L"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <UploadZone
          title="Reference documents"
          slots={refSlots}
          onPick={(f) => handlePick(f, setRefSlots)}
          onRemove={(id) => setRefSlots((p) => p.filter((s) => s.localId !== id))}
        />
        <UploadZone
          title="Target document(s)"
          slots={tgtSlots}
          onPick={(f) => handlePick(f, setTgtSlots)}
          onRemove={(id) => setTgtSlots((p) => p.filter((s) => s.localId !== id))}
        />
      </div>

      <div className="flex justify-end">
        <button onClick={onSubmit} className="btn-primary" disabled={!canSubmit || submitting}>
          {submitting ? "Starting…" : "Verify ▶"}
        </button>
      </div>
    </div>
  );
}
